from database import get_connection
import scraper as scraper
from notifications import send_price_alert
from apscheduler.schedulers.background import BackgroundScheduler
import threading

# Global scheduler instance and lock for thread-safe initialization
_scheduler = None
_scheduler_lock = threading.Lock()

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
    """Check for products that hit target prices and notify users"""
    query = """
    SELECT u.email, p.product_url, p.current_price, ut.target_price, p.product_name, ut.user_item_id
    FROM usertrackeditems ut
    JOIN products p ON ut.user_item_id = p.product_id
    JOIN accounts u ON ut.utt_user_id = u.user_id
    WHERE p.current_price <= ut.target_price AND ut.notified = FALSE;
    """
    
    update_query = "UPDATE usertrackeditems SET notified = TRUE WHERE user_item_id = %s;"
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            
            for email, product_url, current_price, target_price, product_name, user_item_id in results:
                send_price_alert(email, product_name, target_price, current_price)
                
                cur.execute(update_query, (user_item_id,))
                conn.commit()
                print(f"Notification sent to {email} for {product_name}")


def reset_notified_prices():
    """Reset notified flag if price went up above target"""
    query = """
    UPDATE usertrackeditems SET notified = FALSE WHERE notified = TRUE 
    AND target_price < (
        SELECT current_price FROM products 
        WHERE products.product_id = usertrackeditems.user_item_id
    );
    """
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()
            print(f"Reset {cur.rowcount} items")


def get_scheduler():
    """Get the current scheduler instance without starting it"""
    return _scheduler


def start_scheduler():
    """Initialize and start the background scheduler for price updates and notifications.
    Uses singleton pattern to prevent multiple schedulers from running concurrently."""
    global _scheduler
    
    # Double-checked locking pattern for thread safety
    if _scheduler is not None and _scheduler.running:
        print("Scheduler already running")
        return _scheduler
    
    with _scheduler_lock:
        # Check again inside the lock in case another thread started it
        if _scheduler is not None and _scheduler.running:
            print("Scheduler already running")
            return _scheduler
        
        _scheduler = BackgroundScheduler()
        
        # Run price refresher every 30 minutes
        _scheduler.add_job(price_refresher, 'interval', minutes=30, id='price_refresher')
        
        # Check and notify every 30 minutes
        _scheduler.add_job(check_and_notify_targets, 'interval', minutes=30, id='check_targets')
        
        # Reset notified prices every hour
        _scheduler.add_job(reset_notified_prices, 'interval', minutes=60, id='reset_notified')
        
        _scheduler.start()
        print("Scheduler started: price updates every 30 minutes")
    
    return _scheduler
