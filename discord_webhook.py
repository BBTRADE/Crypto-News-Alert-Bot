# -*- coding: utf-8 -*-
"""
Discord Webhook 送信（Cloudflare / GitHub Actions 用。Botトークン不要）
"""
import json
import urllib.request
import urllib.error

from config import DISCORD_WEBHOOK_URL_30M, DISCORD_WEBHOOK_URL_DAILY


def send_webhook(webhook_url: str, content: str = None, embeds: list = None):
    """Discord Webhook にメッセージを送信。content は最大2000文字。"""
    if not webhook_url:
        return False, "DISCORD_WEBHOOK_URL が未設定です"
    body = {}
    if content:
        body["content"] = content[:2000]
    if embeds:
        body["embeds"] = embeds[:10]
    if not body:
        return False, "content または embeds が必要です"
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Crypto-News-Alert-Bot/1.0 (GitHub Actions)",
    }
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            if 200 <= res.status < 300:
                return True, None
            return False, f"HTTP {res.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode()[:200]}"
    except Exception as e:
        return False, str(e)


def send_30m(contents: list):
    """30分Bot用Webhook。複数メッセージは順に送信（Discord制限に合わせて分割可能）。"""
    url = DISCORD_WEBHOOK_URL_30M
    if not url:
        return False, "DISCORD_WEBHOOK_URL_30M が未設定です"
    for text in contents:
        ok, err = send_webhook(url, content=text)
        if not ok:
            return False, err
    return True, None


def send_daily(content: str):
    """日次まとめBot用Webhook。長文は分割送信。"""
    url = DISCORD_WEBHOOK_URL_DAILY
    if not url:
        return False, "DISCORD_WEBHOOK_URL_DAILY が未設定です"
    # 2000文字超なら分割
    chunk = 1900
    for i in range(0, len(content), chunk):
        part = content[i : i + chunk]
        ok, err = send_webhook(url, content=part)
        if not ok:
            return False, err
    return True, None
