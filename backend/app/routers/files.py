from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
import os
from pathlib import Path
from datetime import datetime

from app.core.config import settings
from app.models.schemas import FileInfo, FileListResponse
from app.utils.file_utils import is_beancount_file, get_beancount_files

router = APIRouter()

@router.get("/", response_model=FileListResponse)
async def list_files():
    """获取data目录下的所有beancount文件"""
    try:
        data_dir = settings.data_dir
        files = []
        
        if data_dir.exists():
            # 使用工具函数获取所有Beancount文件
            beancount_files = get_beancount_files(data_dir)
            for file_path in beancount_files:
                stat = file_path.stat()
                file_info = FileInfo(
                    name=file_path.name,
                    path=str(file_path.relative_to(data_dir)),
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    is_main=(file_path.name == settings.default_beancount_file)
                )
                files.append(file_info)
        
        # 去重（如果有重复的文件）
        unique_files = {f.name: f for f in files}.values()
        files = list(unique_files)
        
        # 按修改时间排序
        files.sort(key=lambda x: x.modified, reverse=True)
        
        main_file = None
        for file in files:
            if file.is_main:
                main_file = file.name
                break
        
        return FileListResponse(files=files, main_file=main_file)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@router.get("/{filename}/content")
async def get_file_content(filename: str):
    """获取指定文件的内容"""
    try:
        file_path = settings.data_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not is_beancount_file(filename):
            raise HTTPException(status_code=400, detail="只支持Beancount文件(.bean/.beancount)")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "filename": filename,
            "content": content,
            "size": len(content),
            "lines": len(content.split('\n'))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

@router.put("/{filename}/content")
async def update_file_content(filename: str, content: dict):
    """更新指定文件的内容"""
    try:
        file_path = settings.data_dir / filename
        
        if not is_beancount_file(filename):
            raise HTTPException(status_code=400, detail="只支持Beancount文件(.bean/.beancount)")
        
        # 写入新内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content.get('content', ''))
        
        # 重新加载beancount数据
        from app.services.beancount_service import beancount_service
        beancount_service._load_entries(force_reload=True)
        
        return {"message": "文件更新成功", "filename": filename}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新文件失败: {str(e)}")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传beancount文件"""
    try:
        if not is_beancount_file(file.filename):
            raise HTTPException(status_code=400, detail="只支持上传Beancount文件(.bean/.beancount)")
        
        file_path = settings.data_dir / file.filename
        
        # 检查文件是否已存在
        if file_path.exists():
            raise HTTPException(status_code=400, detail="文件已存在，请先删除或重命名")
        
        # 保存上传的文件
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return {
            "message": "文件上传成功",
            "filename": file.filename,
            "size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.delete("/{filename}")
async def delete_file(filename: str):
    """删除指定文件"""
    try:
        file_path = settings.data_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if filename == settings.default_beancount_file:
            raise HTTPException(status_code=400, detail="不能删除主账本文件")
        
        file_path.unlink()
        
        return {"message": "文件删除成功", "filename": filename}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

@router.post("/{filename}/validate")
async def validate_file(filename: str):
    """验证beancount文件语法"""
    try:
        file_path = settings.data_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 使用beancount加载器验证文件
        from beancount import loader
        
        entries, errors, options_map = loader.load_file(str(file_path))
        
        return {
            "valid": len(errors) == 0,
            "entries_count": len(entries),
            "errors_count": len(errors),
            "errors": [str(error) for error in errors[:10]],  # 最多返回10个错误
            "options": dict(options_map) if options_map else {}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证文件失败: {str(e)}") 