# app.py
import os
import re
from flask import Flask, session, request, render_template
from auth import login_user, register_user
from database import insert_user_products
from database import get_connection
import scraper as scraper
from flask import redirect

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_KEY")


def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_url(url):
    """Validate URL format"""
    pattern = r'^https?://.+'
    return re.match(pattern, url) is not None


@app.route('/register', methods=['POST'])
def register():
    # Validate required fields
    if 'username' not in request.form or not request.form['username'].strip():
        return render_template('register.html', error="Username is required"), 400
    if 'email' not in request.form or not request.form['email'].strip():
        return render_template('register.html', error="Email is required"), 400
    if 'password' not in request.form or not request.form['password'].strip():
        return render_template('register.html', error="Password is required"), 400
    
    username = request.form['username'].strip()
    email = request.form['email'].strip()
    password = request.form['password']
    
    # Validate username length
    if len(username) < 3 or len(username) > 50:
        return render_template('register.html', error="Username must be between 3 and 50 characters"), 400
    
    # Validate email format
    if not is_valid_email(email):
        return render_template('register.html', error="Invalid email format"), 400
    
    # Validate password strength
    if len(password) < 6:
        return render_template('register.html', error="Password must be at least 6 characters"), 400
    
    try:
        user_id = register_user(username, email, password)
        session['user_id'] = user_id
        return redirect('/dashboard')
    except ValueError as e:
        return render_template('register.html', error=str(e)), 400
    

@app.route('/register', methods=['GET'])
def register_form():
    return render_template('register.html')


@app.route('/login', methods=['POST'])
def login():
    # Validate required fields
    if 'username' not in request.form or not request.form['username'].strip():
        return render_template('login.html', error="Username is required"), 400
    if 'password' not in request.form or not request.form['password'].strip():
        return render_template('login.html', error="Password is required"), 400
    
    username = request.form['username'].strip()
    password = request.form['password']
    
    try:
        user_id = login_user(username, password)
        session['user_id'] = user_id
        return redirect('/dashboard')
    except ValueError as e:
        return render_template('login.html', error=str(e)), 401
    

@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')


@app.route('/add_product', methods=['POST'])
def add_product():
    query1 = """
    UPDATE usertrackeditems SET notified = FALSE WHERE user_item_id = %s;
    """

    user_id = session.get('user_id')
    
    if not user_id:
        return "Not logged in", 401
    
    # Validate required fields
    if 'product_url' not in request.form or not request.form['product_url'].strip():
        return render_template('add_product.html', error="Product URL is required"), 400
    if 'target_price' not in request.form or not request.form['target_price'].strip():
        return render_template('add_product.html', error="Target price is required"), 400
    
    product_url = request.form['product_url'].strip()
    
    # Validate URL format
    if not is_valid_url(product_url):
        return render_template('add_product.html', error="Invalid URL format. URL must start with http:// or https://", 
                             product_url=product_url), 400
    
    # Validate target price is a valid number
    try:
        target_price = float(request.form['target_price'])
    except ValueError:
        return render_template('add_product.html', error="Target price must be a valid number",
                             product_url=product_url), 400
    
    # Validate target price is positive
    if target_price <= 0:
        return render_template('add_product.html', error="Target price must be greater than 0",
                             product_url=product_url), 400

    product = scraper.return_dict(product_url)
    current_price = product["product_price"]

    if target_price >= current_price:
        return render_template('add_product.html', 
                             error="Target price must be less than current price",
                             product_url=product_url,
                             current_price=current_price), 400

    user_item_id = insert_user_products(user_id, product_url, target_price)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query1, (user_item_id,))
            conn.commit()

    return "Product added"


@app.route('/add_product', methods=['GET'])
def add_product_form():
    return render_template('add_product.html')


@app.route('/delete_product', methods=['POST'])
def delete_product():
    user_id = session.get('user_id')
    
    if not user_id:
        return "Not logged in", 401
    
    # Get the product ID from the request
    if 'product_id' not in request.form:
        return "Product ID is required", 400
    
    try:
        product_id = int(request.form['product_id'])
    except ValueError:
        return "Invalid product ID", 400
    
    # Verify the product belongs to the user before deleting
    query_verify = """
    SELECT 1 FROM usertrackeditems 
    WHERE user_item_id = %s AND utt_user_id = %s;
    """
    
    query_delete = "DELETE FROM usertrackeditems WHERE user_item_id = %s;"
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check ownership
            cur.execute(query_verify, (product_id, user_id))
            if not cur.fetchone():
                return "Product not found or unauthorized", 403
            
            # Delete the product
            cur.execute(query_delete, (product_id,))
            conn.commit()
    
    return "Product deleted successfully"


@app.route('/dashboard', methods=['GET'])
def dashboard():
    user_id = session.get('user_id')

    if not user_id:
        return "Not logged in", 401
    
    # Query database for user's products
    query = """
    SELECT ut.user_item_id, p.product_name, p.current_price, ut.target_price
    FROM usertrackeditems ut
    JOIN products p ON ut.user_item_id = p.product_id
    WHERE ut.utt_user_id = %s
    """
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (user_id,))
            products = cur.fetchall()
    
    return render_template('dashboard.html', products=products)


@app.route('/price_graph', methods=['GET'])
def price_graph():
    from price_history import createGraph
    
    product_id = request.args.get('product_id')
    product_name = request.args.get('product_name')
    
    if not product_id or not product_name:
        return "Product ID and name are required", 400
    
    try:
        product_id = int(product_id)
    except ValueError:
        return "Invalid product ID", 400
    
    # Create and display the graph
    createGraph(product_id, product_name)


if __name__ == '__main__':
    app.run(debug=True)