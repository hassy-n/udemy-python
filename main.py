import streamlit as st
from PIL import Image
import time

st.write("プログレスバーの表示")
"Start!!"

latest_iteration =st.empty()
bar = st.progress(0)

for i in range(100):
  latest_iteration.text(f"Iteration {i+1}")
  bar.progress(i+1)
  time.sleep(0.5)

"done"



# left_column, right_column = st.columns(2)

# button = left_column.button("右カラムに文字を表示")
# if button:
#   right_column.write("ここは右カラム")

# expander1 = st.expander("Q.足が臭い")
# expander1.write("よく洗いましょう")

# expander2 = st.expander("あっちに行きたい")
# expander2.write("いってらっしゃいませ")

# タイトル
#st.title("はじめてのStreamlitアプリ")

# 説明文
#st.write("これはStreamlitで作った簡単なWebアプリです。")

# 名前入力
#name = st.text_input("あなたの名前を入力してください")

# ボタン
#if st.button("あいさつする"):
#    if name:
#        st.success(f"こんにちは、{name}さん！")
#    else:
#        st.warning("名前を入力してください。")

# スライダー
#age = st.slider(" ",0,100,20) 
#st.write(f"あなたは {age} 歳ですね。")

# 今日の日付表示
#today = datetime.date.today()
#st.write(f"今日は {today} です。")

# チェックボックス
#if st.checkbox("秘密のメッセージを見る"):
#    st.info("Streamlitはとても簡単にWebアプリが作れます！")

#option = st.selectbox("好きな数字を選んでください", list(range(1,10)))
#st.write(f"あなたの好きな数字は {option} です")


#st.title('Streamlit超入門')
#st.title('Display Image')

#img = Image.open('IMG_9600.JPG')
#st.image(img, caption='Ishigaki')


#df = pd.DataFrame(np.random.rand(100,2)+[35.69,139.70],
#columns = ["lat","lon"])

#st.write(df)
#st.map(df)
#st.line_chart(df)
#st.bar_chart(df)


#st.dataframe(df.style.highlight_max(axis=0) ) #動的なテーブル（ソートなど）
#st.table(df) #静的なテーブル