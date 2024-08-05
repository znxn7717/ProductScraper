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

# Start the timer for whole of process
process_start_time = time.time()

if not os.path.exists('products_details.json'):

    # Open the website
    driver.get('https://basalam.com/arayeshii_artemis')

    # Function to scroll to the end of the page
    def scroll_to_end(driver, max_attempts=25):
        action = ActionChains(driver)
        unchanged_attempts = 0
        last_count = 0
        
        while unchanged_attempts < max_attempts:
            # Get the current number of products
            current_count = len(driver.find_elements(By.XPATH, '/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div'))
            
            if current_count == last_count:
                unchanged_attempts += 1
            else:
                unchanged_attempts = 0
            
            last_count = current_count

            action.scroll_by_amount(0, 10000).perform()  # Scroll down by 10000 pixels
            time.sleep(0.1)  # Wait for the page to load

    # Scroll to the end of the page to load all products
    scroll_to_end(driver)
    time.sleep(3)

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
    time.sleep(1)  # Wait for the page to load

    try:
        product_group = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/div/div').text
        product_group = product_group.replace("خانه\n", "").replace("\n", ">")
        product_group = product_group.rsplit(">", 1)[0]
    except:
        product_group = None

    try:
        title = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[1]/div[1]/div/div/div[2]/div[1]/div[1]/h1').text
    except:
        title = None

    try:
        stock = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[2]/div/div[2]/div/div[2]/div[1]/span').text
        stock = re.search(r'\d+', stock ).group() if stock  else None
    except:
        stock = None

    try:
        price = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[2]/div/div[2]/div/div[2]/div[1]/div/span').text
        price = re.sub(r'\D', '', price)
        stock = int(stock)
    except:
        price = None
        stock = 0

    try:
        main_pic_link = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[1]/div[1]/div/div/div[1]/div/div[1]/div/div/div[1]/div[1]/div/div')
        main_pic_alt = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[1]/div[1]/div/div/div[2]/div[1]/div[1]/h1').text
        
        # Check if there is a video tag within the main_pic_element
        try:
            video_tag = main_pic_link.find_element(By.TAG_NAME, 'video')
            main_pic_link = "video"
        except:
            img_element = main_pic_link.find_element(By.TAG_NAME, 'img')
            main_pic_link = img_element.get_attribute('src')
            main_pic_link = main_pic_link.replace("_512X512X70.jpg", "")
    except:
        main_pic_link = None
        main_pic_alt = None

    try:
        # Click on the first image to open the gallery
        main_pic = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[1]/div[1]/div/div/div[1]/div/div[1]/div/div/div[1]/div[1]/div/div/div/img')
        main_pic.click()
        time.sleep(1)
        # List to store image URLs
        gallery = []
        for i in range(2, 21):
            try:
                # Locate the image elements within the current slide
                images = driver.find_elements(By.XPATH, f'/html/body/div[8]/div/div[1]/div/div/div/div/div/div[2]/div/div[{i}]//img')
                # Extract the src attribute (URL) from each image element
                for img in images:
                    gallery.append(img.get_attribute('src').replace("_256X256X70.jpg", ""))

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
            if elapsed_time > 12:
                print(f"Product details extraction took too long ({elapsed_time} seconds). Restarting driver...")
                driver.quit()
                driver = init_driver()

    # Close the browser
    driver.quit()

    # End the timer for whole of process
    process_end_time = time.time()

    # Calculate the elapsed time for whole of process
    process_elapsed_time = process_end_time - process_start_time
    print(f"Process elapsed time: {process_elapsed_time} seconds")