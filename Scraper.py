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
from utiles.digikala_data_extractor import get_product_data
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException, TimeoutException

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
        self.db.connect_to_database()
        self.db.setup_product_table()

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
        with open(f'data/{prefix}_{type}.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def read_json(self, prefix, type):
        with open(f'data/{prefix}_{type}.json', 'r', encoding='utf-8') as file:
            return json.load(file)

    def find_key_by_value(self, path, value):
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        for key, values in data.items():
            if value in values:
                return key
        return "سایر"

    def basalam_scroll_to_end(self, driver, products_num='auto'):
        action = ActionChains(driver)
        products_num = self.basalam_determine_products_num(driver, products_num)
        getted_num = 0
        start_time = time.time()
        while getted_num < products_num:
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time > (products_num * 0.2):
                print(f"Scrolling timeout reached.")
                break
            last_product = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div._KeJul:last-child'))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", last_product)
            getted_num = len(driver.find_elements(By.XPATH, '/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div'))
            print(f'{getted_num} | {products_num}', end="\r")

    def torob_scroll_to_end(self, driver):
        action = ActionChains(driver)
        while True:
            try:
                driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div/div[2]/div/div[2]/div[2]/div/div[2]')
                action.scroll_by_amount(0, 10000).perform()
                time.sleep(0.1)
            except:
                break

    def digikala_scroll_to_end(self, driver):
        action = ActionChains(driver)
        products_num = int(re.sub(r'\D', '', driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[1]/div/div/div/div[3]/span').text))
        getted_num = 0
        while getted_num < products_num:
            driver.execute_script("arguments[0].scrollIntoView(true);", driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]/span'))
            time.sleep(1)
            getted_num = len(driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]').find_elements(By.TAG_NAME, 'a'))

    def basalam_determine_products_num(self, driver, products_num):
        if products_num != 'auto':
            return products_num
        else:
            try:
                element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.ENqTVF:nth-child(3)')))
                return int(re.search(r'\d+', element.text).group())
            except TimeoutException:
                self.basalam_scroll_to_end(driver)
                elements = WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, '/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div')
                    )
                )
                return len(elements)
            except Exception as e:
                print(f"Unexpected error while determining section length: {e}")
                return None

    def basalam_links_extractor(self, seller_url, sid, driver='firefox', products_num='auto'):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        target_seller_id = seller_url.rstrip('/').split('/')[-1]
        existing_links = []
        if os.path.exists(f'data/{sid+"_"+target_seller_id}_links.json'):
            existing_links = self.read_json(prefix=sid+"_"+target_seller_id, type='links')
        last_id = existing_links[-1]['id'] if existing_links else 0
        if os.path.exists(f'data/{sid+"_"+target_seller_id}_products_details.json'):
            existing_products_details = self.read_json(prefix=sid+"_"+target_seller_id, type='products_details')
            products_last_id = existing_products_details[-1]['id'] if existing_products_details else 0
            products_num = self.basalam_determine_products_num(driver, products_num)
            if products_num > products_last_id:
                existing_links = []
        driver.get(seller_url)
        products_num = self.basalam_determine_products_num(driver, products_num)
        start_time = time.time()
        while len(existing_links) < products_num:
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time > (products_num * 0.4):
                print(f"Timeout reached. Collected {len(existing_links)} links so far.")
                break
            self.basalam_scroll_to_end(driver, products_num)
            for i in range(last_id + 1, products_num + 1):
                try:
                    link = driver.find_element(By.XPATH, f'/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div[{i}]/div[1]/a').get_attribute('href')
                    new_link = {'id': i, 'link': link}
                    existing_links.append(new_link)
                    last_id = i
                    self.write_json(prefix=sid+"_"+target_seller_id, type='links', data=existing_links)
                except:
                    continue
        print(f"Total number of links: {len(existing_links)}", end="\r")

    def torob_links_extractor(self, seller_url, driver='firefox'):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        seller_id = seller_url.rstrip('/').split('/')[-2]
        decoded_segment = unquote(seller_id)
        seller_id = decoded_segment
        if not os.path.exists(f'data/{seller_id}_products_details.json'):
            existing_links = []
            if os.path.exists(f'data/{seller_id}_links.json'):
                existing_links = self.read_json(prefix=seller_id, type='links')
            last_id = existing_links[-1]['id'] if existing_links else 0
            driver.get(seller_url)
            self.torob_scroll_to_end(driver)
            try:
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '/html/body/div/div/div[2]/div/div/div/div[2]/div/div[2]/div[2]/div/div[1]/div')
                    )
                )
            except Exception as e:
                print(f"Error waiting for elements: {e}")
                return
            new_links = []
            section = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div/div[2]/div/div[2]/div[2]/div/div[1]/div').find_elements(By.TAG_NAME, 'a')
            for i in range(last_id + 1, len(section) + 1):
                try:
                    link = driver.find_element(By.XPATH, f'/html/body/div/div/div[2]/div/div/div/div[2]/div/div[2]/div[2]/div/div[1]/div/div[{i}]/a').get_attribute('href')
                    new_links.append({'id': i, 'link': link})
                except Exception as e:
                    print(f"Error occurred at link {i}: {e}")
                    continue
            links = existing_links + new_links
            df = pd.DataFrame(links)
            print(f"Total number of links: {len(df)}")
            self.write_json(prefix=seller_id, type='links', data=links)

    def digikala_links_extractor(self, seller_url, driver='chrome'):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        seller_id = seller_url.rstrip('/').split('/')[-1]
        if not os.path.exists(f'data/{seller_id}_products_details.json'):
            existing_links = []
            if os.path.exists(f'data/{seller_id}_links.json'):
                existing_links = self.read_json(prefix=seller_id, type='links')
            last_id = existing_links[-1]['id'] if existing_links else 0
            driver.get(seller_url)
            try:
                WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[1]/div/div/div/div[3]/span')
                    )
                )
            except Exception as e:
                print(f"Error waiting for elements: {e}")
                return
            products_num = int(re.sub(r'\D', '', driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[1]/div/div/div/div[3]/span').text))
            page_len = 500 if math.ceil(products_num / 20) > 500 else math.ceil(products_num / 20)
            if page_len <= 10:
                self.digikala_scroll_to_end(driver)
                new_links = []
                section = driver.find_element(By.CSS_SELECTOR, '.product-list_ProductList__pagesContainer__zAhrX').find_elements(By.TAG_NAME, 'a')
                for i in range(last_id + 1, len(section) + 1):
                    try:
                        link = driver.find_element(By.CSS_SELECTOR, f'div.product-list_ProductList__item__LiiNI:nth-child({i}) > a:nth-child(1)').get_attribute('href')
                        new_links.append({'id': i, 'link': link})
                    except Exception as e:
                        print(f"Error occurred at link {i}: {e}")
                        continue
                links = existing_links + new_links
                df = pd.DataFrame(links)
                print(f"Total number of links: {len(df)}")
                self.write_json(prefix=seller_id, type='links', data=links)
            else:
                start_page = (last_id // 20) + 1  # Assuming each page has up to 20 links
                current_id = last_id
                driver.get(f'{seller_url}?page={start_page}')
                try:
                    WebDriverWait(driver, 6).until(
                        EC.presence_of_element_located(
                            (By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[1]/div/div/div/div[3]/span')
                        )
                    )
                except Exception as e:
                    print(f"Error waiting for elements: {e}")
                    return
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
                    retry_count = 0
                    max_retries = 3
                    while retry_count < max_retries:
                        try:
                            new_links = extract_links(current_id)
                            links = existing_links.extend(new_links) 
                            current_id += len(new_links)  # Update the id counter
                            break  # If extraction is successful, exit the retry loop
                        except StaleElementReferenceException:
                            retry_count += 1
                            time.sleep(2)
                    self.write_json(prefix=seller_id, type='links', data=links)
                print(f"Total number of links: {current_id}")

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
            title = re.sub(r'\nجدید', '', title)
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
                    if not images:
                        images = driver.find_elements(By.XPATH, f'/html/body/div[9]/div/div[1]/div/div/div/div/div/div[2]/div/div[{i}]//img')
                    for img in images:
                        gallery.append(img.get_attribute('src').replace("_256X256X70.jpg", ""))
                except Exception as e:
                    print(f'Error processing gallery {i}: {e}')
        except:
            gallery = None
        return {
            'id': None,
            'is_scraped': None,
            'seller_id': None,
            'link': None,
            'product_group': product_group,
            'title': title,
            'stock': stock,
            'price': price,
            'main_pic_link': main_pic_link,
            'main_pic_alt': main_pic_alt,
            'gallery': gallery
        }

    def torob_product_details_dict(self, product_url, driver='firefox'):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        driver.get(product_url)
        time.sleep(2)
        try:
            product_group = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div[2]/div/div[1]/div[1]/div/div').text
            product_group = product_group.replace("ترب\n", "").replace("\n", ">")
            product_group = self.find_key_by_value("data/reference/fuzzed_listed_sorted_torob_categories.json", product_group)
            # product_group = product_group.rsplit(">", 1)[0]
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
            main_pic_alt = title
            main_pic_link = main_pic_link.replace("_/280x280.jpg", "")
        except:
            main_pic_link = None
            main_pic_alt = None
        try:
            gallery_len = len(driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div[2]/div/div[2]/div[1]/div/div/div[1]/div/div/div[1]').find_elements(By.XPATH, './div'))
            if gallery_len == 4:
                div_4_element = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div[2]/div/div[2]/div[1]/div/div/div[1]/div/div/div[1]/div[4]/div').text
                move_len = int(re.sub(r'\D', '', div_4_element)) + 3
            else:
                move_len = gallery_len
            main_pic = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div[2]/div/div[2]/div[1]/div/div/div[1]/div/div/div[2]/picture/img')
            main_pic.click()
            time.sleep(3)
            gallery = []
            for i in range(1, move_len):
                try:
                    driver.find_element(By.XPATH, '/html/body/div[4]/div/div/div/button[2]').click()
                    time.sleep(.5)
                    image = driver.find_element(By.XPATH, '/html/body/div[4]/div/div/div/div[1]/img[2]').get_attribute('src')
                    gallery.append(image)
                except Exception as e:
                    print(f'Error processing gallery {i}: {e}')
        except:
            gallery = None
        return {
            'id': None,
            'seller_id': None,
            'link': None,
            'product_group': product_group,
            'title': title,
            'stock': stock,
            'price': price,
            'main_pic_link': main_pic_link,
            'main_pic_alt': main_pic_alt,
            'gallery': gallery
        }

    def digikala_product_details_dict(self, product_url, driver='chrome', api=True):
        if api:
            try:
                if re.search(r'-(\d+)', product_url):
                    pid = re.search(r'-(\d+)', product_url).group(1)
                data = get_product_data(pid)
                product_group = data[5]
                product_group = self.find_key_by_value("data/reference/fuzzed_listed_sorted_digikala_categories.json", product_group)
                title = data[1]
                if data[8]:
                        price = str(int(data[8]/10))
                        stock = 1
                else:
                        price = data[8]
                        stock = 0
                main_pic_link = data[6]
                main_pic_alt = title
                gallery = data[7]
                gallery = [link.split('?')[0] for link in gallery]
                # time.sleep(1)
            except Exception as e:
                print(f'Error processing api: {e}')
                product_group, title, price, stock, main_pic_link, main_pic_alt, gallery = (None,) * 7
        else:
            if driver == 'firefox':
                driver = self.init_firefox_driver()
            elif driver == 'chrome':
                driver = self.init_chrome_driver()
            driver.get(product_url)
            time.sleep(4)
            try:
                product_group = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[2]/div[1]/nav/div/div/div[1]').text
                product_group = product_group.replace("دیجی‌کالا/\n", "").replace("/\n", ">")
                product_group = self.find_key_by_value("data/reference/fuzzed_listed_sorted_digikala_categories.json", product_group)
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
                main_pic_alt = title
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
                        images = driver.find_elements(By.CSS_SELECTOR, f'div.bg-white:nth-child(1) > div:nth-child({i}) > div:nth-child(1) > picture:nth-child(1) > img:nth-child(3)')
                        for img in images:
                            gallery.append(img.get_attribute('src').replace("?x-oss-process=image/resize,m_lfit,h_800,w_800/quality,q_90", ""))
                    except Exception as e:
                        print(f'Error processing gallery {i}: {e}')
            except:
                gallery = None
        return {
            'id': None,
            'seller_id': None,
            'link': None,
            'product_group': product_group,
            'title': title,
            'stock': stock,
            'price': price,
            'main_pic_link': main_pic_link,
            'main_pic_alt': main_pic_alt,
            'gallery': gallery
        }

    def basalam_products_details_extractor(self, seller_url, sid, driver='firefox', products_num='auto', progress_callback=None):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        process_start_time = time.time()
        target_seller_id = seller_url.rstrip('/').split('/')[-1]
        if not os.path.exists(f'data/{sid+"_"+target_seller_id}_links.json'):
            self.basalam_links_extractor(seller_url.rstrip('/'), sid, driver, products_num)
        existing_links = []
        if os.path.exists(f'data/{sid+"_"+target_seller_id}_links.json'):
            existing_links = self.read_json(prefix=sid+"_"+target_seller_id, type='links')
            links_last_id = existing_links[-1]['id'] if existing_links else 0
            products_num = self.basalam_determine_products_num(driver, products_num)
            print(f'links_last_id: {links_last_id}')
            print(f'products_num: {products_num}')
            if products_num > links_last_id:
                self.basalam_links_extractor(sid, seller_url.rstrip('/'), driver, products_num)
                existing_links = self.read_json(prefix=sid+"_"+target_seller_id, type='links')
                links_last_id = existing_links[-1]['id'] if existing_links else 0
        existing_products_details = []
        if os.path.exists(f'data/{sid+"_"+target_seller_id}_products_details.json'):
            existing_products_details = self.read_json(prefix=sid+"_"+target_seller_id, type='products_details')
        products_last_id = existing_products_details[-1]['id'] if existing_products_details else 0
        for i in existing_products_details:
            self.db.upsert_product_in_table(i)
            self.db.update_total_scraped_product_num(sid)
        new_products_details = []
        for item in existing_links:
            if item['id'] > products_last_id:
                start_time = time.time()
                details = self.basalam_product_details_dict(item['link'], driver)
                details['id'] = item['id']
                details['is_scraped'] = 1
                details['seller_id'] = sid
                details['link'] = item['link']
                new_products_details.append(details)
                products_details = existing_products_details + new_products_details
                self.write_json(prefix=sid+"_"+target_seller_id, type='products_details', data=products_details)
                self.db.upsert_product_in_table(details)
                self.db.update_total_scraped_product_num(sid)

                end_time = time.time()
                elapsed_time = end_time - start_time
                if elapsed_time > 12:
                    print(f"Product details extraction took too long ({elapsed_time} seconds).")
                    driver = self.reset_driver(driver)
                progress = int((item['id'] / links_last_id) * 100)
                print(f'Progress: {progress}%')
                if progress_callback:
                    progress_callback(progress)
        self.db.close()
        driver.quit()
        process_end_time = time.time()
        process_elapsed_time = process_end_time - process_start_time
        print(f"Process elapsed time: {process_elapsed_time} seconds")
        
    def torob_products_details_extractor(self, seller_url, sid, driver='firefox'):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        process_start_time = time.time()
        self.torob_links_extractor(seller_url.rstrip('/'), driver)
        seller_id = seller_url.rstrip('/').split('/')[-2]
        decoded_segment = unquote(seller_id)
        seller_id = decoded_segment
        existing_links = []
        if os.path.exists(f'data/{seller_id}_links.json'):
            existing_links = self.read_json(prefix=seller_id, type='links')
        existing_products_details = []
        if os.path.exists(f'data/{seller_id}_products_details.json'):
            existing_products_details = self.read_json(prefix=seller_id, type='products_details')
        last_id = existing_products_details[-1]['id'] if existing_products_details else 0
        for i in existing_products_details:
            self.db.product_create(i)
        new_products_details = []
        for item in existing_links:
            if item['id'] > last_id:
                start_time = time.time()
                details = self.torob_product_details_dict(item['link'], driver)
                details['id'] = item['id']
                details['seller_id'] = sid
                details['link'] = item['link']
                new_products_details.append(details)
                products_details = existing_products_details + new_products_details
                self.write_json(prefix=seller_id, type='products_details', data=products_details)
                self.db.product_create(details)
                end_time = time.time()
                elapsed_time = end_time - start_time
                if elapsed_time > 15:
                    print(f"Product details extraction took too long ({elapsed_time} seconds).")
                    driver = self.reset_driver(driver)

        driver.quit()
        process_end_time = time.time()
        process_elapsed_time = process_end_time - process_start_time
        print(f"Process elapsed time: {process_elapsed_time} seconds")

    def digikala_products_details_extractor(self, seller_url, sid, driver='chrome'):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        process_start_time = time.time()
        self.digikala_links_extractor(seller_url.rstrip('/'), driver)
        seller_id = seller_url.rstrip('/').split('/')[-1]
        existing_links = []
        if os.path.exists(f'data/{seller_id}_links.json'):
            existing_links = self.read_json(prefix=seller_id, type='links')
        existing_products_details = []
        if os.path.exists(f'data/{seller_id}_products_details.json'):
            existing_products_details = self.read_json(prefix=seller_id, type='products_details')
        last_id = existing_products_details[-1]['id'] if existing_products_details else 0
        for i in existing_products_details:
            self.db.product_create(i)
        new_products_details = []
        for item in existing_links:
            if item['id'] > last_id:
                start_time = time.time()
                details = self.digikala_product_details_dict(item['link'], driver)
                details['id'] = item['id']
                details['seller_id'] = sid
                details['link'] = item['link']
                new_products_details.append(details)
                products_details = existing_products_details + new_products_details
                self.write_json(prefix=seller_id, type='products_details', data=products_details)
                self.db.product_create(details)
                end_time = time.time()
                elapsed_time = end_time - start_time
                if elapsed_time > 15:
                    print(f"Product details extraction took too long ({elapsed_time} seconds).")
                    driver = self.reset_driver(driver)

        driver.quit()
        process_end_time = time.time()
        process_elapsed_time = process_end_time - process_start_time
        print(f"Process elapsed time: {process_elapsed_time} seconds")