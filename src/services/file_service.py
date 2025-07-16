"""文件服务类"""

import os
import uuid
import logging
import aiohttp
import aiofiles
from pathlib import Path
from typing import List
from fastapi import HTTPException

from models.request_models import RefFile

logger = logging.getLogger(__name__)


class FileService:
    """文件服务管理类"""
    
    @staticmethod
    async def download_ref_files(ref_files: List[RefFile], work_dir: Path) -> List[str]:
        """下载引用文件到工作目录"""
        downloaded_files = []
        
        if not ref_files:
            return downloaded_files
            
        logger.info(f"开始下载 {len(ref_files)} 个引用文件")
        
        async with aiohttp.ClientSession() as session:
            for ref_file in ref_files:
                try:
                    # 确定文件名
                    if ref_file.filename:
                        filename = ref_file.filename
                    else:
                        # 从URL推断文件名
                        filename = Path(str(ref_file.url)).name or f"file_{uuid.uuid4().hex[:8]}"
                    
                    # 创建目标路径
                    target_path = work_dir / filename
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 下载文件
                    async with session.get(str(ref_file.url)) as response:
                        if response.status == 200:
                            async with aiofiles.open(target_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    await f.write(chunk)
                            
                            # 设置文件权限，确保容器内的sandbox用户可以访问
                            os.chmod(target_path, 0o666)
                            
                            downloaded_files.append(str(target_path))
                            logger.info(f"文件下载成功: {ref_file.url} -> {target_path}")
                        else:
                            logger.error(f"文件下载失败: {ref_file.url}, 状态码: {response.status}")
                            raise HTTPException(
                                status_code=400, 
                                detail=f"Failed to download file from {ref_file.url}"
                            )
                            
                except Exception as e:
                    logger.error(f"下载文件时发生错误: {ref_file.url}, 错误: {e}")
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Error downloading file: {str(e)}"
                    )
        
        return downloaded_files
    
    @staticmethod
    def cleanup_directory(directory: Path) -> None:
        """清理目录"""
        try:
            if directory.exists():
                import shutil
                shutil.rmtree(directory)
                logger.info(f"工作目录 {directory} 已清理")
        except Exception as e:
            logger.warning(f"清理目录失败 {directory}: {e}")