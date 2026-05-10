import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_trend_chart(multi_year_data: dict) -> go.Figure:
    """根据多年数据生成营收+净利润双Y轴趋势图"""
    revenue_data = multi_year_data.get("revenue", [])
    profit_data = multi_year_data.get("net_profit", [])

    if not revenue_data and not profit_data:
        return None

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if revenue_data:
        years = [d["year"] for d in revenue_data]
        values = [d["value"] for d in revenue_data]
        unit = revenue_data[0].get("unit", "")

        fig.add_trace(
            go.Scatter(
                x=years, y=values,
                mode='lines+markers',
                name=f'营业总收入（{unit}）',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8),
            ),
            secondary_y=False
        )

    if profit_data:
        years = [d["year"] for d in profit_data]
        values = [d["value"] for d in profit_data]
        unit = profit_data[0].get("unit", "")

        fig.add_trace(
            go.Scatter(
                x=years, y=values,
                mode='lines+markers',
                name=f'净利润（{unit}）',
                line=dict(color='#2ca02c', width=3, dash='dot'),
                marker=dict(size=8, symbol='diamond'),
            ),
            secondary_y=True
        )

    fig.update_layout(
        title=dict(
            text="近5年核心指标趋势",
            font=dict(size=16, color="#333")
        ),
        hovermode='x unified',
        template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    fig.update_xaxes(title_text="年份", tickformat='d')
    fig.update_yaxes(title_text="营业总收入", secondary_y=False)
    fig.update_yaxes(title_text="净利润", secondary_y=True)

    return fig


def create_kpi_delta(value: float, prev_value: float = None) -> dict:
    """计算指标变化信息，用于 st.metric 的 delta 参数"""
    if prev_value is None or prev_value == 0:
        return {"delta_value": None, "delta_color": "off"}

    change_pct = round((value - prev_value) / prev_value * 100, 1)
    return {
        "delta_value": f"{change_pct:+.1f}%",
        "delta_color": "normal"
    }
