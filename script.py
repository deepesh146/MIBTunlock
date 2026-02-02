#!/usr/bin/env python3

import subprocess
import sys
import os
import platform
import hashlib
import random
import time
from datetime import datetime, timezone, timedelta
import ntplib
import pytz
import urllib3
import json
import linecache
from colorama import init, Fore, Style

# ================== DEPENDENCY CHECK ==================

def install_package(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

required = ["ntplib", "pytz", "urllib3", "colorama"]
for p in required:
    try:
        __import__(p)
    except ImportError:
        install_package(p)

# ================== ARGUMENT HANDLING ==================

if len(sys.argv) < 2:
    print("Usage: python unlock.py <token_number>")
    sys.exit(1)

token_number = int(sys.argv[1])

# ================== FILE PATHS ==================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "token.txt")
TIMESHIFT_FILE = os.path.join(BASE_DIR, "timeshift.txt")

# ================== COLOR SETUP ==================

init(autoreset=True)
G = Fore.GREEN
Y = Fore.YELLOW
R = Fore.RED
B = Fore.BLUE
GB = Style.BRIGHT + Fore.GREEN

os.system("clear")

# ================== LOAD TOKEN & TIME ==================

token = linecache.getline(TOKEN_FILE, token_number).strip()
feedtime = float(linecache.getline(TIMESHIFT_FILE, token_number).strip())
feed_time_shift_1 = feedtime / 1000

if not token:
    print(R + "Invalid token line number")
    sys.exit(1)

print(GB + f"ARU_FHL | TOKEN SLOT #{token_number}")
print(Y + "Checking account status...")

# ================== CONSTANTS ==================

ntp_servers = [
    "ntp0.ntp-servers.net",
    "ntp1.ntp-servers.net",
    "ntp2.ntp-servers.net"
]

# ================== HELPERS ==================

def generate_device_id():
    seed = f"{random.random()}-{time.time()}"
    return hashlib.sha1(seed.encode()).hexdigest().upper()

def get_initial_beijing_time():
    client = ntplib.NTPClient()
    tz = pytz.timezone("Asia/Shanghai")
    for s in ntp_servers:
        try:
            res = client.request(s, version=3)
            utc = datetime.fromtimestamp(res.tx_time, timezone.utc)
            bj = utc.astimezone(tz)
            print(G + "[Beijing Time]:", bj.strftime("%Y-%m-%d %H:%M:%S.%f"))
            return bj
        except:
            pass
    return None

def synced_time(start_bt, start_ts):
    return start_bt + timedelta(seconds=(time.time() - start_ts))

# ================== HTTP SESSION ==================

class HTTP11Session:
    def __init__(self):
        self.http = urllib3.PoolManager(
            maxsize=10,
            timeout=urllib3.Timeout(connect=2.0, read=15.0),
            retries=True
        )

    def request(self, method, url, headers=None, body=None):
        try:
            return self.http.request(
                method,
                url,
                headers=headers,
                body=body,
                preload_content=False
            )
        except:
            return None

# ================== MAIN LOGIC ==================

def main():
    device_id = generate_device_id()
    session = HTTP11Session()

    start_bt = get_initial_beijing_time()
    if not start_bt:
        print(R + "Failed to sync time")
        sys.exit(1)

    start_ts = time.time()

    target = (start_bt + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(seconds=feed_time_shift_1)

    print(G + "[Waiting until]:", target.strftime("%Y-%m-%d %H:%M:%S.%f"))
    print(Y + "Do not close Termux...")

    while synced_time(start_bt, start_ts) < target:
        time.sleep(0.0001)

    print(GB + ">>> SENDING REQUEST <<<")

    url = "https://sgp-api.buy.mi.com/bbs/api/global/apply/bl-auth"
    headers = {
        "Cookie": f"new_bbs_serviceToken={token};versionCode=500411;versionName=5.4.11;deviceId={device_id};",
        "User-Agent": "okhttp/4.12.0",
        "Content-Type": "application/json"
    }

    while True:
        now = synced_time(start_bt, start_ts)
        print(G + "[Request @]", now.strftime("%H:%M:%S.%f"))
        r = session.request("POST", url, headers=headers, body=b'{"is_retry":true}')
        if not r:
            continue

        data = json.loads(r.data.decode())
        r.release_conn()

        code = data.get("code")
        print(B + "[Response]:", data)

        if code in [0, 100003]:
            print(GB + "✔ Request processed")
            break

        time.sleep(0.2)

if __name__ == "__main__":
    main()
