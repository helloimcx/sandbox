"""验证器工具"""

from typing import Optional
from fastapi import HTTPException


def validate_code(code: str) -> None:
    """验证代码内容"""
    if not code or not code.strip():
        raise HTTPException(status_code=400, detail="代码不能为空")
    
    # 可以添加更多验证逻辑，比如检查危险操作
    dangerous_imports = ['subprocess', 'os.system', 'eval', 'exec']
    for dangerous in dangerous_imports:
        if dangerous in code:
            # 这里可以根据需要决定是否完全禁止或者只是警告
            pass


def validate_timeout(timeout: Optional[int]) -> None:
    """验证超时时间"""
    if timeout is not None:
        if timeout < 1 or timeout > 300:
            raise HTTPException(
                status_code=400, 
                detail="超时时间必须在1-300秒之间"
            )


def validate_work_dir(work_dir: str) -> None:
    """验证工作目录"""
    # 确保工作目录是安全的
    if not work_dir.startswith('/data'):
        raise HTTPException(
            status_code=400,
            detail="工作目录必须在/data路径下"
        )