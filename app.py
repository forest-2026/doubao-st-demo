import streamlit as st
from openai import OpenAI
import traceback

st.title("API 连通性诊断")

key = st.secrets["DOUBAO_API_KEY"]
mid = st.secrets["DOUBAO_MODEL_ID"]

st.write("key 长度：", len(key))
st.write("key 前缀：", key[:8])
st.write("key 有没有前后空格：", key != key.strip())
st.write("model_id：", mid)
st.write("model_id 是不是 ep- 开头：", mid.startswith("ep-"))

client = OpenAI(
    api_key=key,
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

if st.button("开始测试"):
    try:
        r = client.chat.completions.create(
            model=mid,
            messages=[{"role": "user", "content": "你好"}],
            timeout=60.0
        )
        st.success("调用成功：" + r.choices[0].message.content)
    except Exception as e:
        st.error("错误类型：" + type(e).__name__)
        st.code(traceback.format_exc())
