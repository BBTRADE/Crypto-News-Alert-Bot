# -*- coding: utf-8 -*-
"""
環境変数で設定。トークン・Webhook URLはコードに書かず .env または 実行環境のシークレット で渡す。
"""
import os

# Discord（Webhook方式: Cloudflare / GitHub Actions 向け）
DISCORD_WEBHOOK_URL_30M = os.environ.get("DISCORD_WEBHOOK_URL_30M", "").strip()
DISCORD_WEBHOOK_URL_DAILY = os.environ.get("DISCORD_WEBHOOK_URL_DAILY", "").strip()

# 30分Bot用・日次まとめBot用で同じWebhookでも可（未設定ならそのBotは送信スキップ）

# GLM API（日次まとめの整形用・任意）
GLM_API_KEY = os.environ.get("GLM_API_KEY", "").strip()
GLM_API_URL = os.environ.get("GLM_API_URL", "https://api.z.ai/api/paas/v4/chat/completions").strip()
GLM_MODEL = os.environ.get("GLM_MODEL", "glm-4-flash")  # 無料: glm-4-flash, glm-4.7-flash

# 日次まとめでGLMを使うか（GLM_API_KEY が設定されていれば使用）
USE_GLM_FOR_DAILY = os.environ.get("USE_GLM_FOR_DAILY", "0").strip().lower() in ("1", "true", "yes")

RSS_URLS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://news.bitcoin.com/feed/",
    "https://cryptonews.com/news/feed/",
    "https://jp.cointelegraph.com/rss",
    "https://coinpost.jp/?feed=rss2",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://www.reuters.com/finance/economy/rss",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www3.nhk.or.jp/rss/news/cat0.xml",
]

# 暗号資産専門メディア（これらは threshold=1 で判定）
CRYPTO_MEDIA_KEYWORDS = [
    "coindesk", "cointelegraph", "decrypt", "bitcoin.com", "cryptonews", "coinpost",
]

IMPORTANT_KEYWORDS = [
    "FOMC", "利上げ", "利下げ", "インフレ", "破綻", "暴落", "金融", "混乱", "デフォルト",
    "制裁", "戦争", "侵攻", "大統領", "トランプ", "バイデン", "発表", "緊急", "G7", "BRICS",
    "SEC", "ETF", "訴訟", "規制", "禁止", "制限",
    "暗号資産", "仮想通貨", "暗号通貨", "ビットコイン", "イーサリアム", "取引所",
]
