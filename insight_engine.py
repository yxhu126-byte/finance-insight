from llm_client import chat

def generate_executive_summary(metrics: dict, management_discussion: list) -> str:
    """根据财务指标和管理层讨论，生成200-300字的分析摘要"""
    revenue = metrics.get("revenue", {})
    profit = metrics.get("net_profit", {})
    margin = metrics.get("gross_margin", {})

    summary_lines = []
    if revenue.get("value"):
        yoy = revenue.get("yoy_growth", "N/A")
        summary_lines.append(f"营收：{revenue['value']}{revenue.get('unit', '')}，同比{yoy}%")
    if profit.get("value"):
        yoy = profit.get("yoy_growth", "N/A")
        summary_lines.append(f"净利润：{profit['value']}{profit.get('unit', '')}，同比{yoy}%")
    if margin.get("value"):
        summary_lines.append(f"毛利率：{margin['value']}%")

    data_summary = "；".join(summary_lines) if summary_lines else "财务数据提取不完整"

    mgmt_text = "\n".join([f"- {m}" for m in management_discussion]) if management_discussion else "无"

    prompt = f"""请根据以下信息，生成一份简短的财务分析摘要（200-300字）：

## 核心财务数据
{data_summary}

## 管理层讨论要点
{mgmt_text}

## 要求
1. 第一句概括公司今年整体表现（好/平稳/有压力）
2. 列出 2-3 个亮点
3. 列出 1-2 个需要关注的风险或挑战
4. 语言简洁专业，面向金融从业者

请直接输出摘要内容，不要加标题。"""

    return chat(
        system="你是资深金融分析师，能快速从数据中提炼关键洞察。",
        user_message=prompt,
        temperature=0.5,
        max_tokens=600
    )
