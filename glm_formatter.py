# -*- coding: utf-8 -*-
"""
GLM API でニュース一覧を整形する（日次まとめオプション）
OpenAI互換の chat/completions エンドポイントを想定。
"""
import json
import urllib.request
import urllib.error

from config import GLM_API_KEY, GLM_API_URL, GLM_MODEL


def format_news_with_glm(news_items: list, max_items=50) -> str:
    """
    ニュースの [{"title": "...", "link": "..."}, ...] をGLMに渡し、
    読みやすいまとめテキスト（Markdown可）で返す。失敗時は整形せずプレーン一覧を返す。
    """
    if not GLM_API_KEY or not GLM_API_URL:
        return ""

    lines = []
    for i, item in enumerate(news_items[:max_items], 1):
        title = (item.get("title") or "").strip()
        link = (item.get("link") or "").strip()
        lines.append(f"{i}. {title}\n   {link}")
    raw_list = "\n".join(lines)

    system = (
        "あなたはニュース編集者です。以下のニュース一覧を、Discordで読みやすい形にまとめてください。"
        "見出し・箇条書き・重要そうなトピックを簡潔に要約してよい。"
        "各項目のリンクURLは必ずそのまま含めてください。"
        "出力は日本語で、2000文字以内に収めてください。"
    )
    user = f"以下のニュース一覧を整形してください：\n\n{raw_list}"

    body = {
        "model": GLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 2048,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        GLM_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GLM_API_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            out = json.loads(res.read().decode())
            content = (out.get("choices") or [{}])[0].get("message", {}).get("content", "")
            return (content or "").strip()
    except Exception:
        return ""
