import asyncio
import os
import sys
from pathlib import Path

# Thêm đường dẫn thư mục backend vào sys.path để import được services
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv

# TruLens imports
from trulens_eval import Tru, Feedback, Select, TruCustomApp
from trulens_eval.feedback.provider.openai import OpenAI
from trulens_eval.tru_custom_app import instrument

from services.rag_service import get_rag_service
from prompts.prompts import RAG_POLICY_PROMPT_TEMPLATE
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# Khởi tạo TruLens
tru = Tru()
tru.reset_database()  # Xóa data test cũ (nếu có)

# 1. Chuẩn bị RAG Service từ project SmartShop-AI
print("[System] Đang khởi tạo RAG Service và ChromaDB...")

# Lấy cấu hình Groq từ .env (Project hiện đang dùng Groq thông qua OpenAI interface)
llm_provider = os.getenv("LLM_PROVIDER", "openai")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
model_name = os.getenv("OPENAI_MODEL", "llama-3.3-70b-versatile")
api_key = os.getenv("OPENAI_API_KEY")

print(f"[System] Thông tin cấu hình LLM (Groq):")
print(f"  - Provider : {llm_provider}")
print(f"  - Base URL : {base_url}")
print(f"  - Model    : {model_name}")
print(f"  - API Key  : {'*' * 15}{api_key[-4:] if api_key else 'None'}")

# Khởi tạo dịch vụ RAG của bạn
rag_service = get_rag_service(llm_provider=llm_provider, model_name=model_name)
loop = asyncio.get_event_loop()
loop.run_until_complete(rag_service.initialize())
print("[System] Khởi tạo ChromaDB xong!")

# 2. Khởi tạo Giám khảo (LLM Judge) bằng Groq
# Đảm bảo biến môi trường chính xác để TruLens sử dụng Groq làm giám khảo
if api_key:
    os.environ["OPENAI_API_KEY"] = api_key
if base_url:
    os.environ["OPENAI_BASE_URL"] = base_url

provider = OpenAI(model_engine=model_name)

# Đo Groundedness: So sánh giữa [Đầu ra của hàm retrieve_context] và [Câu trả lời cuối]
f_groundedness = (
    Feedback(provider.groundedness_measure_with_cot_reasons, name="Groundedness")
    .on(Select.RecordCalls.retrieve_context.rets)  # Context
    .on_output()                                   # Answer
)

# Thêm Answer Relevance: Câu trả lời có đúng trọng tâm câu hỏi không?
f_answer_relevance = (
    Feedback(provider.relevance_with_cot_reasons, name="Answer Relevance")
    .on_input()                                    # Question
    .on_output()                                   # Answer
)

# 3. Tạo Wrapper cho hệ thống RAG để TruLens có thể theo dõi (track)
class SmartShopRAGEvalApp:
    def __init__(self, rag_service):
        self.rag = rag_service

    @instrument
    def retrieve_context(self, question: str) -> str:
        """Hàm lấy tài liệu từ ChromaDB (đã được theo dõi bởi TruLens)"""
        results = self.rag._collection.query(
            query_texts=[question],
            n_results=min(3, self.rag._collection.count())
        )
        documents = results.get("documents", [[]])[0]
        if not documents:
            return "Không có thông tin."
        return "\n\n---\n\n".join(documents)

    @instrument
    def generate_answer(self, question: str, context: str) -> str:
        """Hàm sinh câu trả lời bằng LLM (đã được theo dõi bởi TruLens)"""
        prompt = RAG_POLICY_PROMPT_TEMPLATE.format(context=context, question=question)
        llm = self.rag._get_llm()
        chain = llm | StrOutputParser()
        # Dùng invoke đồng bộ (sync) cho dễ test
        return chain.invoke(prompt)

    @instrument
    def query_with_rag(self, question: str) -> str:
        """Hàm RAG hoàn chỉnh"""
        context = self.retrieve_context(question)
        return self.generate_answer(question, context)

# 4. Tạo Wrapper cho Base LLM (Không có RAG) để so sánh
class BaseLLMEvalApp:
    def __init__(self, rag_service):
        self.rag = rag_service

    @instrument
    def query_no_rag(self, question: str) -> str:
        """Chỉ gọi LLM thuần túy, không có Context"""
        prompt = f"Bạn là trợ lý AI của SmartShop. Hãy trả lời câu hỏi sau của khách hàng: {question}"
        llm = self.rag._get_llm()
        chain = llm | StrOutputParser()
        return chain.invoke(prompt)

# Bọc các App lại với TruCustomApp để đo lường
rag_eval_app = SmartShopRAGEvalApp(rag_service)
tru_rag_app = TruCustomApp(
    rag_eval_app,
    app_id="1. SmartShop RAG Pipeline",
    feedbacks=[f_groundedness, f_answer_relevance]
)

base_llm_app = BaseLLMEvalApp(rag_service)
# Base LLM không có Context nên không đo được Groundedness với tài liệu truy xuất, 
# ta chỉ đo Answer Relevance hoặc tự kiểm tra lỗi (Hallucination) sau
tru_base_llm_app = TruCustomApp(
    base_llm_app,
    app_id="0. Base LLM (No RAG)",
    feedbacks=[f_answer_relevance]
)

# 5. Chạy tập dữ liệu đánh giá
test_questions = [
    "Tôi có thể trả hàng sau 10 ngày mua không?",
    "SmartShop có chính sách hoàn tiền qua thẻ tín dụng như thế nào?",
    "Nếu sản phẩm bị lỗi do vận chuyển thì SmartShop xử lý sao?",
    "Chính sách bảo hành đối với các mặt hàng điện tử là bao lâu?",
    "Mua hàng trực tiếp tại cửa hàng có được áp dụng mã giảm giá online không?"
]

print("\n--- BẮT ĐẦU ĐÁNH GIÁ BASE LLM (KHÔNG RAG) ---")
with tru_base_llm_app as recording:
    for q in test_questions:
        print(f"Hỏi: {q}")
        ans = base_llm_app.query_no_rag(q)
        print(f"Đáp: {ans}\n")

print("\n--- BẮT ĐẦU ĐÁNH GIÁ RAG PIPELINE ---")
with tru_rag_app as recording:
    for q in test_questions:
        print(f"Hỏi: {q}")
        ans = rag_eval_app.query_with_rag(q)
        print(f"Đáp: {ans}\n")

# 6. Khởi chạy Dashboard để xem kết quả
print("\n[System] Chạy xong! Mở Dashboard để xem điểm Groundedness...")
tru.run_dashboard(port=8501)
