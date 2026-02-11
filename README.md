# 暗号資産ニュース Bot（Webhook版）

**リポジトリ:** [https://github.com/BBTRADE/Crypto-News-Alert-Bot](https://github.com/BBTRADE/Crypto-News-Alert-Bot)

30分ごとと1日1回、RSSニュースを **Discord Webhook** で配信します。  
**GitHub Actions** または **Cloudflare** の Cron で動かす想定です（常時接続の Discord Bot は不要）。

## 構成

| 種類 | 説明 | 実行 |
|------|------|------|
| **30分Bot** | 過去30分のニュースを Discord に投稿 | 30分ごと |
| **日次まとめBot** | 過去24時間のニュース一覧を投稿（オプションで GLM 整形） | 1日1回 |

## 必要なもの

- **Discord Webhook URL**  
  配信したいチャンネルで「チャンネル設定 → 連携サービス → Webhook」から作成し、URL をコピー。
- （任意）**GLM API キー**  
  日次まとめを「要約・整形」して出したい場合のみ。智譜AI 等の OpenAI 互換 API。

## 設定（環境変数）

| 変数 | 必須 | 説明 |
|------|------|------|
| `DISCORD_WEBHOOK_URL_30M` | 30分Bot用 | 30分配信用 Webhook URL |
| `DISCORD_WEBHOOK_URL_DAILY` | 日次Bot用 | 日次まとめ用 Webhook URL |
| `USE_GLM_FOR_DAILY` | 任意 | `1` / `true` で日次まとめを GLM で整形 |
| `GLM_API_KEY` | GLM 使用時 | GLM API キー |
| `GLM_API_URL` | 任意 | デフォルト: 智譜AI 互換エンドポイント |
| `GLM_MODEL` | 任意 | 例: `glm-4-flash` |
| `ALERT_30M_IMPORTANT_ONLY` | 任意 | `1` にすると重要キーワードに当たる記事のみ配信 |
| `DAILY_SUMMARY_HOURS` | 任意 | 日次まとめの対象時間（デフォルト: 24） |

`.env.example` をコピーして `.env` を作成し、ローカル実行時に読み込むこともできます（`python-dotenv` で読み込む場合は各自で追加）。

## GitHub Actions で動かす

1. リポジトリを GitHub に push する。
2. **Settings → Secrets and variables → Actions** で以下を登録：
   - `DISCORD_WEBHOOK_URL_30M` … 30分配信用 Webhook URL
   - `DISCORD_WEBHOOK_URL_DAILY` … 日次まとめ用 Webhook URL
   - （GLM を使う場合）`USE_GLM_FOR_DAILY` = `1`、`GLM_API_KEY`、必要なら `GLM_API_URL` / `GLM_MODEL`
3. あとは cron で自動実行されます。
   - 30分Bot: `.github/workflows/alert_30m.yml` … 30分ごと
   - 日次Bot: `.github/workflows/summary_daily.yml` … 毎日 0:00 UTC（日本時間 9:00）

手動実行する場合は、Actions タブから「News Alert (30min)」「News Summary (Daily)」の **Run workflow** を実行してください。

## ローカルで試す

```bash
pip install -r requirements.txt
```

環境変数を設定してから実行：

```bash
# 30分Bot（1回だけ実行）
set DISCORD_WEBHOOK_URL_30M=https://discord.com/api/webhooks/...
python alert_30m.py

# 日次まとめ（1回だけ実行）
set DISCORD_WEBHOOK_URL_DAILY=https://discord.com/api/webhooks/...
python summary_daily.py
```

GLM で整形する場合（例: Windows）：

```bash
set USE_GLM_FOR_DAILY=1
set GLM_API_KEY=your_key
python summary_daily.py
```

## Cloudflare で動かす場合

- **Cloudflare Workers** で Cron Trigger を設定し、30分ごと・1日1回で Worker を起動する方法があります。
- Worker 内で RSS 取得と Webhook 送信を実装する場合は、同じロジックを JavaScript/TypeScript または Cloudflare の Python Workers で書き直す必要があります。
- まずは **GitHub Actions** で運用し、必要になったら Worker 用コードを追加する形が簡単です。

## RSS・キーワードの変更

- `config.py` の `RSS_URLS` で RSS フィードを追加・削除できます。
- `IMPORTANT_KEYWORDS` は、`ALERT_30M_IMPORTANT_ONLY=1` のときの「重要記事」判定に使います。

## ファイル一覧

- `config.py` … 環境変数・RSS URL・キーワード
- `rss_fetcher.py` … RSS 取得・時間フィルタ
- `discord_webhook.py` … Webhook 送信
- `glm_formatter.py` … GLM による日次まとめ整形
- `alert_30m.py` … 30分Bot のエントリポイント
- `summary_daily.py` … 日次まとめBot のエントリポイント
- `.github/workflows/alert_30m.yml` … 30分実行ワークフロー
- `.github/workflows/summary_daily.yml` … 日次実行ワークフロー
