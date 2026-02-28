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
