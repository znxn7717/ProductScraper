from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl, validator
from Scraper import ProductScraper

app = FastAPI()
scraper = ProductScraper()

class URLItem(BaseModel):
    seller_url: HttpUrl
    sid: str

    @validator('seller_url')
    def validate_url(cls, v):
        allowed_domains = ['basalam.com', 'torob.com', 'digikala.com']
        url_str = str(v)  # Convert HttpUrl to string
        if not any(domain in url_str for domain in allowed_domains):
            raise ValueError('URL must be from one of the allowed domains: basalam.com, torob.com, digikala.com')
        return v

@app.post("/scrape/")
async def scrape(item: URLItem):
    url = str(item.seller_url)  # Convert HttpUrl to string
    sid = item.sid

    if 'basalam.com' in url:
        scraper.basalam_products_details_extractor(url, sid)
    elif 'torob.com' in url:
        scraper.torob_products_details_extractor(url, sid)
    elif 'digikala.com' in url:
        scraper.digikala_products_details_extractor(url, sid)
    else:
        raise HTTPException(status_code=400, detail="Unsupported URL")

    return {"message": "Scraping started successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)