"""
Firecrawl提取器模块
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Union

import requests
from requests.exceptions import RequestException

from src.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)


class FirecrawlExtractor(BaseExtractor):
    """
    使用Firecrawl API提取网页内容
    """

    BASE_URL = "https://api.firecrawl.dev/v1"

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        初始化Firecrawl提取器

        Args:
            api_key: Firecrawl API密钥
            **kwargs: 其他配置参数
        """
        super().__init__(api_key, **kwargs)
        self.timeout = kwargs.get("timeout", 30)
        self.retry_count = kwargs.get("retry_count", 3)

    def extract(self, url: str) -> Dict[str, Union[str, dict]]:
        """
        使用Firecrawl从URL提取内容

        Args:
            url: 网页URL

        Returns:
            包含markdown和原始HTML的字典
        """
        endpoint = f"{self.BASE_URL}/scrape"

        for attempt in range(self.retry_count):
            try:
                response = requests.post(
                    endpoint,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    json={"url": url, "formats": ["markdown", "html"]},
                    timeout=self.timeout,
                )

                response.raise_for_status()
                data = response.json()

                if data.get("success"):
                    result_data = data.get("data", {})
                    return {
                        "markdown": result_data.get("markdown", ""),
                        "html": result_data.get("html", ""),
                        "metadata": {
                            "title": result_data.get("title", ""),
                            "url": url,
                            "extractor": "firecrawl",
                        },
                    }
                else:
                    error_msg = data.get("error", "未知错误")
                    logger.error(f"Firecrawl提取失败: {error_msg}")

                    # 最后一次尝试失败时返回空结果
                    if attempt == self.retry_count - 1:
                        return {
                            "markdown": "",
                            "html": "",
                            "metadata": {"error": error_msg, "url": url},
                        }

            except RequestException as e:
                logger.error(
                    f"Firecrawl API请求异常 (尝试 {attempt+1}/{self.retry_count}): {str(e)}"
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
            包含markdown和原始HTML的字典
        """
        # 这里使用同步方法的简单实现，实际项目中应使用aiohttp等异步库
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
        results = []

        # 使用Firecrawl批量API
        endpoint = f"{self.BASE_URL}/batch/scrape"

        try:
            response = requests.post(
                endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={"urls": urls, "formats": ["markdown", "html"]},
                timeout=self.timeout,
            )

            response.raise_for_status()
            data = response.json()

            if data.get("success"):
                job_id = data.get("data", {}).get("jobId")

                # 轮询任务状态
                status_endpoint = f"{self.BASE_URL}/jobs/{job_id}"

                for _ in range(30):  # 最多轮询30次
                    status_response = requests.get(
                        status_endpoint,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        timeout=self.timeout,
                    )

                    status_data = status_response.json().get("data", {})
                    job_status = status_data.get("status")

                    if job_status == "completed":
                        results_data = status_data.get("results", [])

                        for result in results_data:
                            item_url = result.get("url", "")
                            results.append(
                                {
                                    "markdown": result.get("markdown", ""),
                                    "html": result.get("html", ""),
                                    "metadata": {
                                        "title": result.get("title", ""),
                                        "url": item_url,
                                        "extractor": "firecrawl",
                                    },
                                }
                            )

                        return results

                    elif job_status == "failed":
                        error_msg = status_data.get("error", "批处理任务失败")
                        logger.error(f"Firecrawl批处理失败: {error_msg}")
                        break

                    # 等待后再次轮询
                    time.sleep(2)

            # 如果批处理失败，尝试逐个提取
            logger.warning("批处理失败，使用单个请求模式")
            for url in urls:
                results.append(self.extract(url))

            return results

        except RequestException as e:
            logger.error(f"Firecrawl批处理API异常: {str(e)}")

            # 如果批处理失败，尝试逐个提取
            logger.warning("批处理失败，使用单个请求模式")
            for url in urls:
                results.append(self.extract(url))

            return results
