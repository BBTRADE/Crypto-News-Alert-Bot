# -*- coding: utf-8 -*-
"""
GLM API でニュース一覧を整形する（日次まとめオプション）
+ 英語テキストの日本語翻訳（速報用）
OpenAI互換の chat/completions エンドポイントを想定。
無料モデル: glm-4-flash, glm-4.7-flash
"""
import json
import urllib.request
import urllib.error

from config import GLM_API_KEY, GLM_API_URL, GLM_MODEL


def _is_mostly_english(text):
    """テキストが主に英語かどうかを判定（ASCII文字の割合で簡易判定）"""
    if not text:
        return False
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    ratio = ascii_chars / len(text)
    return ratio > 0.7  # 70%以上がASCIIなら英語と判定


def _call_glm(system_prompt, user_prompt, max_tokens=256):
    """GLM API を呼び出す共通関数"""
    if not GLM_API_KEY:
        print("[GLM] API Key が未設定です")
        return None
    if not GLM_API_URL:
        print("[GLM] API URL が未設定です")
        return None
    
    print(f"[GLM] 翻訳リクエスト送信中... (model={GLM_MODEL}, url={GLM_API_URL[:50]}...)")
    
    body = {
        "model": GLM_MODEL or "glm-4-flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
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
        with urllib.request.urlopen(req, timeout=30) as res:
            out = json.loads(res.read().decode())
            content = (out.get("choices") or [{}])[0].get("message", {}).get("content", "")
            print(f"[GLM] 翻訳成功")
            return (content or "").strip()
    except urllib.error.HTTPError as e:
        print(f"[GLM] HTTP エラー: {e.code} - {e.read().decode()[:200]}")
        return None
    except Exception as e:
        print(f"[GLM] エラー: {type(e).__name__}: {e}")
        return None


def translate_to_japanese(text):
    """
    英語テキストを日本語に翻訳。
    - 英語でなければそのまま返す
    - GLM_API_KEY が未設定ならそのまま返す
    - 翻訳失敗時もそのまま返す
    """
    if not text:
        return text
    if not _is_mostly_english(text):
        return text
    if not GLM_API_KEY:
        return text
    
    system = "あなたは優秀な翻訳者です。与えられた英語テキストを自然な日本語に翻訳してください。翻訳結果のみを出力し、説明は不要です。"
    user = text
    result = _call_glm(system, user, max_tokens=512)
    return result if result else text


def translate_title_and_summary(title, summary):
    """
    タイトルと要約をまとめて翻訳（API呼び出し回数を減らすため）。
    英語でなければそのまま返す。
    """
    if not title:
        return title, summary
    
    # タイトルが英語でなければ翻訳不要
    if not _is_mostly_english(title):
        print(f"[GLM] 日本語のためスキップ: {title[:30]}...")
        return title, summary
    
    if not GLM_API_KEY:
        return title, summary
    
    # シンプルなプロンプトで翻訳
    system = "あなたは英日翻訳者です。与えられた英語を自然な日本語に翻訳してください。翻訳結果のみを出力し、説明は不要です。"
    
    # タイトルと要約を別々に翻訳（パースの問題を回避）
    translated_title = title
    translated_summary = summary
    
    # タイトルを翻訳
    result = _call_glm(system, title, max_tokens=256)
    if result:
        translated_title = result.strip()
        print(f"[GLM] タイトル翻訳: {title[:30]}... → {translated_title[:30]}...")
    
    # 要約を翻訳
    if summary and _is_mostly_english(summary):
        result = _call_glm(system, summary, max_tokens=512)
        if result:
            translated_summary = result.strip()
            print(f"[GLM] 要約翻訳完了")
    
    return translated_title, translated_summary


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

    result = _call_glm(system, user, max_tokens=2048)
    return result if result else ""
