import requests
import json
from bs4 import BeautifulSoup
import os
import time

def get_product_data(browse_id, existing_categories):
    url = f"https://torob.com/browse/{browse_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code.
    except requests.exceptions.RequestException as e:
        print(f"Error occurred for browse_id {browse_id}: {e}")
        return None
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        c2 = soup.select_one("li.jsx-72379d3b42dfae8d:nth-child(2) > a:nth-child(1)")
        c3 = soup.select_one("li.jsx-72379d3b42dfae8d:nth-child(3) > a:nth-child(1)")
        c4 = soup.select_one("li.jsx-72379d3b42dfae8d:nth-child(4) > a:nth-child(1)")
        c5 = soup.select_one("li.jsx-72379d3b42dfae8d:nth-child(5) > a:nth-child(1)")
        c6 = soup.select_one("li.jsx-72379d3b42dfae8d:nth-child(6) > a:nth-child(1)")
        
        if c6:
            product_group = f'{c2.get_text(strip=True)}>{c3.get_text(strip=True)}>{c4.get_text(strip=True)}>{c5.get_text(strip=True)}>{c6.get_text(strip=True)}'
        elif c5:
            product_group = f'{c2.get_text(strip=True)}>{c3.get_text(strip=True)}>{c4.get_text(strip=True)}>{c5.get_text(strip=True)}'
        elif c4:
            product_group = f'{c2.get_text(strip=True)}>{c3.get_text(strip=True)}>{c4.get_text(strip=True)}'
        elif c3:
            product_group = f'{c2.get_text(strip=True)}>{c3.get_text(strip=True)}'
        elif c2:
            product_group = c2.get_text(strip=True)
        else:
            return None
        
        if product_group not in existing_categories.values():
            return {
                "browse_id": browse_id,
                "product_group": product_group
            }
    
    return None

def main():
    json_file = "data/torob_categories.json"
    
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
    else:
        data = []

    existing_categories = {entry["browse_id"]: entry["product_group"] for entry in data}
    
    last_browse_id = max([entry["browse_id"] for entry in data], default=0)
    
    for browse_id in range(last_browse_id + 1, 7001):
        result = get_product_data(browse_id, existing_categories)
        if result:
            data.append(result)
            existing_categories[result["browse_id"]] = result["product_group"]
        
        print(browse_id)
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        
        time.sleep(1)

if __name__ == "__main__":
    main()
