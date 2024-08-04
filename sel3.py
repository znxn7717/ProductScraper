import time
import json
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, TimeoutException

# Set up Chrome options
options = Options()
options.binary_location = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'  # Update this path if needed
options.add_argument("--incognito")  # Run in incognito mode
# options.add_argument("--headless")  # Run in headless mode (optional)

# Function to initialize the Chrome driver
def init_driver():
    return webdriver.Chrome(options=options)

# Initialize the Chrome driver
driver = init_driver()

# Start the timer for the whole process
process_start_time = time.time()

output_file = 'products_details.json'
all_links = []
last_id = 0

# Load existing data if the file exists
if os.path.exists(output_file):
    with open(output_file, 'r', encoding='utf-8') as file:
        all_links = json.load(file)
    if all_links:
        last_id = all_links[-1]['id']

# Open the website to get the total number of pages
merchent = 'https://www.digikala.com/seller/5a6gg/'
driver.get(f'{merchent}?page=1')
time.sleep(6)

# Get the total number of pages
page_len = int(driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]/div[21]/div/div[2]/span[4]/span').text)

def extract_links(start_id):
    page_links = []
    elements = driver.find_elements(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]//a')
    for idx, element in enumerate(elements):
        href = element.get_attribute('href')
        page_links.append({
            'id': start_id + idx + 1,  # Start ids from start_id + 1
            'href': href
        })
    return page_links

# Calculate the start page and the initial id
start_page = (last_id // 20) + 1  # Assuming each page has up to 20 links
current_id = last_id

# Navigate to the start page
if start_page > 1:
    driver.get(f'{merchent}?page={start_page}')
    time.sleep(6)

def click_next_button():
    retries = 0
    max_retries = 3
    while retries < max_retries:
        try:
            next_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]/div[21]/div/div[3]'))
            )
            driver.execute_script("arguments[0].scrollIntoView();", next_btn)
            next_btn.click()
            time.sleep(6)  # Wait for the new page to load
            return True
        except (ElementClickInterceptedException, TimeoutException):
            retries += 1
            time.sleep(5)  # Wait a bit before retrying
            driver.refresh()  # Refresh the page if the button is not clickable
    return False

for i in range(start_page, page_len + 1):
    if i > start_page:
        success = click_next_button()
        if not success:
            print(f"Failed to click next button after {max_retries} attempts.")
            break

    # Attempt to extract links, with retries to handle stale element references
    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            page_links = extract_links(current_id)
            all_links.extend(page_links)
            current_id += len(page_links)  # Update the global id counter
            break  # If extraction is successful, exit the retry loop
        except StaleElementReferenceException:
            retry_count += 1
            time.sleep(2)  # Wait a bit before retrying

    # Save the current state to the JSON file
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(all_links, file, ensure_ascii=False, indent=4)

# Close the driver
driver.quit()

# Print the total time taken
process_end_time = time.time()
print(f'Total time taken: {process_end_time - process_start_time} seconds')
