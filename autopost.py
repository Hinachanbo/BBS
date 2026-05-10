import requests
import schedule
import time
import re
from urllib.parse import urlparse
from pprint import pprint

def make_thread_url(board_url: str, thread_id: str) -> str:
    # URLを解析
    parsed = urlparse(board_url)
    domain = parsed.netloc
    board_dir = parsed.path.strip("/")
    
    # thread URL を組み立て
    thread_url = f"https://{domain}/test/read.cgi/{board_dir}/{thread_id}/"
    return thread_url, board_dir

def find_active_thread(board_url, keyword):
    # 指定キーワードを含むスレのうち、満杯でない最新スレを返す
    subject_url = f"{board_url}/subject.txt"
    print(f"{subject_url=}")
    res = requests.get(subject_url)
    res.encoding = "shift_jis"
    lines = res.text.splitlines() #スレッドの配列
    candidates = []
    for line in lines:
        m = re.match(r"(\d+)\.dat<>(.+)\((\d+)\)", line)
        """
        ()でグルーピングし、分けている
        \d+は1文字以上の数字, .+は１文字以上の文字
        \., \(, \)はエスケープ
        """
        if not m:
            continue
        thread_id, title, res_count = m.groups()
        res_count = int(res_count)

        if keyword in title and res_count < 1000:
            candidates.append((int(thread_id), thread_id, title, res_count))

    if not candidates:
        print("該当スレなし")
        return

    # thread_id（UNIX時刻）でソート → 新しいスレを選ぶ
    candidates.sort(reverse=True)
    _, thread_id, title, res_count = candidates[0]
    return thread_id, title, res_count

def post_to_5ch(board_url, keyword, message):
    thread_id, title, res_count = find_active_thread(board_url,keyword)
    thread_url, board_dir = make_thread_url(board_url,thread_id)

    bbs_url = re.sub(r"/read\.cgi/", "/bbs.cgi/", thread_url)
    print(f"{bbs_url=}")
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
    }
    """
    res = session.get(thread_url, headers=headers)
    sid_match = re.search(r'name="sid" value="(\w+)"', res.text)
    sid = sid_match.group(1) if sid_match else ""
    print(f"sid={sid}")
    """
    data = {
        "FROM": "運営Bot",
        "mail": "sage",
        "MESSAGE": message,
        "bbs": board_dir,
        "key": thread_id,
        "time": str(int(time.time())),
        "submit": "書き込む"
    }

    pprint(data)

    response = session.post(bbs_url, data=data, headers=headers)
    if response.status_code == 200:
        print("投稿成功にゃ！")
    else:
        print("投稿失敗にゃ…:", response.status_code)


board_url = "https://egg.5ch.net/mj"
keyword = "5chカップ"
message = "botのtestにゃ"
post_to_5ch(board_url,keyword,message)

"""
# 定期投稿
schedule.every().day.at("15:51").do(lambda: post_to_5ch(board_url,keyword,message))

print("一姫散歩中...")
while True:
    schedule.run_pending() #実行
    time.sleep(60)
"""