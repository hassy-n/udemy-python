import os  # 環境変数を取得するための標準ライブラリ
import streamlit as st  # WebアプリのUIを作るライブラリ
import requests  # URLから画像をダウンロードするためのライブラリ
from PIL import Image, ImageDraw  # 画像の読み込みと枠の描画に使うライブラリ
from io import BytesIO  # バイトデータを画像として扱うためのライブラリ
from azure.ai.vision.imageanalysis import ImageAnalysisClient  # Azure Vision APIのクライアント
from azure.ai.vision.imageanalysis.models import VisualFeatures  # 解析する機能を指定するクラス
from azure.core.credentials import AzureKeyCredential  # APIキーを認証情報として渡すクラス
from deep_translator import GoogleTranslator  # Google翻訳で英語→日本語に翻訳するライブラリ
from openai import AzureOpenAI  # Azure OpenAI APIのクライアント
from PIL import Image, ImageDraw, ImageFont  # ImageFontを追加

# --- クライアントの準備 ---
endpoint = os.environ["VISION_ENDPOINT"]  # Azure Vision APIのエンドポイントURLを環境変数から取得
key = os.environ["VISION_KEY"]  # Azure Vision APIのキーを環境変数から取得
client = ImageAnalysisClient(endpoint, AzureKeyCredential(key))  # Azure Vision APIクライアントを初期化

openai_client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_KEY"],  # Azure OpenAI APIのキーを環境変数から取得
    api_version="2025-03-01-preview",  # 使用するAPIのバージョンを指定
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]  # Azure OpenAIのエンドポイントURLを環境変数から取得
)

# --- 画面のタイトル ---
st.title("🔍 物体検出アプリ")  # ページのタイトルを表示

# --- URL入力 & ファイルアップロード ---
image_url = st.text_input(
    "画像URLを入力してください",  # 入力欄のラベル
    value="https://learn.microsoft.com/azure/ai-services/computer-vision/media/quickstarts/presentation.png"  # デフォルトで表示するURL
)
uploaded_file = st.file_uploader("またはファイルをアップロード", type=["jpg", "jpeg", "png"])  # jpg/jpeg/pngのみアップロード可能なファイル選択欄を表示

if st.button("解析する"):  # 「解析する」ボタンが押されたときに以下の処理を実行
    if uploaded_file is not None:  # ファイルがアップロードされている場合
        image_data = uploaded_file.read()  # アップロードされたファイルをバイトデータとして読み込む
        result = client.analyze(
            image_data=image_data,  # バイトデータを渡してAzure Vision APIで解析
            visual_features=[VisualFeatures.OBJECTS, VisualFeatures.CAPTION, VisualFeatures.TAGS],  # 物体・キャプション・タグの3つを取得
        )
        image = Image.open(BytesIO(image_data)).convert("RGB")  # バイトデータを画像オブジェクトに変換
    else:  # ファイルがアップロードされていない場合はURLを使う
        result = client.analyze_from_url(
            image_url=image_url,  # 入力されたURLを渡してAzure Vision APIで解析
            visual_features=[VisualFeatures.OBJECTS, VisualFeatures.CAPTION, VisualFeatures.TAGS],  # 物体・キャプション・タグの3つを取得
        )
        response = requests.get(image_url)  # URLから画像をダウンロード
        image = Image.open(BytesIO(response.content)).convert("RGB")  # ダウンロードした画像を画像オブジェクトに変換

    draw = ImageDraw.Draw(image)  # 画像に図形を描画するためのオブジェクトを作成

    detected = []  # 検出された物体の情報を格納するリストを初期化
    if result.objects:  # 物体が1つ以上検出されていた場合
        for obj in result.objects.list:  # 検出された物体を1つずつ処理
            name = obj.tags[0].name  # 物体の名前を取得
            conf = obj.tags[0].confidence  # 物体の信頼度（0〜1）を取得
            box = obj.bounding_box  # 物体の位置情報（x, y, width, height）を取得
            draw.rectangle(
                [box.x, box.y, box.x + box.width, box.y + box.height],  # 左上と右下の座標を指定
                outline="red", width=3  # 赤色・太さ3の枠を描画
            )
            font = ImageFont.truetype("arial.ttf", size=40)  # サイズは数字で調整
            draw.text((box.x, box.y - 30), name, fill="red", font=font)
            detected.append(f"**{name}** （信頼度: {conf:.0%}）")  # 物体名と信頼度をリストに追加

    col1, col2 = st.columns(2)  # 画面を左右2カラムに分割

    with col1:  # 左カラムの内容
        st.subheader("検出結果")  # 「検出結果」という見出しを表示
        st.image(image, use_container_width=True)  # 枠を描画した画像をカラム幅に合わせて表示

    with col2:  # 右カラムの内容
        st.subheader("キャプション")  # 「キャプション」という見出しを表示
        if result.caption:  # キャプションが取得できていた場合
            translated = GoogleTranslator(source="en", target="ja").translate(result.caption.text)  # 英語のキャプションを日本語に翻訳
            st.write(translated)  # 翻訳されたキャプションを表示

        st.subheader("検出された物体")  # 「検出された物体」という見出しを表示
        if detected:  # 物体が1つ以上検出されていた場合
            for item in detected:  # 検出された物体を1つずつ表示
                st.markdown(f"- {item}")  # 箇条書きで物体名と信頼度を表示
        else:
            st.write("物体が検出されませんでした")  # 物体が検出されなかった場合のメッセージを表示

        st.subheader("タグ")  # 「タグ」という見出しを表示
        if result.tags:  # タグが1つ以上取得できていた場合
            tag_names = [t.name for t in result.tags.list]  # タグ名だけのリストを作成
            st.write(", ".join(tag_names))  # タグをカンマ区切りで表示

            # Azure OpenAIで文章生成
            st.subheader("画像の説明")  # 「画像の説明」という見出しを表示
            response = openai_client.responses.create(
                model="gpt-5-mini",  # 使用するモデルのデプロイ名を指定
                input=f"以下のタグは画像認識AIが検出したものです。タグをもとに、この画像に何が映っているか、どんな場面や雰囲気かを3〜5文で詳しく日本語で説明してください。タグ: {', '.join(tag_names)}"  # タグを埋め込んだプロンプトを送信
            )
            st.write(response.output_text)  # AIが生成した説明文を表示
        else:
            st.write("タグが検出されませんでした")  # タグが取得できなかった場合のメッセージを表示