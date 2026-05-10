import json
import re
from llm_client import chat
from config import MAX_EXTRACTION_CHARS

EXTRACTION_PROMPT = """你是一个专业的财务数据分析师。请从以下年报文本中提取关键财务指标。

## 提取要求

### 当前年度核心指标（core_metrics）
请从年报中提取以下指标的本年度数值。找不到的填 null，绝对不要编造。

每个指标需要返回：
- value: 数值（数字类型）
- unit: 单位（"亿元" / "万元" / "元" / "%"）
- yoy_growth: 同比增长率（%，保留1位小数，下降用负数）
- source_quote: 原文引用段落（简短摘录，20字以内）

需要提取的指标列表：
1. revenue: 营业总收入 / 营业收入
2. net_profit: 净利润 / 归母净利润
3. net_profit_deducted: 扣非净利润
4. gross_margin: 毛利率（如年报未直接给出，填null）
5. net_margin: 净利率（如年报未直接给出，填null）
6. roe: 净资产收益率 ROE
7. eps: 每股收益 EPS
8. operating_cf: 经营活动现金流量净额
9. total_assets: 总资产
10. total_liabilities: 总负债
11. employee_count: 员工人数
12. sales_expense: 销售费用
13. admin_expense: 管理费用
14. rd_expense: 研发费用

对于费用类指标（sales_expense, admin_expense, rd_expense），同时提取同比增长率。

### 多年数据（multi_year_data）
如果年报中包含近3-5年的对比数据，请分别提取每年的：
- revenue（营收）
- net_profit（净利润）
- gross_margin（毛利率，如有）

格式：{"revenue": [{"year": 2020, "value": 980, "unit": "亿元"}, ...], ...}

### 管理层讨论要点（management_discussion）
从"管理层讨论与分析"章节提取3-5条核心战略要点。每条要点控制在50字以内，用中文概括。

## 输出格式
严格按以下 JSON 格式输出。不要输出任何JSON之外的文字，不要用markdown代码块包裹。

{
  "company_name": "公司名称",
  "report_year": "2024",
  "core_metrics": {
    "revenue": {"value": null, "unit": null, "yoy_growth": null, "source_quote": ""},
    "net_profit": {"value": null, "unit": null, "yoy_growth": null, "source_quote": ""},
    "net_profit_deducted": {"value": null, "unit": null, "yoy_growth": null, "source_quote": ""},
    "gross_margin": {"value": null, "unit": "%", "yoy_growth": null, "source_quote": ""},
    "net_margin": {"value": null, "unit": "%", "yoy_growth": null, "source_quote": ""},
    "roe": {"value": null, "unit": "%", "yoy_growth": null, "source_quote": ""},
    "eps": {"value": null, "unit": "元", "yoy_growth": null, "source_quote": ""},
    "operating_cf": {"value": null, "unit": null, "yoy_growth": null, "source_quote": ""},
    "total_assets": {"value": null, "unit": null, "yoy_growth": null, "source_quote": ""},
    "total_liabilities": {"value": null, "unit": null, "yoy_growth": null, "source_quote": ""},
    "employee_count": {"value": null, "unit": "人", "yoy_growth": null, "source_quote": ""},
    "sales_expense": {"value": null, "unit": null, "yoy_growth": null, "source_quote": ""},
    "admin_expense": {"value": null, "unit": null, "yoy_growth": null, "source_quote": ""},
    "rd_expense": {"value": null, "unit": null, "yoy_growth": null, "source_quote": ""}
  },
  "multi_year_data": {
    "revenue": [],
    "net_profit": []
  },
  "management_discussion": []
}

## 年报文本
{report_text}"""


def parse_llm_json(response: str) -> dict:
    """尽力从 LLM 输出中提取合法 JSON，4层fallback策略"""
    # 策略1：直接解析
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # 策略2：提取 ```json ... ``` 中的内容
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 策略3：找到第一个 { 和最后一个 } 之间的内容
    match = re.search(r'\{[\s\S]*\}', response)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # 策略4：修复常见问题后重试
    cleaned = response
    cleaned = cleaned.replace('“', '"').replace('”', '"')  # 中文双引号
    cleaned = cleaned.replace('‘', "'").replace('’', "'")  # 中文单引号
    cleaned = re.sub(r',\s*}', '}', cleaned)  # 移除尾随逗号
    cleaned = re.sub(r',\s*]', ']', cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    return {"error": "JSON解析失败", "raw_response": response[:500]}


def extract_financial_data(report_text: str) -> dict:
    """从年报文本中提取结构化财务数据"""
    truncated = report_text[:MAX_EXTRACTION_CHARS]

    prompt = EXTRACTION_PROMPT.replace('{report_text}', truncated)

    response = chat(
        system="你是一个专业的财务数据提取助手。只输出JSON，不输出任何其他内容。找不到的数据填null，绝对不要编造。",
        user_message=prompt,
        temperature=0.1,
        max_tokens=4000
    )

    if response.startswith("[LLM调用失败]"):
        return {"error": response}

    result = parse_llm_json(response)

    if "company_name" not in result and "error" not in result:
        result["_warning"] = "返回的JSON缺少company_name字段，可能是LLM输出格式不正确"

    return result
