import os
import json
# import torch
import numpy as np
from rapidfuzz import process
# from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity

def merge_json(path1, path2, pathr):
    with open(path1, 'r') as f1, open(path2, 'r') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)
    merged_data = {}
    for key in set(data1.keys()).union(data2.keys()):
        merged_data[key] = sorted(list(set(data1.get(key, []) + data2.get(key, []))))
    with open(pathr, 'w') as f_out:
        json.dump(merged_data, f_out, indent=4)

def categories_fuzz(path, threshold=86):
    base_name = os.path.splitext(os.path.basename(path))[0]
    
    if os.path.exists(f'data/notused_{base_name}.json'):
        with open(f'data/notused_{base_name}.json', 'r', encoding='utf-8') as f:
            categories = json.load(f)
    else:
        with open('data/basalam_categories.json', 'r', encoding='utf-8') as f:
            categories = json.load(f)        

    final_dict = {category: [] for category in categories}

    unused_products = []

    with open(path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    # تنظیم یک آستانه برای تطبیق (بین 0 تا 100)
    threshold = threshold

    # تطبیق دسته‌بندی‌ها و محصولات با استفاده از تطبیق مبهم
    for product in products:
        product_group = product['product_group']
        best_match, score, _ = process.extractOne(product_group, categories)
        # بررسی اینکه آیا امتیاز تطبیق بیشتر از آستانه است یا نه
        if score >= threshold:
            final_dict[best_match].append(product_group)
        else:
            unused_products.append(product)

    with open(f'data/fuzzed_{base_name}.json', 'w', encoding='utf-8') as f:
        json.dump(final_dict, f, ensure_ascii=False, indent=4)

    with open(f'data/notused_{base_name}.json', 'w', encoding='utf-8') as f:
        json.dump(unused_products, f, ensure_ascii=False, indent=4)

    print("دیتا با موفقیت ذخیره شد.")


def categories_hoosh(path, threshold=0.85):
    base_name = os.path.splitext(os.path.basename(path))[0]

    # لود کردن مدل و tokenizer
    model_name = "HooshvareLab/bert-fa-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    
    with open('data/basalam_categories.json', 'r', encoding='utf-8') as f:
        categories = json.load(f)

    final_dict = {category: [] for category in categories}

    unused_products = []

    if os.path.exists(f'data/notused_{base_name}.json'):
        with open(f'data/notused_{base_name}.json', 'r', encoding='utf-8') as f:
            categories = json.load(f)
    else:
        with open('data/basalam_categories.json', 'r', encoding='utf-8') as f:
            categories = json.load(f)

    # تبدیل جملات دسته‌بندی به امبدینگ
    def get_embedding(text):
        inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True)
        outputs = model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).detach().numpy()

    category_embeddings = {category: get_embedding(category) for category in categories}

    # تطبیق دسته‌بندی‌ها و محصولات
    for product in products:
        product_group = product['product_group']
        product_embedding = get_embedding(product_group)

        best_match = None
        best_score = 0

        for category, category_embedding in category_embeddings.items():
            score = cosine_similarity(product_embedding, category_embedding)[0][0]
            if score > best_score:
                best_match = category
                best_score = score

        # بررسی اینکه آیا امتیاز تطبیق بیشتر از آستانه است یا نه
        if best_score >= threshold:
            final_dict[best_match].append(product_group)
        else:
            unused_products.append(product)

    with open(f'data/hooshed_{base_name}.json', 'w', encoding='utf-8') as f:
        json.dump(final_dict, f, ensure_ascii=False, indent=4)

    with open(f'data/notused_{base_name}.json', 'w', encoding='utf-8') as f:
        json.dump(unused_products, f, ensure_ascii=False, indent=4)

    print("دیتا با موفقیت ذخیره شد.")

