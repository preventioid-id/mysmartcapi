import os
import subprocess

os.chdir('c:\\xampp\\htdocs\\smartcapi_pwa\\smartcapi-backend')
subprocess.run(['uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'])
