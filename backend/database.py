import psycopg2
from psycopg2 import sql, IntegrityError
from dotenv import load_dotenv  
import os
import scraper as scraper

load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')


def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def insert_user_products():
    "Inserts a new product into the products table based on user input URL"
    product = scraper.return_dict(input("Enter the URL: "))
    
    query1 = sql.SQL(
        """
        INSERT INTO products (product_url, product_name, price_history, current_price)
        VALUES (%s, %s, %s, %s)
        RETURNING product_id;
        """
    )
    query2 = sql.SQL(
        """
        INSERT INTO usertrackeditems (user_item_id, product_, price_history, current_price)
        VALUES (%s, %s, %s, %s)
        RETURNING product_id;
        """
    )
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(query1, (product["product_url"], product["product_name"], product["product_price"], product["product_price"]))
                product_id = cur.fetchone()[0]
                conn.commit()
                print(f"Product inserted with ID: {product_id}")
            except IntegrityError as e:
                conn.rollback()
                print(f"Error inserting product: {e}")


def check_duplicate_product(product_url: str) -> bool:
    "Checks if the product already exists in the products table"
    query = "SELECT EXISTS(SELECT 1 FROM usertrackeditems WHERE product_url = %s);"
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (product_url,))
            exists = cur.fetchone()[0]
            return exists
    



def select_price() -> int:
    "User inputs a target price for a product"
    target_price = int(input("Enter your target price: "))
    return target_price


def check_connection() -> bool:
    "Checks if database connection is successful"
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                print("Database successfully connected.")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
                

