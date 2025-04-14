"""
提取器测试模块
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from src.extractors.firecrawl import FirecrawlExtractor
from src.extractors.jina import JinaExtractor


class TestExtractors(unittest.TestCase):
    """测试提取器功能"""

    def setUp(self):
        """测试准备"""
        self.test_url = "https://example.com"
        self.api_key = "test_api_key"

    @patch("requests.post")
    def test_firecrawl_extract(self, mock_post):
        """测试Firecrawl提取器"""
        # 模拟响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "markdown": "# 测试Markdown",
                "html": "<h1>测试HTML</h1>",
                "title": "测试标题",
            },
        }
        mock_post.return_value = mock_response

        # 创建提取器
        extractor = FirecrawlExtractor(api_key=self.api_key)

        # 执行提取
        result = extractor.extract(self.test_url)

        # 验证结果
        self.assertEqual(result["markdown"], "# 测试Markdown")
        self.assertEqual(result["html"], "<h1>测试HTML</h1>")
        self.assertEqual(result["metadata"]["title"], "测试标题")
        self.assertEqual(result["metadata"]["url"], self.test_url)
        self.assertEqual(result["metadata"]["extractor"], "firecrawl")

        # 验证调用
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], f"Bearer {self.api_key}")
        self.assertEqual(kwargs["json"]["url"], self.test_url)
        self.assertEqual(kwargs["json"]["formats"], ["markdown", "html"])

    @patch("requests.post")
    def test_jina_extract(self, mock_post):
        """测试Jina提取器"""
        # 模拟响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "# 测试Markdown",
            "html": "<h1>测试HTML</h1>",
            "title": "测试标题",
        }
        mock_post.return_value = mock_response

        # 创建提取器
        extractor = JinaExtractor(api_key=self.api_key)

        # 执行提取
        result = extractor.extract(self.test_url)

        # 验证结果
        self.assertEqual(result["markdown"], "# 测试Markdown")
        self.assertEqual(result["html"], "<h1>测试HTML</h1>")
        self.assertEqual(result["metadata"]["title"], "测试标题")
        self.assertEqual(result["metadata"]["url"], self.test_url)
        self.assertEqual(result["metadata"]["extractor"], "jina")

        # 验证调用
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], f"Bearer {self.api_key}")
        self.assertEqual(kwargs["json"]["url"], self.test_url)
        self.assertEqual(kwargs["json"]["format"], "markdown")


if __name__ == "__main__":
    unittest.main()
