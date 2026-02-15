import re
from dataclasses import dataclass
from typing import Dict, List

import requests
import streamlit as st
from bs4 import BeautifulSoup


@dataclass
class SourceDocument:
    url: str
    title: str
    text: str


KEYWORD_MAP: Dict[str, List[str]] = {
    "AI・データ活用": ["ai", "人工知能", "機械学習", "データ活用", "analytics", "llm"],
    "SaaS / クラウド": ["saas", "cloud", "クラウド", "subscription", "platform"],
    "グローバル展開": ["global", "海外", "international", "cross-border"],
    "製造・ハードウェア": ["製造", "factory", "hardware", "半導体", "automotive"],
    "金融・Fintech": ["fintech", "金融", "決済", "bank", "保険"],
    "新規事業・変革": ["新規事業", "変革", "transformation", "dx", "事業開発"],
}

ROLE_HINTS: Dict[str, List[str]] = {
    "法人営業": ["sales", "顧客", "売上", "導入", "提案"],
    "インサイドセールス": ["lead", "獲得", "ナーチャリング", "マーケティング", "架電"],
    "カスタマーサクセス": ["オンボーディング", "継続", "解約", "活用支援", "アップセル"],
    "パートナー営業": ["代理店", "アライアンス", "partner", "チャネル"],
}


def fetch_page_text(url: str) -> SourceDocument:
    response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = (soup.title.string or "") if soup.title else ""
    main_candidates = []
    for selector in ["main", "article", "body"]:
        node = soup.select_one(selector)
        if node:
            main_candidates.append(node)

    text_parts: List[str] = []
    for node in main_candidates:
        for element in node.find_all(["h1", "h2", "h3", "p", "li"]):
            t = " ".join(element.get_text(separator=" ", strip=True).split())
            if t and len(t) > 20:
                text_parts.append(t)

    text = "\n".join(text_parts)
    text = re.sub(r"\n{2,}", "\n", text)
    return SourceDocument(url=url, title=title.strip(), text=text[:9000])


def detect_topics(corpus: str) -> List[str]:
    lower = corpus.lower()
    topics: List[str] = []
    for topic, words in KEYWORD_MAP.items():
        if any(word.lower() in lower for word in words):
            topics.append(topic)
    return topics or ["汎用B2B"]


def detect_role(corpus: str) -> str:
    lower = corpus.lower()
    score: Dict[str, int] = {k: 0 for k in ROLE_HINTS}
    for role, words in ROLE_HINTS.items():
        score[role] = sum(1 for w in words if w.lower() in lower)
    best = max(score, key=score.get)
    return best if score[best] > 0 else "法人営業"


def build_requirement(corpus: str, topics: List[str], role: str) -> Dict[str, List[str] | str]:
    growth_words = ["成長", "拡大", "increase", "投資", "中期"]
    challenge_words = ["課題", "競争", "cost", "効率", "生産性", "解約"]

    growth_phase = "拡大フェーズ" if sum(w.lower() in corpus.lower() for w in growth_words) >= 2 else "基盤強化フェーズ"
    primary_challenge = "市場拡大と差別化" if sum(w.lower() in corpus.lower() for w in challenge_words) >= 2 else "再現性ある営業体制の構築"

    must_have = [
        f"{role}としての実務経験（目安3年以上）",
        "顧客課題を構造化し、提案ストーリーに落とし込む力",
        "CRM/SFAを使ったパイプライン管理スキル",
    ]

    if "AI・データ活用" in topics:
        must_have.append("データ分析・AI関連商材の提案経験")
    if "SaaS / クラウド" in topics:
        must_have.append("SaaSまたはクラウド商材の営業経験")
    if "グローバル展開" in topics:
        must_have.append("英語でのドキュメント読解または商談経験")

    nice_to_have = [
        "営業企画（KPI設計、勝ちパターン化）の経験",
        "マーケティングやプロダクト部門との横断プロジェクト経験",
        "経営層向け提案資料の作成経験",
    ]

    persona = [
        "曖昧な状況でも仮説を立てて前進できる",
        "顧客・社内双方のステークホルダー調整が得意",
        "数字へのコミットメントが高く、改善を継続できる",
    ]

    interview_points = [
        "過去の受注/失注案件を、課題→提案→成果で説明できるか",
        "KPI未達時にどのような打ち手を講じたか",
        "新規プロダクトや新市場で成果を出した再現性があるか",
    ]

    return {
        "想定職種": role,
        "事業フェーズ": growth_phase,
        "採用背景": primary_challenge,
        "注力テーマ": topics,
        "必須要件": must_have,
        "歓迎要件": nice_to_have,
        "人物像": persona,
        "面接評価ポイント": interview_points,
    }


def to_markdown(requirement: Dict[str, List[str] | str], sources: List[SourceDocument]) -> str:
    lines = [
        "# 人材要件定義（営業活動向け）",
        "",
        f"- 想定職種: **{requirement['想定職種']}**",
        f"- 事業フェーズ: **{requirement['事業フェーズ']}**",
        f"- 採用背景: {requirement['採用背景']}",
        f"- 注力テーマ: {', '.join(requirement['注力テーマ'])}",
        "",
    ]

    for key in ["必須要件", "歓迎要件", "人物像", "面接評価ポイント"]:
        lines.append(f"## {key}")
        for item in requirement[key]:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## 参照ソース")
    for source in sources:
        label = source.title if source.title else source.url
        lines.append(f"- {label}: {source.url}")

    return "\n".join(lines)


st.set_page_config(page_title="営業向け人材要件ジェネレーター", layout="wide")
st.title("営業向け 人材要件定義アプリ")
st.caption("企業ホームページ・IR情報を基に、採用ターゲットの要件ドラフトを自動生成します。")

with st.sidebar:
    st.header("入力")
    homepage_url = st.text_input("企業ホームページURL", placeholder="https://example.com")
    ir_url = st.text_input("IRページURL（任意）", placeholder="https://example.com/ir")
    extra_notes = st.text_area("補足メモ（任意）", placeholder="狙いたい職種、業界、現場課題など")

if st.button("要件を生成", type="primary"):
    sources: List[SourceDocument] = []
    errors: List[str] = []

    for url in [homepage_url, ir_url]:
        if not url.strip():
            continue
        try:
            sources.append(fetch_page_text(url.strip()))
        except Exception as exc:
            errors.append(f"{url}: {exc}")

    if not sources and not extra_notes.strip():
        st.error("URLまたは補足メモを入力してください。")
    else:
        corpus = "\n".join([s.text for s in sources] + [extra_notes])
        topics = detect_topics(corpus)
        role = detect_role(corpus)
        requirement = build_requirement(corpus, topics, role)
        md = to_markdown(requirement, sources)

        if errors:
            st.warning("一部URLの取得に失敗しました。補足メモを加えると精度が上がります。")
            for msg in errors:
                st.write(f"- {msg}")

        left, right = st.columns([2, 1])
        with left:
            st.markdown(md)
        with right:
            st.subheader("入力ソース")
            if sources:
                for src in sources:
                    st.write(f"- {src.title or '(タイトルなし)'}")
                    st.caption(src.url)
            else:
                st.write("URLソースなし（補足メモのみで生成）")

            st.download_button(
                "Markdownをダウンロード",
                data=md,
                file_name="requirements_draft.md",
                mime="text/markdown",
            )

st.divider()
st.markdown("### 使い方のヒント")
st.markdown(
    "1. 企業トップページURLとIRページURLを入力\n"
    "2. 現場で感じている営業課題を補足メモに追記\n"
    "3. 出力された必須要件・歓迎要件を面接票に転記"
)
