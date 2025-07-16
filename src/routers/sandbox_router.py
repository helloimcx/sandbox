"""沙盒API路由"""

import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from models.request_models import ExecuteRequest
from models.response_models import ExecuteResponse
from services.sandbox_service import SandboxService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="",
    tags=["sandbox"]
)

# 初始化沙盒服务
sandbox_service = SandboxService()


@router.get("/")
async def root():
    """根路径健康检查"""
    return {"message": "Sandbox API is running", "status": "healthy"}


@router.get("/health")
async def health_check():
    """健康检查端点"""
    if sandbox_service.docker_service.is_available():
        return {"status": "healthy", "docker": "available"}
    else:
        raise HTTPException(status_code=503, detail="Docker service unavailable")


@router.post("/execute", response_model=ExecuteResponse)
async def execute_code(request: ExecuteRequest):
    """执行Python代码"""
    try:
        logger.info(f"收到代码执行请求，代码长度: {len(request.code)} 字符")
        
        # 验证请求
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="代码不能为空")
        
        if request.timeout and (request.timeout < 1 or request.timeout > 300):
            raise HTTPException(status_code=400, detail="超时时间必须在1-300秒之间")
        
        # 执行代码
        result = await sandbox_service.execute_code(
            code=request.code,
            timeout=request.timeout,
            work_dir_str=request.work_dir,
            ref_files=request.ref_files
        )
        
        logger.info(f"代码执行完成，成功: {result.success}, 退出码: {result.exit_code}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行代码时发生未预期错误: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# 全局异常处理器应该在main.py的app级别添加，而不是在router级别