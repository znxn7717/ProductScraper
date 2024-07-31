import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import time
import json
import os

# Set up Firefox options
options = Options()
options.binary_location = 'C:\\Program Files\\Mozilla Firefox\\firefox.exe'  # Update this path if needed
# options.add_argument("--headless")  # Run in headless mode (optional)

# Specify the path to the geckodriver
geckodriver_path = 'C:\\geckodriver.exe'  # Update this path

# Set up the Firefox service
service = Service(geckodriver_path)

# Initialize the Firefox driver
driver = webdriver.Firefox(service=service, options=options)

# Start the timer
start_time = time.time()

if not os.path.exists('products_details.json'):

    # Open the website
    driver.get('https://basalam.com/khaneyesalamat')

    # Function to scroll to the end of the page
    def scroll_to_end(driver):
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2.5)  # Wait for the page to load
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    # Scroll to the end of the page to load all products
    scroll_to_end(driver)

    # Load existing links from JSON file
    existing_links = []
    if os.path.exists('links.json'):
        with open('links.json', 'r', encoding='utf-8') as file:
            existing_links = json.load(file)

    # Get the id of the last item
    last_id = existing_links[-1]['id'] if existing_links else 0

    # Extract the href of the link in the first div of each section
    new_links = []
    section = driver.find_elements(By.XPATH, '/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div')
    for i in range(last_id + 1, len(section) + 1):
        try:
            # Find the first div within the section
            link = driver.find_element(By.XPATH, f'/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div[{i}]/div[1]/a').get_attribute('href')
            new_links.append({'id': i, 'link': link})
        except Exception as e:
            print(f"Error occurred at link {i}: {e}")
            continue

    # Combine existing links with new links
    links = existing_links + new_links

    # Create a DataFrame from the combined list of links with IDs
    df = pd.DataFrame(links)

    # Print the number of links found
    print(f"Total number of links: {len(df)}")

    # Save the DataFrame to a JSON file using the json library
    with open('links.json', 'w', encoding='utf-8') as file:
        json.dump(links, file, ensure_ascii=False, indent=2)

# Function to extract product details
def product_details(driver, url):
    driver.get(url)
    time.sleep(2)  # Wait for the page to load

    try:
        product_group = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/div/div').text
    except:
        product_group = None

    try:
        title = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[1]/div[1]/div/div/div[2]/div[1]/div[1]/h1').text
    except:
        title = None

    try:
        stock = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[2]/div/div[2]/div/div[2]/div[1]/span').text
    except:
        stock = None

    try:
        price = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[2]/div/div[2]/div/div[2]/div[1]/div/span').text
    except:
        price = None

    try:
        main_pic_element = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[1]/div[1]/div/div/div[1]/div/div[1]/div/div/div[1]/div[1]/div/div/div/img')
        main_pic_link = main_pic_element.get_attribute('src')
        main_pic_alt = main_pic_element.get_attribute('alt')
    except:
        main_pic_link = None
        main_pic_alt = None

    return {
        'product_group': product_group,
        'title': title,
        'stock': stock,
        'price': price,
        'main_pic_link': main_pic_link,
        'main_pic_alt': main_pic_alt
    }

# Load existing links from JSON file
existing_links = []
if os.path.exists('links.json'):
    with open('links.json', 'r', encoding='utf-8') as file:
        existing_links = json.load(file)

    # Load existing product details from JSON file
    existing_products_details = []
    if os.path.exists('products_details.json'):
        with open('products_details.json', 'r', encoding='utf-8') as file:
            existing_products_details = json.load(file)

    # Get the id of the last processed item
    last_id = existing_products_details[-1]['id'] if existing_products_details else 0

    # Extract details for new links only
    new_products_details = []
    for item in existing_links:
        if item['id'] > last_id:
            details = product_details(driver, item['link'])
            details['id'] = item['id']
            details['link'] = item['link']
            new_products_details.append(details)
            # Save details incrementally to prevent data loss
            with open('products_details.json', 'w', encoding='utf-8') as file:
                products_details = existing_products_details + new_products_details
                json.dump(products_details, file, ensure_ascii=False, indent=2)

    # Close the browser
    driver.quit()

    # End the timer
    end_time = time.time()

    # Calculate the elapsed time
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time} seconds")