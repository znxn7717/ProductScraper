#celery_app.py
import redis
from celery import Celery
from Scraper import ProductScraper

redis_client = redis.Redis(host='localhost', port=6379, db=0)
celery_app = Celery(
    "scraper",
    broker="redis://127.0.0.1:6379/0",  # setting Redis as broker
    backend="redis://127.0.0.1:6379/0",  # useing Redis for saving results
)

@celery_app.task(name="scrape_task")
def run_scraper(url, sid, products_num):
    scraper = ProductScraper()
    def progress_callback(progress):
        redis_client.publish(f"progress_{sid}", progress)
    if 'basalam.com' in url:
        scraper.basalam_products_details_extractor(url, sid, products_num=products_num, progress_callback=progress_callback)
    elif 'torob.com' in url:
        scraper.torob_products_details_extractor(url, sid, products_num=products_num, progress_callback=progress_callback)
    elif 'digikala.com' in url:
        scraper.digikala_products_details_extractor(url, sid, products_num=products_num, progress_callback=progress_callback)
    else:
        raise HTTPException(status_code=400, detail="Unsupported URL")
    return "Scraping completed successfully"