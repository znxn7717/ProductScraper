# basalam.py
import os
import re
import time
import math
from . import ProductExtractor
from urllib.parse import unquote
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from utiles.digikala_data_extractor import get_product_data
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

class Basalam(ProductExtractor):
    def basalam_scroll_to_end(self, seller_url, driver, products_num='auto'):
        action = ActionChains(driver)
        products_num = self.basalam_determine_products_num(seller_url, driver, products_num)
        getted_num = 0
        start_time = time.time()
        while getted_num < products_num:
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time > (products_num * 0.2):
                self.logger.warning("Scrolling timeout reached.")
                break
            last_product = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div._KeJul:last-child'))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", last_product)
            getted_num = len(driver.find_elements(By.XPATH, '/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div'))
            self.logger.info(f'{getted_num} | {products_num}')

    def basalam_determine_products_num(self, seller_url, driver, products_num):
        if products_num != 'auto':
            return products_num
        else:
            try:
                driver.get(seller_url)
                element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.ENqTVF:nth-child(3)')))
                return int(re.search(r'\d+', element.text).group())
            except TimeoutException:
                self.basalam_scroll_to_end(seller_url, driver, products_num)
                elements = WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, '/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div')
                    )
                )
                return len(elements)
            except Exception as e:
                self.logger.error(f"Unexpected error while determining section length: {e}")
                return 0

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
            products_num = self.basalam_determine_products_num(seller_url, driver, products_num)
            if products_num > products_last_id:
                existing_links = []
        driver.get(seller_url)
        products_num = self.basalam_determine_products_num(seller_url, driver, products_num)
        start_time = time.time()
        while len(existing_links) < products_num:
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time > (products_num * 0.4):
                self.logger.warning(f"Timeout reached. Collected {len(existing_links)} links so far.")
                break
            self.basalam_scroll_to_end(seller_url, driver, products_num)
            for i in range(last_id + 1, products_num + 1):
                try:
                    link = driver.find_element(By.XPATH, f'/html/body/div/main/div/div[4]/div/div[2]/div[2]/section/div[{i}]/div[1]/a').get_attribute('href')
                    new_link = {'id': i, 'link': link}
                    existing_links.append(new_link)
                    last_id = i
                    self.write_json(prefix=sid+"_"+target_seller_id, type='links', data=existing_links)
                except:
                    continue
        self.logger.info(f"Total number of links: {len(existing_links)}")

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
                    self.logger.error(f'Error processing gallery {i}: {e}')
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

    def basalam_products_details_extractor(self, seller_url, sid, driver='firefox', products_num='auto', progress_callback=None):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        process_start_time = time.time()
        target_seller_id = seller_url.rstrip('/').split('/')[-1]
        if not os.path.exists(f'data/{sid+"_"+target_seller_id}_links.json'):
            if products_num > 2000:
                products_num = 2000
            self.basalam_links_extractor(seller_url.rstrip('/'), sid, driver, products_num)
        existing_links = []
        if os.path.exists(f'data/{sid+"_"+target_seller_id}_links.json'):
            existing_links = self.read_json(prefix=sid+"_"+target_seller_id, type='links')
            links_last_id = existing_links[-1]['id'] if existing_links else 0
            self.logger.info(f'links_last_id: {links_last_id}')
            products_num = self.basalam_determine_products_num(seller_url, driver, products_num)
            if products_num > 2000:
                products_num = 2000
            self.logger.info(f'products_num: {products_num}')
            if products_num > links_last_id:
                self.basalam_links_extractor(seller_url.rstrip('/'), sid, driver, products_num)
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
                    self.logger.warning(f"Product details extraction took too long ({elapsed_time} seconds).")
                    driver = self.reset_driver(driver)
                progress = int((item['id'] / links_last_id) * 100)
                self.logger.info(f'Progress: {progress}%')
                if progress_callback:
                    progress_callback(progress)
        self.db.close()
        driver.quit()
        process_end_time = time.time()
        process_elapsed_time = process_end_time - process_start_time
        self.logger.info(f"Process elapsed time: {process_elapsed_time} seconds")