from database import get_connection
import scraper as scraper
from notifications import send_price_alert

def price_refresher():
    "Refreshes current prices of all products in the database"
    select_query = "SELECT product_url from products;"
    check_query = "SELECT current_price from products WHERE product_url = %s;"
    update_query = "UPDATE products SET current_price = %s WHERE product_url = %s;"
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(select_query)
            urls_list = cur.fetchall()

            for (product_urls, ) in urls_list:
                new_price = scraper.return_dict(product_urls)["product_price"]
                cur.execute(check_query, (product_urls,))
                old_price = cur.fetchone()[0]
                if new_price != old_price:
                    cur.execute(update_query, (new_price, product_urls))
                    conn.commit()
                    print(f"Price updated for {product_urls}")


def check_and_notify_targets():
    query = """
    SELECT u.email, p.product_url, p.current_price, ut.target_price, p.product_name
    FROM usertrackeditems ut
    JOIN products p ON ut.product_id = p.id
    JOIN users u ON ut.user_id = u.id
    WHERE p.current_price <= ut.target_price AND ut.notified = FALSE;
    """
    
    update_query = "UPDATE usertrackeditems SET notified = TRUE WHERE user_id = %s AND product_id = %s;"
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            
            for email, product_url, current_price, target_price, product_name in results:
                send_price_alert(email, product_name, target_price, current_price)
                
                # Get product_id for the update query
                cur.execute("SELECT id FROM products WHERE product_url = %s;", (product_url,))
                product_id = cur.fetchone()[0]
                
                cur.execute("SELECT user_id FROM usertrackeditems WHERE product_id = %s AND user_id = (SELECT id FROM users WHERE email = %s);", (product_id, email))
                user_id = cur.fetchone()[0]
                
                cur.execute(update_query, (user_id, product_id))
                conn.commit()
                print(f"Notification sent to {email} for {product_name}")