import streamlit as st
import time
import pandas as pd
import requests
import json
from streamlit.components.v1 import html

st.set_page_config(page_title="AI思辨训练助手", layout="wide")

WARNING_KEYWORDS = ["作弊", "帮我写答案", "直接给结论", "抄", "代写", "写文章"]

SHAKE_SCRIPT = """
<script>
function shakePage(){
  document.body.style.animation = "shake 0.5s";
  setTimeout(()=>{document.body.style.animation = ""},500);
}
</script>
<style>
@keyframes shake {
  0%,100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(6px); }
  60% { transform: translateX(-6px); }
  80% { transform: translateX(6px); }
}
</style>
"""
html(SHAKE_SCRIPT, height=0)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "log_list" not in st.session_state:
    st.session_state.log_list = []
if "draft" not in st.session_state:
    st.session_state.draft = ""
if "show_warn" not in st.session_state:
    st.session_state.show_warn = False

with st.sidebar:
    st.header("⚙️ 设置面板")
    style_mode = st.radio("思考风格", ["严谨论证", "发散联想", "辩证权衡"])
    st.divider()
    st.subheader("📝 草稿箱")
    st.session_state.draft = st.text_area("草稿内容", value=st.session_state.draft, height=120)
    if st.button("保存草稿"):
        st.success("✅ 草稿已保存")
    if st.button("读取草稿"):
        st.session_state["user_input"] = st.session_state.draft

tab1, tab2 = st.tabs(["学生思辨对话端", "👩‍🏫 教师抽查面板"])

with tab1:
    st.title("AI思辨训练助手")
    st.markdown("<div style='color:#4472C4'>训练多角度思辨，拒绝直接标准答案</div>", unsafe_allow_html=True)
    st.divider()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("在这里输入你的思辨议题……", key="user_input")

    if user_input:
        hit_keyword = any(k in user_input for k in WARNING_KEYWORDS)
        if hit_keyword:
            html("<script>shakePage()</script>", height=0)
            st.warning("⚠️ 检测到请求代写/直接获取答案类关键词！本工具仅用于思辨训练，禁止直接索要成品答案。")
            st.session_state.show_warn = True

        st.session_state.messages.append({"role":"user", "content":user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        prompt_prefix = {
            "严谨论证": "请严格逻辑推演，分论点、论据、逻辑漏洞分析，不要直接给最终结论：",
            "发散联想": "多角度发散思考，拓展不同立场和可能性，引导自主思考，不要直接给最终结论：",
            "辩证权衡": "同时列出正反双方论据，对比利弊，引导辩证看待，不要直接给最终结论："
        }[style_mode]
        final_prompt = prompt_prefix + "\n" + user_input

        # 真实ARK大模型调用
        url = st.secrets["ark_url"]
        api_key = st.secrets["ark_key"]
        model_id = st.secrets["model_id"]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": final_prompt}
            ]
        }
        resp = requests.post(url, headers=headers, json=payload)
        res_json = resp.json()
        ai_reply = res_json["choices"][0]["message"]["content"]

        st.session_state.messages.append({"role":"assistant", "content":ai_reply})
        with st.chat_message("assistant"):
            st.markdown(ai_reply)

        st.session_state.log_list.append({
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "style": style_mode,
            "user_msg": user_input,
            "ai_msg": ai_reply,
            "risk_triggered": hit_keyword
        })

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("撤回上一条"):
            if len(st.session_state.messages)>=2:
                st.session_state.messages.pop()
                st.session_state.messages.pop()
                if st.session_state.log_list:
                    st.session_state.log_list.pop()
                st.rerun()
    with col2:
        if st.button("清空对话"):
            st.session_state.messages = []
            st.rerun()
    with col3:
        if st.button("导出对话日志CSV"):
            if st.session_state.log_list:
                df_log = pd.DataFrame(st.session_state.log_list)
                st.download_button("下载日志", df_log.to_csv(index=False).encode("utf-8-sig"), file_name="对话日志.csv", mime="text/csv")
            else:
                st.info("暂无对话日志")

with tab2:
    st.title("👩‍🏫 教师抽查面板｜会话记录查看")
    st.markdown("查看全部学生对话记录、风险关键词命中记录")
    st.divider()
    if st.session_state.log_list:
        df = pd.DataFrame(st.session_state.log_list)
        st.dataframe(df, use_container_width=True)
        st.download_button("批量导出全部日志", df.to_csv(index=False).encode("utf-8-sig"), "教师端_全部会话日志.csv")
        risk_count = len(df[df["risk_triggered"]==True])
        st.metric("⚠️ 风险触发次数", risk_count)
    else:
        st.info("暂无对话记录，在学生端发起对话后会同步到这里")
