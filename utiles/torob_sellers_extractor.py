import os
import pandas as pd
from Scraper import ProductScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

scraper = ProductScraper()

def torob_links_extractor():
    driver = scraper.init_firefox_driver()
    existing_sellers_details = []
    if os.path.exists('data/reference/sellers_details.json'):
        existing_sellers_details = scraper.read_json(prefix='reference/sellers', type='details')
    last_id = existing_sellers_details[-1]['id'] if existing_sellers_details else 0
    new_sellers_details = []
    for i in range(last_id + 1, 150000):
        try:
            driver.get(f'https://torob.com/shop/{i}/')
            wait = WebDriverWait(driver, 3)
            header_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'tr.jsx-637019445:nth-child(1) > td:nth-child(1) > h2:nth-child(1)')))
            if header_element.text != 'مجوزها و اعتبار':
                print(f"Skipping {i}")
                continue 
            seller_name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ShopInfoHeader_title__8wNZ0 > h1:nth-child(1)'))).text
            seller_url = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ShopInfoHeader_title__8wNZ0 > a:nth-child(2)'))).get_attribute('href')
            seller_location = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#province-city'))).text
            history_of_cooperation = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'tr.jsx-637019445:nth-child(2) > td:nth-child(2)'))).text
            performance_score = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'tr.jsx-637019445:nth-child(3) > td:nth-child(2)'))).text
            contact_information = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'tr.jsx-637019445:nth-child(8) > td:nth-child(2)'))).text    
            new_sellers_details.append({
                'id': i,
                'sn': seller_name,
                'su': seller_url,
                'sl': seller_location,
                'hof': history_of_cooperation,
                'ps': performance_score,
                'ci': contact_information
            })
            sellers_details = existing_sellers_details + new_sellers_details
            df = pd.DataFrame(sellers_details)
            print(f"Total number of links: {len(df)} | id: {i}")
            scraper.write_json(prefix='reference/sellers', type='details', data=sellers_details)
        except Exception as e:
            print(f"Error occurred at {i}: {e}")
            continue




# def torob_links_extractor():
#     driver = scraper.init_firefox_driver()
#     existing_links = []
#     if os.path.exists('data/reference/sellers_links.json'):
#         existing_links = scraper.read_json(prefix='reference/sellers', type='links')
#     last_id = existing_links[-1]['id'] if existing_links else 0
#     page_len = 3241
#     start_page = (last_id // 30) + 1  
#     for page_num in range(start_page, page_len + 1):
#         try:
#             driver.get(f'https://torob.com/shop-list/?page={page_num}')
#             try:
#                 section = WebDriverWait(driver, 3).until(
#                     EC.presence_of_element_located(
#                         (By.CSS_SELECTOR, 'html body.custom_class div#__next div div div div#layout-wrapp.layout_desktop_layoutWrapp__4CNgx div.layout_desktop_content__fNKMt div.withRightProfilePanel_containerPanel__KgSeK div.withRightProfilePanel_leftContain__TaSNd div.jsx-253f75a3454794e1 div.jsx-253f75a3454794e1 div.jsx-253f75a3454794e1.shops-wrapper')
#                     )
#                 )
#             except Exception as e:
#                 print(f"Error waiting for elements: {e}")
#                 continue
#             new_links = []
#             for i in range(1, len(section.find_elements(By.TAG_NAME, 'a')) + 1):
#                 try:
#                     link = driver.find_element(By.CSS_SELECTOR, f'.shops-wrapper > a:nth-child({i})').get_attribute('href')
#                     new_links.append({'id': last_id + i, 'link': link})
#                 except Exception as e:
#                     print(f"Error occurred at link {i}: {e}")
#                     continue
#             last_id += len(new_links)
#             existing_links.extend(new_links)
#             df = pd.DataFrame(existing_links)
#             print(f"Total number of links: {len(df)}")
#             scraper.write_json(prefix='reference/sellers', type='links', data=existing_links)
#         except Exception as e:
#             print(f"Error occurred at page {page_num}: {e}")