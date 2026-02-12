# -*- coding: utf-8 -*-
"""
GLM API でニュース一覧を整形する（日次まとめオプション）
+ 英語テキストの日本語翻訳（速報用）
OpenAI互換の chat/completions エンドポイントを想定。
無料モデル: glm-4-flash, glm-4.7-flash
"""
import json
import time
import urllib.request
import urllib.error

from config import GLM_API_KEY, GLM_API_URL, GLM_MODEL

# レート制限対策：APIコール間の待機時間（秒）
API_CALL_DELAY = 2


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
        "temperature": 0.3,  # 一貫性のある翻訳のため低めに設定
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
            raw_response = res.read().decode()
            print(f"[GLM] APIレスポンス全体: {raw_response[:300]}...")
            out = json.loads(raw_response)
            choices = out.get("choices") or []
            if not choices:
                print(f"[GLM] 警告: choicesが空です")
                return None

            message = choices[0].get("message", {})
            # content または reasoning_content から結果を取得
            content = message.get("content", "")
            reasoning = message.get("reasoning_content", "")

            print(f"[GLM] content: {content[:100] if content else '(空)'}")
            print(f"[GLM] reasoning_content: {reasoning[:100] if reasoning else '(空)'}")

            # reasoning_content に翻訳結果がある場合、最後の翻訳結果を抽出
            if not content and reasoning:
                import re
                # 「出力:」の後の部分を優先的に抽出
                match = re.search(r'出力[：:]\s*(.+?)(?:\n|$)', reasoning, re.IGNORECASE)
                if match:
                    content = match.group(1).strip()
                    print(f"[GLM] reasoning_contentから「出力:」パターンで抽出: {content[:50]}...")
                else:
                    # reasoning から日本語翻訳を抽出（最後の行または ** で囲まれた結果）
                    lines = reasoning.strip().split('\n')
                    # 最後の意味のある行を探す
                    for line in reversed(lines):
                        line = line.strip()
                        if line and not line.startswith('*') and not line.startswith('#') and not line.startswith('入力'):
                            content = line
                            print(f"[GLM] reasoning_contentから最後の行を抽出: {content[:50]}...")
                            break
                    # それでも見つからない場合、reasoning全体から日本語部分を探す
                    if not content:
                        # 「翻訳:」や「Translation:」の後の部分を探す
                        match = re.search(r'(?:翻訳|Translation|Result)[：:]\s*(.+)', reasoning, re.IGNORECASE)
                        if match:
                            content = match.group(1).strip()
                            print(f"[GLM] reasoning_contentから「翻訳:」パターンで抽出: {content[:50]}...")

            print(f"[GLM] 最終的な翻訳結果 (content長さ: {len(content)}): {content[:100] if content else '(なし)'}...")
            # レート制限対策：次のAPIコールまで待機
            time.sleep(API_CALL_DELAY)
            return (content or "").strip()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"[GLM] HTTP エラー: {e.code} - {error_body[:300]}")
        return None
    except Exception as e:
        print(f"[GLM] エラー: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
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
        print(f"[GLM] API Key未設定のためスキップ")
        return title, summary

    print(f"[GLM] 翻訳対象タイトル: {title}")

    # Few-shot プロンプトで期待する出力形式を明示（より厳格に）
    system = """あなたは英語から日本語への翻訳専門家です。
与えられた英語のニュースタイトルを、自然な日本語に翻訳してください。

重要な指示:
- 翻訳結果のみを1行で出力してください
- 説明、分析、追加情報は一切不要です
- 「出力:」などのラベルも不要です
- 日本語の翻訳文だけを返してください

例:
入力: Bitcoin Hits New All-Time High
出力: ビットコインが史上最高値を更新

入力: SEC Approves Spot Bitcoin ETF
出力: SECがビットコイン現物ETFを承認

入力: Ethereum Price Drops 10% Amid Market Uncertainty
出力: イーサリアム価格、市場の不確実性で10%下落"""

    # タイトルのみ翻訳（無料プランのレート制限対策）
    translated_title = title

    # タイトルを翻訳（Few-shot形式で入力）
    user_prompt = f"入力: {title}\n出力:"
    result = _call_glm(system, user_prompt, max_tokens=256)

    if result:
        # 「出力:」などのラベルが含まれている場合は除去
        import re
        result = re.sub(r'^(?:出力|Output)[：:]\s*', '', result, flags=re.IGNORECASE).strip()

        # 複数行の場合は最初の行だけを使用
        if '\n' in result:
            lines = [line.strip() for line in result.split('\n') if line.strip()]
            for line in lines:
                # 日本語を含む行を優先
                if any('\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FFF' for c in line):
                    result = line
                    break
            else:
                result = lines[0] if lines else result

        result = result.strip()

        # 結果が日本語を含んでいるかチェック（ひらがな・カタカナ・漢字）
        has_japanese = any('\u3040' <= c <= '\u309F' or  # ひらがな
                          '\u30A0' <= c <= '\u30FF' or  # カタカナ
                          '\u4E00' <= c <= '\u9FFF'     # 漢字
                          for c in result)
        if has_japanese:
            translated_title = result
            print(f"[GLM] ✓ タイトル翻訳成功: {title[:40]}... → {translated_title[:40]}...")
        else:
            print(f"[GLM] ✗ 警告: 翻訳結果が日本語でない: {result[:80]}...")
    else:
        print(f"[GLM] ✗ 翻訳失敗: resultがNone")

    # 要約は翻訳しない（レート制限回避のため）
    return translated_title, summary


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
