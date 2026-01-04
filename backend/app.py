# app.py
import os
import re
from flask import Flask, session, request, render_template
from auth import login_user, register_user
from database import insert_user_products
from database import get_connection
import scraper as scraper


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
        return "Registered successfully"
    except ValueError as e:
        return render_template('register.html', error=str(e)), 400


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
        return "Logged in successfully"
    except ValueError as e:
        return render_template('login.html', error=str(e)), 401


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

    insert_user_products(user_id, product_url, target_price)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query1, (user_id,))
            conn.commit()

    return "Product added"


if __name__ == '__main__':
    app.run(debug=True)