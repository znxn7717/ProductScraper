# api.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from models import URLItem, Origin, RateLimit, CSRF, APIKeyManager, ConnectionManager
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from celery_app import celery_app, run_scraper, redis_client
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio

app = FastAPI()
manager = ConnectionManager()
csrf_protect = CSRF()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_manager = APIKeyManager()

@app.get("/get-csrf-token")
async def get_csrf_token():
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = JSONResponse({"csrf_token": csrf_token})
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response

def api_key_then_rate_limit(
    api_key: str = Depends(api_key_manager.get_api_key),
    rate_limit: None = Depends(RateLimit(0.3))
):
    # اگر API key معتبر باشد، محدودیت نرخ اعمال می‌شود
    return rate_limit

@app.post("/scrape", dependencies=[Depends(Origin), Depends(api_key_then_rate_limit), Depends(csrf_protect.validate_csrf)])
async def scrape(item: URLItem, request: Request):
    task = run_scraper.delay(str(item.seller_url), item.sid, item.products_num)
    response = JSONResponse(status_code=200, content={"detail": "OK"})
    csrf_protect.unset_csrf_cookie(response)
    return {"message": "Scraping started in background", "task_id": task.id}

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    task = run_scraper.AsyncResult(task_id)
    if task.state == 'PENDING':
        return {"status": "Pending"}
    elif task.state == 'SUCCESS':
        return {"status": "Success", "result": task.result}
    elif task.state == 'FAILURE':
        return {"status": "Failure", "error": str(task.info)}
    else:
        return {"status": task.state}

@app.websocket("/ws/{sid}")
async def websocket_endpoint(websocket: WebSocket, sid: str):
    await manager.connect(websocket)
    pubsub = redis_client.pubsub()
    pubsub.subscribe(f"progress_{sid}")
    try:
        while True:
            message = pubsub.get_message()
            if message and not message['type'] == 'subscribe':
                await manager.send_message(f"Progress: {message['data'].decode('utf-8')}%", websocket)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    finally:
        pubsub.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)