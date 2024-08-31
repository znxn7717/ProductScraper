@echo off
call .venv\Scripts\activate
start cmd /k "celery -A celery_app.celery_app worker --loglevel=info -P threads"
@REM start cmd /k "py api.py"
start cmd /k "uvicorn api:app --reload --port 8000"
start cmd /k "uvicorn api:app --reload --port 8001"
start cmd /k "cd client_nuxt && pnpm run dev"
start cmd /k "E:\xampp\xampp-control.exe"
start cmd /k "E:\xampp\mysql_start"
start cmd /k "E:\xampp\apache_start"
