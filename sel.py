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
link_list = []
section = driver.find_elements(By.XPATH, '/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div')
for i in range(last_id + 1, len(section) + 1):
    try:
        # Find the first div within the section
        link = driver.find_element(By.XPATH, f'/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div[{i}]/div[1]/a').get_attribute('href')
        link_list.append({'id': i, 'link': link})
    except Exception as e:
        print(f"Error occurred at link {i}: {e}")
        continue

# Combine existing links with new links
combined_links = existing_links + link_list

# Create a DataFrame from the combined list of links with IDs
df = pd.DataFrame(combined_links)

# Print the DataFrame
print(df.tail())

# Print the number of links found
print(f"Total number of links: {len(df)}")

# Save the DataFrame to a JSON file using the json library
with open('links.json', 'w', encoding='utf-8') as file:
    json.dump(combined_links, file, ensure_ascii=False, indent=2)

# Close the browser
driver.quit()

# End the timer
end_time = time.time()

# Calculate the elapsed time
elapsed_time = end_time - start_time
print(f"Elapsed time: {elapsed_time} seconds")