"""
SmartShop AI - RAG Service
Build RAG pipeline with ChromaDB to answer policy questions.
"""

import logging
import asyncio
import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser

from prompts.prompts import RAG_POLICY_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

POLICIES_PATH = Path(__file__).parent.parent / "data" / "policies.txt"
COLLECTION_NAME = "smartshop_policies"


class RAGService:
    """
    RAG (Retrieval-Augmented Generation) Service using ChromaDB.
    Using in-memory ChromaDB for MVP, no dedicated server required.
    """

    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4o-mini"):
        self.llm_provider = llm_provider
        self.model_name = model_name
        self._client: Optional[chromadb.Client] = None
        self._collection = None
        self._is_initialized = False
        logger.info(f"[RAGService] Initialized with provider={llm_provider}, model={model_name}")

    def _get_embedding_function(self):
        """Create embedding function matching the provider.
        
        Note: Groq does not have an embedding API, so it automatically fallbacks to DefaultEmbeddingFunction.
        """
        base_url = os.getenv("OPENAI_BASE_URL")
        is_groq = base_url and "groq" in base_url.lower()
        
        if self.llm_provider == "openai" and not is_groq:
            return embedding_functions.OpenAIEmbeddingFunction(
                model_name="text-embedding-3-small"
            )
        else:
            # Fallback: ChromaDB default embedding (all-MiniLM-L6-v2, runs locally)
            # Used when: Groq, Gemini, or any provider without an embedding API
            return embedding_functions.DefaultEmbeddingFunction()

    def _get_llm(self):
        """Initialize LLM based on provider, supports custom base_url (Groq, Together, etc.)."""
        if self.llm_provider == "openai":
            base_url = os.getenv("OPENAI_BASE_URL")  # None = default OpenAI
            return ChatOpenAI(
                model=self.model_name,
                temperature=0.3,
                streaming=False,
                base_url=base_url,  # Groq: https://api.groq.com/openai/v1
            )
        elif self.llm_provider == "gemini":
            return ChatGoogleGenerativeAI(model=self.model_name, temperature=0.3)
        else:
            raise ValueError(f"Unsupported provider: {self.llm_provider}")

    async def initialize(self) -> None:
        """
        Initialize ChromaDB client, load and index policy documents.
        Only runs once on startup.
        """
        if self._is_initialized:
            return

        logger.info("[RAGService] Starting ChromaDB initialization and document indexing...")
        
        try:
            # Run blocking IO in a thread pool to avoid blocking the event loop
            await asyncio.get_event_loop().run_in_executor(None, self._init_sync)
            self._is_initialized = True
            logger.info("[RAGService] Initialization complete!")
        except Exception as e:
            logger.error(f"[RAGService] Initialization error: {e}", exc_info=True)
            raise

    def _init_sync(self) -> None:
        """Synchronous initialization part (runs in executor)."""
        # Initialize in-memory ChromaDB client
        self._client = chromadb.Client()
        
        embed_fn = self._get_embedding_function()
        
        # Create or get collection
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embed_fn,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Only index if collection is empty
        if self._collection.count() == 0:
            self._index_policies()

    def _index_policies(self) -> None:
        """Read policy file, chunk it, and index into ChromaDB."""
        logger.info(f"[RAGService] Reading policy file: {POLICIES_PATH}")
        
        if not POLICIES_PATH.exists():
            logger.error(f"[RAGService] Policy file not found: {POLICIES_PATH}")
            return

        with open(POLICIES_PATH, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # Chunk the document
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", "。", " "]
        )
        chunks = splitter.split_text(raw_text)
        
        logger.info(f"[RAGService] Split document into {len(chunks)} chunks")

        # Index into ChromaDB
        self._collection.add(
            documents=chunks,
            ids=[f"policy_chunk_{i}" for i in range(len(chunks))],
            metadatas=[{"source": "policies.txt", "chunk_index": i} for i in range(len(chunks))]
        )
        
        logger.info(f"[RAGService] Indexed {len(chunks)} chunks into ChromaDB")

    async def query_policy(self, question: str, n_results: int = 3) -> str:
        """
        Query policy based on user question using RAG.
        
        Args:
            question: Customer policy question.
            n_results: Number of relevant chunks to retrieve.
        
        Returns:
            Answer synthesized by LLM based on context.
        """
        if not self._is_initialized:
            await self.initialize()

        logger.info(f"[RAGService] Query: '{question}'")

        try:
            # Retrieve: find relevant chunks
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._collection.query(
                    query_texts=[question],
                    n_results=min(n_results, self._collection.count())
                )
            )
            
            documents = results.get("documents", [[]])[0]
            
            if not documents:
                logger.warning("[RAGService] No relevant documents found")
                return "Tôi chưa có thông tin về vấn đề này. Vui lòng liên hệ hotline 1800-5555 để được hỗ trợ."

            context = "\n\n---\n\n".join(documents)
            logger.info(f"[RAGService] Found {len(documents)} relevant chunks")

            # Generate: synthesize answer with LLM
            prompt = RAG_POLICY_PROMPT_TEMPLATE.format(context=context, question=question)
            
            llm = self._get_llm()
            chain = llm | StrOutputParser()
            
            response = await chain.ainvoke(prompt)
            logger.info(f"[RAGService] Successfully answered: '{question}'")
            return response

        except Exception as e:
            logger.error(f"[RAGService] Error during query: {e}", exc_info=True)
            return "Xin lỗi, tôi gặp sự cố khi tìm kiếm thông tin. Vui lòng liên hệ hotline 1800-5555 để được hỗ trợ trực tiếp."


# Singleton instance
_rag_service_instance: Optional[RAGService] = None


def get_rag_service(llm_provider: str = "openai", model_name: str = "gpt-4o-mini") -> RAGService:
    """Get singleton instance of RAGService."""
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService(llm_provider=llm_provider, model_name=model_name)
    return _rag_service_instance
