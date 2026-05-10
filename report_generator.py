import streamlit as st
from visualization import create_trend_chart
from anomaly_detector import generate_anomaly_insight
from insight_engine import generate_executive_summary
from llm_client import chat


def render_kpi_cards(metrics: dict):
    """渲染4列KPI指标卡片"""
    cols = st.columns(4)

    revenue = metrics.get("revenue", {})
    net_profit = metrics.get("net_profit", {})
    gross_margin = metrics.get("gross_margin", {})
    roe = metrics.get("roe", {})

    with cols[0]:
        delta_value = None
        if revenue.get("yoy_growth") is not None:
            delta_value = f"{revenue['yoy_growth']:+.1f}%"
        st.metric(
            label="营业总收入",
            value=f"{revenue.get('value', 'N/A')}{revenue.get('unit', '')}" if revenue.get("value") else "N/A",
            delta=delta_value
        )

    with cols[1]:
        delta_value = None
        if net_profit.get("yoy_growth") is not None:
            delta_value = f"{net_profit['yoy_growth']:+.1f}%"
        st.metric(
            label="净利润",
            value=f"{net_profit.get('value', 'N/A')}{net_profit.get('unit', '')}" if net_profit.get("value") else "N/A",
            delta=delta_value
        )

    with cols[2]:
        value_str = f"{gross_margin.get('value', 'N/A')}%" if gross_margin.get("value") else "N/A"
        delta_value = None
        if gross_margin.get("yoy_growth") is not None:
            delta_value = f"{gross_margin['yoy_growth']:+.1f} pp"
        st.metric(
            label="毛利率",
            value=value_str,
            delta=delta_value,
            delta_color="normal"
        )

    with cols[3]:
        value_str = f"{roe.get('value', 'N/A')}%" if roe.get("value") else "N/A"
        delta_value = None
        if roe.get("yoy_growth") is not None:
            delta_value = f"{roe['yoy_growth']:+.1f}%"
        st.metric(
            label="ROE",
            value=value_str,
            delta=delta_value
        )


def render_trend_section(multi_year_data: dict):
    """渲染趋势图区域"""
    st.subheader("📈 核心指标趋势")

    fig = create_trend_chart(multi_year_data)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("该年报未包含多年对比数据，无法绘制趋势图表。")


def render_anomaly_section(anomalies: list):
    """渲染异常预警区域"""
    st.subheader("⚠️ 异常预警")

    if not anomalies:
        st.success("✅ 未检测到明显异常指标")
        return

    high_anomalies = [a for a in anomalies if a.get("severity") == "high"]
    medium_anomalies = [a for a in anomalies if a.get("severity") == "medium"]

    if high_anomalies:
        for a in high_anomalies:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%);
                        border-left: 4px solid #e53e3e; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
                <strong style="color: #c53030;">🔴 {a['type']}</strong><br/>
                <span style="color: #666; font-size: 0.9em;">{a.get('explanation', '')}</span>
            </div>
            """, unsafe_allow_html=True)

    if medium_anomalies:
        for a in medium_anomalies:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fffff0 0%, #fff5dc 100%);
                        border-left: 4px solid #ecc94b; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
                <strong style="color: #b7791f;">🟡 {a['type']}</strong><br/>
                <span style="color: #666; font-size: 0.9em;">{a.get('explanation', '')}</span>
            </div>
            """, unsafe_allow_html=True)

    # LLM 通俗解释
    with st.expander("💡 查看通俗解读"):
        insight = generate_anomaly_insight(anomalies, chat)
        st.markdown(insight)


def render_management_insights(management_discussion: list):
    """渲染管理层讨论要点"""
    st.subheader("💬 管理层讨论要点")

    if not management_discussion:
        st.info("未提取到管理层讨论要点")
        return

    for i, point in enumerate(management_discussion, 1):
        st.markdown(f"""
        <div style="display: flex; align-items: flex-start; margin-bottom: 8px;">
            <div style="background: #1f77b4; color: white; border-radius: 50%;
                        width: 24px; height: 24px; display: flex; align-items: center;
                        justify-content: center; font-size: 0.8em; margin-right: 12px;
                        flex-shrink: 0;">{i}</div>
            <div style="color: #333; padding-top: 2px;">{point}</div>
        </div>
        """, unsafe_allow_html=True)


def render_executive_summary_section(metrics: dict, management_discussion: list):
    """渲染管理层摘要"""
    st.subheader("📋 AI 分析摘要")

    summary = generate_executive_summary(metrics, management_discussion)
    if summary.startswith("[LLM调用失败]"):
        st.error(summary)
        return

    st.info(summary)


def render_full_dashboard(data: dict, anomalies: list):
    """组装完整仪表板 — 主入口函数"""

    metrics = data.get("core_metrics", {})
    multi_year = data.get("multi_year_data", {})
    management_discussion = data.get("management_discussion", [])

    # 公司信息标题
    company_name = data.get("company_name", "未知公司")
    report_year = data.get("report_year", "")
    st.title(f"📊 {company_name}")
    if report_year:
        st.caption(f"报告年份：{report_year}")

    st.divider()

    # KPI 指标卡片
    if metrics:
        render_kpi_cards(metrics)
    else:
        st.warning("未提取到核心财务指标")
        return

    st.divider()

    # 趋势图
    if multi_year:
        render_trend_section(multi_year)

    # 异常预警
    render_anomaly_section(anomalies)

    st.divider()

    # 管理层讨论
    render_management_insights(management_discussion)

    st.divider()

    # AI 分析摘要
    render_executive_summary_section(metrics, management_discussion)
