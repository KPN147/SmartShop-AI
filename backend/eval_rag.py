import asyncio
import os
import sys
from pathlib import Path

# Thêm đường dẫn thư mục backend vào sys.path để import được services
sys.path.append(str(Path(__file__).parent))
from dotenv import load_dotenv

from services.rag_service import get_rag_service
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# --- Custom LLM-as-a-Judge Evaluator ---
# Chúng ta sẽ tự viết một Judge Prompt thay vì phụ thuộc vào thư viện bên thứ 3 (tránh lỗi phiên bản)
JUDGE_PROMPT = """Bạn là một giám khảo chuyên đánh giá mô hình AI. 
Nhiệm vụ của bạn là kiểm tra xem "Câu Trả Lời" có BỊA ĐẶT (ảo giác) so với "Chính Sách Thực Tế" hay không.

Chính Sách Thực Tế (Context lấy từ cơ sở dữ liệu):
{context}

Câu Trả Lời của AI:
{answer}

Luật chấm điểm:
- Chấm "1": Nếu AI nói đúng chính sách dựa trên tài liệu, hoặc AI thật thà từ chối trả lời vì không có thông tin.
- Chấm "0": Nếu AI BỊA RA (Hallucinate) các thông tin, điều khoản, hoặc lời hứa không hề có trong Chính Sách Thực Tế.

CHỈ IN RA DUY NHẤT MỘT CON SỐ (0 hoặc 1). KHÔNG IN THÊM BẤT KỲ CHỮ NÀO KHÁC.
"""

async def run_evaluation():
    print("[System] Đang khởi tạo RAG Service và ChromaDB...")
    
    # Đọc cấu hình từ .env
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    model_name = os.getenv("OPENAI_MODEL", "llama-3.3-70b-versatile")
    
    rag_service = get_rag_service(llm_provider=llm_provider, model_name=model_name)
    await rag_service.initialize()
    
    # Sử dụng chính model Groq làm giám khảo
    judge_llm = rag_service._get_llm()
    judge_chain = PromptTemplate.from_template(JUDGE_PROMPT) | judge_llm | StrOutputParser()

    test_questions = [
        "Tôi có thể trả hàng sau 10 ngày mua không?",
        "SmartShop có chính sách hoàn tiền qua thẻ tín dụng như thế nào?",
        "Nếu sản phẩm bị lỗi do vận chuyển thì SmartShop xử lý sao?",
        "Chính sách bảo hành đối với các mặt hàng điện tử là bao lâu?",
        "Mua hàng trực tiếp tại cửa hàng có được áp dụng mã giảm giá online không?"
    ]

    base_llm_hallucinations = 0
    rag_hallucinations = 0

    print("\n" + "="*60)
    print("BẮT ĐẦU ĐÁNH GIÁ (Custom LLM-as-a-Judge Pipeline)")
    print("="*60)

    for i, q in enumerate(test_questions):
        print(f"\n--- Câu hỏi {i+1}: {q} ---")
        
        # 1. Lấy context thực tế từ DB làm chuẩn (Ground Truth)
        results = rag_service._collection.query(
            query_texts=[q],
            n_results=min(3, rag_service._collection.count())
        )
        documents = results.get("documents", [[]])[0]
        true_context = "\n".join(documents) if documents else "Không có quy định."

        # 2. Sinh câu trả lời bằng Base LLM (Không có RAG)
        prompt_base = f"Bạn là nhân viên hỗ trợ khách hàng. Hãy trả lời câu hỏi: {q}"
        # .invoke() trả về AIMessage object, lấy .content
        base_ans = judge_llm.invoke(prompt_base).content
        
        # 3. Sinh câu trả lời bằng RAG Pipeline
        rag_ans = await rag_service.query_policy(q)

        # 4. Giám khảo chấm điểm Base LLM
        score_base = judge_chain.invoke({"context": true_context, "answer": base_ans}).strip()
        if score_base == "0":
            base_llm_hallucinations += 1
            
        # 5. Giám khảo chấm điểm RAG
        score_rag = judge_chain.invoke({"context": true_context, "answer": rag_ans}).strip()
        if score_rag == "0":
            rag_hallucinations += 1

        print(f"[Base LLM]  Trả lời: {base_ans[:100]}...")
        print(f"            -> Điểm Groundedness: {score_base} (0=Bịa đặt, 1=Tốt)")
        
        print(f"[RAG Model] Trả lời: {rag_ans[:100]}...")
        print(f"            -> Điểm Groundedness: {score_rag} (0=Bịa đặt, 1=Tốt)")

    # Tính toán kết quả cho CV
    total = len(test_questions)
    base_error_rate = (base_llm_hallucinations / total) * 100
    rag_error_rate = (rag_hallucinations / total) * 100
    
    if base_error_rate > 0:
        reduction = ((base_error_rate - rag_error_rate) / base_error_rate) * 100
    else:
        reduction = 0

    print("\n" + "="*60)
    print("KẾT QUẢ ĐÁNH GIÁ (GHI VÀO CV)")
    print("="*60)
    print(f"Mô hình sử dụng: {llm_provider.upper()} - {model_name}")
    print(f"- Tỷ lệ ảo giác (Bịa đặt) của mô hình gốc: {base_error_rate:.0f}% ({base_llm_hallucinations}/{total} câu)")
    print(f"- Tỷ lệ ảo giác sau khi áp dụng RAG:       {rag_error_rate:.0f}% ({rag_hallucinations}/{total} câu)")
    print(f"\n=> KẾT LUẬN: Hệ thống RAG giúp giảm {reduction:.1f}% tỷ lệ ảo giác so với mô hình gốc.")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
