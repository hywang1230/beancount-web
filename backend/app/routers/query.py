"""
BQL 查询 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.models.schemas import (
    BQLQueryRequest, 
    BQLQueryResponse, 
    BQLQueryExample, 
    BQLFunction,
    SavedQuery as SavedQuerySchema
)
from app.models.saved_query import SavedQuery
from app.services.bql_service import BQLService
from app.services.beancount_service import beancount_service
from app.database import get_db

router = APIRouter()


@router.post("/execute", response_model=BQLQueryResponse)
async def execute_query(request: BQLQueryRequest):
    """
    执行 BQL 查询
    
    示例查询:
    ```sql
    SELECT account, SUM(position) 
    WHERE account ~ "Expenses" 
    GROUP BY account 
    ORDER BY SUM(position) DESC
    ```
    """
    try:
        bql_service = BQLService(beancount_service.loader)
        result = bql_service.execute_query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询执行失败: {str(e)}")


@router.post("/validate")
async def validate_query(request: BQLQueryRequest):
    """
    验证 BQL 查询语法
    """
    try:
        bql_service = BQLService(beancount_service.loader)
        result = bql_service.validate_query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.get("/examples", response_model=List[BQLQueryExample])
async def get_query_examples():
    """
    获取常用查询示例
    """
    try:
        bql_service = BQLService(beancount_service.loader)
        examples = bql_service.get_query_examples()
        return examples
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取示例失败: {str(e)}")


@router.get("/functions", response_model=List[BQLFunction])
async def get_available_functions():
    """
    获取可用的 BQL 函数列表
    """
    try:
        bql_service = BQLService(beancount_service.loader)
        functions = bql_service.get_available_functions()
        return functions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取函数列表失败: {str(e)}")


# 保存的查询管理
@router.get("/saved", response_model=List[SavedQuerySchema])
async def get_saved_queries(db: Session = Depends(get_db)):
    """
    获取所有保存的查询
    """
    try:
        queries = db.query(SavedQuery).order_by(SavedQuery.updated_at.desc()).all()
        return [query.to_dict() for query in queries]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取保存的查询失败: {str(e)}")


@router.post("/saved", response_model=SavedQuerySchema)
async def save_query(query_data: SavedQuerySchema, db: Session = Depends(get_db)):
    """
    保存查询
    """
    try:
        saved_query = SavedQuery(
            name=query_data.name,
            description=query_data.description,
            query=query_data.query
        )
        db.add(saved_query)
        db.commit()
        db.refresh(saved_query)
        return saved_query.to_dict()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存查询失败: {str(e)}")


@router.get("/saved/{query_id}", response_model=SavedQuerySchema)
async def get_saved_query(query_id: int, db: Session = Depends(get_db)):
    """
    获取特定的保存查询
    """
    try:
        query = db.query(SavedQuery).filter(SavedQuery.id == query_id).first()
        if not query:
            raise HTTPException(status_code=404, detail="查询不存在")
        return query.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取查询失败: {str(e)}")


@router.put("/saved/{query_id}", response_model=SavedQuerySchema)
async def update_saved_query(
    query_id: int, 
    query_data: SavedQuerySchema, 
    db: Session = Depends(get_db)
):
    """
    更新保存的查询
    """
    try:
        query = db.query(SavedQuery).filter(SavedQuery.id == query_id).first()
        if not query:
            raise HTTPException(status_code=404, detail="查询不存在")
        
        query.name = query_data.name
        query.description = query_data.description
        query.query = query_data.query
        query.updated_at = settings.now()
        
        db.commit()
        db.refresh(query)
        return query.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新查询失败: {str(e)}")


@router.delete("/saved/{query_id}")
async def delete_saved_query(query_id: int, db: Session = Depends(get_db)):
    """
    删除保存的查询
    """
    try:
        query = db.query(SavedQuery).filter(SavedQuery.id == query_id).first()
        if not query:
            raise HTTPException(status_code=404, detail="查询不存在")
        
        db.delete(query)
        db.commit()
        return {"success": True, "message": "查询已删除"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除查询失败: {str(e)}")

