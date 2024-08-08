import requests
import random
import json
import time

def get_product_data(product_id):
    url = f"https://api.digikala.com/v2/product/{product_id}/"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json().get('data', {})
            product = data.get('product', {})
            product_data_layer = product.get('data_layer', {})
            
            product_id = product.get('id')
            c2 = product_data_layer.get('item_category2', '')
            c3 = product_data_layer.get('item_category3', '')
            c4 = product_data_layer.get('item_category4', '')
            c5 = product_data_layer.get('item_category5', '')
            
            if c5:
                product_group = f'{c2}>{c3}>{c4}>{c5}'
            elif c4:
                product_group = f'{c2}>{c3}>{c4}'
            elif c3:
                product_group = f'{c2}>{c3}'
            else:
                product_group = c2
                
            return product_id, product_group
    except requests.RequestException as e:
        print(f"خطا در ارسال درخواست: {e}")
    return None, None

def main():
    results = []
    try:
        with open('digikala_categories.json', 'r', encoding='utf-8') as file:
            results = json.load(file)
    except FileNotFoundError:
        pass

    seen_groups = {item['product_group'] for item in results}
    
    for _ in range(100000000):
        product_id = random.randint(0, 17000000)
        pid, pgroup = get_product_data(product_id)
        
        if pid and pgroup and pgroup not in seen_groups:
            results.append({'pid': pid, 'product_group': pgroup})
            seen_groups.add(pgroup)
            with open('digikala_categories.json', 'w', encoding='utf-8') as file:
                json.dump(results, file, ensure_ascii=False, indent=4)
        
        time.sleep(1)

if __name__ == "__main__":
    main()
