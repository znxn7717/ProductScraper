# api.py
import asyncio
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from celery_app import celery_app, run_scraper, redis_client
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from middlewares.models import URLItem, Origin, RateLimit, CSRF, APIKeyManager, ConnectionManager

app = FastAPI()
manager = ConnectionManager()
csrf_protect = CSRF()
api_key_manager = APIKeyManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    hashed_value = manager.get_hashed_header(request)
    task = run_scraper.delay(str(item.seller_url), item.sid, item.products_num, hashed_value)
    response = JSONResponse(status_code=200, content={"detail": "OK"})
    csrf_protect.unset_csrf_cookie(response)
    return {"message": "استخراج در پس‌زمینه در حال اجراست.", "task_id": task.id}

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
    hashed_value = manager.get_hashed_header(websocket)
    await manager.connect(websocket)
    redis_channel = f"Progress_{sid}_{hashed_value}"
    pubsub = redis_client.pubsub()
    pubsub.subscribe(redis_channel)
    try:
        while True:
            message = pubsub.get_message()
            if message and not message['type'] == 'subscribe':
                await manager.send_message(f"Progress_{sid}_{hashed_value}:{message['data'].decode('utf-8')}%", websocket)
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    finally:
        pubsub.close()


import uvicorn
import multiprocessing
def run_server(port):
    uvicorn.run("api:app", host="0.0.0.0", port=port)
if __name__ == "__main__":
    ports = [8000, 8001, 8002]
    processes = []
    for port in ports:
        p = multiprocessing.Process(target=run_server, args=(port,))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()