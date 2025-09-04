"""
提取器基类模块
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union


class BaseExtractor(ABC):
    """
    提取器基类，定义所有提取器的通用接口
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        初始化提取器

        Args:
            api_key: API密钥
            **kwargs: 其他配置参数
        """
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    def extract(self, url: str) -> Dict[str, Union[str, dict]]:
        """
        从URL中提取内容

        Args:
            url: 网页URL

        Returns:
            包含以下字段的字典:
            - markdown: 提取的markdown文本
            - html: 原始HTML (可选)
            - metadata: 元数据 (可选)
        """
        pass

    @abstractmethod
    async def extract_async(self, url: str) -> Dict[str, Union[str, dict]]:
        """
        从URL中异步提取内容

        Args:
            url: 网页URL

        Returns:
            包含以下字段的字典:
            - markdown: 提取的markdown文本
            - html: 原始HTML (可选)
            - metadata: 元数据 (可选)
        """
        pass

    @abstractmethod
    def extract_batch(self, urls: List[str]) -> List[Dict[str, Union[str, dict]]]:
        """
        批量从URL中提取内容

        Args:
            urls: 网页URL列表

        Returns:
            提取结果列表
        """
        pass
