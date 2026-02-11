# -*- coding: utf-8 -*-
"""
RSS取得・フィルタの共通ロジック（30分Bot・日次まとめBotで共用）
"""
import feedparser
from datetime import datetime, timedelta, timezone

from config import RSS_URLS, IMPORTANT_KEYWORDS


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


def is_important(text, threshold=2):
    if not text:
        return False
    return sum(1 for k in IMPORTANT_KEYWORDS if k in text) >= threshold


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
                entries.append(entry)
                seen_titles.append(entry.title or "")
        except Exception:
            continue

    # 新しい順
    entries.sort(key=lambda e: _parse_published(e), reverse=True)
    return entries


def get_recent_news_30m(important_only=False):
    """過去30分のニュース。important_only=True ならキーワードでフィルタ。"""
    items = get_news(minutes=30)
    if important_only:
        items = [e for e in items if is_important(e.title or "")]
    return items


def get_daily_news(hours=24):
    """過去 hours 時間のニュース（日次まとめ用）。"""
    return get_news(hours=hours)
