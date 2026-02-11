# -*- coding: utf-8 -*-
"""
1日1回、ニュース一覧をDiscordへ配信するエントリポイント。
オプションで GLM API で整形してから送信。
環境変数: DISCORD_WEBHOOK_URL_DAILY, USE_GLM_FOR_DAILY, GLM_API_KEY 等
"""
import os
import sys

from config import DISCORD_WEBHOOK_URL_DAILY, USE_GLM_FOR_DAILY
from rss_fetcher import get_daily_news
from discord_webhook import send_daily
from glm_formatter import format_news_with_glm


def main():
    if not DISCORD_WEBHOOK_URL_DAILY:
        print("DISCORD_WEBHOOK_URL_DAILY が未設定です", file=sys.stderr)
        sys.exit(1)

    hours = int(os.environ.get("DAILY_SUMMARY_HOURS", "24"))
    items = get_daily_news(hours=hours)
    if not items:
        body = "📢 **本日のニュースまとめ**\n\n過去{}時間のニュースはありません。".format(hours)
        send_daily(body)
        print("0件のため挨拶のみ送信")
        return

    # 整形: GLM を使う場合
    if USE_GLM_FOR_DAILY:
        formatted = format_news_with_glm(
            [{"title": e.title, "link": e.link} for e in items]
        )
        if formatted:
            body = "📢 **本日のニュースまとめ**（GLM整形）\n\n" + formatted
        else:
            formatted = None
    else:
        formatted = None

    if not formatted:
        lines = ["📢 **本日のニュースまとめ**（過去{}時間）\n".format(hours)]
        for e in items[:80]:
            lines.append("• {}\n  <{}>".format(e.title, e.link))
        body = "\n".join(lines)

    ok, err = send_daily(body)
    if not ok:
        print("送信失敗:", err, file=sys.stderr)
        sys.exit(1)
    print("送信完了: {}件".format(len(items)))


if __name__ == "__main__":
    main()
