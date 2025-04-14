"""
LLM处理器模块，用于优化提取的markdown
"""

import logging
from typing import Dict, Optional, Union

import openai

logger = logging.getLogger(__name__)


class LLMProcessor:
    """
    使用LLM优化提取的markdown内容
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        初始化LLM处理器

        Args:
            api_key: OpenAI API密钥
            **kwargs: 其他配置参数
        """
        self.api_key = api_key
        self.model = kwargs.get("model", "gpt-4")
        self.temperature = kwargs.get("temperature", 0.1)
        self.provider = kwargs.get("provider", "openai")

        # 根据提供者设置API客户端
        if self.provider == "openai":
            openai.api_key = self.api_key

    def optimize_markdown(
        self, extracted_data: Dict[str, Union[str, dict]]
    ) -> Dict[str, Union[str, dict]]:
        """
        使用LLM优化提取的markdown

        Args:
            extracted_data: 提取的数据，包含markdown和HTML

        Returns:
            优化后的数据
        """
        markdown = extracted_data.get("markdown", "")
        html = extracted_data.get("html", "")

        if not markdown:
            logger.warning("没有提供markdown内容进行优化")
            return extracted_data

        # 构建提示词
        system_prompt = """
你是一个专业的HTML到Markdown转换专家。你的任务是检查从HTML生成的Markdown文本，
改进其质量，确保其格式正确，并修复任何问题。遵循以下规则：

1. 确保保留原始内容的结构和层次
2. 正确处理标题、列表、表格、链接和图片
3. 移除不必要的空白行和重复内容
4. 修正格式错误，如标题级别跳过或嵌套不当的列表
5. 保持代码块的格式和语法高亮
6. 保留原始的链接URL和图片URL

返回优化后的Markdown文本，不要添加任何解释或注释。
"""

        user_prompt = f"""
请检查并优化下面的Markdown内容。

这是原始提取的Markdown:
```
{markdown}
```

需要时，你可以参考原始HTML:
```
{html}
```

请返回优化后的Markdown:
"""

        try:
            if self.provider == "openai":
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                )

                optimized_markdown = response.choices[0].message.content

                # 返回结果，包含原始和优化后的内容
                result = extracted_data.copy()
                result["markdown"] = optimized_markdown
                result["metadata"] = result.get("metadata", {})
                result["metadata"]["optimized"] = True

                return result

            else:
                logger.error(f"不支持的LLM提供者: {self.provider}")
                return extracted_data

        except Exception as e:
            logger.error(f"LLM处理失败: {str(e)}")
            return extracted_data
