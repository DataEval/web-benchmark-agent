"""
Jina.ai提取器模块
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Union

import requests
from requests.exceptions import RequestException

from src.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class JinaExtractor(BaseExtractor):
    """
    使用Jina.ai Reader API提取网页内容
    """

    BASE_URL = "https://api.jina.ai/v1/reader"

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        初始化Jina提取器

        Args:
            api_key: Jina API密钥
            **kwargs: 其他配置参数
        """
        super().__init__(api_key, **kwargs)
        self.timeout = kwargs.get("timeout", 30)
        self.retry_count = kwargs.get("retry_count", 3)

    def extract(self, url: str) -> Dict[str, Union[str, dict]]:
        """
        使用Jina.ai从URL提取内容

        Args:
            url: 网页URL

        Returns:
            包含markdown和元数据的字典
        """
        for attempt in range(self.retry_count):
            try:
                response = requests.post(
                    self.BASE_URL,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    json={"url": url, "format": "markdown"},
                    timeout=self.timeout,
                )

                response.raise_for_status()
                data = response.json()

                # 注意：这里的返回结构需要根据实际Jina.ai API调整
                return {
                    "markdown": data.get("content", ""),
                    "html": data.get("html", ""),
                    "metadata": {
                        "title": data.get("title", ""),
                        "url": url,
                        "extractor": "jina",
                    },
                }

            except RequestException as e:
                logger.error(
                    f"Jina API请求异常 (尝试 {attempt+1}/{self.retry_count}): {str(e)}"
                )

                # 最后一次尝试失败时返回空结果
                if attempt == self.retry_count - 1:
                    return {
                        "markdown": "",
                        "html": "",
                        "metadata": {"error": str(e), "url": url},
                    }

                # 短暂延迟后重试
                time.sleep(1)

        # 不应该到达这里，但为安全起见
        return {
            "markdown": "",
            "html": "",
            "metadata": {"error": "所有请求尝试均失败", "url": url},
        }

    async def extract_async(self, url: str) -> Dict[str, Union[str, dict]]:
        """
        异步从URL提取内容

        Args:
            url: 网页URL

        Returns:
            包含markdown和元数据的字典
        """
        # 简单实现，实际项目中应使用aiohttp等异步库
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.extract, url)

    def extract_batch(self, urls: List[str]) -> List[Dict[str, Union[str, dict]]]:
        """
        批量从URL提取内容

        Args:
            urls: URL列表

        Returns:
            提取结果列表
        """
        # Jina.ai可能没有批量API，使用简单实现
        results = []
        for url in urls:
            results.append(self.extract(url))
        return results
