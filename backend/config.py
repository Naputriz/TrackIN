import os
import requests
from dotenv import load_dotenv

# Memuat variabel lingkungan dari file .env di folder yang sama dengan config.py
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path)

# Kredensial Astra DB (Dimuat dari file .env yang aman, tidak dipush ke GitHub)
ASTRA_DB_ID = os.getenv("ASTRA_DB_ID")
ASTRA_DB_REGION = os.getenv("ASTRA_DB_REGION", "us-east-2")
ASTRA_DB_KEYSPACE = os.getenv("ASTRA_DB_KEYSPACE", "trackin_ks")
ASTRA_DB_CLIENT_ID = os.getenv("ASTRA_DB_CLIENT_ID")
ASTRA_DB_CLIENT_SECRET = os.getenv("ASTRA_DB_CLIENT_SECRET")
ASTRA_DB_TOKEN = os.getenv("ASTRA_DB_TOKEN")

# Path ke Secure Connect Bundle yang didownload
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCB_PATH = os.path.join(BASE_DIR, "secure-connect-bundle.zip")

def download_secure_connect_bundle():
    """
    Downloads the secure connect bundle zip file programmatically from the DataStax Astra DevOps API.
    If it is already downloaded, it does nothing.
    """
    if os.path.exists(SCB_PATH):
        print(f"[+] Secure Connect Bundle already exists at: {SCB_PATH}")
        return SCB_PATH

    print("[*] Secure Connect Bundle not found. Attempting to download programmatically...")
    
    if not ASTRA_DB_ID or not ASTRA_DB_TOKEN:
        print("[-] Gagal mendownload: ASTRA_DB_ID atau ASTRA_DB_TOKEN tidak diset di file .env!")
        return None
        
    try:
        url = f"https://api.astra.datastax.com/v2/databases/{ASTRA_DB_ID}/secureBundleURL"
        headers = {
            "Authorization": f"Bearer {ASTRA_DB_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            download_url = data.get("downloadURL")
            
            print("[*] Downloading bundle zip file...")
            zip_response = requests.get(download_url, timeout=20)
            if zip_response.status_code == 200:
                with open(SCB_PATH, "wb") as f:
                    f.write(zip_response.content)
                print(f"[+] Secure Connect Bundle downloaded successfully to: {SCB_PATH}")
                return SCB_PATH
            else:
                print(f"[-] Failed to download zip file. Status: {zip_response.status_code}")
        else:
            print(f"[-] Failed to get secure bundle URL from Astra DevOps API. Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[!] Error downloading Secure Connect Bundle: {e}")
    
    return None
