"""响应数据模型"""

from pydantic import BaseModel
from typing import List, Optional


class ImageFile(BaseModel):
    """图片文件模型"""
    filename: str
    content: str  # base64编码的图片内容
    size: int  # 文件大小（字节）


class ExecuteResponse(BaseModel):
    """代码执行响应模型"""
    success: bool
    output: str
    exit_code: int
    container_id: str
    generated_images: List[ImageFile] = []
    error_message: Optional[str] = None