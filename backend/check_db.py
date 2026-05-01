import asyncio
import os
import sys
from pathlib import Path

# Thêm đường dẫn thư mục backend vào sys.path để import được services
sys.path.append(str(Path(__file__).parent))
from dotenv import load_dotenv

from services.rag_service import get_rag_service

load_dotenv()

async def check_chromadb():
    print("[System] Đang khởi tạo RAG Service và Load Database...")
    
    # Lấy cấu hình LLM từ .env (Tự động nhận diện Groq thông qua cấu hình OpenAI interface)
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    model_name = os.getenv("OPENAI_MODEL", "llama-3.3-70b-versatile")
    
    rag_service = get_rag_service(llm_provider=llm_provider, model_name=model_name)
    await rag_service.initialize()
    
    # Truy cập trực tiếp vào collection của ChromaDB
    collection = rag_service._collection
    count = collection.count()
    
    print("=" * 60)
    print(f"✅ KẾT QUẢ: Đã nhúng (embed) thành công {count} đoạn văn bản (chunks) vào ChromaDB!")
    print("=" * 60)
    
    # Lấy toàn bộ dữ liệu ra xem
    data = collection.get()
    
    print("\n--- XEM TRƯỚC 3 ĐOẠN ĐẦU TIÊN (Đầu file policies.txt) ---")
    for i in range(min(3, count)):
        print(f"\n[Chunk {i+1}] ID: {data['ids'][i]}")
        print(f"Nội dung: {data['documents'][i][:200]}...")
        print(f"Metadata: {data['metadatas'][i]}")

    print("\n--- XEM TRƯỚC 2 ĐOẠN CUỐI CÙNG (Cuối file policies.txt) ---")
    if count >= 2:
        for i in range(count-2, count):
            print(f"\n[Chunk {i+1}] ID: {data['ids'][i]}")
            print(f"Nội dung: {data['documents'][i][:200]}...")
            print(f"Metadata: {data['metadatas'][i]}")

if __name__ == "__main__":
    asyncio.run(check_chromadb())
