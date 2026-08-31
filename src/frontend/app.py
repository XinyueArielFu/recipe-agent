import streamlit as st
import requests

APP_PASSWORD = "Tinawangchina"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pwd = st.text_input("请输入密码 / Enter password", type="password")
    if pwd == APP_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()

st.title("Tina's Recipe Agent")

backend_choice = st.selectbox("选择模型 / Choose Model", ["claude", "llama"])
question = st.text_input("想做什么菜 / What dish you want to make?")

if st.button("提问 / Ask"):
    with st.spinner("Thinking..."):
        res = requests.post(
            "http://localhost:8000/query",
            json={"question": question, "backend": backend_choice}
        )
        st.write(res.json()["answer"])

st.divider()
st.subheader("所有菜谱 / All Recipes")
if st.button("加载菜谱列表"):
    res = requests.get("http://localhost:8000/recipes")
    for recipe in res.json():
        st.write(f"**{recipe['name_zh']}** ({recipe['name_en']}) - {recipe['difficulty']}")