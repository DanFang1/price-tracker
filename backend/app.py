# app.py
from flask import Flask, session, request
from auth import login_user
from database import insert_user_products

app = Flask(__name__)
app.secret_key = ""

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    try:
        user_id = login_user(username, password)
        session['user_id'] = user_id
        return "Logged in successfully"
    except ValueError as e:
        return str(e)

@app.route('/add_product', methods=['POST'])
def add_product():
    user_id = session.get('user_id')
    
    if not user_id:
        return "Not logged in", 401
    
    product_url = request.form['product_url']
    insert_user_products(user_id, product_url)
    return "Product added"

if __name__ == '__main__':
    app.run(debug=True)