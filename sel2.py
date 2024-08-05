import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import json
import os
import re

# Set up Firefox options
options = Options()
options.binary_location = 'C:\\Program Files\\Mozilla Firefox\\firefox.exe'  # Update this path if needed
options.add_argument("--private")  # Run in incognito mode
# options.add_argument("--headless")  # Run in headless mode (optional)
# options.add_argument('--window-size=1920,1080')

# Specify the path to the geckodriver
geckodriver_path = '/geckodriver.exe'  # Update this path

# Function to initialize the Firefox driver
def init_driver():
    service = Service(geckodriver_path)
    return webdriver.Firefox(service=service, options=options)

# Initialize the Firefox driver
driver = init_driver()

# Start the timer for the whole process
process_start_time = time.time()

if not os.path.exists('products_details.json'):

    # Open the website
    driver.get('https://torob.com/shop/5566/%D8%B2%D8%B1%D9%BE%D9%88%D8%B4%D8%A7%D9%86/%D9%85%D8%AD%D8%B5%D9%88%D9%84%D8%A7%D8%AA/')

    def scroll_to_end(driver):
        action = ActionChains(driver)
        while True:
            try:
                driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div/div[2]/div/div[2]/div[2]/div/div[2]')
                action.scroll_by_amount(0, 10000).perform()  # Scroll down by 1000 pixels
                time.sleep(.1)  # Wait for the page to load
            except:
                break

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
    section = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div/div[2]/div/div[2]/div[2]/div/div[1]/div').find_elements(By.TAG_NAME, 'a')

    for i in range(1, len(section) + 1):
        try:
            # Find the first div within the section
            link = driver.find_element(By.XPATH, f'/html/body/div/div/div[2]/div/div/div/div[2]/div/div[2]/div[2]/div/div[1]/div/div[{i}]/a').get_attribute('href')
            new_links.append({'id': i, 'link': link})
        except Exception as e:
            print(f"Error occurred at link {i}: {e}")
            continue

    # Combine existing links with new links
    links = existing_links + new_links

    # Create a DataFrame from the combined list of links with IDs
    df = pd.DataFrame(links)

    # Print the number of child <div> elements
    print(f"Total number of links: {len(df)}")

    # Save the DataFrame to a JSON file using the json library
    with open('links.json', 'w', encoding='utf-8') as file:
        json.dump(links, file, ensure_ascii=False, indent=2)

# Function to extract product details
def product_details(driver, url):
    driver.get(url)
    time.sleep(1)  # Wait for the page to load

    try:
        product_group = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div[2]/div/div[1]/div[1]/div/div').text
        product_group = product_group.replace("ترب\n", "").replace("\n", ">")
        product_group = product_group.rsplit(">", 1)[0]
    except:
        product_group = None

    try:
        title = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[2]/h1').text
    except:
        title = None
    try:
        price = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[4]/a/div/div[1]/div[2]').text
        persian_to_english_digits = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
        price = re.sub(r'\D', '', price).translate(persian_to_english_digits)
        stock = 1
    except:
        price = None
        stock = 0
    try:
        main_pic_link = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div[2]/div/div[2]/div[1]/div/div/div[1]/div/div/div[2]/picture/img').get_attribute('src')
        main_pic_alt = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[2]/h1').text
        main_pic_link = main_pic_link.replace("_/280x280.jpg", "")
    except:
        main_pic_link = None
        main_pic_alt = None
    try:
        # Click on the first image to open the gallery
        gallery_len = len(driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div[2]/div/div[2]/div[1]/div/div/div[1]/div/div/div[1]').find_elements(By.XPATH, './div'))
        if gallery_len == 4:
            div_4_element = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div[2]/div/div[2]/div[1]/div/div/div[1]/div/div/div[1]/div[4]/div').text
            move_len = int(re.sub(r'\D', '', div_4_element)) + 3
        else:
            move_len = gallery_len
        main_pic = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div[2]/div/div[2]/div[1]/div/div/div[1]/div/div/div[2]/picture/img')
        main_pic.click()
        time.sleep(3)
        # List to store image URLs
        gallery = []
        for i in range(1, move_len):
            try:
                # Locate the image elements within the current slide
                driver.find_element(By.XPATH, '/html/body/div[4]/div/div/div/button[2]').click()
                time.sleep(.5)
                image = driver.find_element(By.XPATH, '/html/body/div[4]/div/div/div/div[1]/img[2]').get_attribute('src')
                gallery.append(image)
            except Exception as e:
                print(f'Error processing gallery {i}: {e}')
    except:
        gallery = None


    # Create the dictionary with the desired order
    product_details_dict = {
        'id': id,
        'link': url,
        'product_group': product_group,
        'title': title,
        'stock': stock,
        'price': price,
        'main_pic_link': main_pic_link,
        'main_pic_alt': main_pic_alt,
        'gallery': gallery
    }

    return product_details_dict

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
            start_time = time.time()  # Start time for the product details extraction
            details = product_details(driver, item['link'])
            details['id'] = item['id']
            details['link'] = item['link']
            new_products_details.append(details)
            # Save details incrementally to prevent data loss
            with open('products_details.json', 'w', encoding='utf-8') as file:
                products_details = existing_products_details + new_products_details
                json.dump(products_details, file, ensure_ascii=False, indent=2)
                end_time = time.time()  # End time for the product details extraction

            elapsed_time = end_time - start_time

            # If extracting details takes more than 8 seconds, restart the driver
            if elapsed_time > 15:
                print(f"Product details extraction took too long ({elapsed_time} seconds). Restarting driver...")
                driver.quit()
                driver = init_driver()

# Close the browser
driver.quit()

# End the timer for the whole process
process_end_time = time.time()

# Calculate the elapsed time for the whole process
process_elapsed_time = process_end_time - process_start_time
print(f"Process elapsed time: {process_elapsed_time} seconds")
