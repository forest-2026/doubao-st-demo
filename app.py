import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="论文思考引导平台",
    layout="wide"
)

st.title("📘 论文思考引导平台")
st.caption("学生端：AI启发提问｜教师端：备课与引导方案生成")

# ========== 密钥与接入点 ==========
# 从 secrets 读 key，并清除所有空格/换行（防止复制污染）
api_key = "".join(st.secrets["DOUBAO_API_KEY"].split())

# 接入点写死，只有一个 ep-
model_id = "ep-20261125200620-lkmcg"

# 侧边栏临时输入 key（不填就用上面 secrets 里的）
manual_key = st.sidebar.text_input(
    "API Key（临时备用，不填就用 secrets 里的）",
    type="password"
)
if manual_key.strip():
    api_key = "".join(manual_key.split())

client = OpenAI(
    api_key=api_key,
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

# ========== 三种引导模式提示词 ==========
system_prompt_strict = """
【身份：学术思考引导教练｜严谨论证模式】
铁律：只允许输出启发式问题，不允许输出任何分析、总结、观点、逻辑框架、论文大纲、分论点、文献、结论。
一轮只给 2～4 个递进问题。

固定递进顺序：
第1轮：锁定边界：研究范围、限定文本、排除范围、基础定义
第2轮：切入点与研究价值：和已有研究区分、核心猜想
第3轮：论证材料与证据：支撑材料、冲突细节
第4轮：反思反方局限：反驳角度、论证短板

规则：
1.基于用户上一轮回答生成问题，不要凭空提问
2.禁止解读文本梳理脉络
3.用户索要框架就回复：我不能直接给分析框架，我们继续用提问梳理你的想法
4.只输出问题，不要多余文字。
"""

system_prompt_diverge = """
【身份：学术思考引导教练｜发散联想模式】
铁律：只提问启发，不写论文、不给大纲、不替用户总结观点。
一轮2～4个开放式问题，用于打开选题思路，鼓励多角度联想。
禁止输出框架、分论点、成文内容。
"""

system_prompt_literature = """
【身份：学术思考引导教练｜文献线索引导模式】
铁律：只输出启发式问题，绝对不要列出具体文献名称、作者、期刊、链接。
一轮只给 2～4 个问题。
引导方向：
1.你想找的是理论概念类资料，还是具体案例/数据类资料？
2.如果去数据库检索，你打算用哪几个关键词？这些关键词还能换成哪些同义词？
3.你需要哪一类材料来支撑你的观点？哪一类材料反而可能反驳你？
4.你打算用哪些渠道查？(知网/万方/Google Scholar/图书馆)
禁止直接给文献清单，只帮他想清楚该找什么、去哪找、怎么搜。
"""

teacher_system_prompt = """
你是课程论文指导助教，面向老师。
输出三部分：
1.学生当前思考亮点
2.学生容易踩的误区盲区
3.3-5条递进备选追问
不要替学生写论文，不要输出大纲，输出为教师备课参考。
"""

# ========== 面板切换 ==========
role = st.radio("选择面板", ["👨‍🎓 学生面板", "👩‍🏫 教师面板"], horizontal=True)

# ========== 学生面板 ==========
if role == "👨‍🎓 学生面板":
    with st.sidebar:
        st.title("设置")
        mode = st.radio(
            "选择引导模式",
            ["严谨论证引导", "发散联想引导", "文献线索引导"]
        )
        if st.button("🔄清空对话"):
            del st.session_state["stu_messages"]
            st.rerun()

        st.markdown("""
        - 严谨论证：边界→切入点→证据→反思
        - 发散联想：打开思路找选题
        - 文献线索：想清楚查什么、怎么搜
        """)

    # 初始化 / 切换模式时重建对话
    if "stu_messages" not in st.session_state or st.session_state.get("stu_last_mode") != mode:
        if mode == "严谨论证引导":
            p = system_prompt_strict
        elif mode == "发散联想引导":
            p = system_prompt_diverge
        else:
            p = system_prompt_literature
        st.session_state["stu_messages"] = [{"role": "system", "content": p}]
        st.session_state["stu_last_mode"] = mode

    for msg in st.session_state["stu_messages"][1:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    ban_words = ["帮我写论文", "写大纲", "给我框架", "给我论点", "写摘要", "帮我成文", "梳理逻辑"]
    user_input = st.chat_input("输入论文题目或研究问题：")

    if user_input:
        if any(w in user_input for w in ban_words):
            st.info("不能直接帮你写论文，我们通过提问梳理思路。")
            st.stop()

        st.session_state["stu_messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            res_box = st.empty()
            full_reply = ""
            try:
                stream = client.chat.completions.create(
                    model=model_id,
                    messages=st.session_state["stu_messages"],
                    stream=True,
                    temperature=0.25,
                    timeout=60.0
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_reply += chunk.choices[0].delta.content
                        res_box.write(full_reply)
                st.session_state["stu_messages"].append({"role": "assistant", "content": full_reply})
            except Exception as e:
                st.error(f"调用失败：{e}")

# ========== 教师面板 ==========
else:
    st.subheader("教师备课引导方案")
    topic = st.text_input("学生选题")
    record = st.text_area("学生思考记录", height=200)
    if st.button("生成引导方案"):
        if not topic.strip():
            st.warning("请先填写学生选题")
        else:
            user_content = f"""
学生选题：{topic}
学生思考记录：
{record}
"""
            with st.spinner("处理中..."):
                try:
                    resp = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": teacher_system_prompt},
                            {"role": "user", "content": user_content}
                        ],
                        temperature=0.3,
                        timeout=60.0
                    )
                    result = resp.choices[0].message.content
                    st.markdown("### 引导方案")
                    st.write(result)
                except Exception as e:
                    st.error(f"调用失败：{e}")
