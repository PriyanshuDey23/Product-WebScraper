import csv
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver(headless_mode):
    """Setup Chrome WebDriver with headless mode option."""
    chrome_options = Options()
    if headless_mode:
        chrome_options.add_argument("--headless=new")  # Use the new headless mode for better performance
    chrome_options.add_argument("--no-sandbox")  
    chrome_options.add_argument("--disable-gpu")  
    chrome_options.add_argument("--window-size=1920x1080")  
    chrome_options.add_argument("--disable-dev-shm-usage")  
    chrome_options.add_argument("--log-level=3")  # Suppress unnecessary logs
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36')

    return webdriver.Chrome(options=chrome_options)

# User inputs
max_pages = int(input("Enter the number of pages to scrape (Enter 0 to scrape all available pages): "))
outputFileName = input("Enter the File Name (without extension): ").strip()
browser_mode = input("Enter 'headless' to run in headless mode, or press Enter for standard mode: ").strip().lower()
headless_mode = browser_mode == 'headless'

# Initialize WebDriver
driver = setup_driver(headless_mode)
url = "https://www.myntra.com/jewellery"

if max_pages == 0:
    max_pages = float('inf')  # Infinite loop until no more pages are available

try:
    page_number = 1
    while True:
        driver.get(url + f"?p={page_number}")
        print(f"Scraping page {page_number}...")

        try:
            products = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "product-base"))
            )
        except TimeoutException:
            print(f"⚠ No more products found. Stopping at page {page_number}.")
            break

        product_data = []
        for product in products:
            try:
                product_details = {
                    "brand": None,
                    "name": None,
                    "actual_price": None,
                    "discounted_price": None,
                    "discount_percentage": None,
                    "rating": None,
                    "product_url": None
                }

                # Extract main product details
                product_details["brand"] = product.find_element(By.CLASS_NAME, "product-brand").text.strip()
                product_details["name"] = product.find_element(By.CLASS_NAME, "product-product").text.strip()
                product_details["actual_price"] = product.find_element(By.CLASS_NAME, "product-strike").text.strip()
                product_details["discounted_price"] = product.find_element(By.CLASS_NAME, "product-discountedPrice").text.strip()
                product_details["discount_percentage"] = product.find_element(By.CLASS_NAME, "product-discountPercentage").text.strip()

                # Optional fields with error handling
                try:
                    product_details["rating"] = product.find_element(By.CLASS_NAME, "product-ratingsContainer").text.strip()
                except NoSuchElementException:
                    product_details["rating"] = "No Rating"

                product_details["product_url"] = product.find_element(By.CSS_SELECTOR, "a[data-refreshpage='true']").get_attribute("href")

                product_data.append(product_details)

            except NoSuchElementException as e:
                print(f"⚠ Skipping a product due to missing field: {e}")

        # Write data to CSV after each page
        mode = 'a' if os.path.exists(outputFileName + ".csv") else 'w'
        with open(outputFileName + ".csv", mode, newline='', encoding="utf-8") as csvfile:
            fieldnames = list(product_details.keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if mode == 'w':
                writer.writeheader()
            writer.writerows(product_data)

        print(f"✅ Data from page {page_number} saved successfully.")
        page_number += 1
        time.sleep(2)  # Small delay to avoid rate limiting

        if page_number > max_pages:
            print("✅ Scraping complete.")
            break

except Exception as e:
    print(f"❌ Error occurred: {e}")

finally:
    driver.quit()
