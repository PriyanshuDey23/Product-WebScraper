import streamlit as st
import pandas as pd
import time
import os
import csv
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
        chrome_options.add_argument("--headless=new")  # New headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36')
    return webdriver.Chrome(options=chrome_options)

st.title("🔍 Web Scraper for Multiple Websites")
st.sidebar.header("Scraping Options")


# User inputs
urls = st.sidebar.text_area("Enter URLs (comma-separated):")
max_pages = st.sidebar.number_input("Number of pages to scrape (0 for all available):", min_value=0, value=1)
outfile_name = st.sidebar.text_input("Output File Name (without extension):", "scraped_data")
headless_mode = st.sidebar.checkbox("Run in headless mode", True)

start_scraping = st.sidebar.button("Start Scraping")

if start_scraping:
    url_list = [url.strip() for url in urls.split(",") if url.strip()]  # Process comma-separated URLs
    driver = setup_driver(headless_mode)
    all_data = []

    try:
        for url in url_list:
            st.write(f"Scraping data from {url}...")
            page_number = 1
            while True:
                driver.get(url + f"?p={page_number}")
                st.write(f"Scraping page {page_number}...")

                try:
                    products = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, "product-base"))
                    )
                except TimeoutException:
                    st.write(f"⚠ No more products found on {url}. Stopping at page {page_number}.")
                    break

                for product in products:
                    try:
                        product_details = {
                            "brand": product.find_element(By.CLASS_NAME, "product-brand").text.strip(),
                            "name": product.find_element(By.CLASS_NAME, "product-product").text.strip(),
                            "actual_price": product.find_element(By.CLASS_NAME, "product-strike").text.strip(),
                            "discounted_price": product.find_element(By.CLASS_NAME, "product-discountedPrice").text.strip(),
                            "discount_percentage": product.find_element(By.CLASS_NAME, "product-discountPercentage").text.strip(),
                            "rating": "No Rating",
                            "product_url": product.find_element(By.CSS_SELECTOR, "a[data-refreshpage='true']").get_attribute("href")
                        }

                        try:
                            product_details["rating"] = product.find_element(By.CLASS_NAME, "product-ratingsContainer").text.strip()
                        except NoSuchElementException:
                            pass

                        all_data.append(product_details)
                    except NoSuchElementException as e:
                        st.write(f"⚠ Skipping a product due to missing field: {e}")

                st.write(f"✅ Data from page {page_number} scraped successfully.")
                page_number += 1
                time.sleep(2)

                if max_pages > 0 and page_number > max_pages:
                    break

    except Exception as e:
        st.error(f"❌ Error occurred: {e}")
    finally:
        driver.quit()

    # Save to CSV
    if all_data:
        df = pd.DataFrame(all_data)
        csv_path = f"{outfile_name}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')
        st.success("✅ Scraping complete! Download your data below.")
        st.download_button("Download CSV", open(csv_path, "rb"), f"{outfile_name}.csv", "text/csv")
    else:
        st.warning("No data was scraped. Check the URLs and try again.")
