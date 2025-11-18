from playwright.sync_api import sync_playwright, TimeoutError

url = input('Enter the URL: ')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # False --> see the browser
    page = browser.new_page()
    page.goto(url)
    try:
        page.wait_for_timeout(5000)  # Wait 5 seconds for dynamic content
        print(page.content())  # Print the HTML content for inspection
        price_element = page.query_selector('span.price.font-semibold.my-auto.text-2xl')
        item_name = page.query_selector('#product-title') # Example XPath selector for title
        if item_name:
            name = item_name.inner_text()
            name_found = name.strip()
            print(name_found)
        else:
            print("Item name element not found. Check the selector.")
        if price_element:
            price = price_element.inner_text()
            price_found = price.strip()
            print(price_found)
        else:
            print("Price element not found. Check the selector.")
    except Exception as e:
        print("Error:", e)
    finally:
        browser.close()