# -*- coding: utf-8 -*-
"""
30分ごとにニュースをDiscordへ配信するエントリポイント。
Cloudflare Cron または GitHub Actions から実行する想定。
環境変数: DISCORD_WEBHOOK_URL_30M
"""
import os
import sys
from config import DISCORD_WEBHOOK_URL_30M
from rss_fetcher import get_recent_news_30m
from discord_webhook import send_30m

# 重要キーワードに当てはまるものだけ送る（0で全件）
IMPORTANT_ONLY = int(os.environ.get("ALERT_30M_IMPORTANT_ONLY", "0"))

def main():
    if not DISCORD_WEBHOOK_URL_30M:
        print("DISCORD_WEBHOOK_URL_30M が未設定です", file=sys.stderr)
        sys.exit(1)
    items = get_recent_news_30m(important_only=bool(IMPORTANT_ONLY))
    if not items:
        print("過去30分のニュースはありません")
        return
    # 1件ずつまたはまとめて送信（Discord 2000文字制限に合わせてまとめる）
    messages = []
    buf = "⚡ **直近30分のニュース**\n\n"
    for e in items:
        line = f"• {e.title}\n  <{e.link}>\n"
        if len(buf) + len(line) > 1900:
            messages.append(buf)
            buf = line
        else:
            buf += line
    if buf.strip():
        messages.append(buf)
    ok, err = send_30m(messages)
    if not ok:
        print(f"送信失敗: {err}", file=sys.stderr)
        sys.exit(1)
    print(f"送信完了: {len(items)}件")

if __name__ == "__main__":
    main()
