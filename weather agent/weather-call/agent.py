"""天气查询助手：通过兼容 OpenAI Chat Completions 的网关调用模型。"""

import json
import os
import sys

import requests
from dotenv import load_dotenv

from weather_tool import get_weather


load_dotenv()

TOOLS = [
    {
        "name": "get_weather",
        "description": (
            "查询指定城市和日期的天气情况，包括温度、降水和天气状况。"
            "当用户询问天气、温度、是否带伞或城市天气对比时调用。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，例如上海或 Beijing。",
                },
                "date": {
                    "type": "string",
                    "enum": ["today", "tomorrow", "day_after_tomorrow"],
                    "description": "查询日期。未指定日期时使用 today。",
                },
            },
            "required": ["city", "date"],
        },
    }
]

OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["input_schema"],
        },
    }
    for tool in TOOLS
]

SYSTEM_PROMPT = (
    "你是天气问答助手，用简洁友好的中文回答用户的天气问题。"
    "需要天气数据时必须调用 get_weather 工具。"
    "回答时包含温度范围和天气状况；如果用户问是否带伞，根据降水情况给出建议。"
)


def run_tool(name: str, tool_input: dict) -> str:
    if name == "get_weather":
        result = get_weather(**tool_input)
    else:
        result = {"error": f"未知工具：{name}"}
    return json.dumps(result, ensure_ascii=False)


def call_llm(token: str, base_url: str, model: str, messages: list) -> dict:
    """调用网关的 OpenAI 兼容接口。"""
    response = requests.post(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 1024,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                *messages,
            ],
            "tools": OPENAI_TOOLS,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def handle_response(
    token: str, base_url: str, model: str, messages: list, response: dict
) -> str:
    """执行模型返回的工具调用，直到得到最终文本回复。"""
    while True:
        message = response["choices"][0]["message"]
        tool_calls = message.get("tool_calls") or []

        assistant_message = {"role": "assistant"}
        if message.get("content") is not None:
            assistant_message["content"] = message["content"]
        if tool_calls:
            assistant_message["tool_calls"] = tool_calls
        messages.append(assistant_message)

        if not tool_calls:
            return message.get("content") or "（无文本回复）"

        for tool_call in tool_calls:
            function = tool_call["function"]
            try:
                tool_input = json.loads(function.get("arguments", "{}"))
                tool_output = run_tool(function["name"], tool_input)
            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                tool_output = json.dumps(
                    {"error": f"工具参数格式错误：{exc}"},
                    ensure_ascii=False,
                )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_output,
                }
            )

        response = call_llm(token, base_url, model, messages)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")

    token = os.getenv("ANTHROPIC_AUTH_TOKEN")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    model = os.getenv("DEFAULT_LLM_MODEL", "MiniMax-M2.5")

    if not token:
        print("错误：请设置环境变量 ANTHROPIC_AUTH_TOKEN")
        sys.exit(1)
    if not base_url:
        print("错误：请设置环境变量 ANTHROPIC_BASE_URL")
        sys.exit(1)

    messages = []
    print("天气问答助手（输入“退出”结束）\n")

    while True:
        try:
            user_input = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n助手：再见！")
            break

        if not user_input:
            continue
        if user_input.lower() in {"退出", "exit", "quit", "q"}:
            print("助手：再见！")
            break

        messages.append({"role": "user", "content": user_input})
        try:
            response = call_llm(token, base_url, model, messages)
            reply = handle_response(token, base_url, model, messages, response)
            print(f"助手：{reply}\n")
        except requests.RequestException as exc:
            detail = (
                exc.response.text
                if exc.response is not None and exc.response.text
                else str(exc)
            )
            print(f"助手：请求失败（{detail}）\n")
            messages.pop()


if __name__ == "__main__":
    main()
