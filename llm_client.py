from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, LLM_MODEL

_client = None


def _get_client():
    """延迟初始化客户端 — 首次调用时从 st.secrets 或 .env 读取密钥。"""
    global _client
    if _client is not None:
        return _client

    api_key = DEEPSEEK_API_KEY
    base_url = DEEPSEEK_BASE_URL

    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            api_key = st.secrets.get("DEEPSEEK_API_KEY", api_key)
            base_url = st.secrets.get("DEEPSEEK_BASE_URL", base_url)
    except Exception:
        pass

    _client = OpenAI(api_key=api_key, base_url=base_url)
    return _client


def chat(system: str, user_message: str, temperature: float = 0.3, max_tokens: int = 2000) -> str:
    """统一的 LLM 调用封装。异常时返回 "[LLM调用失败] ..." 字符串。"""
    try:
        response = _get_client().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=60
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[LLM调用失败] {str(e)}"
