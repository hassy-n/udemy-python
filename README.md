# Python Mission Quest (Streamlit)

初心者向けに、1画面1ミッションでPythonの基礎からアプリ開発思考まで学べる学習アプリです。

## 特徴

- 1画面に1つのミッション
- クリア時に報酬演出（`st.balloons`, `st.snow`）
- 段階的な難易度アップ（変数 -> 条件分岐 -> 関数 -> Streamlit部品 -> ミニアプリ設計）

## ローカル実行

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## GitHub経由で公開（Streamlit Community Cloud）

1. このフォルダをGitHubリポジトリにpushする
2. https://share.streamlit.io/ にログイン（GitHub連携）
3. `New app` を選択
4. リポジトリ・ブランチ・`app.py` を指定してデプロイ

## ファイル構成

- `app.py`: 学習アプリ本体
- `requirements.txt`: 必要ライブラリ

## X投稿案の自動生成

このリポジトリには、OpenAI APIを使ってX（旧Twitter）投稿案を毎日5本生成するNode.jsスクリプトを含めています。Xへ直接投稿はせず、生成結果はGitHub ActionsのログとJob Summaryに出力します。投稿前に必ず人間が内容・事実関係・表現を確認する前提です。

### 生成する投稿案

- テーマ: AI活用、業務改善、PM/PdM、個人開発、競合分析自動化
- 本数: 5本
- 文字数目安: 各140〜240文字程度
- 形式:
  1. 実体験風
  2. 学び共有
  3. 失敗談
  4. Tips
  5. 問いかけ型
- トーン: 煽りすぎず、情報商材っぽくせず、誇大表現を避ける

### 必要なGitHub Secrets

GitHubリポジトリの `Settings > Secrets and variables > Actions` に以下を設定してください。

| Secret | 必須 | 説明 |
| --- | --- | --- |
| `OPENAI_API_KEY` | 必須 | OpenAI APIキー |
| `OPENAI_MODEL` | 任意 | 使用モデル。未設定時は `gpt-4.1-mini` |

### GitHub Actions

`.github/workflows/generate-x-posts.yml` は以下のタイミングで実行されます。

- 毎日 08:00 JST（cronでは前日 23:00 UTC）
- `workflow_dispatch` による手動実行

実行結果はActionsログとJob SummaryにMarkdown形式で出力されます。メール通知が必要な場合は、GitHub Actionsの通知設定、または将来的な通知ステップ追加で対応できます。

### ローカル実行

```bash
# APIを呼ばずに出力形式だけ確認
npm run generate:x-posts:dry-run

# OpenAI APIを使って生成
OPENAI_API_KEY=sk-... npm run generate:x-posts
```

### 将来のX API投稿への拡張方針

現在の `scripts/generate-x-posts.js` は、生成処理と出力処理を分けています。将来的にX API投稿を追加する場合は、生成された `posts` を人間確認済みの状態にしてから、別の投稿関数や承認済みワークフローに渡す構成にしてください。自動投稿を有効化する場合でも、誤投稿を避けるため承認ステップを挟むことを推奨します。
