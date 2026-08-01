import streamlit as st
import requests

st.set_page_config(page_title="PDF Chatbot", layout="centered")
st.title("📄 Chat with your PDF (OpenRouter)")

BACKEND_URL = "http://127.0.0.1:8000"

# Initialize conversation tracking session states
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_history" not in st.session_state:
    st.session_state.api_history = []
if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False

# Sidebar for document uploading management
with st.sidebar:
    st.header("Document Setup")
    uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])
    if uploaded_file and not st.session_state.pdf_uploaded:
        with st.spinner("Processing PDF on backend..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            response = requests.post(f"{BACKEND_URL}/upload", files=files)
            if response.status_code == 200:
                st.success("PDF processed successfully!")
                st.session_state.pdf_uploaded = True
            else:
                st.error("Failed to process document on backend server.")

# Render operational interface instructions or active message boards
if not st.session_state.pdf_uploaded:
    st.info("Please upload a PDF document in the sidebar to begin chatting.")
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_query := st.chat_input("Ask a question about your document..."):
        with st.chat_message("user"):
            st.markdown(user_query)
        st.session_state.messages.append({"role": "user", "content": user_query})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                payload = {"question": user_query, "chat_history": st.session_state.api_history}
                response = requests.post(f"{BACKEND_URL}/chat", json=payload)
                if response.status_code == 200:
                    answer = response.json()["answer"]
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.session_state.api_history.append((user_query, answer))
                else:
                    st.error("Error communicating with backend.")
