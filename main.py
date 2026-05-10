import streamlit as st
from config import PAGE_TITLE, PAGE_ICON
from pdf_extractor import extract_text, get_metadata
from financial_extractor import extract_financial_data
from anomaly_detector import detect_by_rules
from report_generator import render_full_dashboard
from llm_client import chat

# ========== 页面配置 ==========
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 自定义 CSS ==========
st.markdown("""
<style>
    /* KPI 卡片背景 */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        transform: translateY(-2px);
        transition: all 0.2s ease;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #666 !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #1a202c !important;
    }

    /* 主标题 */
    .main-header {
        background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 20px;
    }

    /* 底部状态栏 */
    .footer-bar {
        text-align: center;
        color: #999;
        font-size: 0.8em;
        padding: 12px;
        border-top: 1px solid #eee;
        margin-top: 40px;
    }
</style>
""", unsafe_allow_html=True)

# ========== Session State 初始化 ==========
if "financial_data" not in st.session_state:
    st.session_state.financial_data = None
if "doc_name" not in st.session_state:
    st.session_state.doc_name = None
if "report_text" not in st.session_state:
    st.session_state.report_text = None
if "anomalies" not in st.session_state:
    st.session_state.anomalies = None

# ========== 侧边栏 ==========
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/coins.png", width=60)
    st.title("财报深析")

    st.markdown("---")

    # 文件上传
    uploaded_file = st.file_uploader(
        "📄 上传年报 PDF",
        type=["pdf"],
        help="支持 A 股、港股上市公司年报 PDF"
    )

    st.markdown("---")

    # 产品说明
    with st.expander("💡 产品亮点"):
        st.markdown("""
        **与通用 AI 的区别：**
        - 📊 **结构化提取**而非全文摘要
        - 🔍 **可追溯**每个数据点有原文引用
        - ⚠️ **异常预警**规则+AI双重检测
        - 📈 **交互图表**Plotly 趋势图可缩放
        """)

    st.markdown("---")

    # 技术栈
    st.caption("技术栈")
    st.caption("DeepSeek V3 · Streamlit · Plotly")
    st.caption("PyMuPDF · Pandas")


# ========== PDF 处理逻辑 ==========
if uploaded_file is not None:
    # 检查是否是新文件
    if st.session_state.doc_name != uploaded_file.name:
        st.session_state.doc_name = uploaded_file.name

        # 保存临时文件
        with open("temp_upload.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("📖 正在解析 PDF 文件..."):
            report_text = extract_text("temp_upload.pdf", max_pages=30)

        if not report_text:
            st.error("PDF 解析失败。可能原因：文件损坏、扫描件（无文字层）、或格式不兼容。请尝试其他 PDF 文件。")
            st.stop()

        st.session_state.report_text = report_text

        with st.spinner("🤖 正在提取财务指标..."):
            financial_data = extract_financial_data(report_text)

        if "error" in financial_data:
            st.error(f"财务数据提取失败：{financial_data.get('error', '未知错误')}")
            st.stop()

        st.session_state.financial_data = financial_data

        with st.spinner("🔍 正在检测异常信号..."):
            metrics = financial_data.get("core_metrics", {})
            st.session_state.anomalies = detect_by_rules(metrics)

    # ========== 渲染仪表板 ==========
    if st.session_state.financial_data:
        render_full_dashboard(
            st.session_state.financial_data,
            st.session_state.anomalies or []
        )

    # ========== 底部深入问答 ==========
    st.markdown("---")
    with st.expander("💬 深入问答（基于年报原文）"):
        user_question = st.text_input("输入你的问题", key="qa_input", placeholder="例如：这家公司的应收账款风险如何？")

        if user_question:
            context = ""
            if st.session_state.financial_data:
                context += f"财务数据摘要：\n{st.session_state.financial_data.get('core_metrics', {})}\n\n"
            if st.session_state.report_text:
                context += f"年报原文（前10000字符）：\n{st.session_state.report_text[:10000]}"

            with st.spinner("正在分析..."):
                answer = chat(
                    system="你是一个专业的金融分析师。请根据提供的年报数据回答用户问题。引用具体数据和证据。如果数据不足以回答，请明确说明。",
                    user_message=f"上下文信息：\n{context}\n\n用户问题：{user_question}",
                    temperature=0.3,
                    max_tokens=800
                )

            if answer.startswith("[LLM调用失败]"):
                st.error(f"AI 回答失败：{answer}")
            else:
                st.markdown(answer)

else:
    # ========== 空状态引导页 ==========
    st.markdown("""
    <div class="main-header">
        <h1 style="margin:0; font-size:1.8rem;">📊 财报深析 · AI 金融分析工作台</h1>
        <p style="margin:8px 0 0; opacity:0.85;">上传上市公司年报 PDF，30秒生成结构化分析仪表板</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### 📈 结构化提取
        自动识别 15+ 核心财务指标，包括营收、净利润、毛利率、ROE、EPS、现金流等。每个数据点附带原文引用，可追溯验证。
        """)

    with col2:
        st.markdown("""
        ### ⚠️ 异常检测
        规则引擎 + AI 双重校验，自动识别费用增速异常、利润现金流背离、毛利率下滑等风险信号，并提供通俗解读。
        """)

    with col3:
        st.markdown("""
        ### 💬 深度问答
        基于年报原文的智能问答，可追问具体业务细节、财务政策、风险因素等，获取即时有据可查的分析。
        """)

    st.markdown("---")
    st.info("👈 请在左侧边栏上传一份年报 PDF 开始分析。推荐使用茅台、五粮液等格式规范的 A 股年报。")

    st.markdown("""
    <div class="footer-bar">
        <strong>技术栈</strong>：DeepSeek V3 · Streamlit · Plotly · PyMuPDF · Pandas &nbsp;|&nbsp;
        数据本地处理，不上传任何服务器
    </div>
    """, unsafe_allow_html=True)

# ========== 底部状态栏 ==========
st.markdown("""
<div class="footer-bar">
    财报深析 v1.0 · DeepSeek V3 驱动 · 数据仅本地处理
</div>
""", unsafe_allow_html=True)
