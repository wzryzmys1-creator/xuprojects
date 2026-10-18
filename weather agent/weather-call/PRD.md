# 天气问答助手 PRD

## 一、产品概述

### 1.1 产品定位

一个运行在命令行的天气问答助手。用户用自然语言提问，助手自动查询真实天气数据后回答。

核心价值：以最少的代码展示 Function Call 的完整工作机制——LLM 自主决定何时调用工具、调用什么工具、传入什么参数，并根据返回结果生成最终回复。

### 1.2 目标用户

学习 AI Agent / Function Call 原理的开发者。

### 1.3 使用场景

```
$ python agent.py

你：明天上海天气怎么样，要带伞吗？
助手：明天上海有小雨，气温 16~22°C，建议带伞出门。

你：北京和广州哪个城市今天更热？
助手：今天广州气温 33°C，高于北京的 28°C，广州更热。

你：退出
助手：再见！
```

---

## 二、功能需求

### 2.1 MVP 功能

| 功能 | 描述 | 说明 |
|------|------|------|
| 自然语言问天气 | 用户用口语提问，不需要固定格式 | 核心功能 |
| 自动解析城市和日期 | LLM 从问题里提取城市名和日期意图 | 由 Function Call 机制完成 |
| 查询真实天气 | 调用 Open-Meteo API 获取真实数据 | 无需 API Key |
| 多城市对比 | 单次提问可同时查多个城市 | LLM 并行发起多个工具调用 |
| 多轮对话 | 保留对话历史，支持追问 | 维护 messages 列表即可 |
| 友好的中文回复 | 包含温度、天气状况、是否带伞等建议 | 由 LLM 组织语言 |

### 2.2 不在范围内

- Web UI 或移动端界面
- 用户账号 / 历史记录持久化
- 气象预警推送
- 超过 7 天的长期预报（Open-Meteo 免费版支持 16 天，但本项目只用近 3 天）

---

## 三、技术选型

| 模块 | 选型 | 理由 |
|------|------|------|
| 语言 | Python 3.10+ | 生态好，异步支持完整 |
| LLM | MiniMax-M2.5（通过 Anthropic SDK 兼容接口） | Tool Use 支持完整，已有可用密钥和接入地址 |
| 天气 API | Open-Meteo | 完全免费，无需注册和 API Key，JSON 返回 |
| 地理编码 | Open-Meteo Geocoding API | 城市名→坐标，和天气 API 同一服务商 |
| HTTP 请求 | requests | 简单够用，无需引入 httpx |
| 依赖管理 | pip + requirements.txt | 无需 Poetry 等重工具 |
| 环境变量 | python-dotenv | 管理 ANTHROPIC_AUTH_TOKEN 和 ANTHROPIC_BASE_URL |

**不引入的东西：** FastAPI、数据库、前端框架、LangChain。目标是最精简的代码量。

---

## 四、代码结构

```
weather/
├── requirements.txt      # 依赖声明
├── .env.example          # 环境变量模板
├── weather_tool.py       # 工具层：调用 Open-Meteo，返回天气数据
└── agent.py              # Agent 层：Function Call 主循环
```

共 2 个核心文件，约 130 行代码。

### 4.1 文件职责说明

**`weather_tool.py`** — 工具实现，与 LLM 无关

- `get_coordinates(city: str) -> dict`：城市名 → 经纬度，调用 Open-Meteo Geocoding API
- `get_weather(city: str, date: str) -> dict`：查指定城市和日期的天气，内部先调 `get_coordinates`，再调 Open-Meteo Forecast API
- 返回统一格式的字典，供 LLM 读取

**`agent.py`** — Agent 主循环，体现 Function Call 六步流程

- 定义工具声明（`TOOLS` 列表），对应第一步「工具声明」
- `chat()` 函数维护 `messages` 列表，每轮对话追加消息
- 循环检查 `stop_reason`：`"end_turn"` → 输出回复；`"tool_use"` → 执行工具，把结果追加回 `messages`，再次请求 LLM
- 支持单次请求里多个工具调用（多城市场景）

---

## 五、关键接口说明

### 5.1 Open-Meteo Geocoding API

```
GET https://geocoding-api.open-meteo.com/v1/search
  ?name=上海
  &count=1
  &language=zh
```

返回示例：
```json
{
  "results": [
    {
      "name": "上海",
      "latitude": 31.22,
      "longitude": 121.46,
      "country": "中国"
    }
  ]
}
```

### 5.2 Open-Meteo Forecast API

```
GET https://api.open-meteo.com/v1/forecast
  ?latitude=31.22
  &longitude=121.46
  &daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode
  &timezone=Asia/Shanghai
  &forecast_days=3
```

返回字段说明：

| 字段 | 含义 |
|------|------|
| `temperature_2m_max` | 当日最高气温（°C） |
| `temperature_2m_min` | 当日最低气温（°C） |
| `precipitation_sum` | 当日降水量（mm） |
| `weathercode` | WMO 天气代码（0=晴，61-67=雨，71-77=雪，等） |

### 5.3 工具声明（Function Call 核心）

```python
TOOLS = [
    {
        "name": "get_weather",
        "description": (
            "查询指定城市和日期的天气情况，包括温度、降水和天气状况。"
            "当用户询问天气、温度、是否带伞、城市天气对比时调用。"
            "可以同时为多个城市分别调用本工具。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，用中文或英文均可，如"上海"、"Beijing""
                },
                "date": {
                    "type": "string",
                    "description": (
                        "查询日期，支持以下值：\n"
                        "- \"today\"：今天\n"
                        "- \"tomorrow\"：明天\n"
                        "- \"day_after_tomorrow\"：后天\n"
                        "如果用户没有指定日期，默认填 \"today\""
                    )
                }
            },
            "required": ["city", "date"]
        }
    }
]
```

---

## 六、核心逻辑伪代码

```
启动 → 初始化 messages = [system_prompt]

loop:
    用户输入 → 追加到 messages
    调用 Claude API（携带 TOOLS 声明）

    if stop_reason == "end_turn":
        输出 LLM 回复
        继续等待下一轮用户输入

    if stop_reason == "tool_use":
        解析响应中所有 tool_use 块
        for each tool_call:
            执行 get_weather(city, date)
            把结果包装为 tool_result 追加到 messages
        再次调用 Claude API（不携带用户新输入，只把工具结果传回）
        输出 LLM 最终回复
```

---

## 七、错误处理策略

| 错误场景 | 处理方式 |
|----------|----------|
| 城市名找不到 | `get_weather` 返回 `{"error": "找不到城市：xxx"}` |
| Open-Meteo 请求超时 | `requests` 设置 `timeout=5`，超时返回错误信息 |
| 日期参数不合法 | `get_weather` 内部检查，不合法时默认返回今天数据 |
| ANTHROPIC_API_KEY 未设置 | 启动时检查环境变量，缺失时打印提示并退出 |
| LLM 返回异常 | 捕获 `anthropic.APIError`，打印错误后继续等待输入 |

所有错误均以字符串形式通过 `tool_result` 返回给 LLM，让 LLM 自行决定如何告知用户，不在工具层抛出异常。

---

## 八、环境配置

### 8.1 requirements.txt

```
anthropic>=0.40.0
requests>=2.31.0
python-dotenv>=1.0.0
```

### 8.2 .env.example

```
ANTHROPIC_AUTH_TOKEN=your_token_here
ANTHROPIC_BASE_URL=https://your_gateway_url
DEFAULT_LLM_MODEL=MiniMax-M2.5
```

### 8.3 启动步骤

```bash
cd weather
pip install -r requirements.txt
cp .env.example .env
# 在 .env 填入 ANTHROPIC_AUTH_TOKEN、ANTHROPIC_BASE_URL
python agent.py
```

---

## 九、验收标准

- [ ] 用中文自然语言问天气，能得到包含温度和天气状况的回答
- [ ] 问"要带伞吗"能正确判断是否有降水
- [ ] 问两个城市哪个更热，能同时查两个城市并对比
- [ ] 连续追问（如"那明天呢"）能保持上下文正确理解
- [ ] 城市名拼写错误时给出友好提示而不是报错崩溃
- [ ] 代码总行数不超过 150 行（不含注释和空行）
