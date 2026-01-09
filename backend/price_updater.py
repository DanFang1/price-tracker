from database import get_connection
import scraper as scraper
from notifications import send_price_alert
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

# Global scheduler instance
_scheduler = None

# Configure logging for APScheduler
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.WARNING)

def price_refresher():
    """Refreshes current prices of all products in the database.
    Runs via cron job without locks - APScheduler ensures only one instance runs."""
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
    except Exception as e:
        print(f"Error in price_refresher: {e}")


def check_and_notify_targets():
    """Check for products that hit target prices and notify users.
    Runs via cron job without locks - APScheduler ensures only one instance runs."""
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
    except Exception as e:
        print(f"Error in check_and_notify_targets: {e}")


def reset_notified_prices():
    """Reset notified flag if price went up above target.
    Runs via cron job without locks - APScheduler ensures only one instance runs."""
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
    except Exception as e:
        print(f"Error in reset_notified_prices: {e}")


def get_scheduler():
    """Get the current scheduler instance"""
    return _scheduler


def start_scheduler():
    """Initialize and start the background scheduler with cron-based jobs.
    
    Jobs:
    - price_refresher: Runs every 30 minutes at :00 and :30
    - check_and_notify_targets: Runs every 30 minutes at :00 and :30
    - reset_notified_prices: Runs every hour at :00
    """
    global _scheduler
    
    if _scheduler is not None and _scheduler.running:
        print("Scheduler already running")
        return _scheduler
    
    _scheduler = BackgroundScheduler()
    
    # Price refresher: Every 30 minutes (at :00 and :30)
    _scheduler.add_job(
        price_refresher, 
        CronTrigger(minute='0,30'),
        id='price_refresher',
        name='Price Refresher',
        replace_existing=True
    )
    
    # Check and notify targets: Every 30 minutes (at :00 and :30)
    _scheduler.add_job(
        check_and_notify_targets, 
        CronTrigger(minute='0,30'),
        id='check_targets',
        name='Check and Notify Targets',
        replace_existing=True
    )
    
    # Reset notified prices: Every hour at :00
    _scheduler.add_job(
        reset_notified_prices, 
        CronTrigger(minute='0'),
        id='reset_notified',
        name='Reset Notified Prices',
        replace_existing=True
    )
    
    _scheduler.start()
    print("Scheduler started with cron-based jobs")
    
    return _scheduler