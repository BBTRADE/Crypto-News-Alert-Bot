# -*- coding: utf-8 -*-
"""
30分ごとにニュースをDiscordへ配信するエントリポイント。
Cloudflare Cron または GitHub Actions から実行する想定。
環境変数: DISCORD_WEBHOOK_URL_30M
"""
import os
import re
import sys
from config import DISCORD_WEBHOOK_URL_30M
from rss_fetcher import get_recent_news_30m
from discord_webhook import send_30m

# 重要キーワードに当てはまるものだけ送る（1=速報は重要ニュースのみ推奨）
IMPORTANT_ONLY = int(os.environ.get("ALERT_30M_IMPORTANT_ONLY", "1"))
# 要約の最大文字数
SUMMARY_MAX_CHARS = int(os.environ.get("ALERT_30M_SUMMARY_CHARS", "120"))


def _strip_html(text):
    """HTMLタグを除去してプレーンテキストにする"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _get_summary(entry, max_chars=120):
    """RSSエントリから要約を取得（summary または description）"""
    raw = getattr(entry, 'summary', '') or getattr(entry, 'description', '') or ''
    text = _strip_html(raw)
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(' ', 1)[0] + '…'
    return text

def _load_posted_links(filepath, max_lines=800):
    """送信済みURL一覧を読み込み（前回実行分を除外するため）。"""
    if not filepath or not os.path.exists(filepath):
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return set(lines[-max_lines:])


def _save_posted_links(filepath, new_urls, max_lines=800):
    """今回送ったURLを追記し、ファイルを一定行数に刈り込む。"""
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    existing = _load_posted_links(filepath, max_lines=999999)
    existing.update(new_urls)
    lines = list(existing)[-max_lines:]
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))


def main():
    if not DISCORD_WEBHOOK_URL_30M:
        print("DISCORD_WEBHOOK_URL_30M が未設定です", file=sys.stderr)
        sys.exit(1)
    posted_file = os.environ.get("POSTED_LINKS_FILE", ".cache/posted_links_30m.txt")
    posted = _load_posted_links(posted_file)
    items = get_recent_news_30m(important_only=bool(IMPORTANT_ONLY))
    items = [e for e in items if e.link not in posted]
    if not items:
        print("送信対象の新着重要ニュースはありません（過去30分・未送信のみ）")
        return
    # 各ニュースを個別メッセージとして送信
    messages = []
    for e in items:
        title = e.title or "(タイトルなし)"
        summary = _get_summary(e, SUMMARY_MAX_CHARS)
        url = e.link
        if summary:
            msg = f"⚡速報⚡\n**{title}**\n{summary}\n{url}"
        else:
            msg = f"⚡速報⚡\n**{title}**\n{url}"
        messages.append(msg)
    ok, err = send_30m(messages)
    if not ok:
        print(f"送信失敗: {err}", file=sys.stderr)
        sys.exit(1)
    new_urls = [e.link for e in items]
    _save_posted_links(posted_file, new_urls)
    print(f"送信完了: {len(items)}件（送信済みリストを更新しました）")

if __name__ == "__main__":
    main()
