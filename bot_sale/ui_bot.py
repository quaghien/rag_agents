from bot import get_reponse
from agents import trace
import streamlit as st
import asyncio
import os

# Thiết lập API Key
os.environ["OPENAI_API_KEY"] = '###'

st.set_page_config(
    page_title="Chatbot Tư Vấn TechLife",
    page_icon="🤖"
)

# Lưu lịch sử hội thoại trong session_state
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Hàm gọi đến chatbot (async -> sync)
def call_bot(message: str) -> str:
    # Hàm này chỉ đơn giản gọi hàm get_reponse
    # và trả về nội dung 'final_output' (text) từ chatbot
    result = asyncio.run(get_reponse(message))
    return result["final_output"]

st.title("🤖 Chatbot Tư Vấn TechLife")

# Hàm gọi bot
def call_bot(message: str) -> str:
    result = asyncio.run(get_reponse(message))
    return result["final_output"]

# Callback khi bấm nút Gửi
def send_message():
    msg = st.session_state["input_text"].strip()
    if not msg:
        return
    # 1) Lưu và hiển thị user
    st.session_state["messages"].append({"role": "user", "content": msg})
    # 2) Gọi bot và lưu
    bot_resp = call_bot(msg)
    st.session_state["messages"].append({"role": "assistant", "content": bot_resp})
    # 3) Clear input
    st.session_state["input_text"] = ""

# Hiển thị lịch sử hội thoại
for chat in st.session_state.get("messages", []):
    with st.chat_message(chat["role"]):
        st.write(chat["content"])

# Tạo widget và gắn callback
st.text_input("Nhập tin nhắn:", key="input_text")
st.button("Gửi", on_click=send_message, type="primary")