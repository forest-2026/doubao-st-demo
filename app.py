
    api_key = st.secrets["DOUBAO_API_KEY"],
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
)
model_id = st.secrets["DOUBAO_MODEL_ID"]

# 网页标题
st.title("豆包AI演示Demo")

# 聊天输入框
user_input = st.chat_input("请在这里输入你的问题")

if user_input:
    # 展示用户消息
    with st.chat_message("user"):
        st.write(user_input)
    # 调用豆包模型
    response = client.chat.completions.create(
        model = model_id,
        messages = [{"role": "user", "content": user_input}],
        stream = True
    )
    # 流式输出（字一个个跳出来，好看）
    with st.chat_message("assistant"):
        res_box = st.empty()
        full_text = ""
        for chunk in response:
            if chunk.choices:
                full_text += chunk.choices[0].delta.content or ""
                res_box.write(full_text)
