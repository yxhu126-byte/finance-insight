from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, LLM_MODEL

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

def chat(system: str, user_message: str, temperature: float = 0.3, max_tokens: int = 2000) -> str:
    """统一的 LLM 调用封装。异常时返回 "[LLM调用失败] ..." 字符串。"""
    try:
        response = client.chat.completions.create(
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
