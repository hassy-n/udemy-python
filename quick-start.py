import os  # 環境変数を取得するための標準ライブラリ
import streamlit as st  # WebアプリのUIを作るライブラリ
import requests  # URLから画像をダウンロードするためのライブラリ
from io import BytesIO  # バイトデータを画像として扱うためのライブラリ

from PIL import Image, ImageDraw, ImageFont  # 画像処理（フォント含む）
from azure.ai.vision.imageanalysis import ImageAnalysisClient  # Azure Vision APIのクライアント
from azure.ai.vision.imageanalysis.models import VisualFeatures  # 解析する機能を指定するクラス
from azure.core.credentials import AzureKeyCredential  # APIキーを認証情報として渡すクラス
from deep_translator import GoogleTranslator  # Google翻訳で英語→日本語に翻訳するライブラリ
from openai import AzureOpenAI  # Azure OpenAI APIのクライアント


# -----------------------------
# Secrets / 環境変数の取得を安全にする
# -----------------------------
def get_setting(name: str) -> str | None:
    """Streamlit Cloudでは st.secrets が確実。ローカルは os.getenv でもOK。"""
    try:
        if name in st.secrets:
            value = st.secrets[name]
            if isinstance(value, str) and value.strip() != "":
                return value
    except Exception:
        pass
    value = os.getenv(name)
    return value.strip() if isinstance(value, str) and value.strip() != "" else None


def require_setting(name: str) -> str:
    v = get_setting(name)
    if not v:
        raise RuntimeError(f"{name} が未設定です。Streamlit Cloud の Secrets に設定してください。")
    return v


# -----------------------------
# フォントを安全にロード（Cloud/Linux対応）
# -----------------------------
def get_font(size: int = 40) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    優先順位：
    1) リポジトリ同梱 fonts/ のフォント（日本語ならこれ推奨）
    2) LinuxにありがちなDejaVu
    3) 最後はPILのデフォルト
    """
    here = os.path.dirname(__file__)
    candidates = [
        os.path.join(here, "fonts", "NotoSansJP-Regular.ttf"),  # 推奨：同梱
        os.path.join(here, "fonts", "NotoSansCJKjp-Regular.otf"),  # 代替
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linuxにあることが多い
    ]

    for path in candidates:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size=size)
        except OSError:
            pass

    # 最後の手段（日本語は□になりがち）
    return ImageFont.load_default()


# -----------------------------
# クライアントの準備
# -----------------------------
vision_endpoint = require_setting("VISION_ENDPOINT")
vision_key = require_setting("VISION_KEY")
client = ImageAnalysisClient(vision_endpoint, AzureKeyCredential(vision_key))

openai_client = AzureOpenAI(
    api_key=require_setting("AZURE_OPENAI_KEY"),
    api_version=get_setting("AZURE_OPENAI_API_VERSION") or "2025-03-01-preview",
    azure_endpoint=require_setting("AZURE_OPENAI_ENDPOINT"),
)

# -----------------------------
# 画面のタイトル
# -----------------------------
st.title("🔍 物体検出アプリ")

# -----------------------------
# URL入力 & ファイルアップロード
# -----------------------------
image_url = st.text_input(
    "画像URLを入力してください",
    value="https://learn.microsoft.com/azure/ai-services/computer-vision/media/quickstarts/presentation.png",
)
uploaded_file = st.file_uploader("またはファイルをアップロード", type=["jpg", "jpeg", "png"])

if st.button("解析する"):
    # 画像取得＆解析
    if uploaded_file is not None:
        image_data = uploaded_file.read()
        result = client.analyze(
            image_data=image_data,
            visual_features=[VisualFeatures.OBJECTS, VisualFeatures.CAPTION, VisualFeatures.TAGS],
        )
        image = Image.open(BytesIO(image_data)).convert("RGB")
    else:
        result = client.analyze_from_url(
            image_url=image_url,
            visual_features=[VisualFeatures.OBJECTS, VisualFeatures.CAPTION, VisualFeatures.TAGS],
        )
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")

    draw = ImageDraw.Draw(image)

    detected = []
    font = get_font(size=40)  # ← ループ外で1回だけロード（高速＆安定）

    if result.objects:
        for obj in result.objects.list:
            name = obj.tags[0].name
            conf = obj.tags[0].confidence
            box = obj.bounding_box

            # 枠
            draw.rectangle(
                [box.x, box.y, box.x + box.width, box.y + box.height],
                outline="red",
                width=3,
            )

            # ラベル（画像の上にはみ出す場合の簡易対策）
            text_y = max(0, box.y - 45)
            draw.text((box.x, text_y), name, fill="red", font=font)

            detected.append(f"**{name}** （信頼度: {conf:.0%}）")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("検出結果")
        st.image(image, use_container_width=True)

    with col2:
        st.subheader("キャプション")
        if result.caption:
            translated = GoogleTranslator(source="en", target="ja").translate(result.caption.text)
            st.write(translated)

        st.subheader("検出された物体")
        if detected:
            for item in detected:
                st.markdown(f"- {item}")
        else:
            st.write("物体が検出されませんでした")

        st.subheader("タグ")
        if result.tags:
            tag_names = [t.name for t in result.tags.list]
            st.write(", ".join(tag_names))

            st.subheader("画像の説明")
            resp = openai_client.responses.create(
                model="gpt-5-mini",  # デプロイ名
                input=(
                    "以下のタグは画像認識AIが検出したものです。"
                    "タグをもとに、この画像に何が映っているか、どんな場面や雰囲気かを3〜5文で詳しく日本語で説明してください。"
                    f" タグ: {', '.join(tag_names)}"
                ),
            )
            st.write(resp.output_text)
        else:
            st.write("タグが検出されませんでした")
