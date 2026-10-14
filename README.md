# BBS 自動投稿ボット

5ch の掲示板で、キーワードに一致する最新スレッドを探し、指定した時刻に `template.txt` の内容を自動で書き込むスクリプトです。

## 必要なもの

- Python 3.8 以上
- Google Chrome（Selenium が headless で操作します）
- Python パッケージ: `selenium`, `requests`, `schedule`

```bash
pip install selenium requests schedule
```

## セットアップ

1. `.env.example` を `.env` にコピーして、値を書き換えます。

   ```bash
   cp .env.example .env
   ```

   | 変数 | 必須 | 内容 |
   |---|---|---|
   | `NAME` | | 投稿時の名前 |
   | `TRIP` | | トリップのパスワード（`名前#パスワード` の `#` 以降） |
   | `BOARD_URL` | ○ | 掲示板のURL（例: `https://egg.5ch.net/mj`） |
   | `KEYWORDS` | ○ | 投稿先スレッドのタイトルに含まれるキーワード。カンマ区切りで複数指定可 |
   | `POST_TIME` | | 投稿時刻（`HH:MM`）。カンマ区切りで複数指定可（例: `12:00,18:30`）。省略時は `15:41` |

2. `template.txt` に投稿したい本文を書きます。

## 実行

```bash
python autopost.py
```

起動すると常駐し、`POST_TIME` になるたびに投稿します。止めるときは `Ctrl+C` です。

## 動作の流れ

1. `BOARD_URL/subject.txt` から、`KEYWORDS` を含み、1000レス未満のスレッドを探す
2. 該当スレッドのうち最新のものを選ぶ
3. headless Chrome でスレッドを開き、`NAME#TRIP`・メール欄 `sage`・本文を入力して投稿する