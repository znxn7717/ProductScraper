# basalam.py
import os
import re
import time
import math
from . import ProductExtractor
from urllib.parse import unquote
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from utiles.digikala_data_extractor import get_product_data
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

class Torob(ProductExtractor):
    def torob_scroll_to_end(self, seller_url, driver, products_num='auto'):
        action = ActionChains(driver)
        products_num = self.torob_determine_products_num(seller_url, driver, products_num)
        getted_num = 0
        start_time = time.time()
        while getted_num < products_num:
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time > (products_num * 0.2):
                self.logger.warning("Scrolling timeout reached.")
                break
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div/div/div[2]/div/div/div/div[2]/div/div[2]/div[2]/div/div[2]')))
                action.scroll_by_amount(0, 10000).perform()
            except:
                self.logger.info("Scrolling final stop.")
                break
            getted_num = len(driver.find_elements(By.CSS_SELECTOR, '.ProductCards_cards__MYvdn > div'))
            self.logger.info(f'{getted_num} | {products_num}')

    def torob_determine_products_num(self, seller_url, driver, products_num):
        if products_num != 'auto':
            return products_num
        else:
            try:
                driver.get(seller_url)
                action = ActionChains(driver)
                while True:
                    try:
                        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div/div[2]/div/div[2]/div[2]/div/div[2]')
                        action.scroll_by_amount(0, 10000).perform()
                        time.sleep(0.1)
                    except:
                        elements = WebDriverWait(driver, 30).until(
                            EC.presence_of_all_elements_located(
                                (By.CSS_SELECTOR, '.ProductCards_cards__MYvdn > div')
                            )
                        )
                        return len(elements)
                        break
            except Exception as e:
                self.logger.error(f"Unexpected error while determining section length: {e}")
                return 0

    def torob_links_extractor(self, seller_url, sid, driver='firefox', products_num='auto'):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        target_seller_id = seller_url.rstrip('/').split('/')[-2]
        decoded_segment = unquote(target_seller_id)
        target_seller_id = decoded_segment
        existing_links = []
        if os.path.exists(f'data/{sid+"_"+target_seller_id}_links.json'):
            existing_links = self.read_json(prefix=sid+"_"+target_seller_id, type='links')
        last_id = existing_links[-1]['id'] if existing_links else 0
        if os.path.exists(f'data/{sid+"_"+target_seller_id}_products_details.json'):
            existing_products_details = self.read_json(prefix=sid+"_"+target_seller_id, type='products_details')
            products_last_id = existing_products_details[-1]['id'] if existing_products_details else 0
            products_num = self.torob_determine_products_num(seller_url, driver, products_num)
            if products_num > products_last_id:
                existing_links = []
        driver.get(seller_url)
        products_num = self.torob_determine_products_num(seller_url, driver, products_num)
        start_time = time.time()
        while len(existing_links) < products_num:
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time > (products_num * 0.4):
                self.logger.warning(f"Timeout reached. Collected {len(existing_links)} links so far.")
                break
            self.torob_scroll_to_end(seller_url, driver, products_num)
            for i in range(last_id + 1, products_num + 1):
                try:
                    link = driver.find_element(By.XPATH, f'/html/body/div/div/div[2]/div/div/div/div[2]/div/div[2]/div[2]/div/div[1]/div/div[{i}]/a').get_attribute('href')
                    new_link = {'id': i, 'link': link}
                    existing_links.append(new_link)
                    last_id = i
                    self.write_json(prefix=sid+"_"+target_seller_id, type='links', data=existing_links)
                except:
                    continue
        self.logger.info(f"Total number of links: {len(existing_links)}")

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
            product_group = self.find_key_by_value("data/reference/categories/fuzzed_listed_sorted_torob_categories.json", product_group)
            # product_group = product_group.rsplit(">", 1)[0]
        except:
            product_group = None
        try:
            title = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[2]/h1').text
        except:
            title = None
        try:
            price = driver.find_element(By.CSS_SELECTOR, 'div.Showcase_buy_box_text__otYW_:nth-child(2)').text
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
        
    def torob_products_details_extractor(self, seller_url, sid, driver='firefox', products_num='auto', progress_callback=None):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        process_start_time = time.time()
        target_seller_id = seller_url.rstrip('/').split('/')[-2]
        decoded_segment = unquote(target_seller_id)
        target_seller_id = decoded_segment
        if not os.path.exists(f'data/{sid+"_"+target_seller_id}_links.json'):
            products_num = self.torob_determine_products_num(seller_url, driver, products_num)
            if products_num > 2000:
                products_num = 2000
            self.torob_links_extractor(seller_url.rstrip('/'), sid, driver, products_num)
        existing_links = []
        if os.path.exists(f'data/{sid+"_"+target_seller_id}_links.json'):
            existing_links = self.read_json(prefix=sid+"_"+target_seller_id, type='links')
            links_last_id = existing_links[-1]['id'] if existing_links else 0
            self.logger.info(f'links_last_id: {links_last_id}')
            products_num = self.torob_determine_products_num(seller_url, driver, products_num)
            if products_num > 2000:
                products_num = 2000
            self.logger.info(f'products_num: {products_num}')
            if products_num > links_last_id:
                self.torob_links_extractor(seller_url.rstrip('/'), sid, driver, products_num)
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
                details = self.torob_product_details_dict(item['link'], driver)
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
                if elapsed_time > 15:
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