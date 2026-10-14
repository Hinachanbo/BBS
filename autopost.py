from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import re
import requests
from urllib.parse import urlparse
import schedule

def make_thread_url(board_url: str, thread_id: str) -> str:
    parsed = urlparse(board_url)
    domain = parsed.netloc
    board_dir = parsed.path.strip("/")
    thread_url = f"https://{domain}/test/read.cgi/{board_dir}/{thread_id}/"
    return thread_url, board_dir

def find_active_thread(board_url, keyword):
    subject_url = f"{board_url}/subject.txt"
    res = requests.get(subject_url)
    res.encoding = "shift_jis"
    lines = res.text.splitlines()
    candidates = []
    for line in lines:
        m = re.match(r"(\d+)\.dat<>(.+)\((\d+)\)", line)
        if not m:
            continue
        thread_id, title, res_count = m.groups()
        res_count = int(res_count)
        if keyword in title and res_count < 1000:
            candidates.append((int(thread_id), thread_id, title, res_count))

    if not candidates:
        print("該当スレなし")
        return None

    candidates.sort(reverse=True)
    _, thread_id, title, res_count = candidates[0]
    return thread_id, title, res_count

def post_to_5ch_selenium(board_url, keywords, message):
    for keyword in keywords:
        result = find_active_thread(board_url, keyword)
        if not result:
            return
        thread_id, title, res_count = result
        thread_url, board_dir = make_thread_url(board_url, thread_id)
        print(f"[INFO] 投稿先スレッド: {thread_url}")

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=options)

        try:
            driver.get(thread_url)
            time.sleep(2)

            from_input = driver.find_element(By.NAME, "FROM")
            from_input.clear()
            from_input.send_keys("運営Bot#" + os.environ.get("TRIP", ""))

            mail_input = driver.find_element(By.NAME, "mail")
            mail_input.clear()
            mail_input.send_keys("sage")

            message_input = driver.find_element(By.NAME, "MESSAGE")
            message_input.clear()
            message_input.send_keys(message)

            submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            submit_button.click()

            time.sleep(3)

            print("[DEBUG] URL:", driver.current_url)

            confirm_button = driver.find_element(By.NAME, "submit")
            confirm_button.click()

            time.sleep(3)

            print("[DEBUG] URL:", driver.current_url)

            print(f"[INFO] 投稿成功: {message}")
        except Exception as e:
            print(f"[ERROR] 投稿失敗: {e}")
        finally:
            driver.quit()


import os
from pathlib import Path

# --- 定期投稿設定 ---
board_url = "https://egg.5ch.net/mj"
keywords = ["5chカップ"]
message = Path("template.txt").read_text(encoding="utf-8")

# 毎日15:51に投稿
schedule.every().day.at("15:41").do(lambda: post_to_5ch_selenium(board_url, keywords, message))

print("[INFO] Botを起動しました…")
while True:
    schedule.run_pending()
    time.sleep(60)