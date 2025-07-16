"""日志配置工具"""

import logging
from config import config


def setup_logging() -> None:
    """设置应用程序日志配置"""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            # 可以添加文件处理器
            # logging.FileHandler('app.log')
        ]
    )
    
    # 设置第三方库的日志级别
    logging.getLogger('docker').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)