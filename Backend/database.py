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


def insert_products():
    "Inserts a new product into the products tabke based on user input URL"
    product = scraper.return_dict(input("Enter the URL: "))
    
    query = sql.SQL(
        """
        INSERT INTO products (product_name, current_price, product_url)
        VALUES (%s, %s, %s)
        RETURNING product_id;
        """
    )
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(query, (product["product_name"], product["current_price"], product["product_url"]))
                product_id = cur.fetchone()[0]
                conn.commit()
                print(f"Product inserted with ID: {product_id}")
            except IntegrityError as e:
                conn.rollback()
                print(f"Error inserting product: {e}")
    

def check_connection():
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
                

