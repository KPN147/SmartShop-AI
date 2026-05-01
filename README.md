# SmartShop AI 🛒🤖

<div align="center">

![SmartShop AI Banner](https://img.shields.io/badge/SmartShop_AI-Multi--Agent_Chatbot-7C3AED?style=for-the-badge&logo=robot&logoColor=white)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.11x-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=flat-square&logo=chainlink)](https://langchain.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6B35?style=flat-square)](https://trychroma.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python)](https://python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript)](https://typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

**A Multi-Agent E-commerce AI Chatbot System with RAG Architecture**  
Automated sales consulting, order tracking, and policy answering in real-time.

[🚀 Live Demo](https://smart-shop-ai-orcin.vercel.app/) · [📖 API Docs](#api-docs) · [🐳 Docker Setup](#docker-setup)

</div>

---

## 📋 Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Key Features](#key-features)
- [Quick Start & Installation](#quick-start--installation)
- [Docker Setup](#docker-setup)
- [Configuration](#configuration)
- [Project Structure](#project-structure)

---

<a id="overview"></a>
## 🎯 Overview

**SmartShop AI** is a full-stack web application leveraging Generative AI to automate the sales consulting and customer care process for E-commerce platforms.

What makes this project different from a typical chatbot:

- ✅ **No Hallucination:** AI only answers based on actual product data and policies through the RAG architecture.
- ✅ **Multi-Agent Routing:** The Manager Agent automatically analyzes intent and routes to the appropriate Sales Agent or Support Agent.
- ✅ **Sentiment-Aware:** Analyzes user sentiment to adjust the AI's response tone (more empathetic when customers complain).
- ✅ **Multi-Provider LLM:** Flexibly switch between OpenAI, Google Gemini, and Groq (Free Open-Source) just via the `.env` file.
- ✅ **Streaming UI:** Text appears word-by-word like ChatGPT via Server-Sent Events (SSE).

---

<a id="demo-and-screenshots"></a>
## 📸 Demo & Screenshots

> **[🔥 TRẢI NGHIỆM LIVE DEMO TẠI ĐÂY](https://smart-shop-ai-henna.vercel.app)**

*(💡 Lời khuyên: Hãy chụp 1-2 bức ảnh giao diện web của bạn và chèn vào đây để nhà tuyển dụng xem ngay lập tức mà không cần bấm link. Xóa dòng này đi sau khi bạn chèn ảnh)*
<p align="center">
  <img src="https://via.placeholder.com/800x450?text=Insert+Your+Demo+Screenshot+Here" width="800" alt="SmartShop AI Demo">
</p>

---

<a id="system-architecture"></a>
## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER (Browser)                           │
│              Next.js 16 + TypeScript + Tailwind             │
│         Chat UI · Streaming SSE · Markdown Render           │
└───────────────────────────┬─────────────────────────────────┘
                            │  REST API / SSE
┌───────────────────────────▼─────────────────────────────────┐
│                FastAPI Backend (Python)                      │
│                                                             │
│   ┌──────────────────────────────────────────────────────┐  │
│   │              Multi-Agent Orchestrator                │  │
│   │                                                      │  │
│   │  [User Query] → [Manager Agent: Intent Routing]      │  │
│   │        ┌─────────────┴────────────────┐             │  │
│   │        ▼                              ▼             │  │
│   │  [Sales Agent]              [Support Agent]         │  │
│   │  • Product Search           • Order Lookup          │  │
│   │  • Price Comparison         • RAG Policy Query      │  │
│   │  • Recommendations          • Complaint Handler     │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                             │
│   ┌────────────────┐   ┌─────────────────────────────────┐  │
│   │ Sentiment      │   │ RAG Pipeline                    │  │
│   │ Analysis       │   │ policies.txt → Chunks →         │  │
│   │ (Keyword-based)│   │ Embeddings → ChromaDB →         │  │
│   │                │   │ Cosine Search → LLM Context     │  │
│   └────────────────┘   └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴────────────┐
              ▼                          ▼
    ┌──────────────────┐     ┌──────────────────────┐
    │    LLM APIs      │     │     Data Storage      │
    │ • OpenAI GPT-4o  │     │ • ChromaDB (Vector)   │
    │ • Google Gemini  │     │ • products.json       │
    │ • Groq (Free)    │     │ • orders.json         │
    └──────────────────┘     │ • policies.txt        │
                             └──────────────────────┘
```

---

<a id="tech-stack"></a>
## 🛠️ Tech Stack

### Backend
| Technology | Version | Role |
|---|---|---|
| **FastAPI** | 0.11x | Web Framework, REST API & SSE Streaming |
| **Python** | 3.10+ | Primary Language |
| **LangChain** | 0.3 | Multi-Agent Orchestration, RAG Pipeline |
| **ChromaDB** | Latest | In-memory Vector Database |
| **Pydantic** | v2 | Data Validation & Serialization |
| **Uvicorn** | Latest | ASGI Web Server |

### Frontend
| Technology | Version | Role |
|---|---|---|
| **Next.js** | 16 (App Router) | React Framework |
| **TypeScript** | 5 | Primary Language |
| **Tailwind CSS** | 4 | Styling |
| **React** | 19 | UI Library |

### AI / LLM Providers
| Provider | Model | Notes |
|---|---|---|
| **OpenAI** | gpt-4o-mini, gpt-4o | Configurable |
| **Google Gemini** | gemini-2.5-flash | Configurable |
| **Groq** | llama-3.3-70b-versatile, llama-3.1-8b-instant | Free, high-speed |

---

<a id="key-features"></a>
## ✨ Key Features

### 🛍️ Sales Agent
- Product consultation based on smart keyword search (Keyword Scoring).
- Product comparison, suggestions matching needs and budget.
- Displays product images right in the chat frame.

### 🎧 Support Agent
- Order status lookup by order code (`ORD-XXXX-XXX`) or phone number.
- Answers warranty, return, and shipping policies based on actual documents (RAG).
- Never fabricates policy information.

### 🧠 AI Infrastructure
- **Streaming Response (SSE):** Text appears gradually like ChatGPT, no need to wait for the entire response.
- **Sentiment Analysis:** Detects customer sentiment and adjusts AI tone.
- **LangSmith Tracing:** Monitors the entire Agent flow, token costs, step latency.
- **Multi-Provider Fallback:** Easily switch LLM Provider via `.env` file without changing code.

---

<a id="quick-start--installation"></a>
## 🚀 Quick Start & Installation

### Requirements
- Python 3.10+
- Node.js 18+
- API Key from OpenAI, Groq, or Google Gemini

### 1. Clone the project
```bash
git clone https://github.com/your-username/smartshop-ai.git
cd smartshop-ai
```

### 2. Run Backend
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # macOS/Linux

# Install libraries
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# → Open .env and fill in your API Key

# Start server
uvicorn main:app --reload
# Backend will run at: http://localhost:8000
# Swagger API Docs: http://localhost:8000/docs
```

### 3. Run Frontend
```bash
# Open a new terminal
cd frontend
npm install
npm run dev
# Frontend will run at: http://localhost:3000
```

---

<a id="docker-setup"></a>
## 🐳 Docker Setup

Run the entire project with just **1 command**:

```bash
# At the root directory of the project
docker-compose up --build
```

Then access:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs

> **Note:** Remember to create `backend/.env` from `backend/.env.example` and fill in the API Key before running Docker.

---

<a id="configuration"></a>
## ⚙️ Configuration

Copy `backend/.env.example` to `backend/.env` and fill in the values:

```env
# Choose LLM Provider
LLM_PROVIDER=openai

# --- Using OpenAI ---
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# --- Or using Groq (Free) ---
# OPENAI_API_KEY=gsk_...
# OPENAI_BASE_URL=https://api.groq.com/openai/v1
# OPENAI_MODEL=llama-3.3-70b-versatile

# --- LangSmith (AI Monitoring) ---
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT=SmartShop-AI
```

---

<a id="project-structure"></a>
## 📁 Project Structure

```
smartshop-ai/
├── backend/
│   ├── data/
│   │   ├── products.json       # Product DB (10 products, with images)
│   │   ├── orders.json         # Order DB (15 orders, multi-status)
│   │   └── policies.txt        # Policy document (RAG source)
│   ├── models/
│   │   └── schemas.py          # Pydantic schemas (request/response)
│   ├── prompts/
│   │   └── prompts.py          # System prompts for Agents
│   ├── routers/
│   │   └── chat.py             # API endpoints (/chat, /chat/stream)
│   ├── services/
│   │   ├── agent_service.py    # Multi-Agent Orchestrator
│   │   ├── rag_service.py      # RAG Pipeline with ChromaDB
│   │   └── sentiment_service.py # Sentiment Analysis
│   ├── tools/
│   │   ├── search_product.py   # Tool: Search for products
│   │   └── check_order.py      # Tool: Look up orders
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   └── page.tsx            # Main chat page
│   ├── components/
│   │   ├── ChatWindow.tsx      # Chat message display frame
│   │   ├── MessageBubble.tsx   # Message bubble (Markdown render)
│   │   └── AgentStatus.tsx     # Agent status bar
│   ├── lib/
│   │   └── api.ts              # API client functions
│   └── .env.local.example
├── docker-compose.yml          # Docker Compose (runs entire project)
├── overview.md                 # Detailed Tech Stack overview
└── README.md
```

---

<a id="api-docs"></a>
## 📊 API Docs

When the backend is running, access:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Main Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/chat` | Send message, receive full response |
| `GET` | `/api/v1/chat/stream` | Chat with Streaming (SSE) |
| `GET` | `/api/v1/health` | Check system status |

---

## 👨‍💻 Author

The project is built with an **Applied AI** orientation, focusing on efficiency, cost optimization, and scalability to Production environments.

---

*Built with ❤️ using FastAPI, LangChain, Next.js and ChromaDB*
