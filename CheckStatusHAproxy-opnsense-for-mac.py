#for use on mac
#check status HAPROXY-OPNSENSE USING SELENIUM
# CREATED BY HARADA

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import requests

# --- Konfigurasi ---
BOT_TOKEN = "YOUR BOT TOKEN TELEGRAM"
CHAT_ID = "YOUR CHAT ID TELEGRAM"
OPNSENSE_URL = "https://127.0.0.1"
USERNAME = "tarot"
PASSWORD = "apajaboleh"

# Target servers dan mapping nama
TARGET_SERVERS = {
    "HOST_HA-PROXY1": "UAT01",
    "HOST_HA-PROXY2": "UAT02"
}

# --- Konfigurasi browser headless Firefox ---
options = Options()
options.add_argument("--headless")
options.add_argument("--ignore-certificate-errors")  # opsional

# --- Mulai browser ---
driver = webdriver.Firefox(options=options)

try:
    # Login ke OPNsense
    driver.get(OPNSENSE_URL + "/ui/")
    time.sleep(2)

    driver.find_element(By.ID, "usernamefld").send_keys(USERNAME)
    driver.find_element(By.ID, "passwordfld").send_keys(PASSWORD)
    driver.find_element(By.NAME, "login").click()
    time.sleep(2)

    # Navigasi ke halaman statistik HAProxy
    driver.get(OPNSENSE_URL + "/ui/haproxy/statistics")
    time.sleep(5)  # Beri waktu cukup untuk load

    # Parsing status dengan BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    rows = soup.find_all("tr")

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
            print(f"[INFO] Status server {display_name}: {status_found}")
            if "DOWN" in status_found or "UP 1/3" in status_found:
                # Kirim alert ke Telegram
                message = f"Status pada OPNSense :  ALERT: Server {display_name} ⚠️ {status_found}"
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    data={"chat_id": CHAT_ID, "text": message}
                )
            elif "UP" in status_found:
                # Kirim pesan jika status UP
                message = f"Status pada OPNSense : Server {display_name} ✅ {status_found}"
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    data={"chat_id": CHAT_ID, "text": message}
                )
        else:
            print(f"[WARN] Status server {display_name} tidak ditemukan.")
finally:
    driver.quit()
