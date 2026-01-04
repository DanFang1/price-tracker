# app.py
import os
from flask import Flask, session, request, render_template
from auth import login_user, register_user
from database import insert_user_products
from database import get_connection
import scraper as scraper


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_KEY")


@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    
    try:
        user_id = register_user(username, email, password)
        session['user_id'] = user_id
        return "Registered successfully"
    except ValueError as e:
        return render_template('register.html', error=str(e))


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    try:
        user_id = login_user(username, password)
        session['user_id'] = user_id
        return "Logged in successfully"
    except ValueError as e:
        return render_template('login.html', error=str(e))


@app.route('/add_product', methods=['POST'])
def add_product():
    query1 = """
    UPDATE usertrackeditems SET notified = FALSE WHERE user_item_id = %s;
    """

    user_id = session.get('user_id')
    
    if not user_id:
        return "Not logged in", 401
    
    product_url = request.form['product_url']
    target_price = float(request.form['target_price'])

    product = scraper.return_dict(product_url)
    current_price = product["product_price"]

    if target_price >= current_price:
        return render_template('add_product.html', 
                             error="Target price must be less than current price",
                             product_url=product_url,
                             current_price=current_price)

    insert_user_products(user_id, product_url, target_price)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query1, (user_id,))
            conn.commit()

    return "Product added"


if __name__ == '__main__':
    app.run(debug=True)