"""
基本用法示例
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main import convert_batch_urls, convert_url_to_markdown


def single_url_example():
    """单个URL转换示例"""
    print("=== 单个URL转换示例 ===")

    # 1. 基本使用
    result = convert_url_to_markdown(
        url="https://github.com/mendableai/firecrawl", optimize=True
    )

    print("\n转换结果:")
    print(result.get("markdown")[:500] + "...(省略)")  # 只显示前500个字符


def batch_urls_example():
    """批量URL转换示例"""
    print("\n=== 批量URL转换示例 ===")

    # 示例URL列表
    urls = [
        "https://github.com/mendableai/firecrawl",
        "https://jina.ai/api-dashboard/reader",
    ]

    # 创建输出目录
    output_dir = "examples/output"
    os.makedirs(output_dir, exist_ok=True)

    # 批量转换
    results = convert_batch_urls(
        urls=urls, extractor_type="firecrawl", optimize=True, output_dir=output_dir
    )

    print(f"\n已将{len(results)}个URL转换结果保存到 {output_dir} 目录")


if __name__ == "__main__":
    # 确保设置了环境变量
    if not os.getenv("FIRECRAWL_API_KEY") or not os.getenv("OPENAI_API_KEY"):
        print("错误: 请先设置FIRECRAWL_API_KEY和OPENAI_API_KEY环境变量")
        print("可以通过创建.env文件或在命令行设置环境变量")
        sys.exit(1)

    # 运行示例
    single_url_example()
    batch_urls_example()
