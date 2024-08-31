import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from extractors import ProductExtractor
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from requests.packages.urllib3.exceptions import InsecureRequestWarning

scraper = ProductExtractor()

def sort_json_by_id():
    json = scraper.read_json(prefix='reference/sellers', type='details')
    sorted_json = sorted(json, key=lambda x: x['id'])
    scraper.write_json(prefix='reference/sellers', type='details', data=sorted_json)

def read_counter():
    if os.path.exists('data/reference/seller_details_scounter.txt'):
        with open('data/reference/seller_details_scounter.txt', 'r') as f:
            content = f.read().strip()
            if content:
                return int(content.split(' | ')[0])
    return 0

def write_counter(i, ID):
    with open('data/reference/seller_details_scounter.txt', 'w') as f:
        f.write(f'{i} | {ID}\r')

def contact_info(soup, phone_pattern, email_pattern, whatsapp_patterns, telegram_patterns, instagram_patterns):
    phone_numbers = set(re.findall(phone_pattern, soup.get_text(separator=' ')))
    emails = set(re.findall(email_pattern, soup.get_text(separator=' ')))
    emails = {email.replace('[at]', '@').replace('[dot]', '.') for email in emails}
    whatsapp = set()
    telegram = set()
    instagram = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if any(re.search(pattern, href) for pattern in whatsapp_patterns):
            whatsapp.add(href)
            phone_match = re.search(r'phone=(98\d{10})', href)
            if not phone_match:
                phone_match = re.search(r'wa\.me/(98\d{10})', href)
            if phone_match:
                phone_number = phone_match.group(1)
                phone_number = '0' + phone_number[2:]
                phone_numbers.add(phone_number)
        if any(re.search(pattern, href) for pattern in telegram_patterns):
            telegram.add(href)
        if any(re.search(pattern, href) for pattern in instagram_patterns):
            instagram.add(href)
    return phone_numbers, emails, whatsapp, telegram, instagram

def xci_extend(sellers_details, new_phone_numbers, new_emails, new_whatsapp, new_telegram, new_instagram):
    if 'xci' not in sellers_details:
        sellers_details['xci'] = {}
    if new_phone_numbers:
        if 'phone_numbers' not in sellers_details['xci']:
            sellers_details['xci']['phone_numbers'] = list(new_phone_numbers)
        else:
            sellers_details['xci']['phone_numbers'].extend(list(new_phone_numbers))
    if new_emails:
        if 'emails' not in sellers_details['xci']:
            sellers_details['xci']['emails'] = list(new_emails)
        else:
            sellers_details['xci']['emails'].extend(list(new_emails))
    if new_whatsapp:
        if 'whatsapp' not in sellers_details['xci']:
            sellers_details['xci']['whatsapp'] = list(new_whatsapp)
        else:
            sellers_details['xci']['whatsapp'].extend(list(new_whatsapp))
    if new_telegram:
        if 'telegram' not in sellers_details['xci']:
            sellers_details['xci']['telegram'] = list(new_telegram)
        else:
            sellers_details['xci']['telegram'].extend(list(new_telegram))
    if new_instagram:
        if 'instagram' not in sellers_details['xci']:
            sellers_details['xci']['instagram'] = list(new_instagram)
        else:
            sellers_details['xci']['instagram'].extend(list(new_instagram))

def remove_duplicates(xci_data):
    if 'phone_numbers' in xci_data:
        xci_data['phone_numbers'] = list(set(xci_data['phone_numbers']))
    if 'emails' in xci_data:
        xci_data['emails'] = list(set(xci_data['emails']))
    if 'whatsapp' in xci_data:
        xci_data['whatsapp'] = list(set(xci_data['whatsapp']))
    if 'telegram' in xci_data:
        xci_data['telegram'] = list(set(xci_data['telegram']))
    if 'instagram' in xci_data:
        xci_data['instagram'] = list(set(xci_data['instagram']))

def sellers_crawler():
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    if os.path.exists('data/reference/sellers_details.json'):
        existing_sellers_details = scraper.read_json(prefix='reference/sellers', type='details')
    start_index = read_counter()
    for i in range(start_index, len(existing_sellers_details)):
        if 'xci' in existing_sellers_details[i]:
            continue
        ID = existing_sellers_details[i]['id']
        SU = existing_sellers_details[i]['su']
        write_counter(i, ID)
        try:
            phone_pattern = r'(?:\+98|0098|۰۹|0?9)\d{9}'
            email_pattern = r'[a-zA-Z0-9._%+-]+(?:\[at\]|@)[a-zA-Z0-9.-]+(?:\[dot\]|\.)[a-zA-Z]{2,}'
            whatsapp_patterns = [r'api\.whatsapp\.com', r'wa\.me']
            telegram_patterns = [r't\.me', r'telegram\.me', r'telegram\.com']
            instagram_patterns = [r'instagram\.com']
            response = requests.get(SU, verify=False)
            if response.status_code != 200:
                if "offline-shop.torob.ir" in SU:
                    phone_match = re.findall(phone_pattern, existing_sellers_details[i]['ci'])
                    persian_to_english_digits = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
                    phone_match = [phone.translate(persian_to_english_digits) for phone in phone_match]
                    existing_sellers_details[i]['xci'] = {
                        'phone_numbers': phone_match
                    }
                    print(f'>>>>> at {i} | {ID} ("su" : {SU}): {existing_sellers_details[i]["xci"]}')
                else:
                    print(f'>>>>> at {i} | {ID} ("su" : {SU}): Failed to fetch page. Status code: {response.status_code}')
                    existing_sellers_details[i]['xci'] = {
                        'error': f"Failed to fetch page. Status code: {response.status_code}"
                    }
                scraper.write_json(data=existing_sellers_details, prefix='reference/sellers', type='details')
                continue
            soup = BeautifulSoup(response.content, 'html.parser')
            phone_numbers, emails, whatsapp, telegram, instagram = contact_info(
                soup, phone_pattern, email_pattern, whatsapp_patterns, telegram_patterns, instagram_patterns)
            xci_extend(existing_sellers_details[i], phone_numbers, emails, whatsapp, telegram, instagram)
            contact_tag = soup.find('a', href=re.compile(r"contact|%D8%AA%D9%85%D8%A7%D8%B3", re.IGNORECASE))
            if not contact_tag:
                contact_tag = soup.find(lambda tag: tag.name == 'a' and tag.find_all(text=re.compile(r"تماس با|ارتباط با", re.IGNORECASE)))
            if contact_tag and contact_tag.get('href'):
                contact_url = contact_tag['href']
                contact_url = urljoin(SU, contact_url)
                contact_response = requests.get(contact_url, verify=False)
                if contact_response.status_code != 200:
                    print(f'>>>>> at {i} | {ID} ("su" : {SU}): Failed to fetch contact page. Status code: {contact_response.status_code}')
                    existing_sellers_details[i]['xci'] = {
                        'error': f"Failed to fetch contact page. Status code: {contact_response.status_code}"
                    }
                    continue
                contact_soup = BeautifulSoup(contact_response.content, 'html.parser')
                phone_numbers, emails, whatsapp, telegram, instagram = contact_info(
                    contact_soup, phone_pattern, email_pattern, whatsapp_patterns, telegram_patterns, instagram_patterns)
                xci_extend(existing_sellers_details[i], phone_numbers, emails, whatsapp, telegram, instagram)
                # existing_sellers_details[i]['xci']['emails'].append(f'info@{SU.split("//")[-1].split("/")[0]}')
                remove_duplicates(existing_sellers_details[i]['xci'])
                scraper.write_json(data=existing_sellers_details, prefix='reference/sellers', type='details')
                print(f'>>>>> at {i} | {ID} ("su" : {SU}): {existing_sellers_details[i]["xci"]}')
            else:
                print(f'>>>>> at {i} | {ID} ("su" : {SU}): Contact link not found')
                existing_sellers_details[i]['xci'] = {
                    'error': "Contact link not found"
                }
                continue
        except Exception as e:
            print(f'>>>>> at {i} | {ID} ("su" : {SU}): {e}')
            existing_sellers_details[i]['xci'] = {
                'error': f'{e}'
            }
            continue

def sellers_details_extractor_wd(check_missing_ids=False):
    driver = scraper.init_firefox_driver()
    existing_sellers_details = []
    
    if os.path.exists('data/reference/sellers_details.json'):
        existing_sellers_details = scraper.read_json(prefix='reference/sellers', type='details')
    
    if check_missing_ids:
        existing_ids = {detail['id'] for detail in existing_sellers_details}
        all_ids = set(range(1, 160000))
        inrange = sorted(list(all_ids - existing_ids))
    else:
        last_id = existing_sellers_details[-1]['id'] if existing_sellers_details else 0
        inrange = range(last_id + 1, 160000)
    
    new_sellers_details = []
    
    for i in inrange:
        try:
            driver.get(f'https://torob.com/shop/{i}/')
            wait = WebDriverWait(driver, 3)
            header_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'tr.jsx-637019445:nth-child(1) > td:nth-child(1) > h2:nth-child(1)')))
            
            if header_element.text in ['مجوزها و اعتبار', 'سابقه همکاری با ترب']:
                try:
                    seller_name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ShopInfoHeader_title__8wNZ0 > h1:nth-child(1)'))).text
                except Exception:
                    seller_name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ShopInfoHeader_shopName__6Vmrc'))).text
                
                try:
                    seller_url = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ShopInfoHeader_title__8wNZ0 > a:nth-child(2)'))).get_attribute('href')
                except Exception:
                    seller_url = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.ShopInfoHeader_white__XJYKB'))).get_attribute('href')
                
                try:
                    seller_location = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#province-city'))).text
                except Exception:
                    seller_location = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.ShopInfoHeader_white__XJYKB'))).text
                
                history_of_cooperation_selector = 'tr.jsx-637019445:nth-child(2) > td:nth-child(2)' if header_element.text == 'مجوزها و اعتبار' else 'tr.jsx-637019445:nth-child(1) > td:nth-child(2)'
                performance_score_selector = 'tr.jsx-637019445:nth-child(3) > td:nth-child(2)' if header_element.text == 'مجوزها و اعتبار' else 'tr.jsx-637019445:nth-child(2) > td:nth-child(2)'
                contact_information_selector = 'tr.jsx-637019445:nth-child(8) > td:nth-child(2)' if header_element.text == 'مجوزها و اعتبار' else 'tr.jsx-637019445:nth-child(7) > td:nth-child(2)'
                
                history_of_cooperation = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, history_of_cooperation_selector))).text
                performance_score = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, performance_score_selector))).text
                contact_information = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, contact_information_selector))).text
                
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





# def sellers_details_extractor_wd():
#     driver = scraper.init_firefox_driver()
#     existing_sellers_details = []
#     if os.path.exists('data/reference/sellers_details.json'):
#         existing_sellers_details = scraper.read_json(prefix='reference/sellers', type='details')
#     last_id = existing_sellers_details[-1]['id'] if existing_sellers_details else 0
#     new_sellers_details = []
#     for i in range(last_id + 1 , 160000):
#         try:
#             driver.get(f'https://torob.com/shop/{i}/')
#             wait = WebDriverWait(driver, 3)
#             header_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'tr.jsx-637019445:nth-child(1) > td:nth-child(1) > h2:nth-child(1)')))
#             if header_element.text in ['مجوزها و اعتبار', 'سابقه همکاری با ترب']:
#                 try:
#                     seller_name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ShopInfoHeader_title__8wNZ0 > h1:nth-child(1)'))).text
#                 except Exception:
#                     seller_name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ShopInfoHeader_shopName__6Vmrc'))).text
#                 try:
#                     seller_url = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ShopInfoHeader_title__8wNZ0 > a:nth-child(2)'))).get_attribute('href')
#                 except Exception:
#                     seller_url = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.ShopInfoHeader_white__XJYKB'))).get_attribute('href')
#                 try:
#                     seller_location = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#province-city'))).text
#                 except Exception:
#                     seller_location = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.ShopInfoHeader_white__XJYKB'))).text
#                 history_of_cooperation_selector = 'tr.jsx-637019445:nth-child(2) > td:nth-child(2)' if header_element.text == 'مجوزها و اعتبار' else 'tr.jsx-637019445:nth-child(1) > td:nth-child(2)'
#                 performance_score_selector = 'tr.jsx-637019445:nth-child(3) > td:nth-child(2)' if header_element.text == 'مجوزها و اعتبار' else 'tr.jsx-637019445:nth-child(2) > td:nth-child(2)'
#                 contact_information_selector = 'tr.jsx-637019445:nth-child(8) > td:nth-child(2)' if header_element.text == 'مجوزها و اعتبار' else 'tr.jsx-637019445:nth-child(7) > td:nth-child(2)'
#                 history_of_cooperation = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, history_of_cooperation_selector))).text
#                 performance_score = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, performance_score_selector))).text
#                 contact_information = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, contact_information_selector))).text
#                 new_sellers_details.append({
#                     'id': i,
#                     'sn': seller_name,
#                     'su': seller_url,
#                     'sl': seller_location,
#                     'hof': history_of_cooperation,
#                     'ps': performance_score,
#                     'ci': contact_information
#                 })
#             sellers_details = existing_sellers_details + new_sellers_details
#             df = pd.DataFrame(sellers_details)
#             print(f"Total number of links: {len(df)} | id: {i}")
#             scraper.write_json(prefix='reference/sellers', type='details', data=sellers_details)
#         except Exception as e:
#             print(f"Error occurred at {i}: {e}")
#             continue

def sellers_details_extractor_bs4():
    existing_sellers_details = []
    if os.path.exists('data/reference/sellers_details.json'):
        existing_sellers_details = scraper.read_json(prefix='reference/sellers', type='details')
    last_id = existing_sellers_details[-1]['id'] if existing_sellers_details else 0
    new_sellers_details = []

    for i in range(last_id + 1 , 150000):
        try:
            response = requests.get(f'https://torob.com/shop/{i}/')
            if response.status_code != 200:
                print(f"Failed to fetch page {i}. Status code: {response.status_code}")
                continue
            soup = BeautifulSoup(response.content, 'html.parser')
            header_element = soup.select_one('tr.jsx-637019445:nth-child(1) > td:nth-child(1) > h2:nth-child(1)')
            if header_element.get_text() in ['مجوزها و اعتبار', 'سابقه همکاری با ترب']:
                try:
                    seller_name = soup.select_one('.ShopInfoHeader_title__8wNZ0 > h1:nth-child(1)').get_text()
                except:
                    seller_name = soup.select_one('.ShopInfoHeader_shopName__6Vmrc').get_text()
                try:
                    seller_url = soup.select_one('.ShopInfoHeader_title__8wNZ0 > a:nth-child(2)').get('href')
                except:
                    seller_url = soup.select_one('a.ShopInfoHeader_white__XJYKB').get('href')
                try:
                    seller_location = soup.select_one('#province-city').get_text()
                except:
                    seller_location = soup.select_one('div.ShopInfoHeader_white__XJYKB').get_text()
                history_of_cooperation_selector = 'tr.jsx-637019445:nth-child(2) > td:nth-child(2)' if header_element.get_text() == 'مجوزها و اعتبار' else 'tr.jsx-637019445:nth-child(1) > td:nth-child(2)'
                performance_score_selector = 'tr.jsx-637019445:nth-child(3) > td:nth-child(2)' if header_element.get_text() == 'مجوزها و اعتبار' else 'tr.jsx-637019445:nth-child(2) > td:nth-child(2)'
                contact_information_selector = 'tr.jsx-637019445:nth-child(8) > td:nth-child(2)' if header_element.get_text() == 'مجوزها و اعتبار' else 'tr.jsx-637019445:nth-child(7) > td:nth-child(2)'
                history_of_cooperation = soup.select_one(history_of_cooperation_selector).get_text()
                performance_score = soup.select_one(performance_score_selector).get_text()
                contact_information = soup.select_one(contact_information_selector).get_text()
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



# def sellers_details_extractor():
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




# def structure_data():
#     existing_sellers_details = scraper.read_json(prefix='reference/sellers', type='details')
#     for item in existing_sellers_details:
#         hof_cleaned = item['hof'].replace("\n", " ").replace("ترب", "").strip()
#         hof_parts = re.split(r'وضعیت فعلی در :|زمان فعالیت در :|شروع همکاری با :', hof_cleaned)
#         item['hof'] = {}
#         if len(hof_parts) > 1:
#             item['hof']["وضعیت"] = hof_parts[1].strip()
#         if len(hof_parts) > 2:
#             item['hof']["زمان فعالیت"] = hof_parts[2].strip()
#         if len(hof_parts) > 3:
#             item['hof']["شروع"] = hof_parts[3].strip()
#         ps_cleaned = item['ps'].replace("\n", " ").replace("ترب", "").strip()
#         ps_parts = re.split(r'کاربری در|پیگیری سفارش|امتیاز:', ps_cleaned)
#         item['ps'] = {}
#         if len(ps_parts) > 1:
#             item['ps']["امتیاز"] = ps_parts[1].strip()
#         if len(ps_parts) > 2:
#             item['ps']["پیگیری سفارش"] = ps_parts[2].strip()
#         ci_cleaned = item['ci'].replace("\n", " ").replace("ترب", "").strip()
#         ci_parts = re.split(r'دامنه:|آدرس:', ci_cleaned)
#         item['ci'] = {}
#         if len(ci_parts) > 1:
#             item['ci']["دامنه"] = ci_parts[1].strip()
#         if len(ci_parts) > 2:
#             item['ci']["آدرس"] = ci_parts[2].strip()
#     scraper.write_json(data=existing_sellers_details, prefix='reference/sellers', type='details')