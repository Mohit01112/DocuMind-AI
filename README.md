# DocuMind-AI 🤖📄

**DocuMind-AI** is an intelligent document assistant that lets you chat with your PDFs using **Retrieval-Augmented Generation (RAG)**. Upload any research paper, report, or document and ask questions in natural language — get accurate, context-grounded answers instantly.

live:https://9hgk7rbmfkivwapevd3agt.streamlit.app/

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ Features

- 📤 **PDF Upload** — Drag & drop any text-based PDF
- 🔍 **Smart Retrieval** — Hybrid BM25 + Vector search for precise chunk matching
- 🧠 **Conversational Memory** — Follow-up questions work naturally
- 🛡️ **Reference Filtering** — Automatically excludes bibliography sections to prevent contamination
- 📊 **Table Extraction** — Handles research tables, scores, and numbers
- 🔎 **Debug Mode** — See exactly which chunks were retrieved for full transparency
- ⚡ **Fast & Free** — Powered by Groq's free tier (1M tokens/day)

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/DocuMind-AI.git
cd DocuMind-AI
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up API Key

Get a **free** Groq API key from [console.groq.com/keys](https://console.groq.com/keys)

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_key_here
```

### 4. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 📖 How to Use

1. **Upload a PDF** — Drag and drop or click to select a PDF file
2. **Process** — Click "🚀 Process Document" to create embeddings
3. **Chat** — Ask questions about the document in the chat interface

### Example Questions

- *"Who are the authors of this paper?"*
- *"What is the main contribution?"*
- *"What accuracy was reported on Natural Questions?"*
- *"How does RAG-Token differ from RAG-Sequence?"*

---

## 🧪 Diagnostic Test

Run these 6 questions to verify your bot is working correctly:

| # | Question | Expected Answer |
|---|----------|-----------------|
| 1 | Who are the authors of this paper? | Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, Douwe Kiela |
| 2 | What accuracy did RAG-Sequence achieve on Natural Questions? | 44.5 Exact Match |
| 3 | Who wrote "The probabilistic relevance framework: BM25 and beyond"? | Should refuse or identify as cited work, not this paper's authors |
| 4 | What is the weather today? | "I couldn't find that information in the uploaded PDF." |
| 5 | What did we just discuss? | Should summarize the previous conversation |
| 6 | What is RAG-Token and how is it different from RAG-Sequence? | RAG-Token uses different documents per token; RAG-Sequence uses one document for the whole sequence |

**Score:** 6/6 = Production Ready 🎉

---

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│   PDF Upload │────▶│  Text Extraction │────▶│ Chunking &   │
│   (Streamlit)│     │  (PyPDFLoader)   │     │ Filtering    │
└─────────────┘     └─────────────────┘     └──────┬───────┘
                                                    │
                           ┌────────────────────────┘
                           ▼
                    ┌─────────────┐
                    │  FAISS      │
                    │  Vector DB  │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐      ┌─────────────┐     ┌──────────┐
   │  BM25   │      │  Vector     │     │ Reranker │
   │ Keyword │  +   │  Similarity │ ──▶ │ (Top 5)  │
   │ Search  │      │  Search     │     │          │
   └─────────┘      └─────────────┘     └────┬─────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │  Groq LLM   │
                                       │ (Llama 3.3) │
                                       └──────┬──────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │   Answer    │
                                       │  + Sources  │
                                       └─────────────┘
```

### Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **PDF Loader** | PyPDFLoader | Extract text from PDFs |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | Convert text to vectors |
| **Vector Store** | FAISS | Fast similarity search |
| **Hybrid Retriever** | BM25 + FAISS | Keyword + semantic search |
| **Reranker** | BAAI/bge-reranker-base | Reorder chunks by relevance |
| **LLM** | Groq (Llama 3.3 70B) | Generate answers |
| **Framework** | LangChain | RAG pipeline orchestration |
| **UI** | Streamlit | Web interface |

---

## 📁 Project Structure

```
DocuMind-AI/
│
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env                   # API keys (not tracked by git)
├── .env.example           # Example environment file
├── README.md              # This file
├── LICENSE                # MIT License
│
└── assets/
    └── demo.png           # Screenshot placeholder
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | Your Groq API key (free at console.groq.com) |

### Model Settings

Edit `app.py` to change the LLM:

```python
# Current model (fast, reliable)
MODEL_NAME = "llama-3.3-70b-versatile"

# Alternatives on Groq free tier:
# MODEL_NAME = "llama-3.1-8b-instant"      # Faster, lighter
# MODEL_NAME = "mixtral-8x7b-32768"        # Good for long context
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No API key found" | Check your `.env` file has `GROQ_API_KEY=gsk_...` |
| "ResourceExhausted" | You're on OpenRouter — switch to Groq (free tier is more stable) |
| "This PDF has no extractable text" | Your PDF is scanned/image-based. Use a text-based PDF or run OCR first |
| Wrong authors listed | The bibliography is leaking. The filter should catch this — check the debug panel |
| "I couldn't find that information" | Try rephrasing your question. The retriever uses exact + semantic matching |
| Chat history not working | Meta-questions ("what did we discuss") are answered from session memory |

---

## 🛡️ Limitations

- **Text-based PDFs only** — Scanned/image PDFs require OCR preprocessing
- **English optimized** — Other languages may work but are not tested
- **Free tier limits** — Groq free: 1M tokens/day, 20 req/min
- **No persistent storage** — Vector index is rebuilt on each upload (not saved to disk)

---

## 🔮 Future Improvements

- [ ] Persistent vector store (save/load FAISS index)
- [ ] Multi-document chat (upload multiple PDFs)
- [ ] OCR support for scanned PDFs
- [ ] Table extraction with structured parsing
- [ ] Citation highlighting in the original PDF
- [ ] Export chat history to PDF/JSON

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🙏 Acknowledgments

- [LangChain](https://langchain.com) for the RAG framework
- [Groq](https://groq.com) for fast, free LLM inference
- [Streamlit](https://streamlit.io) for the beautiful UI
- [HuggingFace](https://huggingface.co) for embeddings and rerankers

---

**Made by Mohit**

> *"Turning static documents into dynamic conversations."*
