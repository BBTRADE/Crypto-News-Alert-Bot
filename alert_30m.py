# -*- coding: utf-8 -*-
"""
30分ごとにニュースをDiscordへ配信するエントリポイント。
Cloudflare Cron または GitHub Actions から実行する想定。
環境変数: DISCORD_WEBHOOK_URL_30M
"""
import os
import re
import sys
from config import DISCORD_WEBHOOK_URL_30M, GLM_API_KEY
from rss_fetcher import get_recent_news_30m, get_news, is_important_for_source
from discord_webhook import send_30m
from glm_formatter import translate_title_and_summary

# 重要キーワードに当てはまるものだけ送る（1=速報は重要ニュースのみ推奨）
IMPORTANT_ONLY = int(os.environ.get("ALERT_30M_IMPORTANT_ONLY", "1"))
# 要約の最大文字数
SUMMARY_MAX_CHARS = int(os.environ.get("ALERT_30M_SUMMARY_CHARS", "120"))
# 取得する時間範囲（分）- テスト時は長めに設定可能
ALERT_MINUTES = int(os.environ.get("ALERT_30M_MINUTES", "30"))


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
    
    # 時間範囲を環境変数で指定可能に（デフォルト30分）
    print(f"[INFO] 過去{ALERT_MINUTES}分のニュースを取得中...")
    items = get_news(minutes=ALERT_MINUTES)
    if IMPORTANT_ONLY:
        items = [e for e in items if is_important_for_source(e.title or "", getattr(e, '_source_url', ''))]
    items = [e for e in items if e.link not in posted]
    print(f"[INFO] 対象ニュース: {len(items)}件")
    if not items:
        print(f"送信対象の新着重要ニュースはありません（過去{ALERT_MINUTES}分・未送信のみ）")
        return
    # 各ニュースを個別メッセージとして送信
    messages = []
    for e in items:
        title = e.title or "(タイトルなし)"
        summary = _get_summary(e, SUMMARY_MAX_CHARS)
        url = e.link

        # 英語の場合は日本語に翻訳＋コメント・分析を生成（GLM_API_KEY が設定されている場合のみ）
        if GLM_API_KEY:
            result = translate_title_and_summary(title, summary)
            title = result['title']
            summary = result['summary']
            comment = result['comment']
            impact_score = result['impact_score']
            sentiment = result['sentiment']
            urgency = result['urgency']
        else:
            comment = ''
            impact_score = 0
            sentiment = ''
            urgency = ''

        # メッセージを構築
        msg_parts = [f"⚡速報⚡", f"**{title}**"]

        if summary:
            msg_parts.append(summary)

        # コメントを追加（1行空けて）
        if comment:
            msg_parts.append("")  # 空行
            msg_parts.append(comment)

        # インパクト分析を追加（1行空けて）
        if impact_score > 0:
            msg_parts.append("")  # 空行
            # 影響度スコアを⭐で表示
            stars = "⭐" * impact_score + "☆" * (5 - impact_score)
            analysis_parts = [
                "📊 インパクト分析",
                f"・影響度: {stars}"
            ]

            # センチメントを絵文字付きで表示
            if sentiment:
                sentiment_emoji = {
                    'ポジティブ': '📈',
                    '中立': '➡️',
                    'ネガティブ': '📉'
                }.get(sentiment, '')
                analysis_parts.append(f"・センチメント: {sentiment_emoji} {sentiment}")

            # 緊急度を絵文字付きで表示
            if urgency:
                urgency_emoji = {
                    '高': '🔥',
                    '中': '⚡',
                    '低': '💡'
                }.get(urgency, '')
                analysis_parts.append(f"・緊急度: {urgency_emoji} {urgency}")

            msg_parts.append("\n".join(analysis_parts))

        msg_parts.append(url)
        msg = "\n".join(msg_parts)
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
