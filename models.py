#models.py
from fastapi import WebSocket, HTTPException, Request, status, Response, Security
from itsdangerous import URLSafeTimedSerializer, BadData, SignatureExpired
from pydantic import BaseModel, HttpUrl, validator, conint
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.security.api_key import APIKeyHeader
from hashlib import sha1, sha256, sha512
from datetime import datetime, timedelta
from celery_app import redis_client
from Seller import SellerDatabase
from typing import Tuple
from typing import Union
from os import urandom
import secrets

class URLItem(BaseModel):
    seller_url: HttpUrl
    sid: str
    products_num: Union[str, conint(gt=0)]

    @validator('seller_url')
    def validate_url(cls, v):
        allowed_domains = ['basalam.com', 'torob.com', 'digikala.com']
        url_str = str(v)  # Convert HttpUrl to string
        if not any(domain in url_str for domain in allowed_domains):
            raise ValueError('URL must be from one of the allowed domains: basalam.com, torob.com, digikala.com')
        return v

    @validator('products_num', pre=True)
    def validate_products_num(cls, v):
        if isinstance(v, str):
            if v.isdigit():  # If the string is numeric, convert it to an integer
                return int(v)
            if v != 'auto':
                raise ValueError("products_num must be 'auto' or a positive integer")
        return v

class Origin:
    def __init__(self, request: Request):
        origin = request.headers.get("Origin")
        if origin not in ["http://localhost:3000", "https://localhost:3000"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="HTTP_403_FORBIDDEN: Invalid Origin")

class RateLimit:
    def __init__(self, limit_minutes, redis_client=redis_client):
        self.limit_minutes = limit_minutes
        self.redis_client = redis_client
    async def __call__(self, request: Request):
        try:
            request_body = await request.json()
            sid = request_body.get("sid")
            if not sid:
                raise HTTPException(status_code=400, detail="seller_id missing in request body")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid request body")
        key = f"last_request_time_{sid}"
        current_time = datetime.utcnow()
        last_request_time = self.redis_client.get(key)
        if last_request_time:
            last_request_time = datetime.fromisoformat(last_request_time.decode('utf-8'))
            time_difference = current_time - last_request_time
            if time_difference < timedelta(minutes=self.limit_minutes):
                raise HTTPException(status_code=429, detail=f"Too many requests. Please wait {self.limit_minutes} minutes before trying again.")
        self.redis_client.setex(key, timedelta(minutes=self.limit_minutes), current_time.isoformat())

class CSRF:
    def __init__(self, secret_key: str = None, cookie_key: str = "csrf_token"):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.cookie_key = cookie_key
        self.serializer = URLSafeTimedSerializer(self.secret_key, salt="fastapi-csrf-token")
    def generate_csrf_tokens(self) -> Tuple[str, str]:
        """Generate and sign a CSRF token."""
        random_data = urandom(64)
        token = sha1(random_data).hexdigest() + sha256(random_data).hexdigest() + sha512(random_data).hexdigest()
        signed_token = self.serializer.dumps(token)
        return token, signed_token
    def set_csrf_cookie(self, csrf_signed_token: str, response: Response) -> None:
        """Set CSRF token in the response cookies."""
        response.set_cookie(
            self.cookie_key,
            csrf_signed_token,
            max_age=3600,
            path="/",
            domain=None,
            secure=True,
            httponly=True,
            samesite="none",
        )
    def unset_csrf_cookie(self, response: Response) -> None:
        """Remove CSRF token from cookies."""
        response.delete_cookie(self.cookie_key)
    async def validate_csrf(self, request: Request) -> None:
        """Validate CSRF token from request against cookie token."""
        signed_token = request.cookies.get(self.cookie_key)
        if not signed_token:
            raise HTTPException(status_code=403, detail="Missing CSRF token in cookies.")
        token = request.headers.get("X-CSRF-Token") or (await request.form()).get("csrf_token")
        if not token:
            raise HTTPException(status_code=403, detail="Missing CSRF token in request.")
        try:
            original_token = self.serializer.loads(signed_token)
            if token != original_token:
                raise HTTPException(status_code=403, detail="Invalid CSRF token.")
        except (SignatureExpired, BadData):
            raise HTTPException(status_code=403, detail="Expired or invalid CSRF token.")

class APIKeyManager:
    def __init__(self, api_key_name: str = "APIKey"):
        self.api_key_header = APIKeyHeader(name=api_key_name, auto_error=False)
        self.db = SellerDatabase()
        self.free_trial = 50

    async def get_api_key(self, request: Request, api_key_header: str = Security(APIKeyHeader(name="APIKey", auto_error=False))):
        item = await request.json()
        sid = item.get('sid')
        products_num = item.get('products_num')
        if not sid:
            raise HTTPException(status_code=400, detail="Missing 'sid' in request body")
        
        _, seller_dict = self.db.fetch_seller_from_table(sid)
        scraper_apikey = seller_dict["scraper_apikey"]
        scraper_apikey_status = seller_dict["scraper_apikey_status"]
        total_scraped_product_num = seller_dict["total_scraped_product_num"]
        remaining_free_trial = self.free_trial - total_scraped_product_num

        if products_num == 'auto':
            # اگر products_num برابر 'auto' بود، وضعیت API Key بررسی می‌شود
            if int(scraper_apikey_status) != 1:
                raise HTTPException(status_code=403, detail=f"You can scrape {remaining_free_trial} products without API Key. Please provide API Key for the rest.")
            if api_key_header != scraper_apikey:
                raise HTTPException(status_code=403, detail=f"You can scrape {remaining_free_trial} products without API Key. Please provide API Key for the rest.")
            return  # پایان، چون بررسی‌ها انجام شدند

        # اگر products_num عددی باشد، ادامه می‌دهیم
        products_num = int(products_num)
        total_after_scraping = products_num + total_scraped_product_num

        # Check if total_after_scraping is within free trial limit
        if total_after_scraping <= self.free_trial:
            if remaining_free_trial >= products_num:
                # Proceed without checking API key, still within free trial
                return
            else:
                raise HTTPException(status_code=200, detail=f"You can scrape {remaining_free_trial} products without API Key. Please provide API Key for the rest.")

        # If over free trial limit, check API key
        if int(scraper_apikey_status) != 1:
            if remaining_free_trial > 0:
                raise HTTPException(status_code=403, detail=f"You can scrape {remaining_free_trial} products without API Key. Please provide API Key for the rest.")
            else:
                raise HTTPException(status_code=403, detail="APIKey status isn't allowed")

        if api_key_header != scraper_apikey:
            if remaining_free_trial > 0:
                raise HTTPException(status_code=403, detail=f"You can scrape {remaining_free_trial} products without API Key. Please provide API Key for the rest.")
            else:
                raise HTTPException(status_code=403, detail="Could not validate APIKey's credentials")

        # No need to return anything, validation is successful
        return

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)