import re
import json

def json_length(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return print(len(data))

def count_phone_numbers():
    with open('data/reference/sellers/phone_numbers1.json', 'r', encoding='utf-8') as f:
        sellers = json.load(f)
    count = 0
    for seller in sellers:
        if 'xci' in seller and 'phone_numbers' in seller['xci'] and seller['xci']['phone_numbers']:
            count += 1
    return print(count)

# Sift offline-shop.torob.ir
def filter1():
    with open('data/reference/sellers_details.json', 'r', encoding='utf-8') as f:
        sellers = json.load(f)
    filtered_sellers = []
    sieved_sellers = []
    for seller in sellers:
        if "offline-shop.torob.ir" in seller['su']:
            sieved_sellers.append(seller)
        else:
            filtered_sellers.append(seller)
    with open('data/reference/sellers_details.json', 'w', encoding='utf-8') as f:
        json.dump(filtered_sellers, f, ensure_ascii=False, indent=4)
    with open('data/reference/sellers/phone_numbers1.json', 'w', encoding='utf-8') as f:
        json.dump(sieved_sellers, f, ensure_ascii=False, indent=4)

def phone_match():
    with open('data/reference/sellers/phone_numbers1.json', 'r', encoding='utf-8') as f:
        sellers = json.load(f)
    phone_pattern = r'(?:\+98|0098|۰۹|09|0?9)\d{9}'
    persian_to_english_digits = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    for seller in sellers:
        phone_match = re.findall(phone_pattern, seller['ci'])
        phone_match = [phone.translate(persian_to_english_digits) for phone in phone_match]
        if 'xci' not in seller:
            seller['xci'] = {}
        seller['xci']['phone_numbers'] = phone_match
    with open('data/reference/sellers/phone_numbers1.json', 'w', encoding='utf-8') as f:
        json.dump(sellers, f, ensure_ascii=False, indent=4)