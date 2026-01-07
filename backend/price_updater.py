from database import get_connection
import scraper as scraper
from notifications import send_price_alert
from apscheduler.schedulers.background import BackgroundScheduler
import threading
import time

# Global scheduler instance and lock for thread-safe initialization
_scheduler = None
_scheduler_lock = threading.Lock()

# Database-based distributed lock for multi-process coordination
def acquire_distributed_lock(lock_name: str, timeout_seconds: int = 30) -> bool:
    """Acquire a distributed lock in the database. Returns True if lock acquired."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Create locks table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS distributed_locks (
                        lock_name VARCHAR(255) PRIMARY KEY,
                        acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
                
                # Try to insert lock (will fail if already exists)
                cur.execute(
                    "INSERT INTO distributed_locks (lock_name) VALUES (%s);",
                    (lock_name,)
                )
                conn.commit()
                return True
    except Exception as e:
        return False


def release_distributed_lock(lock_name: str) -> bool:
    """Release a distributed lock."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM distributed_locks WHERE lock_name = %s;", (lock_name,))
                conn.commit()
                return True
    except Exception:
        return False

def price_refresher():
    """Refreshes current prices of all products in the database.
    Uses distributed lock to prevent concurrent execution across multiple processes."""
    lock_name = "price_refresher_lock"
    
    # Try to acquire lock; skip if another process is already running
    if not acquire_distributed_lock(lock_name):
        print("Price refresher already running in another process")
        return
    
    try:
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
    finally:
        release_distributed_lock(lock_name)


def check_and_notify_targets():
    """Check for products that hit target prices and notify users.
    Uses distributed lock to prevent duplicate notifications across multiple processes."""
    lock_name = "notify_targets_lock"
    
    # Try to acquire lock; skip if another process is already running
    if not acquire_distributed_lock(lock_name):
        print("Notification check already running in another process")
        return
    
    try:
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
    finally:
        release_distributed_lock(lock_name)


def reset_notified_prices():
    """Reset notified flag if price went up above target.
    Uses distributed lock to prevent duplicate resets across multiple processes."""
    lock_name = "reset_notified_lock"
    
    # Try to acquire lock; skip if another process is already running
    if not acquire_distributed_lock(lock_name):
        print("Reset notified already running in another process")
        return
    
    try:
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
    finally:
        release_distributed_lock(lock_name)


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
        # max_instances=1: prevents overlapping executions if job takes too long
        # coalesce=True: skips queued runs if scheduler falls behind
        # misfire_grace_time=60: allows up to 60 seconds late before skipping
        _scheduler.add_job(
            price_refresher, 
            'interval', 
            minutes=30, 
            id='price_refresher',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60
        )
        
        # Check and notify every 30 minutes
        _scheduler.add_job(
            check_and_notify_targets, 
            'interval', 
            minutes=30, 
            id='check_targets',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60
        )
        
        # Reset notified prices every hour
        _scheduler.add_job(
            reset_notified_prices, 
            'interval', 
            minutes=60, 
            id='reset_notified',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60
        )
        
        _scheduler.start()
    
    return _scheduler
