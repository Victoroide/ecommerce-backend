from fastapi import Query
from typing import Generic, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Query as SQLAlchemyQuery

T = TypeVar('T')

class PaginationParams:
    def __init__(
        self, 
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        sort_by: Optional[str] = Query(None, description="Field to sort by"),
        sort_order: str = Query("asc", description="Sort order (asc or desc)")
    ):
        self.page = page
        self.page_size = page_size
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()
        self.offset = (page - 1) * page_size

class PagedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool
    
    class Config:
        orm_mode = True

def paginate(query: SQLAlchemyQuery, params: PaginationParams, schema: Any) -> PagedResponse:
    total = query.count()
    
    if params.sort_by:
        sort_field = getattr(query.column_descriptions[0]['entity'], params.sort_by, None)
        if sort_field:
            if params.sort_order == "desc":
                query = query.order_by(sort_field.desc())
            else:
                query = query.order_by(sort_field.asc())
    
    items = query.offset(params.offset).limit(params.page_size).all()
    
    pages = (total + params.page_size - 1) // params.page_size
    
    return PagedResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=pages,
        has_next=params.page < pages,
        has_prev=params.page > 1
    )