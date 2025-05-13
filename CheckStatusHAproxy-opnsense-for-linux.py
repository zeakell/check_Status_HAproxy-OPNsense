# IM USONG UBUNTU 22.04 FOR RUNNING SCRIPT WITH REQUEREMENT.TXT
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import requests
import logging
import sys

# --- Logging setup ---
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/ckstat_opnsense/checkstatus_opnsense.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# --- Konfigurasi ---
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
BOT_TOKEN = "yourbot token"
CHAT_ID = "-your chatid"
THREAD_ID = "youur thread_id"  # Ganti dengan thread_id yang diinginkan

OPNSENSE_URL = "https://127.0.0.1" #ganti dengan ip address opnsense anda
USERNAME = "userlogin"
PASSWORD = "passwordlogin"

TARGET_SERVERS = {
    "TARGET_SERVER1": "UAT01",
    "TARGET_SERVER2": "UAT02"
}

# --- Setup headless Chrome ---
options = Options()
options.add_argument("--headless")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--no-sandbox")


# --- Mulai browser ---
logging.info("DRIVER ACTIVE")

driver = webdriver.Chrome(options=options)

def login():
    logging.info("DASHBOARD LOGIN OPNSENSE")
    driver.get(OPNSENSE_URL + "/ui/")
    time.sleep(2)

    logging.info("HALAMAN LOGIN")
    driver.find_element(By.ID, "usernamefld").send_keys(USERNAME)
    driver.find_element(By.ID, "passwordfld").send_keys(PASSWORD)
    driver.find_element(By.NAME, "login").click()
    time.sleep(2)

def is_logged_in():
    # Cek apakah elemen yang hanya muncul ketika sudah login ada
    try:
        driver.find_element(By.CSS_SELECTOR, "div.navbar-header")
        return True
    except:
        return False

while True:
    try:
        # Periksa apakah sudah login
        if not is_logged_in():
            login()

        logging.info("Navigasi ke halaman statistik HAProxy...")
        driver.get(OPNSENSE_URL + "/ui/haproxy/statistics")
        time.sleep(5)

        logging.info("Mengambil page source dan parsing dengan BeautifulSoup...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        rows = soup.find_all("tr")

        logging.info("Mulai proses pengecekan status server target...")
        for target_server, display_name in TARGET_SERVERS.items():
            status_found = None
            for row in rows:
                if target_server in row.text:
                    cells = row.find_all("td")
                    for cell in cells:
                        if "UP" in cell.text or "DOWN" in cell.text:
                            status_found = cell.text.strip()
                            break
                    break

            if status_found:
                logging.info(f"Status server {display_name}: {status_found}")
                if "DOWN" in status_found or "UP 1/3" in status_found:
                    message = f"{timestamp}  OPNSense: ALERT: Server {display_name} ⚠️ {status_found}"
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        data={"chat_id": CHAT_ID, "text": message, "message_thread_id": THREAD_ID}
                    )
                    logging.info(f"Pesan ALERT dikirim ke Telegram.")
                elif "UP" in status_found:
                     message = f"{timestamp} OPNSense : Server {display_name} ✅ {status_found}"
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        data={"chat_id": CHAT_ID, "text": message, "message_thread_id": THREAD_ID}
                    )
                    logging.info(f"Pesan STATUS UP dikirim ke Telegram.")
            else:
                logging.warning(f"Status server {display_name} tidak ditemukan.")

    except Exception as e:
        logging.error(f"Terjadi kesalahan: {e}")
    finally:
        logging.info("STANDBY ...")
        # Jangan quit driver agar sesi tetap ada untuk iterasi berikutnya
        time.sleep(60)  # Tunggu 60 detik sebelum mencoba lagi
