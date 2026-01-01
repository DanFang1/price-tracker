from database import get_connection
import scraper as scraper

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