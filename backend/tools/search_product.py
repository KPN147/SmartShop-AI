"""
SmartShop AI - Tool: Search Product
Tìm kiếm sản phẩm từ mock database theo từ khóa.
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).parent.parent / "data" / "products.json"


def _load_products() -> List[Dict[str, Any]]:
    """Load products từ JSON file."""
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Không tìm thấy file: {DATA_PATH}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Lỗi parse JSON products: {e}")
        return []


def search_product(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """
    Tìm kiếm sản phẩm theo từ khóa.
    
    Args:
        query: Từ khóa tìm kiếm (tên, category, brand, tags).
        max_results: Số lượng kết quả tối đa trả về.
    
    Returns:
        Danh sách sản phẩm phù hợp với thông tin đầy đủ.
    """
    logger.info(f"[Tool:search_product] Query='{query}', max_results={max_results}")
    
    products = _load_products()
    if not products:
        return []

    query_lower = query.lower()
    query_words = re.findall(r'\w+', query_lower)
    
    results_with_score: List[tuple[int, Dict[str, Any]]] = []
    
    for product in products:
        score = 0
        searchable_text = " ".join([
            product.get("name", ""),
            product.get("category", ""),
            product.get("brand", ""),
            product.get("description", ""),
            " ".join(product.get("tags", []))
        ]).lower()
        
        # Score tăng theo số từ khóa khớp
        for word in query_words:
            if len(word) > 2 and word in searchable_text:
                score += 1
        
        # Bonus nếu khớp tên chính xác
        if query_lower in product.get("name", "").lower():
            score += 5
        
        # Bonus nếu khớp brand chính xác
        if query_lower in product.get("brand", "").lower():
            score += 3
            
        # Bonus nếu khớp category
        if query_lower in product.get("category", "").lower():
            score += 2

        if score > 0:
            results_with_score.append((score, product))
    
    # Sắp xếp theo score giảm dần
    results_with_score.sort(key=lambda x: x[0], reverse=True)
    
    top_results = [p for _, p in results_with_score[:max_results]]
    
    logger.info(f"[Tool:search_product] Tìm thấy {len(top_results)} sản phẩm cho query='{query}'")
    return top_results


def format_product_for_llm(product: Dict[str, Any]) -> str:
    """Format thông tin sản phẩm thành chuỗi dễ đọc cho LLM."""
    price_formatted = f"{product['price']:,}đ".replace(",", ".")
    stock_status = "Còn hàng" if product.get("stock", 0) > 0 else "Hết hàng"
    
    return (
        f"- **{product['name']}** (ID: {product['id']})\n"
        f"  Giá: {price_formatted} | Tồn kho: {stock_status} ({product.get('stock', 0)} chiếc)\n"
        f"  Đánh giá: {product.get('rating', 0)}/5 ⭐\n"
        f"  Mô tả: {product.get('description', 'N/A')}\n"
        f"  Ảnh minh họa: {product.get('image_url', '')}"
    )
