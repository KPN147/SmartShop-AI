"""
SmartShop AI - Products Router
REST API endpoints cho danh mục sản phẩm.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from tools.search_product import _load_products, search_product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["Products"])


# ===== Response Schema =====

class ProductResponse(BaseModel):
    id: str
    name: str
    category: str
    brand: str
    price: int
    stock: int
    description: str
    rating: float
    tags: List[str]
    image_url: Optional[str] = None


# ===== Endpoints =====

@router.get(
    "",
    response_model=List[ProductResponse],
    summary="Lấy danh sách tất cả sản phẩm",
    description="Trả về toàn bộ danh mục sản phẩm. Hỗ trợ lọc theo category và brand.",
)
async def get_all_products(
    category: Optional[str] = Query(default=None, description="Lọc theo danh mục (Điện thoại, Laptop, Tai nghe...)"),
    brand: Optional[str] = Query(default=None, description="Lọc theo thương hiệu (Apple, Samsung, Sony...)"),
    in_stock: Optional[bool] = Query(default=None, description="Chỉ hiển thị sản phẩm còn hàng"),
    limit: int = Query(default=20, ge=1, le=100, description="Số lượng tối đa kết quả trả về"),
) -> List[ProductResponse]:
    """Lấy danh sách sản phẩm với tùy chọn lọc."""
    products = _load_products()

    if not products:
        raise HTTPException(status_code=503, detail="Không thể tải danh mục sản phẩm.")

    # Áp dụng các bộ lọc
    if category:
        products = [p for p in products if category.lower() in p.get("category", "").lower()]
    if brand:
        products = [p for p in products if brand.lower() in p.get("brand", "").lower()]
    if in_stock is not None:
        products = [p for p in products if (p.get("stock", 0) > 0) == in_stock]

    logger.info(f"[ProductsRouter] GET /products | category={category} | brand={brand} | count={len(products)}")
    return products[:limit]


@router.get(
    "/search",
    response_model=List[ProductResponse],
    summary="Tìm kiếm sản phẩm theo từ khóa",
    description="Tìm kiếm thông minh theo tên, thương hiệu, mô tả hoặc tags.",
)
async def search_products(
    q: str = Query(..., min_length=1, description="Từ khóa tìm kiếm"),
    limit: int = Query(default=5, ge=1, le=20, description="Số lượng kết quả tối đa"),
) -> List[ProductResponse]:
    """Tìm kiếm sản phẩm theo từ khóa."""
    results = search_product(query=q, max_results=limit)
    logger.info(f"[ProductsRouter] GET /products/search | q='{q}' | found={len(results)}")
    return results


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Lấy chi tiết một sản phẩm theo ID",
    description="Tra cứu thông tin đầy đủ của một sản phẩm theo mã sản phẩm (P001, P002...)",
)
async def get_product_by_id(product_id: str) -> ProductResponse:
    """Lấy thông tin chi tiết sản phẩm theo ID."""
    products = _load_products()
    product_id_upper = product_id.upper()

    for product in products:
        if product.get("id", "").upper() == product_id_upper:
            logger.info(f"[ProductsRouter] GET /products/{product_id} → found")
            return product

    logger.warning(f"[ProductsRouter] GET /products/{product_id} → not found")
    raise HTTPException(
        status_code=404,
        detail=f"Không tìm thấy sản phẩm với ID: {product_id}"
    )


@router.get(
    "/category/list",
    response_model=List[str],
    summary="Lấy danh sách tất cả các danh mục",
    description="Trả về danh sách tên các danh mục sản phẩm có sẵn.",
)
async def get_categories() -> List[str]:
    """Lấy danh sách danh mục sản phẩm."""
    products = _load_products()
    categories = sorted(set(p.get("category", "") for p in products if p.get("category")))
    return categories
