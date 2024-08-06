import os
import re
import time
import json
import math
import pandas as pd
from Product import Database
from dotenv import load_dotenv
from selenium import webdriver
from urllib.parse import unquote
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException

class ProductScraper:
    def __init__(self,
                 firefox_driver_path='/geckodriver.exe',
                 chrome_driver_path='/chromedriver.exe',
                 firefox_binary_path='C:\\Program Files\\Mozilla Firefox\\firefox.exe',
                 chrome_binary_path='C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                 window_size='--window-size=1920,1080',
                 incognito_mode=True,
                 headless_mode=False):
        self.firefox_driver_path = firefox_driver_path
        self.chrome_driver_path = chrome_driver_path
        self.firefox_binary_path = firefox_binary_path
        self.chrome_binary_path = chrome_binary_path
        self.window_size = window_size
        self.incognito_mode = incognito_mode
        self.headless_mode = headless_mode
        self.db = Database()
        self.db.product_connect()

    def init_firefox_driver(self):
        service = Service(self.firefox_driver_path)
        options = FirefoxOptions()
        options.binary_location = self.firefox_binary_path
        options.add_argument(self.window_size)
        if self.incognito_mode:
            options.add_argument("--private")
        if self.headless_mode:
            options.add_argument("--headless")
        return webdriver.Firefox(service=service, options=options)

    def init_chrome_driver(self):
        options = ChromeOptions()
        options.binary_location = self.chrome_binary_path
        options.add_argument(self.window_size)
        if self.incognito_mode:
            options.add_argument("--incognito")
        if self.headless_mode:
            options.add_argument("--headless")
        return webdriver.Chrome(options=options)

    def reset_driver(self, driver):
        print("Resetting driver...")
        driver.quit()
        if self.firefox_driver_path:
            return self.init_firefox_driver()
        elif self.chrome_driver_path:
            return self.init_chrome_driver()
        else:
            raise ValueError("No driver path specified.")

    def write_json(self, prefix, type, data):
        with open(f'{prefix}_{type}.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def read_json(self, prefix, type):
        with open(f'{prefix}_{type}.json', 'r', encoding='utf-8') as file:
            return json.load(file)

    def basalam_scroll_to_end(self, driver, max_attempts=25):
        action = ActionChains(driver)
        unchanged_attempts = 0
        last_count = 0
        while unchanged_attempts < max_attempts:
            current_count = len(driver.find_elements(By.XPATH, '/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div'))
            if current_count == last_count:
                unchanged_attempts += 1
            else:
                unchanged_attempts = 0
            last_count = current_count
            action.scroll_by_amount(0, 10000).perform()

    def basalam_links_extractor(self, seller_url, driver='firefox'):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        seller_id = seller_url.rstrip('/').split('/')[-1]
        if not os.path.exists(f'{seller_id}_products_details.json'):
            existing_links = []
            if os.path.exists(f'{seller_id}_links.json'):
                existing_links = self.read_json(prefix=seller_id, type='links')
            last_id = existing_links[-1]['id'] if existing_links else 0
            driver.get(seller_url)
            self.basalam_scroll_to_end(driver)
            time.sleep(3)
            new_links = []
            section = driver.find_elements(By.XPATH, '/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div')
            for i in range(last_id + 1, len(section) + 1):
                try:
                    link = driver.find_element(By.XPATH, f'/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div[{i}]/div[1]/a').get_attribute('href')
                    new_links.append({'id': i, 'link': link})
                except Exception as e:
                    print(f"Error occurred at link {i}: {e}")
                    continue
            links = existing_links + new_links
            df = pd.DataFrame(links)
            print(f"Total number of links: {len(df)}")
            self.write_json(prefix=seller_id, type='links', data=links)

    def basalam_product_details_dict(self, product_url, driver='firefox'):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        driver.get(product_url)
        time.sleep(2)
        try:
            product_group = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/div/div').text
            product_group = product_group.replace("خانه\n", "").replace("\n", ">")
            product_group = product_group.rsplit(">", 1)[0]
        except:
            product_group = None
        try:
            title = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[1]/div[1]/div/div/div[2]/div[1]/div[1]/h1').text
            title = title = re.sub(r'\nجدید', '', title)
        except:
            title = None
        try:
            stock = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[2]/div/div[2]/div/div[2]/div[1]/span').text
            stock = int(re.search(r'\d+', stock).group())
        except:
            stock = None
        try:
            price = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[2]/div/div[2]/div/div[2]/div[1]/div/span').text
            price = re.sub(r'\D', '', price)
        except Exception as e:
            print(f'price e: {e}')
            price = None
            stock = 0
        try:
            main_pic_link = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[1]/div[1]/div/div/div[1]/div/div[1]/div/div/div[1]/div[1]/div/div')
            main_pic_alt = title
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
            main_pic = driver.find_element(By.XPATH, '/html/body/div[1]/main/div/div[2]/section[1]/section[1]/div[1]/div/div/div[1]/div/div[1]/div/div/div[1]/div[1]/div/div/div/img')
            main_pic.click()
            time.sleep(1)
            gallery = []
            for i in range(2, 21):
                try:
                    images = driver.find_elements(By.XPATH, f'/html/body/div[8]/div/div[1]/div/div/div/div/div/div[2]/div/div[{i}]//img')
                    for img in images:
                        gallery.append(img.get_attribute('src').replace("_256X256X70.jpg", ""))
                except Exception as e:
                    print(f'Error processing gallery {i}: {e}')
        except:
            gallery = None
        return {
            'id': None,
            'link': product_url,
            'product_group': product_group,
            'title': title,
            'stock': stock,
            'price': price,
            'main_pic_link': main_pic_link,
            'main_pic_alt': main_pic_alt,
            'gallery': gallery
        }

    def basalam_products_details_extractor(self, seller_url, driver='firefox'):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        process_start_time = time.time()
        self.basalam_links_extractor(seller_url.rstrip('/'), driver)
        seller_id = seller_url.rstrip('/').split('/')[-1]
        existing_links = []
        if os.path.exists(f'{seller_id}_links.json'):
            existing_links = self.read_json(prefix=seller_id, type='links')
        existing_products_details = []
        if os.path.exists(f'{seller_id}_products_details.json'):
            existing_products_details = self.read_json(prefix=seller_id, type='products_details')
        last_id = existing_products_details[-1]['id'] if existing_products_details else 0
        new_products_details = []
        for item in existing_links:
            if item['id'] > last_id:
                start_time = time.time()
                details = self.basalam_product_details_dict(item['link'], driver)
                details['id'] = item['id']
                details['link'] = item['link']
                new_products_details.append(details)
                products_details = existing_products_details + new_products_details
                self.write_json(prefix=seller_id, type='products_details', data=products_details)

                self.db.product_create(details)

                end_time = time.time()
                elapsed_time = end_time - start_time
                if elapsed_time > 12:
                    print(f"Product details extraction took too long ({elapsed_time} seconds). Restarting driver...")
                    driver = self.reset_driver(driver)

        driver.quit()
        process_end_time = time.time()
        process_elapsed_time = process_end_time - process_start_time
        print(f"Process elapsed time: {process_elapsed_time} seconds")