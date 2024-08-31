# app.py
# windows
import subprocess

def start_services():
    command = r'start.bat'
    subprocess.Popen(['cmd', '/c', command], shell=True)

if __name__ == "__main__":
    start_services()

# import subprocess

# def activate_virtualenv():
#     command = r'.venv\Scripts\activate'
#     subprocess.Popen(['cmd', '/k', command], shell=True)

# def start_celery_workers():
#     command = 'celery -A celery_app.celery_app worker --loglevel=info -P threads'
#     subprocess.Popen(['start', 'cmd', '/k', command], shell=True)

# def start_uvicorn():
#     command = 'py api.py'
#     subprocess.Popen(['start', 'cmd', '/k', command], shell=True)

# def start_client_nuxt():
#     command = 'cd client_nuxt && pnpm run dev'
#     subprocess.Popen(['start', 'cmd', '/k', command], shell=True)

# def start_xampp():
#     xampp_control = r"E:\xampp\xampp-control.exe"
#     subprocess.Popen(['start', 'cmd', '/k', xampp_control], shell=True)
#     mysql_start = r"E:\xampp\mysql_start"
#     subprocess.Popen(['start', 'cmd', '/k', mysql_start], shell=True)
#     apache_start = r"E:\xampp\apache_start"
#     subprocess.Popen(['start', 'cmd', '/k', apache_start], shell=True)

# if __name__ == "__main__":
#     activate_virtualenv()
#     start_celery_workers()
#     start_uvicorn()
#     start_client_nuxt()
#     start_xampp()



# # linux
# import subprocess

# def start_celery_workers():
#     command = 'celery -A celery_app.celery_app worker --loglevel=info -P threads'
#     subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', command], shell=False)

# def start_uvicorn():
#     command = 'uvicorn api:app --host 0.0.0.0 --port 8000'
#     subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', command], shell=False)

# if __name__ == "__main__":
#     start_celery_workers()
#     start_uvicorn()



# import subprocess

# def start_celery_workers():
#     command = [
#         'celery',
#         '-A', 'celery_app.celery_app',
#         'worker',
#         '--loglevel=info',
#         '-P', 'threads'
#     ]
#     subprocess.run(command)
# def start_uvicorn():
# 	command = [
# 		'py', 'api.py'
# 	]
# 	subprocess.run(command)

# if __name__ == "__main__":
#     start_celery_workers()
# 	start_uvicorn()