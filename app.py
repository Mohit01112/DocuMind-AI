import os
import tempfile
import re

import streamlit as st
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_classic.chains import ConversationalRetrievalChain
from langchain_core.prompts import PromptTemplate

# Optional reranker — makes answers 2x more accurate
try:
    from langchain.retrievers import ContextualCompressionRetriever
    from langchain.retrievers.document_compressors import CrossEncoderReranker
    from langchain_community.cross_encoders import HuggingFaceCrossEncoder
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False

# ============================
# CONFIGURATION
# ============================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL_NAME = "llama-3.3-70b-versatile"

# ============================
# PAGE CONFIGURATION
# ============================

st.set_page_config(
    page_title="PDF Chatbot",
    page_icon="📄",
    layout="wide"
)

st.title("📄 PDF Chatbot")
st.caption("Chat with your uploaded PDF using Groq + FAISS")

# ============================
# SESSION STATE
# ============================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None


# ============================
# BACKEND FUNCTIONS
# ============================

def load_llm():
    if not GROQ_API_KEY:
        st.error("GROQ_API_KEY not found. Get one free at https://console.groq.com/keys")
        st.stop()

    return ChatOpenAI(
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
        model=MODEL_NAME,
        temperature=0.2,
        max_retries=2,
    )


def load_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def tag_section(text, page_num):
    """Tag each page so we can filter references later."""
    text = text.strip()
    first_200 = text[:200].lower()

    if page_num == 0:
        return "title_page"
    if "abstract" in first_200 and len(text) < 1500:
        return "abstract"
    # Reference lines start with [1], [2], etc. and are short
    if re.search(r'^\s*\[\d+\]', text) and len(text) < 300:
        return "reference_line"
    if "references" in first_200 and len(text) > 2000:
        return "references"
    if any(t in text[:100] for t in ["Table ", "Figure "]):
        return "table_figure"
    return "body"


def process_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        temp_path = tmp.name

    try:
        loader = PyPDFLoader(temp_path)
        documents = loader.load()

        total_text = sum(len(doc.page_content.strip()) for doc in documents)
        if total_text == 0:
            st.error("❌ This PDF has no extractable text. It is likely a scanned image.")
            st.stop()

        # Filter: drop reference lines, truncate references pages
        filtered_docs = []
        for i, doc in enumerate(documents):
            section = tag_section(doc.page_content, i)
            doc.metadata["section"] = section
            doc.metadata["page"] = i + 1

            if section == "reference_line":
                continue  # Skip entirely
            elif section == "references":
                # Keep only a stub so the model knows it exists but can't use it
                doc.page_content = doc.page_content[:100] + "\n[References section excluded from indexing]"
                filtered_docs.append(doc)
            else:
                filtered_docs.append(doc)

        # Smaller chunks = better retrieval precision
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_documents(filtered_docs)

    finally:
        os.remove(temp_path)

    return chunks


def create_vectorstore(chunks):
    embeddings = load_embeddings()
    return FAISS.from_documents(documents=chunks, embedding=embeddings)


def build_chain(vectorstore):
    llm = load_llm()

    condense_question_prompt = PromptTemplate.from_template(
        """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""
    )

    # Strict prompt: forces context-only answers and ignores references
    qa_prompt = PromptTemplate.from_template(
        """You are a strict PDF assistant. Use ONLY the information from the provided context below to answer the question.

CRITICAL RULES:
- If the context does not contain the answer, say exactly: "I couldn't find that information in the uploaded PDF."
- Do NOT use any outside knowledge or training data.
- IGNORE any content marked as [References section excluded from indexing].
- IGNORE standard bibliographic citations like [1], [2], [3] when answering questions about THIS paper.
- For questions about authors, date, or title, only use content from the title_page or abstract sections.

Context:
{context}

Question: {question}

Answer:"""
    )

    # Retrieve 10 chunks, then rerank to best 5 if available
    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    if RERANKER_AVAILABLE:
        try:
            model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")
            compressor = CrossEncoderReranker(model=model, top_n=5)
            retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=base_retriever
            )
        except Exception:
            retriever = base_retriever
    else:
        retriever = base_retriever

    qa = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        condense_question_prompt=condense_question_prompt,
        combine_docs_chain_kwargs={"prompt": qa_prompt},
        return_source_documents=True,
        verbose=False
    )

    return qa


# ============================
# UPLOAD SECTION
# ============================

st.markdown("### 📂 Upload PDF")

uploaded_file = st.file_uploader(
    "Drag & Drop your PDF here",
    type=["pdf"]
)

if uploaded_file:
    st.success(f"Uploaded: **{uploaded_file.name}**")

    if st.button("🚀 Process Document", use_container_width=True):
        with st.spinner("Reading PDF and creating embeddings..."):
            try:
                chunks = process_pdf(uploaded_file)

                with st.expander("🔍 Preview first 3 chunks"):
                    for i, chunk in enumerate(chunks[:3]):
                        section = chunk.metadata.get("section", "unknown")
                        st.markdown(f"**Chunk {i+1}** | section: `{section}`")
                        st.write(chunk.page_content[:300])
                        st.divider()

                vectorstore = create_vectorstore(chunks)
                st.session_state.qa_chain = build_chain(vectorstore)

                st.success(f"✅ Ready! {len(chunks)} chunks indexed.")

            except Exception as e:
                st.error(f"Error: {e}")


# ============================
# CHAT INTERFACE
# ============================

st.divider()
st.subheader("💬 Chat with your PDF")

if st.session_state.qa_chain is None:
    st.info("👆 Please upload and process a PDF first.")

else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_question = st.chat_input("Ask anything about your PDF...")

    if user_question:
        with st.chat_message("user"):
            st.markdown(user_question)

        st.session_state.messages.append(
            {"role": "user", "content": user_question}
        )

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.qa_chain({
                        "question": user_question,
                        "chat_history": st.session_state.chat_history
                    })

                    answer = result["answer"]

                    # DEBUG: Show exactly which chunks were used
                    with st.expander("🔎 Source chunks (debug)"):
                        docs = result.get("source_documents", [])
                        st.write(f"Retrieved {len(docs)} chunks")
                        for i, doc in enumerate(docs):
                            section = doc.metadata.get("section", "unknown")
                            page = doc.metadata.get("page", "?")
                            preview = doc.page_content[:200].replace("\n", " ")
                            st.markdown(f"**Chunk {i+1}** | section: `{section}` | page: {page}")
                            st.write(f"`{preview}...`")
                            st.divider()

                    st.markdown(answer)

                except Exception as e:
                    answer = f"❌ Error: {e}"
                    st.error(answer)

        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )

        st.session_state.chat_history.append(
            (user_question, answer)
        )