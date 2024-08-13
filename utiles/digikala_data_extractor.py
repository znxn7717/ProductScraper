import requests
import json
import time
import os

def get_product_data(product_id):
    url = f"https://api.digikala.com/v2/product/{product_id}/"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json().get('data', {})
            product = data.get('product', {})
            product_id = product.get('id')
            product_title_fa = product.get('title_fa')
            product_title_en = product.get('title_en')

            product_data_layer = product.get('data_layer', {})
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

            images = product.get('images', {})
            main_image_url = images.get('main', {}).get('url', [None])[0]
            list_images = images.get('list', [])
            list_image_urls = [img.get('url', [None])[0] for img in list_images]
            
            product_brand = product.get('brand', {})
            brand_fa = product_brand.get('title_fa', '')
            brand_en = product_brand.get('title_en', '')

            return product_id, product_title_fa, product_title_en, brand_fa, brand_en, product_group, main_image_url, list_image_urls
    except requests.RequestException as e:
        print(f"خطا در ارسال درخواست: {e}")
    return None, None, None, None, None, None, None, None

def load_checkpoint(checkpoint_file):
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as file:
            return json.load(file)
    return {}

def save_checkpoint(checkpoint_file, checkpoints):
    with open(checkpoint_file, 'w') as file:
        json.dump(checkpoints, file, ensure_ascii=False, indent=4)

def main(start_id, end_id, tid, checkpoint_file):
    results = []
    try:
        with open('data/digikala_data.json', 'r', encoding='utf-8') as file:
            results = json.load(file)
    except FileNotFoundError:
        pass

    # Load checkpoints and get last processed ID for this terminal
    checkpoints = load_checkpoint(checkpoint_file)
    last_processed_id = checkpoints.get(str(tid), start_id)

    for product_id in range(last_processed_id, end_id + 1):
        pid, title_fa, title_en, brand_fa, brand_en, pgroup, main_image_url, list_image_urls = get_product_data(product_id)
        if pid:
            results.append({
                'pid': pid,
                'title_fa': title_fa,
                'title_en': title_en,
                'brand_fa': brand_fa,
                'brand_en': brand_en,
                'product_group': pgroup,
                'main_image_url': main_image_url,
                'list_image_urls': list_image_urls
            })
            with open('data/digikala_data.json', 'w', encoding='utf-8') as file:
                json.dump(results, file, ensure_ascii=False, indent=4)
            
            # Save the current product_id as the last processed for this terminal
            checkpoints[str(tid)] = product_id
            save_checkpoint(checkpoint_file, checkpoints)
        
        time.sleep(1)

if __name__ == "__main__":
    # Example for terminal 1
    main(start_id=0, end_id=4250000, tid=1, checkpoint_file='checkpoint.json')

    # Example for terminal 2
    # main(start_id=4250001, end_id=8500000, tid=2, checkpoint_file='checkpoint.json')

    # Example for terminal 3
    # main(start_id=8500001, end_id=12750000, tid=3, checkpoint_file='checkpoint.json')

    # Example for terminal 4
    # main(start_id=12750001, end_id=17000000, tid=4, checkpoint_file='checkpoint.json')
