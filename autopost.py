from __future__ import annotations

import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
import schedule
from selenium import webdriver
from selenium.webdriver.common.by import By

MAX_RES_COUNT = 1000
PAGE_WAIT_SEC = 3
DEFAULT_POST_TIME = "15:41"
DELAY_RES_RANGE = (890, 900)  # このレス数の間は投稿を見送る
DELAY_RETRY_SEC = 60


def load_env(path: Path) -> None:
    """KEY=VALUE 形式の .env を環境変数に読み込む（既存の環境変数は上書きしない）。"""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def make_thread_url(board_url: str, thread_id: str) -> str:
    parsed = urlparse(board_url)
    board_dir = parsed.path.strip("/")
    return f"https://{parsed.netloc}/test/read.cgi/{board_dir}/{thread_id}/"


def find_active_thread(board_url: str, keyword: str):
    """キーワードを含み、1000レス未満で最も新しいスレッドの (ID, タイトル, レス数) を返す。"""
    res = requests.get(f"{board_url}/subject.txt")
    res.encoding = "shift_jis"

    candidates = []
    for line in res.text.splitlines():
        m = re.match(r"(\d+)\.dat<>(.+)\((\d+)\)", line)
        if not m:
            continue
        thread_id, title, res_count = m.groups()
        if keyword in title and int(res_count) < MAX_RES_COUNT:
            candidates.append((thread_id, title, int(res_count)))

    if not candidates:
        print("該当スレなし")
        return None

    # スレッドIDは作成時刻のUNIXタイムなので、最大のものが最新
    return max(candidates, key=lambda c: int(c[0]))


def create_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)


def fill_field(driver, name: str, value: str) -> None:
    field = driver.find_element(By.NAME, name)
    field.clear()
    field.send_keys(value)


def post_message(thread_url: str, message: str) -> None:
    driver = create_driver()
    try:
        driver.get(thread_url)
        time.sleep(2)

        fill_field(driver, "FROM", f"{os.environ.get('NAME', '')}#{os.environ.get('TRIP', '')}")
        fill_field(driver, "mail", "sage")
        fill_field(driver, "MESSAGE", message)

        # 投稿ボタン → 確認画面の投稿ボタンの順にクリック
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        time.sleep(PAGE_WAIT_SEC)
        print("[DEBUG] URL:", driver.current_url)

        driver.find_element(By.NAME, "submit").click()
        time.sleep(PAGE_WAIT_SEC)
        print("[DEBUG] URL:", driver.current_url)

        print(f"[INFO] 投稿成功: {message}")
    except Exception as e:
        print(f"[ERROR] 投稿失敗: {e}")
    finally:
        driver.quit()


def post_to_5ch(board_url: str, keywords: list[str], message: str) -> None:
    for keyword in keywords:
        while True:
            result = find_active_thread(board_url, keyword)
            if not result:
                return
            thread_id, _title, res_count = result
            if not DELAY_RES_RANGE[0] <= res_count <= DELAY_RES_RANGE[1]:
                break
            # 次スレ移行前後の混乱を避けるため、1分待って再確認する
            print(f"[INFO] レス数 {res_count}: {DELAY_RETRY_SEC}秒後に再確認します")
            time.sleep(DELAY_RETRY_SEC)
        thread_url = make_thread_url(board_url, thread_id)
        print(f"[INFO] 投稿先スレッド: {thread_url}")
        post_message(thread_url, message)


def main() -> None:
    load_env(Path(__file__).with_name(".env"))

    board_url = os.environ["BOARD_URL"]
    keywords = split_csv(os.environ["KEYWORDS"])
    post_times = split_csv(os.environ.get("POST_TIME", DEFAULT_POST_TIME))
    message = Path(__file__).with_name("template.txt").read_text(encoding="utf-8")

    # 毎日 POST_TIME（カンマ区切りで複数可）に投稿
    for post_time in post_times:
        schedule.every().day.at(post_time).do(post_to_5ch, board_url, keywords, message)

    print("[INFO] Botを起動しました…")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
