import json
import pandas as pd
import os

def categories_sorter(path):

    base_name = os.path.splitext(os.path.basename(path))[0]

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sorted_data = sorted(data, key=lambda x: x['product_group'])

    df = pd.DataFrame(sorted_data, columns=['product_group', 'pid'])

    df.to_excel(f'data/sorted_{base_name}.xlsx', index=False)

    with open(f'data/sorted_{base_name}.json', 'w', encoding='utf-8') as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=4)

    print(f"داده‌ها مرتب‌سازی شده و در فایل sorted_{base_name}.json ذخیره شدند.")

