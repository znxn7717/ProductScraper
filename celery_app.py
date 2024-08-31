# celery_app.py
import os
import redis
from celery import Celery
from dotenv import load_dotenv
from extractors.torob import Torob
from extractors.basalam import Basalam
from extractors.digikala import Digikala

load_dotenv()
redis_client = redis.Redis(host='localhost', port=6379, db=0)
celery_app = Celery(
    "scraper",
    broker=os.getenv('REDIS_BROKER'),  # setting Redis as broker
    backend=os.getenv('REDIS_BACKEND'),  # useing Redis for saving results
)

@celery_app.task(name="scrape_task")
def run_scraper(url, sid, products_num, hashed_value):
    redis_channel = f"Progress_{sid}_{hashed_value}"  # Create the Redis channel
    def progress_callback(progress):
        redis_client.publish(redis_channel, progress)
        print(f"Progress_{sid}_{hashed_value}: {progress}%")
    if 'torob.com' in url:
        torob = Torob()
        torob.torob_products_details_extractor(url, sid, products_num=products_num, progress_callback=progress_callback)
    elif 'basalam.com' in url:
        basalam = Basalam()
        basalam.basalam_products_details_extractor(url, sid, products_num=products_num, progress_callback=progress_callback)
    elif 'digikala.com' in url:
        digikala = Digikala()
        digikala.digikala_products_details_extractor(url, sid, products_num=products_num, progress_callback=progress_callback)
    else:
        raise HTTPException(status_code=400, detail="URL پشتیبانی نمی‌شود.")
    return "استخراج با موفقیت انجام شد."







# # celery_app.py
# import redis
# from celery import Celery
# from Test import ProductScraper

# redis_client = redis.Redis(host='localhost', port=6379, db=0)
# celery_app = Celery(
#     "scraper",
#     broker="redis://127.0.0.1:6379/0",  # setting Redis as broker
#     backend="redis://127.0.0.1:6379/0",  # useing Redis for saving results
# )

# @celery_app.task(name="scrape_task")
# def run_scraper(url, sid, products_num):
#     scraper = ProductScraper()
#     def progress_callback(progress):
#         redis_client.publish(f"progress_{sid}", progress)
#     if 'basalam.com' in url:
#         scraper.basalam_products_details_extractor(url, sid, products_num=products_num, progress_callback=progress_callback)
#     elif 'torob.com' in url:
#         scraper.torob_products_details_extractor(url, sid, products_num=products_num, progress_callback=progress_callback)
#     elif 'digikala.com' in url:
#         scraper.digikala_products_details_extractor(url, sid, products_num=products_num, progress_callback=progress_callback)
#     else:
#         raise HTTPException(status_code=400, detail="URL پشتیبانی نمی‌شود.")
#     return "استخراج با موفقیت انجام شد."