# -----------------------------
# ここから下は「YouTubeチャンネル比較アプリ」のコードです
# 目的：
#  1) チャンネル内の動画を「再生回数が多い順（人気順）」で取得して表示する
#  2) 表示後に「公開日順 / いいね順 / コメント順」に並び替えできる
#
# 重要な変更点（今回の要件対応）：
#  - uploads（新しい順）を先頭N件だけ取るのをやめて、
#    「古い動画も含めるために」最大fetch_max件までページネーションで取得できるようにした
#  - 取得した候補の中で viewCount（再生数）で人気順を作成
#  - 表示は sort_key で並び替えできる（公開日 / いいね / コメント / 再生）
#  - 表示は show_n 件に制限（上位N本だけ見せる）
# -----------------------------

import os
import re
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# -----------------------------
# Utilities
# -----------------------------
def get_api_key() -> str:
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        raise RuntimeError("環境変数 YOUTUBE_API_KEY が設定されていません。")
    return key


def build_youtube():
    return build("youtube", "v3", developerKey=get_api_key())


def parse_channel_input(text: str) -> dict:
    """
    入力がチャンネルID / @handle / URL のどれかを判定して返す
    Return: {"type": "id"/"handle", "value": "..."}
    """
    t = (text or "").strip()
    if not t:
        return {"type": "id", "value": ""}

    m = re.search(r"youtube\.com/channel/(UC[\w-]{20,})", t)
    if m:
        return {"type": "id", "value": m.group(1)}

    m = re.search(r"youtube\.com/@([A-Za-z0-9._-]+)", t)
    if m:
        return {"type": "handle", "value": m.group(1)}

    if t.startswith("@"):
        return {"type": "handle", "value": t[1:]}

    if t.startswith("UC") and len(t) >= 20:
        return {"type": "id", "value": t}

    return {"type": "handle", "value": t.lstrip("@")}


def iso_to_local_str(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso


def safe_int(v) -> int:
    try:
        return int(v)
    except Exception:
        return 0


def compact_kpi(n: int) -> str:
    return f"{n:,}"


# -----------------------------
# Chat filter
# -----------------------------
def apply_chat_filter(rows, query: str):
    """
    対応例:
      - コメントが10件以上の動画だけ
      - 再生回数が10000以上
      - いいねが500以上
      - タイトルにPythonを含む
      - 直近30日
    """
    if not query or not query.strip():
        return rows, ["条件なし（全件表示）"]

    q = query.strip()
    logs = []
    filtered = rows

    # 直近N日
    m = re.search(r"直近\s*(\d+)\s*日", q)
    if m:
        days = int(m.group(1))
        now = datetime.now(timezone.utc)

        def in_last_days(r):
            try:
                dt = datetime.fromisoformat(r["_published_raw"].replace("Z", "+00:00"))
                return (now - dt).days <= days
            except Exception:
                return True

        filtered = [r for r in filtered if in_last_days(r)]
        logs.append(f"直近{days}日")

    # タイトルにキーワード
    m = re.search(r"タイトル.*?(?:に|で)\s*([^\s]+)\s*(?:を)?含む", q)
    if m:
        word = m.group(1)
        w = word.lower()
        filtered = [r for r in filtered if w in (r.get("タイトル", "") or "").lower()]
        logs.append(f"タイトルに「{word}」")

    # コメント >= N
    m = re.search(r"コメント.*?(\d+)\s*件.*?(以上|より多い|>=)", q)
    if m:
        n = int(m.group(1))
        filtered = [r for r in filtered if int(r.get("コメント", 0)) >= n]
        logs.append(f"コメント>= {n}")

    # いいね >= N
    m = re.search(r"(いいね|高評価).*?(\d+)\s*(?:件)?\s*.*?(以上|より多い|>=)", q)
    if m:
        n = int(m.group(2))
        filtered = [r for r in filtered if int(r.get("いいね", 0)) >= n]
        logs.append(f"いいね>= {n}")

    # 再生 >= N
    m = re.search(r"(再生回数|再生).*?(\d+)\s*(?:回)?\s*.*?(以上|より多い|>=)", q)
    if m:
        n = int(m.group(2))
        filtered = [r for r in filtered if int(r.get("再生", 0)) >= n]
        logs.append(f"再生>= {n}")

    if not logs:
        logs.append("条件を解釈できませんでした（例: コメントが10件以上の動画だけ）")

    return filtered, logs


# -----------------------------
# YouTube API calls (cached)
# -----------------------------
@st.cache_data(ttl=3600)
def fetch_channel_by_id(channel_id: str):
    yt = build_youtube()
    res = (
        yt.channels()
        .list(
            part="snippet,statistics,contentDetails",
            id=channel_id,
            maxResults=1,
        )
        .execute()
    )
    items = res.get("items", [])
    return items[0] if items else None


@st.cache_data(ttl=3600)
def fetch_channel_by_handle(handle: str):
    yt = build_youtube()
    res = (
        yt.search()
        .list(
            part="snippet",
            q=f"@{handle}",
            type="channel",
            maxResults=5,
        )
        .execute()
    )
    items = res.get("items", [])
    if not items:
        return None
    channel_id = items[0]["snippet"]["channelId"]
    return fetch_channel_by_id(channel_id)


@st.cache_data(ttl=3600)
def fetch_uploads_playlist_id(channel_id: str) -> str | None:
    """
    チャンネルに紐づく uploads（全動画のプレイリスト）IDを取得する
    """
    yt = build_youtube()
    res = yt.channels().list(
        part="contentDetails",
        id=channel_id,
        maxResults=1,
    ).execute()

    items = res.get("items", [])
    if not items:
        return None

    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


@st.cache_data(ttl=3600)
def fetch_videos_from_uploads(uploads_playlist_id: str, max_fetch: int):
    """
    uploadsプレイリストをページネーションで辿り、最大 max_fetch 本ぶんの videoId を集める。

    ✅ 重要：
    uploads は「新しい順」なので、max_fetch を大きくすると古い動画も候補に入る
    """
    yt = build_youtube()
    items_out = []
    next_token = None

    while len(items_out) < max_fetch:
        res = yt.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=min(50, max_fetch - len(items_out)),
            pageToken=next_token,
        ).execute()

        for it in res.get("items", []):
            cd = it.get("contentDetails", {})
            vid = cd.get("videoId")
            published_at = cd.get("videoPublishedAt", "")
            if vid:
                items_out.append({"videoId": vid, "publishedAt": published_at})

        next_token = res.get("nextPageToken")
        if not next_token:
            break

    return items_out


@st.cache_data(ttl=3600)
def fetch_video_details(video_ids: list[str]):
    """
    videos.list で、タイトル/サムネ/公開日/統計（再生・いいね・コメント）をまとめて取る
    """
    if not video_ids:
        return {}

    yt = build_youtube()
    out = {}

    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i : i + 50]
        res = yt.videos().list(
            part="snippet,statistics",
            id=",".join(chunk),
            maxResults=len(chunk),
        ).execute()

        for it in res.get("items", []):
            vid = it["id"]
            sn = it.get("snippet", {})
            stt = it.get("statistics", {})
            thumbs = sn.get("thumbnails", {})
            thumb_url = (thumbs.get("medium") or thumbs.get("default") or {}).get("url", "")

            out[vid] = {
                "title": sn.get("title", ""),
                "publishedAt": sn.get("publishedAt", ""),
                "thumbnail": thumb_url,
                "viewCount": safe_int(stt.get("viewCount")),
                "likeCount": safe_int(stt.get("likeCount")),
                "commentCount": safe_int(stt.get("commentCount")),
            }

    return out


def load_channel(input_text: str):
    parsed = parse_channel_input(input_text)
    if parsed["type"] == "id":
        return fetch_channel_by_id(parsed["value"])
    return fetch_channel_by_handle(parsed["value"])


def build_popular_rows(channel_id: str, max_fetch: int):
    """
    1) uploads から最大 max_fetch 本ぶんの動画IDを取る（古い動画も対象にする）
    2) videos.list で統計を取る
    3) 再生回数順（人気順）に並べた rows を返す
    """
    uploads_id = fetch_uploads_playlist_id(channel_id)
    if not uploads_id:
        return []

    vids = fetch_videos_from_uploads(uploads_id, max_fetch)
    ids = [v["videoId"] for v in vids]

    details = fetch_video_details(ids)

    rows = []
    for vid in ids:
        d = details.get(vid, {})
        published_raw = d.get("publishedAt", "")
        rows.append(
            {
                "公開日": iso_to_local_str(published_raw),
                "タイトル": d.get("title", ""),
                "再生": d.get("viewCount", 0),
                "いいね": d.get("likeCount", 0),
                "コメント": d.get("commentCount", 0),
                "動画ID": vid,
                "サムネ": d.get("thumbnail", ""),
                "URL": f"https://www.youtube.com/watch?v={vid}",
                "_published_raw": published_raw,
            }
        )

    # 取得のベースは「再生回数（人気順）」
    rows.sort(key=lambda r: r["再生"], reverse=True)
    return rows


def sort_rows(rows, sort_key: str):
    """
    取得は再生回数順で固定。
    表示だけをユーザーの選択で並び替える。
    """
    if sort_key == "再生回数（多い順）":
        return sorted(rows, key=lambda r: r["再生"], reverse=True)
    if sort_key == "公開日（新しい順）":
        return sorted(rows, key=lambda r: r["_published_raw"], reverse=True)
    if sort_key == "いいね（多い順）":
        return sorted(rows, key=lambda r: r["いいね"], reverse=True)
    return sorted(rows, key=lambda r: r["コメント"], reverse=True)


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="YouTube 2ch 比較", layout="wide")
st.title("📊 YouTubeチャンネル比較（横並び）")

with st.sidebar:
    st.header("入力")
    col_in1, col_in2 = st.columns(2)

    with col_in1:
        ch_a = st.text_input("チャンネルA（ID/URL/@handle）", value="@SixTONES_official")

    with col_in2:
        ch_b = st.text_input("チャンネルB（ID/URL/@handle）", value="@SnowMan.official.9")

    # ✅ 追加：古い動画も候補に入れるための「取得最大数」
    fetch_max = st.slider(
        "人気TOP候補として取得する本数（古い動画も含める）",
        100, 5000, 1000, step=100
    )

    # ✅ 追加：画面に表示する上位N本
    show_n = st.slider(
        "表示する本数（上位N本）",
        5, 100, 20
    )

    # 表示の並び替え
    sort_key = st.selectbox(
        "表示の並び替え",
        [
            "再生回数（多い順）",
            "公開日（新しい順）",
            "いいね（多い順）",
            "コメント（多い順）",
        ],
    )

    top_n = st.slider("チャートに出す上位本数", 5, 20, 10)

    st.caption("※ @handle は検索経由のベストエフォートです。確実にしたい場合はチャンネルID推奨。")
    st.caption("※ 反映されないときは Streamlit のメニューから Clear cache を試してください。")

if "filter_messages" not in st.session_state:
    st.session_state.filter_messages = []

try:
    channelA = load_channel(ch_a)
    channelB = load_channel(ch_b)
except RuntimeError as e:
    st.error(str(e))
    st.stop()
except HttpError as e:
    st.error(f"YouTube API エラー: {e}")
    st.stop()

if not channelA or not channelB:
    st.warning("片方（または両方）のチャンネルが見つかりませんでした。ID/URL/@handle を確認してください。")
    st.stop()


def channel_info(ch):
    sn = ch.get("snippet", {})
    stt = ch.get("statistics", {})
    return {
        "id": ch.get("id", ""),
        "title": sn.get("title", ""),
        "desc": sn.get("description", ""),
        "thumb": (sn.get("thumbnails", {}).get("medium", {}) or {}).get("url", ""),
        "publishedAt": sn.get("publishedAt", ""),
        "subscribers": safe_int(stt.get("subscriberCount")),
        "views": safe_int(stt.get("viewCount")),
        "videos": safe_int(stt.get("videoCount")),
    }


A = channel_info(channelA)
B = channel_info(channelB)

left, right = st.columns(2)


def render_channel_header(col, info):
    with col:
        c1, c2 = st.columns([1, 2], vertical_alignment="center")
        with c1:
            if info["thumb"]:
                st.image(info["thumb"], use_container_width=True)
        with c2:
            st.subheader(info["title"])
            st.caption(f"ID: {info['id']}")
            st.caption(f"開設日: {iso_to_local_str(info['publishedAt'])}")

        m1, m2, m3 = st.columns(3)
        m1.metric("登録者数", compact_kpi(info["subscribers"]))
        m2.metric("総再生回数", compact_kpi(info["views"]))
        m3.metric("総動画数", compact_kpi(info["videos"]))


render_channel_header(left, A)
render_channel_header(right, B)

st.divider()
st.subheader("差分（A - B）")
d1, d2, d3 = st.columns(3)
d1.metric("登録者数", compact_kpi(A["subscribers"] - B["subscribers"]))
d2.metric("総再生回数", compact_kpi(A["views"] - B["views"]))
d3.metric("総動画数", compact_kpi(A["videos"] - B["videos"]))

st.divider()
st.header("🔥 人気動画（比較）")

try:
    # ✅ まず「古い動画も含めて」候補を集める → 再生数順（人気順）でベース作成
    baseA = build_popular_rows(A["id"], fetch_max)
    baseB = build_popular_rows(B["id"], fetch_max)

    # ✅ 表示はユーザーが選んだキーで並べ替えし、最後に上位show_n件だけ表示
    rowsA = sort_rows(baseA, sort_key)[:show_n]
    rowsB = sort_rows(baseB, sort_key)[:show_n]
except HttpError as e:
    st.error(f"YouTube API エラー: {e}")
    st.stop()

# -----------------------------
# Chat filter UI
# -----------------------------
st.subheader("💬 絞り込み（チャットで指示）")
st.caption("例: コメントが10件以上の動画だけ / 再生回数が10000以上 / 直近30日 / タイトルにPythonを含む")

user_q = st.chat_input("絞り込み条件を入力（空なら全件表示）")
if user_q:
    st.session_state.filter_messages.append({"role": "user", "content": user_q})

for msg in st.session_state.filter_messages[-10:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

active_q = ""
for msg in reversed(st.session_state.filter_messages):
    if msg["role"] == "user":
        active_q = msg["content"]
        break

filteredA, logs = apply_chat_filter(rowsA, active_q)
filteredB, _ = apply_chat_filter(rowsB, active_q)

st.info(" / ".join(logs))

# -----------------------------
# Render videos
# -----------------------------
colA, colB = st.columns(2)


def render_videos(col, info, rows):
    with col:
        st.subheader(info["title"])
        st.dataframe(
            [
                {k: r[k] for k in ["公開日", "タイトル", "再生", "いいね", "コメント", "動画ID"]}
                for r in rows
            ],
            use_container_width=True,
            hide_index=True,
        )

        if rows:
            pick = st.selectbox(
                f"プレビュー（{info['title']}）",
                options=rows,
                format_func=lambda r: f"{r['公開日']} | {r['タイトル'][:40]}",
                key=f"pick_{info['id']}",
            )
            if pick:
                if pick["サムネ"]:
                    st.image(pick["サムネ"], use_container_width=True)
                st.write(f"**{pick['タイトル']}**")
                st.write(
                    f"再生: {pick['再生']:,} / いいね: {pick['いいね']:,} / コメント: {pick['コメント']:,}"
                )
                st.link_button("YouTubeで開く", pick["URL"])
        else:
            st.warning("条件に合う動画がありません。")


render_videos(colA, A, filteredA)
render_videos(colB, B, filteredB)

# -----------------------------
# Charts（再生回数Top）
# -----------------------------
st.divider()
st.header("📈 再生回数 Top比較（フィルタ後）")

cA, cB = st.columns(2)


def bar_data(rows, n):
    top = sorted(rows, key=lambda r: r["再生"], reverse=True)[:n]
    return [{"title": r["タイトル"][:30], "views": r["再生"]} for r in top]


with cA:
    st.subheader(f"A: {A['title']}")
    dfA = pd.DataFrame(bar_data(filteredA, top_n))
    if dfA.empty:
        st.warning("A: 条件に合う動画がないためチャートを表示できません。")
    else:
        st.bar_chart(dfA, x="title", y="views")

with cB:
    st.subheader(f"B: {B['title']}")
    dfB = pd.DataFrame(bar_data(filteredB, top_n))
    if dfB.empty:
        st.warning("B: 条件に合う動画がないためチャートを表示できません。")
    else:
        st.bar_chart(dfB, x="title", y="views")
