from config import EXPENSE_GROWTH_OVER_REVENUE_THRESHOLD, PROFIT_CF_DIVERGENCE_THRESHOLD

def detect_by_rules(metrics: dict) -> list:
    """基于规则的异常检测。输入：core_metrics 字典；输出：anomalies 列表"""
    anomalies = []

    revenue_growth = _safe_float(metrics.get("revenue", {}).get("yoy_growth"))

    # 规则1：费用增速检查
    expense_items = [
        ("sales_expense", "销售费用"),
        ("admin_expense", "管理费用"),
        ("rd_expense", "研发费用"),
    ]

    for key, label in expense_items:
        expense = metrics.get(key, {})
        expense_growth = _safe_float(expense.get("yoy_growth"))

        if expense_growth is not None and revenue_growth is not None:
            gap = expense_growth - revenue_growth
            if gap > EXPENSE_GROWTH_OVER_REVENUE_THRESHOLD:
                severity = "high" if gap > 20 else "medium"
                anomalies.append({
                    "type": "费用增速异常",
                    "metric": label,
                    "value": expense_growth,
                    "benchmark": f"营收增速{revenue_growth}%",
                    "gap": round(gap, 1),
                    "severity": severity,
                    "explanation": f"{label}增速({expense_growth}%)显著高于营收增速({revenue_growth}%)，差距{gap:.1f}个百分点。需关注费用管控效率。"
                })

    # 规则2：利润与现金流背离
    profit_growth = _safe_float(metrics.get("net_profit", {}).get("yoy_growth"))
    cf_growth = _safe_float(metrics.get("operating_cf", {}).get("yoy_growth"))

    if (profit_growth is not None and profit_growth > PROFIT_CF_DIVERGENCE_THRESHOLD
            and cf_growth is not None and cf_growth < 0):
        anomalies.append({
            "type": "利润与现金流背离",
            "metric": "经营活动现金流",
            "value": cf_growth,
            "benchmark": f"净利润增速{profit_growth}%",
            "gap": round(profit_growth - cf_growth, 1),
            "severity": "high",
            "explanation": "净利润增长但经营现金流下滑，可能原因：应收账款大幅增加、存货积压、或收入确认政策变更。建议查看现金流量表附注。"
        })

    # 规则3：毛利率大幅下降
    gross_margin_yoy = _safe_float(metrics.get("gross_margin", {}).get("yoy_growth"))

    if gross_margin_yoy is not None and gross_margin_yoy < -3:
        anomalies.append({
            "type": "毛利率下滑",
            "metric": "毛利率",
            "value": gross_margin_yoy,
            "benchmark": "毛利率稳定或微降",
            "gap": abs(gross_margin_yoy),
            "severity": "high" if gross_margin_yoy < -5 else "medium",
            "explanation": f"毛利率同比下降{abs(gross_margin_yoy)}个百分点，需关注原材料成本上升或产品降价压力。"
        })

    return anomalies


def _safe_float(value):
    """安全转换：None → None, 非数字 → None"""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def generate_anomaly_insight(anomalies: list, llm_chat_func) -> str:
    """调用 LLM 生成异常信号的通俗解释"""
    if not anomalies:
        return "✅ 未检测到明显异常指标。各项财务指标在正常范围内。"

    anomaly_text = "\n".join([
        f"- {a['metric']}：{a.get('explanation', '')}"
        for a in anomalies
    ])

    prompt = f"""以下是一家公司年报中检测到的财务异常信号：

{anomaly_text}

请用通俗易懂的语言（面向非财务背景用户）：
1. 简要解释这些异常信号意味着什么（2-3句话）
2. 给出1-2条用户下一步应该关注的方向

控制在150字以内。"""

    return llm_chat_func(
        system="你是金融分析师，擅长将复杂的财务概念转化为通俗解释。",
        user_message=prompt,
        temperature=0.3,
        max_tokens=300
    )
