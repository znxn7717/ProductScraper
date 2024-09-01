# digikala.py
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
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException

class Digikala(ProductExtractor):
    def digikala_scroll_to_end(self, seller_url, driver, products_num='auto'):
        action = ActionChains(driver)
        products_num = self.digikala_determine_products_num(seller_url, driver, products_num)
        getted_num = 0
        start_time = time.time()
        while getted_num < products_num:
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time > (products_num * 0.2):
                self.logger.warning("Scrolling timeout reached.")
                break
            last_product = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]/span'))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", last_product)
            getted_num = len(driver.find_elements(By.CSS_SELECTOR, 'div.product-list_ProductList__item__LiiNI'))
            self.logger.info(f'{getted_num} | {products_num}')

    def digikala_determine_products_num(self, seller_url, driver, products_num):
        if products_num != 'auto':
            return products_num
        else:
            try:
                driver.get(seller_url)
                element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.text-neutral-500:nth-child(1)')))
                return int(re.sub(r'\D', '', element.text))
            except TimeoutException:
                self.digikala_scroll_to_end(seller_url, driver, products_num)
                elements = WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, 'div.product-list_ProductList__item__LiiNI')
                    )
                )
                return len(elements)
            except Exception as e:
                self.logger.error(f"Unexpected error while determining section length: {e}")
                return 0

    def digikala_links_extractor(self, seller_url, sid, driver='chrome', products_num='auto'):
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
            products_num = self.digikala_determine_products_num(seller_url, driver, products_num)
            if products_num > products_last_id:
                existing_links = []
        driver.get(seller_url)
        products_num = self.digikala_determine_products_num(seller_url, driver, products_num)
        page_len = 500 if math.ceil(products_num / 20) > 500 else math.ceil(products_num / 20)
        if page_len <= 10:
            start_time = time.time()
            while len(existing_links) < products_num:
                current_time = time.time()
                elapsed_time = current_time - start_time
                if elapsed_time > (products_num * 0.4):
                    self.logger.warning(f"Timeout reached. Collected {len(existing_links)} links so far.")
                    break
                self.digikala_scroll_to_end(seller_url, driver, products_num)
                for i in range(last_id + 1, products_num + 1):
                    try:
                        link = driver.find_element(By.CSS_SELECTOR, f'div.product-list_ProductList__item__LiiNI:nth-child({i}) > a:nth-child(1)').get_attribute('href')
                        new_link = {'id': i, 'link': link}
                        existing_links.append(new_link)
                        last_id = i
                        self.write_json(prefix=sid+"_"+target_seller_id, type='links', data=existing_links)
                    except:
                        continue
            self.logger.info(f"Total number of links: {len(existing_links)}")
        else:
            start_page = (last_id // 20) + 1  # Assuming each page has up to 20 links
            current_id = last_id
            driver.get(f'{seller_url}?page={start_page}')
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[1]/div/div/div/div[3]/span')
                    )
                )
            except Exception as e:
                self.logger.info(f"Error waiting for elements: {e}")
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
                        next_btn = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[1]/div[3]/div[3]/div[3]/div/section[1]/div[2]/div[21]/div/div[3]')))
                        driver.execute_script("arguments[0].scrollIntoView();", next_btn)
                        next_btn.click()
                    except ElementClickInterceptedException:
                        next_btn.click()
                retry_count = 0
                max_retries = 3
                while retry_count < max_retries:
                    try:
                        new_links = extract_links(current_id)
                        existing_links.extend(new_links)
                        current_id += len(new_links)  # Update the id counter
                        break  # If extraction is successful, exit the retry loop
                    except StaleElementReferenceException:
                        retry_count += 1
                        time.sleep(2)
                self.write_json(prefix=sid+"_"+target_seller_id, type='links', data=existing_links)
            self.logger.info(f"Total number of links: {current_id}")
            if len(existing_links) > products_num:
                existing_links = existing_links[:products_num]
                self.write_json(prefix=sid+"_"+target_seller_id, type='links', data=existing_links)
                self.logger.info(f"Excess links removed. Final number of links: {len(existing_links)}")

    def digikala_product_details_dict(self, product_url, driver='chrome', api=True):
        if api:
            try:
                if re.search(r'-(\d+)', product_url):
                    pid = re.search(r'-(\d+)', product_url).group(1)
                data = get_product_data(pid)
                product_group = data[5]
                product_group = self.find_key_by_value("data/reference/categories/fuzzed_listed_sorted_digikala_categories.json", product_group)
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
                self.logger.error(f'Error processing api: {e}')
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
                product_group = self.find_key_by_value("data/reference/categories/fuzzed_listed_sorted_digikala_categories.json", product_group)
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

    def digikala_products_details_extractor(self, seller_url, sid, driver='chrome', products_num='auto', progress_callback=None):
        if driver == 'firefox':
            driver = self.init_firefox_driver()
        elif driver == 'chrome':
            driver = self.init_chrome_driver()
        process_start_time = time.time()
        target_seller_id = seller_url.rstrip('/').split('/')[-1]
        decoded_segment = unquote(target_seller_id)
        target_seller_id = decoded_segment
        if not os.path.exists(f'data/{sid+"_"+target_seller_id}_links.json'):
            products_num = self.digikala_determine_products_num(seller_url, driver, products_num)
            if products_num > 2000:
                products_num = 2000
            self.digikala_links_extractor(seller_url.rstrip('/'), sid, driver, products_num)
        existing_links = []
        if os.path.exists(f'data/{sid+"_"+target_seller_id}_links.json'):
            existing_links = self.read_json(prefix=sid+"_"+target_seller_id, type='links')
            links_last_id = existing_links[-1]['id'] if existing_links else 0
            self.logger.info(f'links_last_id: {links_last_id}')
            products_num = self.digikala_determine_products_num(seller_url, driver, products_num)
            if products_num > 2000:
                products_num = 2000
            self.logger.info(f'products_num: {products_num}')
            if products_num > links_last_id:
                self.digikala_links_extractor(seller_url.rstrip('/'), sid, driver, products_num)
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
                details = self.digikala_product_details_dict(item['link'], driver)
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