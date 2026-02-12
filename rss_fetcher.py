# -*- coding: utf-8 -*-
"""
RSS取得・フィルタの共通ロジック（30分Bot・日次まとめBotで共用）
"""
import feedparser
from datetime import datetime, timedelta, timezone

from config import RSS_URLS, IMPORTANT_KEYWORDS, CRYPTO_MEDIA_KEYWORDS


def _parse_published(entry):
    try:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def is_recent_by_minutes(entry, minutes=30):
    published = _parse_published(entry)
    return published > datetime.now(timezone.utc) - timedelta(minutes=minutes)


def is_recent_by_hours(entry, hours=24):
    published = _parse_published(entry)
    return published > datetime.now(timezone.utc) - timedelta(hours=hours)


def _is_crypto_media(source_url):
    """暗号資産専門メディアかどうかを判定"""
    if not source_url:
        return False
    url_lower = source_url.lower()
    return any(media in url_lower for media in CRYPTO_MEDIA_KEYWORDS)


def count_keywords(text):
    """キーワードのマッチ数を返す（大文字小文字を無視）"""
    if not text:
        return 0
    text_lower = text.lower()
    return sum(1 for k in IMPORTANT_KEYWORDS if k.lower() in text_lower)


def is_important(text, threshold=2):
    """重要キーワードが threshold 個以上含まれているか（大文字小文字無視）"""
    return count_keywords(text) >= threshold


def is_important_for_source(text, source_url):
    """
    ソースに応じた重要度判定:
    - 暗号資産専門メディア: threshold=1（1つでもキーワードがあれば重要）
    - その他のメディア: threshold=2（2つ以上必要）
    """
    if _is_crypto_media(source_url):
        return count_keywords(text) >= 1
    return count_keywords(text) >= 2


def _is_similar(t1, t2):
    if not t1 or not t2:
        return False
    return (t1[:20] in t2 or t2[:20] in t1) if len(t1) >= 20 and len(t2) >= 20 else (t1 == t2)


def get_news(minutes=None, hours=None, dedup=True):
    """
    RSSからニュースを取得。
    minutes: 過去N分以内に限定（指定しない場合は時間フィルタなし）
    hours: 過去N時間以内に限定（minutes より優先されない。minutes/hours のどちらか指定）
    dedup: タイトルで重複除去
    各 entry に _source_url 属性を付与（フィルタ判定用）
    """
    seen_titles = []
    entries = []
    now = datetime.now(timezone.utc)

    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                published = _parse_published(entry)
                if minutes is not None and (now - published).total_seconds() > minutes * 60:
                    continue
                if hours is not None and (now - published).total_seconds() > hours * 3600:
                    continue
                if dedup and any(_is_similar(entry.title, t) for t in seen_titles):
                    continue
                entry._source_url = url  # ソースURLを記録
                entries.append(entry)
                seen_titles.append(entry.title or "")
        except Exception:
            continue

    # 新しい順
    entries.sort(key=lambda e: _parse_published(e), reverse=True)
    return entries


def get_recent_news_30m(important_only=False):
    """
    過去30分のニュース。
    important_only=True ならソースに応じたキーワードフィルタ:
    - 暗号資産専門メディア: 1つ以上のキーワードでOK
    - その他: 2つ以上必要
    """
    items = get_news(minutes=30)
    if important_only:
        items = [e for e in items if is_important_for_source(e.title or "", getattr(e, '_source_url', ''))]
    return items


def get_daily_news(hours=24):
    """過去 hours 時間のニュース（日次まとめ用）。"""
    return get_news(hours=hours)
