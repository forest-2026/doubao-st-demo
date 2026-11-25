import streamlit as st
from openai import OpenAI

st.title("手动钥匙测试")

mid = st.secrets["DOUBAO_MODEL_ID"]
st.write("接入点：", mid)

st.write("--- secrets 里读到的 key ---")
k = st.secrets["DOUBAO_API_KEY"]
st.write("长度：", len(k))
st.write("原文：", repr(k))

st.divider()

st.write("--- 手动粘贴测试 ---")
manual_key = st.text_input("把方舟后台的 API Key 粘到这里", type="password")

if st.button("用这个 key 测试") and manual_key:
    c = OpenAI(
        api_key=manual_key,
        base_url="https://ark.cn-beijing.volces.com/api/v3"
    )
    try:
        r = c.chat.completions.create(
            model=mid,
            messages=[{"role": "user", "content": "你好"}],
            timeout=60.0
        )
        st.success("成功：" + r.choices[0].message.content)
    except Exception as e:
        st.error(str(e))
