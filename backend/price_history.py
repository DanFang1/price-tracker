import matplotlib.pyplot as plt
from database import get_connection


def createGraph(history_pid, title):
    """Creates a line graph for the price history of a product."""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT time_change, recorded_price FROM price_history WHERE history_pid = %s 
        UNION ALL
        SELECT CURRENT_DATE::timestamp, (SELECT current_price FROM products WHERE product_id = %s)
        ORDER BY time_change ASC
    """, (history_pid, history_pid))
    
    data = cursor.fetchall()
    date_history = [row[0] for row in data]
    price_history = [row[1] for row in data]

    cursor.close()
    conn.close()

    plt.figure(figsize=(10,5))
    plt.plot(date_history, price_history, marker='o', linestyle = '-', color='b')
    plt.title(f"Price history of {title}")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
