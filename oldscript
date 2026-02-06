#!/usr/bin/env python3

import subprocess
import sys
import os
import platform
import hashlib
import random
import time
from datetime import datetime, timezone, timedelta
import json
import linecache

import ntplib
import pytz
import urllib3
from colorama import init, Fore, Style

# =========================
# DEPENDENCY AUTO-INSTALL
# =========================

def install_package(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

required_packages = ["ntplib", "pytz", "urllib3", "colorama"]
for p in required_packages:
    try:
        __import__(p)
    except ImportError:
        install_package(p)

# =========================
# COLOR SETUP
# =========================

init(autoreset=True)
col_g = Fore.GREEN
col_y = Fore.YELLOW
col_r = Fore.RED
col_b = Fore.BLUE
col_gb = Style.BRIGHT + Fore.GREEN

os.system("cls" if os.name == "nt" else "clear")

# =========================
# USER INPUT
# =========================

slot = int(input(col_g + "[Slot number (1-4)]: " + Fore.RESET))

# Map slots to token lines (1&3 -> line 1, 2&4 -> line 2)
if slot in (1, 3):
    token_number = 1
elif slot in (2, 4):
    token_number = 2
else:
    print("Invalid slot number")
    sys.exit(1)


os.system("cls" if os.name == "nt" else "clear")

scriptversion = "ARU_FHL_v070425"

print(col_gb + f"{scriptversion}_token_#{token_number}")
print(col_y + "Checking account status..." + Fore.RESET)

# =========================
# FILE INPUT
# =========================

token = linecache.getline("token.txt", token_number).strip()
feedtime = float(linecache.getline("timeshift.txt", token_number).strip())

if not token:
    print(col_r + "Invalid token line number")
    sys.exit(1)

feed_time_shift_1 = feedtime / 1000

# =========================
# CONSTANTS
# =========================

ntp_servers = [
    "ntp0.ntp-servers.net",
    "ntp1.ntp-servers.net",
    "ntp2.ntp-servers.net"
]

# =========================
# HELPERS
# =========================

def generate_device_id():
    seed = f"{random.random()}-{time.time()}"
    return hashlib.sha1(seed.encode()).hexdigest().upper()

# ✅ FIXED TIME FUNCTION (PC + ANDROID SAFE)
def get_initial_beijing_time():
    beijing_tz = pytz.timezone("Asia/Shanghai")

    # Try NTP first (PC / open networks)
    try:
        client = ntplib.NTPClient()
        for server in ntp_servers:
            try:
                response = client.request(server, version=3, timeout=2)
                ntp_time = datetime.fromtimestamp(response.tx_time, timezone.utc)
                beijing_time = ntp_time.astimezone(beijing_tz)
                print(col_g + "[Beijing time - NTP]: " + Fore.RESET +
                      beijing_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
                return beijing_time
            except:
                continue
    except:
        pass

    # Android-safe fallback (SYSTEM TIME)
    beijing_time = datetime.now(timezone.utc).astimezone(beijing_tz)
    print(col_y + "[Beijing time - SYSTEM]: " + Fore.RESET +
          beijing_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
    return beijing_time

def synced_time(start_bt, start_ts):
    return start_bt + timedelta(seconds=(time.time() - start_ts))

# =========================
# HTTP SESSION
# =========================

class HTTP11Session:
    def __init__(self):
        self.http = urllib3.PoolManager(
            maxsize=10,
            retries=True,
            timeout=urllib3.Timeout(connect=2.0, read=15.0)
        )

    def make_request(self, method, url, headers=None, body=None):
        try:
            return self.http.request(
                method,
                url,
                headers=headers,
                body=body,
                preload_content=False
            )
        except Exception as e:
            print(col_r + f"[Network error] {e}")
            return None

# =========================
# MAIN
# =========================

def main():
    device_id = generate_device_id()
    session = HTTP11Session()

    start_bt = get_initial_beijing_time()
    start_ts = time.time()

    print(col_y + "\nRequesting bootloader unlock..." + Fore.RESET)
    print(col_g + "[Offset set]: " + Fore.RESET + f"{feedtime} ms")

    target = (start_bt + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(seconds=feed_time_shift_1)

    print(col_g + "[Waiting until]: " + Fore.RESET +
          target.strftime("%Y-%m-%d %H:%M:%S.%f"))
    print("Do not close this window...\n")

    while synced_time(start_bt, start_ts) < target:
        time.sleep(0.0001)

    url = "https://sgp-api.buy.mi.com/bbs/api/global/apply/bl-auth"
    headers = {
        "Cookie": f"new_bbs_serviceToken={token};versionCode=500411;versionName=5.4.11;deviceId={device_id};",
        "User-Agent": "okhttp/4.12.0",
        "Content-Type": "application/json"
    }

    while True:
        now = synced_time(start_bt, start_ts)
        print(col_g + "[Request @] " + Fore.RESET + now.strftime("%H:%M:%S.%f"))

        response = session.make_request(
            "POST",
            url,
            headers=headers,
            body=b'{"is_retry":true}'
        )

        if not response:
            continue

        data = json.loads(response.data.decode())
        response.release_conn()

        print(col_b + "[Response]: " + Fore.RESET + str(data))

        code = data.get("code")
        if code in [0, 100003]:
            print(col_gb + "✔ Request processed")
            break

        time.sleep(0.2)

# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    main()
