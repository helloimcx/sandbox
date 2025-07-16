"""请求数据模型"""

from pydantic import BaseModel, HttpUrl
from typing import List, Optional


class RefFile(BaseModel):
    """引用文件模型"""
    url: HttpUrl
    filename: Optional[str] = None  # 可选的文件名，如果不提供则从URL推断


class ExecuteRequest(BaseModel):
    """代码执行请求模型"""
    code: str
    timeout: Optional[int] = 30
    work_dir: Optional[str] = "/data"  # 工作目录，默认为/data
    ref_files: Optional[List[RefFile]] = None