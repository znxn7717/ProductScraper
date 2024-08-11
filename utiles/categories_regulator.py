import os
import json
# import torch
import numpy as np
from rapidfuzz import process
from collections import defaultdict
# from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity


def generate_report():
    with open('data/basalam_categories.json', 'r', encoding='utf-8') as file:
        basalam_categories = json.load(file)
    with open('data/notused_listed_sorted_torob_categories.json', 'r', encoding='utf-8') as file:
        notused_torob_categories = json.load(file)
    with open('data/listed_sorted_torob_categories.json', 'r', encoding='utf-8') as file:
        listed_torob_categories = json.load(file)
    with open('data/fuzzed_listed_sorted_torob_categories.json', 'r', encoding='utf-8') as file:
        fuzzed_torob_categories = json.load(file)
    duplicate_keys = [key for key, count in defaultdict(int, ((key, 1) for key in fuzzed_torob_categories)).items() if count > 1]
    value_count = defaultdict(int)
    for values in fuzzed_torob_categories.values():
        for value in values:
            value_count[value] += 1
    duplicate_values = [value for value, count in value_count.items() if count > 1]
    unused_basalam_categories = [item for item in basalam_categories if item not in fuzzed_torob_categories]
    extra_fuzzed_keys = [key for key in fuzzed_torob_categories if key not in basalam_categories]
    unused_notused_values = [item for item in notused_torob_categories if item not in value_count]
    extra_fuzzed_values = [value for value in value_count if value not in listed_torob_categories]
    report = {
        "duplicate_keys": duplicate_keys,
        "duplicate_values": duplicate_values,
        "unused_basalam_keys": unused_basalam_categories,
        "extra_fuzzed_keys": extra_fuzzed_keys,
        "unused_notused_values": unused_notused_values,
        "extra_fuzzed_values": extra_fuzzed_values,
    }
    with open("data/report.json", "w", encoding='utf-8') as file:
        json.dump(report, file, ensure_ascii=False, indent=4)
    print("گزارش با موفقیت تولید شد و در فایل '{}' ذخیره گردید.".format("data/report.json"))


def merge_json(path1, path2, pathr):
    with open('data/basalam_categories.json', 'r', encoding='utf-8') as f_cat:
        category_order = json.load(f_cat)
    with open(path1, 'r', encoding='utf-8') as f1, open(path2, 'r', encoding='utf-8') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)
    merged_data = {}
    for key in set(data1.keys()).union(data2.keys()):
        merged_data[key] = sorted(list(set(data1.get(key, []) + data2.get(key, []))))
    sorted_merged_data = {key: merged_data[key] for key in category_order if key in merged_data}
    with open(pathr, 'w', encoding='utf-8') as f_out:
        json.dump(sorted_merged_data, f_out, ensure_ascii=False, indent=4)


def filter_by_string(path, string):
    with open(path, 'r', encoding='utf-8') as infile:
        data = json.load(infile)
    filtered_items = [item for item in data if string in str(item)]
    remaining_items = [item for item in data if string not in str(item)]
    os.makedirs(os.path.dirname(f'data/{string}.json'), exist_ok=True)
    with open(f'data/{string}.json', 'w', encoding='utf-8') as outfile:
        json.dump(filtered_items, outfile, indent=4, ensure_ascii=False)
    with open(path, 'w', encoding='utf-8') as outfile:
        json.dump(remaining_items, outfile, indent=4, ensure_ascii=False)


def categories_to_list(inpath, outpath):
    with open(inpath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    product_groups = [item["product_group"] for item in data]
    product_groups = [group for group in product_groups if group.count('>') >= 1]
    with open(outpath, 'w', encoding='utf-8') as output_file:
        json.dump(product_groups, output_file, ensure_ascii=False, indent=4)


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


def categories_fuzz(path, threshold=87):
    base_name = os.path.splitext(os.path.basename(path))[0]
    with open('data/basalam_categories.json', 'r', encoding='utf-8') as f:
        categories = json.load(f)        
    final_dict = {category: [] for category in categories}
    unused_products = []
    if os.path.exists(f'data/notused_{base_name}.json'):
        with open(f'data/notused_{base_name}.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
    else:
        with open(path, 'r', encoding='utf-8') as f:
            products = json.load(f)
    # تنظیم یک آستانه برای تطبیق (بین 0 تا 100)
    threshold = threshold
    # تطبیق دسته‌بندی‌ها و محصولات با استفاده از تطبیق مبهم
    for product in products:
        product_group = product #['product_group']
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
            products = json.load(f)
    else:
        with open(path, 'r', encoding='utf-8') as f:
            products = json.load(f)
    # تبدیل جملات دسته‌بندی به امبدینگ
    def get_embedding(text):
        inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True)
        outputs = model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).detach().numpy()
    category_embeddings = {category: get_embedding(category) for category in categories}
    # تطبیق دسته‌بندی‌ها و محصولات
    for product in products:
        product_group = product #['product_group']
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

