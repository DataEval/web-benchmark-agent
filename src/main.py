"""
Web Benchmark Agent主入口模块
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Union

from dotenv import load_dotenv

from src.extractors.firecrawl import FirecrawlExtractor
from src.extractors.jina import JinaExtractor
from src.llm.processor import LLMProcessor

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


def get_extractor(extractor_type: str = "firecrawl", **kwargs):
    """
    获取指定类型的提取器

    Args:
        extractor_type: 提取器类型，支持"firecrawl"和"jina"
        **kwargs: 提取器配置

    Returns:
        提取器实例
    """
    if extractor_type == "firecrawl":
        api_key = kwargs.get("api_key") or os.getenv("FIRECRAWL_API_KEY")
        return FirecrawlExtractor(api_key=api_key, **kwargs)
    elif extractor_type == "jina":
        api_key = kwargs.get("api_key") or os.getenv("JINA_API_KEY")
        return JinaExtractor(api_key=api_key, **kwargs)
    else:
        raise ValueError(f"不支持的提取器类型: {extractor_type}")


def get_llm_processor(**kwargs):
    """
    获取LLM处理器

    Args:
        **kwargs: 处理器配置

    Returns:
        LLM处理器实例
    """
    api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
    return LLMProcessor(api_key=api_key, **kwargs)


def convert_url_to_markdown(
    url: str,
    extractor_type: str = "firecrawl",
    optimize: bool = True,
    output_file: Optional[str] = None,
    save_html: bool = None,
    **kwargs,
) -> Dict[str, Union[str, dict]]:
    """
    将URL转换为优化的Markdown

    Args:
        url: 网页URL
        extractor_type: 提取器类型
        optimize: 是否使用LLM优化
        output_file: 输出文件路径
        save_html: 是否保存HTML（如果为None则使用环境变量）
        **kwargs: 其他参数

    Returns:
        包含markdown和元数据的字典
    """
    logger.info(f"处理URL: {url}")

    # 获取是否保存HTML的设置
    if save_html is None:
        save_html = os.getenv("SAVE_HTML", "false").lower() == "true"

    # 1. 提取内容
    extractor = get_extractor(extractor_type, **kwargs)
    extracted_data = extractor.extract(url)

    logger.info(f"使用{extractor_type}提取完成")

    # 2. LLM优化（如果启用）
    if optimize and extracted_data.get("markdown"):
        processor = get_llm_processor(**kwargs)
        result = processor.optimize_markdown(extracted_data)
        logger.info("LLM优化完成")
    else:
        result = extracted_data

    # 3. 保存结果（如果需要）
    if output_file:
        output_dir = os.path.dirname(output_file)
        if output_dir:  # 如果文件路径包含目录
            os.makedirs(output_dir, exist_ok=True)

        # 保存Markdown
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.get("markdown", ""))

        # 保存HTML（如果需要）
        if save_html and result.get("html"):
            html_file = os.path.splitext(output_file)[0] + ".html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(result.get("html", ""))
            logger.info(f"已保存HTML到: {html_file}")

        # 保存元数据
        json_file = os.path.splitext(output_file)[0] + ".json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result.get("metadata", {}), f, ensure_ascii=False, indent=2)
        logger.info(f"已保存元数据到: {json_file}")

        logger.info(f"已保存Markdown到: {output_file}")

    return result


def convert_batch_urls(
    urls: List[str],
    extractor_type: str = "firecrawl",
    optimize: bool = True,
    output_dir: Optional[str] = None,
    save_html: bool = None,
    **kwargs,
) -> List[Dict[str, Union[str, dict]]]:
    """
    批量转换URL

    Args:
        urls: URL列表
        extractor_type: 提取器类型
        optimize: 是否使用LLM优化
        output_dir: 输出目录
        save_html: 是否保存HTML（如果为None则使用环境变量）
        **kwargs: 其他参数

    Returns:
        结果列表
    """
    logger.info(f"批量处理{len(urls)}个URL")

    # 获取是否保存HTML的设置
    if save_html is None:
        save_html = os.getenv("SAVE_HTML", "false").lower() == "true"

    # 1. 提取内容
    extractor = get_extractor(extractor_type, **kwargs)
    extracted_data_list = extractor.extract_batch(urls)

    logger.info(f"使用{extractor_type}批量提取完成")

    # 2. LLM优化（如果启用）
    results = []

    if optimize:
        processor = get_llm_processor(**kwargs)

        for i, extracted_data in enumerate(extracted_data_list):
            if extracted_data.get("markdown"):
                result = processor.optimize_markdown(extracted_data)
                results.append(result)

                logger.info(
                    f"优化完成 ({i+1}/{len(extracted_data_list)}): {extracted_data.get('metadata', {}).get('url', '')}"
                )
            else:
                results.append(extracted_data)
    else:
        results = extracted_data_list

    # 3. 保存结果（如果需要）
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

        for i, result in enumerate(results):
            url_str = result.get("metadata", {}).get("url", "")
            # 构建干净的文件名
            filename_base = f"url_{i+1}"

            # 保存Markdown
            md_filename = os.path.join(output_dir, f"{filename_base}.md")
            with open(md_filename, "w", encoding="utf-8") as f:
                f.write(result.get("markdown", ""))

            # 保存HTML（如果需要）
            if save_html and result.get("html"):
                html_filename = os.path.join(output_dir, f"{filename_base}.html")
                with open(html_filename, "w", encoding="utf-8") as f:
                    f.write(result.get("html", ""))

            # 保存元数据
            json_filename = os.path.join(output_dir, f"{filename_base}.json")
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(result.get("metadata", {}), f, ensure_ascii=False, indent=2)

        logger.info(f"批量处理结果已保存到: {output_dir}")

    return results


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description="Web Benchmark Agent - HTML到Markdown转换工具"
    )
    parser.add_argument("--url", help="要处理的URL")
    parser.add_argument("--urls-file", help="包含URL列表的文件路径")
    parser.add_argument(
        "--extractor",
        choices=["firecrawl", "jina"],
        default="firecrawl",
        help="使用的提取器",
    )
    parser.add_argument("--no-optimize", action="store_true", help="禁用LLM优化")
    parser.add_argument("--output-file", help="单个URL的输出文件路径")
    parser.add_argument("--output-dir", help="批量处理的输出目录")
    parser.add_argument("--save-html", action="store_true", help="保存原始HTML")

    args = parser.parse_args()

    if args.url:
        # 处理单个URL
        result = convert_url_to_markdown(
            url=args.url,
            extractor_type=args.extractor,
            optimize=not args.no_optimize,
            output_file=args.output_file,
            save_html=args.save_html,
        )

        if not args.output_file:
            print(result.get("markdown", ""))

    elif args.urls_file:
        # 批量处理URL列表
        with open(args.urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        results = convert_batch_urls(
            urls=urls,
            extractor_type=args.extractor,
            optimize=not args.no_optimize,
            output_dir=args.output_dir,
            save_html=args.save_html,
        )

        if not args.output_dir:
            for i, result in enumerate(results):
                print(f"\n--- 结果 {i+1} ---")
                print(result.get("markdown", ""))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
