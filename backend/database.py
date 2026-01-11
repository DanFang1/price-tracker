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


def insert_user_products(user_id, product_url, target_price):
    """""Inserts a new product into the products table based on product URL, then links to user.
    Uses INSERT...ON CONFLICT to safely handle multiple concurrent processes."""
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                # Fetch product data
                product = scraper.return_dict(product_url)
                
                # Atomically insert product or get existing one using ON CONFLICT
                # This prevents race conditions when multiple processes insert simultaneously
                upsert_query = sql.SQL(
                    """
                    INSERT INTO products (product_url, product_name, current_price)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (product_url) 
                    DO UPDATE SET current_price = EXCLUDED.current_price
                    RETURNING product_id;
                    """
                )
                cur.execute(upsert_query, (product["product_url"], product["product_name"], product["product_price"]))
                product_id = cur.fetchone()[0]
                conn.commit()
                print(f"Product ensured with ID: {product_id}")
                
                # Insert into usertrackeditems (ON CONFLICT handles duplicate user-product pairs)
                user_tracking_query = sql.SQL(
                    """
                    INSERT INTO usertrackeditems (user_item_id, utt_user_id, target_price)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_item_id, utt_user_id) 
                    DO UPDATE SET target_price = EXCLUDED.target_price
                    RETURNING user_item_id;
                    """
                )
                cur.execute(user_tracking_query, (product_id, user_id, target_price))
                user_item_id = cur.fetchone()[0]
                conn.commit()
                print(f"User item upserted for user {user_id}")

                # Insert initial price into price_history if it doesn't exist
                price_history_query = sql.SQL(
                    """
                    INSERT INTO price_history (history_pid, recorded_price)
                    VALUES (%s, %s)
                    ON CONFLICT (history_pid) 
                    DO NOTHING
                    """
                )
                cur.execute(price_history_query, (product_id, product["product_price"]))
                conn.commit()
                
                return user_item_id
                
            except IntegrityError as e:
                conn.rollback()
                print(f"Error inserting product: {e}")
                return None


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
                

