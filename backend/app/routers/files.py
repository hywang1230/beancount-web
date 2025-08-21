from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
import os
from pathlib import Path
from datetime import datetime

from app.core.config import settings
from app.models.schemas import FileInfo, FileListResponse, FileTreeResponse, FileTreeNode
from app.utils.file_utils import (
    is_beancount_file, 
    get_beancount_files, 
    build_file_tree, 
    get_all_included_files
)

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

@router.get("/tree", response_model=FileTreeResponse)
async def get_file_tree():
    """获取账本文件的树状结构"""
    try:
        main_file = settings.data_dir / settings.default_beancount_file
        
        if not main_file.exists():
            raise HTTPException(status_code=404, detail="主账本文件不存在")
        
        # 构建文件树
        tree_data = build_file_tree(main_file)
        
        # 转换为响应模型
        def convert_to_tree_node(data: dict) -> FileTreeNode:
            children = [convert_to_tree_node(child) for child in data.get("includes", [])]
            return FileTreeNode(
                name=data["name"],
                path=data["path"],
                size=data["size"],
                type=data.get("type", "file"),
                is_main=data.get("is_main", False),
                includes=children,
                modified=data.get("modified"),
                error=data.get("error")
            )
        
        tree = convert_to_tree_node(tree_data)
        
        # 计算总文件数
        all_files = get_all_included_files(main_file)
        
        return FileTreeResponse(
            tree=tree,
            total_files=len(all_files),
            main_file=settings.default_beancount_file
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件树失败: {str(e)}")

@router.get("/content")
async def get_file_content(file_path: str):
    """获取指定文件的内容（支持相对路径）"""
    try:
        # 处理路径参数，支持子目录文件
        full_path = settings.data_dir / file_path
        
        # 安全检查：确保文件在data目录内
        try:
            full_path.resolve().relative_to(settings.data_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=400, detail="不允许访问data目录外的文件")
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not is_beancount_file(full_path.name):
            raise HTTPException(status_code=400, detail="只支持Beancount文件(.bean/.beancount)")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "filename": full_path.name,
            "file_path": file_path,
            "content": content,
            "size": len(content),
            "lines": len(content.split('\n'))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

@router.get("/{filename}/content")
async def get_file_content_legacy(filename: str):
    """获取指定文件的内容（兼容旧接口）"""
    return await get_file_content(filename)

@router.put("/content")
async def update_file_content(file_path: str, content: dict):
    """更新指定文件的内容（支持相对路径）"""
    try:
        # 处理路径参数，支持子目录文件
        full_path = settings.data_dir / file_path
        
        # 安全检查：确保文件在data目录内
        try:
            full_path.resolve().relative_to(settings.data_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=400, detail="不允许访问data目录外的文件")
        
        if not is_beancount_file(full_path.name):
            raise HTTPException(status_code=400, detail="只支持Beancount文件(.bean/.beancount)")
        
        # 写入新内容
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content.get('content', ''))
        
        # 重新加载beancount数据
        from app.services.beancount_service import beancount_service
        beancount_service.loader.load_entries(force_reload=True)
        
        return {
            "message": "文件更新成功", 
            "filename": full_path.name,
            "file_path": file_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新文件失败: {str(e)}")

@router.put("/{filename}/content")
async def update_file_content_legacy(filename: str, content: dict):
    """更新指定文件的内容（兼容旧接口）"""
    return await update_file_content(filename, content)

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
        
        # 判断是否为主文件，如果不是主文件，则验证整个账本系统
        if filename == settings.default_beancount_file:
            # 直接验证主文件
            entries, errors, options_map = loader.load_file(str(file_path))
        else:
            # 对于子文件，验证整个账本系统以确保所有引用都能正确解析
            main_file_path = settings.data_dir / settings.default_beancount_file
            if main_file_path.exists():
                entries, errors, options_map = loader.load_file(str(main_file_path))
                # 过滤出与当前文件相关的错误
                file_specific_errors = []
                for error in errors:
                    if hasattr(error, 'source') and error.source and filename in str(error.source.get('filename', '')):
                        file_specific_errors.append(error)
                errors = file_specific_errors
            else:
                # 如果主文件不存在，直接验证单个文件
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