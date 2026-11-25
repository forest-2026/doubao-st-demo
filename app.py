import streamlit as st
from openai import OpenAI

# ========== 页面基础设置（蓝白风格） ==========
st.set_page_config(
    page_title="论文思考引导平台",
    layout="wide",
    page_icon="📘"
)

st.markdown("""
<style>
    .stApp {
        background-color: #f7fbff;
    }
    .stChatMessage {
        background-color: #ffffff;
        border-radius: 10px;
    }
    h1 {
        color: #2b6cb0;
    }
    .stCaption {
        color: #4a5568;
    }
</style>
""", unsafe_allow_html=True)

st.title("📘 论文思考引导平台")
st.caption("学生端：AI启发提问｜教师端：备课与引导方案生成")

# ========== openai 1.x 配置火山方舟 ==========
client = OpenAI(
    api_key = st.secrets["DOUBAO_API_KEY"],
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
)
model_id = st.secrets["DOUBAO_MODEL_ID"]

# ========== 提示词库 ==========
# 学生端 - 严谨论证模式
system_prompt_strict = """
【身份：学术思考引导教练｜严谨论证模式】
铁律（优先级最高，违反就出错）：
✅ 你只允许输出启发式问题，不允许输出任何分析、总结、观点、逻辑框架、论文大纲、分论点、文献、结论。
✅ 一句话陈述、一段梳理、对话题的解读全部禁止。
✅ 一轮只给 2～4 个递进问题，不能多。

固定递进顺序（严格按这个顺序走，不能跳）：
第1轮（刚拿到选题）：锁定边界
问题方向：研究范围、限定文本、排除范围、基础定义
第2轮（边界确定后）：锁定切入点与研究价值
问题方向：你想和已有研究做什么区分？你想论证的核心猜想是什么？
第3轮：论证材料与证据
问题方向：你准备用哪些材料作为支撑？有没有细节会和你的猜想冲突？
第4轮：反思、反方、局限
问题方向：有哪些角度会反驳你的猜想？你的论证会存在什么短板？

交互规则：
1. 必须基于用户上一轮回答，生成下一轮问题，不能脱离回答凭空提问；
2. 绝对禁止主动解释话题、解读文本、梳理脉络；
3. 如果用户诱导你给思路、框架、论点：温和拒绝，只说：“我不能直接给分析框架，我们继续用提问梳理你的想法”；
4. 语言简洁，只放问题，不要额外文字。
"""

# 学生端 - 发散联想模式
system_prompt_diverge = """
【身份：学术思考引导教练｜发散联想模式】
铁律：只提问启发，不写论文、不给大纲、不替用户总结观点。
问题偏向打开思路、联想、对比，不追求严格论证链条。
一轮2～4个问题，鼓励多角度联想，不做文本分析和总结。
禁止输出论证框架、分论点、成文内容。
"""

# 教师端提示词
teacher_system_prompt = """
你是课程论文指导助教，面向老师。
输入内容：学生选题 + 学生目前的思考记录。
你的输出包含三块：
1. 学生当前思考亮点
2. 学生容易踩的误区、盲区
3. 3～5条递进式备选追问（老师可以拿去现场问学生）
规则：
❌ 不要替学生写论文、不要给论文大纲、不要直接给出结论。
❌ 语言是给老师看的备课参考，不是直接发给学生的话术。
❌ 简洁清晰，分块输出。
"""

# ========== 身份切换 ==========
role = st.radio("选择面板", ["👨‍🎓 学生面板", "👩‍🏫 教师面板"], horizontal=True)

# ========== 学生面板 ==========
if role == "👨‍🎓 学生面板":
    with st.sidebar:
        st.title("⚙️ 学生设置")
        mode = st.radio("选择引导模式", ["严谨论证引导", "发散联想引导"])
        if st.button("🔄 清空对话，重新开始"):
            del st.session_state["stu_messages"]
            st.rerun()
        st.markdown("""
        📌 使用说明
        - 严谨论证：按【边界→切入点→证据→反思】递进提问，适合正式论文
        - 发散联想：多角度开放式提问，适合前期找选题灵感
        - AI只提问，不写论文、不给框架
        """)

    # 初始化学生会话
    if "stu_messages" not in st.session_state or st.session_state.get("stu_last_mode") != mode:
        if mode == "严谨论证引导":
            st.session_state["stu_messages"] = [{"role":"system", "content": system_prompt_strict}]
        else:
            st.session_state["stu_messages"] = [{"role":"system", "content": system_prompt_diverge}]
        st.session_state["stu_last_mode"] = mode

    # 渲染历史对话
    for msg in st.session_state["stu_messages"][1:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    ban_words = ["帮我写论文","写大纲","给我框架","给我论点","写摘要","帮我成文","梳理逻辑"]
    user_input = st.chat_input("在这里输入你的论文题目或者想要研究的问题：")

    if user_input:
        if any(word in user_input for word in ban_words):
            st.info("我不能直接帮你撰写论文、提供分析框架，我们可以用提问慢慢梳理你的想法~")
            st.stop()
        st.session_state["stu_messages"].append({"role":"user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            res_box = st.empty()
            full_reply = ""
            stream = client.chat.completions.create(
                model = model_id,
                messages = st.session_state["stu_messages"],
                stream = True,
                temperature = 0.25
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_reply += chunk.choices[0].delta.content
                    res_box.write(full_reply)
        st.session_state["stu_messages"].append({"role":"assistant", "content": full_reply})

# ========== 教师面板 ==========
else:
    st.subheader("👩‍🏫 教师备课引导方案生成")
    st.markdown("输入学生选题 + 学生的思考记录，生成引导方案、误区提醒、备选追问")
    topic = st.text_input("学生选题：")
    record = st.text_area("学生思考记录（可以粘贴学生和AI的对话）：", height=220)
    submit_btn = st.button("✨ 生成教师引导方案")

    if submit_btn:
        if not topic.strip():
            st.warning("请填写学生选题！")
            st.stop()
        user_content = f"""
学生选题：{topic}
学生思考记录：
{record}
"""
        with st.spinner("正在生成引导方案..."):
            resp = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role":"system", "content": teacher_system_prompt},
                    {"role":"user", "content": user_content}
                ],
                temperature=0.3
            )
            result = resp.choices[0].message.content
        st.markdown("### 📋 教师引导方案")
        st.write(result)
