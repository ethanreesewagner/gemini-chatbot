import google.generativeai as genai
import streamlit as st
import os
import json
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
st.set_page_config(page_title="Gemini Chat App", page_icon="💬")
st.title("💬 Gemini Chat App")
st.markdown("Chat with Google's Gemini 3.8 Flash! Create and manage multiple conversations.")

if "chats" not in st.session_state:
    st.session_state["chats"] = {"default": {"name": "Main Chat", "history": [{"role": "system", "content": "You are a helpful assistant."}]}}
    st.session_state["current_chat"] = "default"

def rerun():
    st.rerun()

with st.sidebar:
    st.header("💾 Saved Chats")
    chat_ids = list(st.session_state["chats"].keys())
    chat_names = [st.session_state["chats"][cid]["name"] for cid in chat_ids]
    chat_selection = st.radio(
        "Select a chat",
        chat_ids,
        format_func=lambda x: st.session_state["chats"][x]["name"],
        index=chat_ids.index(st.session_state["current_chat"]) if st.session_state.get("current_chat") in chat_ids else 0
    )
    if st.button("New Chat"):
        import uuid
        new_id = str(uuid.uuid4())[:8]
        new_name = st.text_input("New chat name:", key="new_chat_name")
        if new_name:
            st.session_state["chats"][new_id] = {"name": new_name, "history": [{"role": "system", "content": "You are a helpful assistant."}]}
            st.session_state["current_chat"] = new_id
            rerun()
    if chat_selection != "default":
        if st.button("Delete Selected Chat"):
            del st.session_state["chats"][chat_selection]
            st.session_state["current_chat"] = "default"
            rerun()
    st.session_state["current_chat"] = chat_selection

current_chat_id = st.session_state["current_chat"]
current_chat = st.session_state["chats"][current_chat_id]
st.subheader(f"Chat: {current_chat['name']}")
history = current_chat["history"]

for msg in history:
    if msg["role"] == "user":
        st.markdown(f"**🧑‍💻 You:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"**🤖 Gemini:** {msg['content']}")
    elif msg["role"] == "system":
        st.markdown(f"<span style='color: #888;'>*{msg['content']}*</span>", unsafe_allow_html=True)

with st.form("chat_input_form", clear_on_submit=True):
    user_input = st.text_input("Type your message:")
    submitted = st.form_submit_button("Send")

model = genai.GenerativeModel("gemini-3.8-flash")

if submitted and user_input:
    history.append({"role": "user", "content": user_input})
    model_history = [m for m in history if m["role"] != "system"]
    try:
        response = model.generate_content([m["content"] for m in model_history])
        resp_content = response.text if hasattr(response, "text") else str(response)
    except Exception as e:
        resp_content = f"Error: {e}"
    history.append({"role": "assistant", "content": resp_content})
    st.session_state["chats"][current_chat_id]["history"] = history
    rerun()

with st.sidebar:
    st.write("---")
    st.write(f"Rename selected chat ('{current_chat['name']}'):")
    newname = st.text_input("Rename chat", value=current_chat["name"], key="rename_chat")
    if newname and newname != current_chat["name"]:
        st.session_state["chats"][current_chat_id]["name"] = newname
    st.write("---")
    if st.button("Save All Chats to File"):
        with open("saved_chats.json", "w") as f:
            json.dump(st.session_state["chats"], f, indent=2)
        st.success("Chats saved to 'saved_chats.json'.")
    if st.button("Load Chats from File"):
        try:
            with open("saved_chats.json", "r") as f:
                data = json.load(f)
                st.session_state["chats"] = data
                st.session_state["current_chat"] = list(data.keys())[0]
                rerun()
        except Exception as e:
            st.error(f"Failed to load: {e}")