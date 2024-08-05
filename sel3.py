import time
import json
import os
import re
import math
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException

# Set up Chrome options
options = Options()
options.binary_location = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'  # Update this path if needed
options.add_argument("--incognito")  # Run in incognito mode
# options.add_argument("--headless")  # Run in headless mode (optional)
options.add_argument('--window-size=1920,1080')

# Function to initialize the Chrome driver
def init_driver():
    return webdriver.Chrome(options=options)

# Initialize the Chrome driver
driver = init_driver()

# Start the timer for the whole process
process_start_time = time.time()

if not os.path.exists('products_details.json'):

    # merchent = 'https://www.digikala.com/seller/5a6gg/'
    merchent = 'https://www.digikala.com/seller/c7kvk/'
    driver.get(merchent)
    time.sleep(6)

    # Get the total number of pages
    products_num = int(re.sub(r'\D', '', driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[1]/div/div/div/div[3]/span').text))
    page_len = 500 if math.ceil(products_num / 20) > 500 else math.ceil(products_num / 20)

    existing_links = []
    # Load existing data if the file exists
    if os.path.exists('links.json'):
        with open('links.json', 'r', encoding='utf-8') as file:
            existing_links = json.load(file)

    # Get the id of the last item
    last_id = existing_links[-1]['id'] if existing_links else 0

    if page_len <= 10:
        def scroll_to_end(driver):
            action = ActionChains(driver)
            products_num = int(re.sub(r'\D', '', driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[1]/div/div/div/div[3]/span').text))
            getted_num = 0
            while getted_num < products_num:
                # Scroll to the bottom of the product list section
                driver.execute_script("arguments[0].scrollIntoView(true);", driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]/span'))
                time.sleep(1)  # Wait for the new products to load
                getted_num = len(driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]').find_elements(By.TAG_NAME, 'a'))


        # Scroll to the end of the page to load all products
        scroll_to_end(driver)

        new_links = []
        section = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]').find_elements(By.TAG_NAME, 'a')
        for i in range(last_id , len(section)):
            try:
                link = section[i].get_attribute('href')
                new_links.append({'id': i+1, 'link': link})
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

    else:
        # Calculate the start page and the initial id
        start_page = (last_id // 20) + 1  # Assuming each page has up to 20 links
        current_id = last_id

        driver.get(f'{merchent}?page={start_page}')
        time.sleep(6)

        def extract_links(start_id):
            new_links = []
            elements = driver.find_elements(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]//a')
            for i, element in enumerate(elements):
                link = element.get_attribute('href')
                new_links.append({
                    'id': start_id + i + 1,  # Start ids from start_id + 1
                    'link': link
                })
            return new_links

        for i in range(start_page, page_len + 1):
            if i > start_page:
                try:
                    next_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]/div[21]/div/div[3]')))
                    driver.execute_script("arguments[0].scrollIntoView();", next_btn)
                    next_btn.click()
                except ElementClickInterceptedException:
                    next_btn.click()

            # Attempt to extract links, with retries to handle stale element references
            retry_count = 0
            max_retries = 3
            while retry_count < max_retries:
                try:
                    new_links = extract_links(current_id)
                    links = existing_links.extend(new_links) 
                    current_id += len(new_links)  # Update the global id counter
                    break  # If extraction is successful, exit the retry loop
                except StaleElementReferenceException:
                    retry_count += 1
                    time.sleep(2)  # Wait a bit before retrying

            # Save the current state to the JSON file
            with open('links.json', 'w', encoding='utf-8') as file:
                json.dump(existing_links, file, ensure_ascii=False, indent=2)

        print(f"Total number of links: {current_id}")

# Function to extract product details
def product_details(driver, url):
    driver.get(url)
    time.sleep(4)  # Wait for the page to load

    try:
        product_group = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[2]/div[1]/nav/div/div/div[1]').text
        product_group = product_group.replace("دیجی‌کالا/\n", "").replace("/\n", ">")
        # product_group = product_group.rsplit(">", 1)[0]
    except:
        product_group = None

    try:
        title = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[2]/div[2]/div[2]/div[1]/div/h1').text
    except:
        title = None
    try:
        price = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[2]/div[2]/div[2]/div[2]/div[4]/div/div[4]/div/div/div/div[1]/div[2]/div[1]/span').text
        persian_to_english_digits = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
        price = re.sub(r'\D', '', price).translate(persian_to_english_digits)
        stock = 1
    except:
        price = None
        stock = 0

    try:
        main_pic_link = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/div/picture/img').get_attribute('src')
        main_pic_alt = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[2]/div[2]/div[2]/div[1]/div/h1').text
        main_pic_link = main_pic_link.replace("?x-oss-process=image/resize,m_lfit,h_800,w_800/quality,q_90", "")
    except:
        main_pic_link = None
        main_pic_alt = None

    try:
        main_pic = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/div/picture/img')
        main_pic.click()
        time.sleep(1)
        gallery = []
        for i in range(2, 21):
            try:
                # Locate the image elements within the current slide
                images = driver.find_elements(By.CSS_SELECTOR, f'div.bg-white:nth-child(1) > div:nth-child({i}) > div:nth-child(1) > picture:nth-child(1) > img:nth-child(3)')
                # Extract the src attribute (URL) from each image element
                for img in images:
                    gallery.append(img.get_attribute('src').replace("?x-oss-process=image/resize,m_lfit,h_800,w_800/quality,q_90", ""))
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

    # Close the driver
    driver.quit()

    # Print the total time taken
    process_end_time = time.time()
    print(f'Total time taken: {process_end_time - process_start_time} seconds')