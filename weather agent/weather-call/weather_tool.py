"""工具层：调用 Open-Meteo，返回天气数据。"""

from datetime import date as dt_date, timedelta

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
VALID_DATES = {"today", "tomorrow", "day_after_tomorrow"}
DATE_LABELS = {"today": "今天", "tomorrow": "明天", "day_after_tomorrow": "后天"}

WMO_CODES = {
    0: "晴", 1: "主要晴朗", 2: "部分多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "小毛毛雨", 53: "中毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    80: "小阵雨", 81: "中阵雨", 82: "大阵雨", 95: "雷阵雨",
}


def _weather_desc(code: int) -> str:
    return WMO_CODES.get(code, f"天气代码{code}")


def _need_umbrella(code: int, precip: float) -> bool:
    rainy_codes = set(range(51, 68)) | set(range(80, 83)) | {95}
    return precip > 0 or code in rainy_codes


def get_coordinates(city: str) -> dict:
    try:
        resp = requests.get(
            GEOCODING_URL,
            params={"name": city, "count": 1, "language": "zh"},
            timeout=5,
        )
        resp.raise_for_status()
        results = resp.json().get("results")
        if not results:
            return {"error": f"找不到城市：{city}"}
        loc = results[0]
        return {
            "name": loc["name"],
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "country": loc.get("country", ""),
        }
    except requests.Timeout:
        return {"error": "地理编码服务超时，请稍后重试"}
    except requests.RequestException as exc:
        return {"error": f"地理编码请求失败：{exc}"}


def get_weather(city: str, date: str) -> dict:
    date_key = date if date in VALID_DATES else "today"
    coords = get_coordinates(city)
    if "error" in coords:
        return coords

    try:
        resp = requests.get(
            FORECAST_URL,
            params={
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                "timezone": "auto",
                "forecast_days": 3,
            },
            timeout=5,
        )
        resp.raise_for_status()
        daily = resp.json().get("daily", {})
        dates = daily.get("time", [])
        if not dates:
            return {"error": f"无法获取 {city} 的天气数据"}

        target = dt_date.today()
        if date_key == "tomorrow":
            target += timedelta(days=1)
        elif date_key == "day_after_tomorrow":
            target += timedelta(days=2)

        target_str = target.isoformat()
        if target_str not in dates:
            return {"error": f"找不到日期 {target_str} 的预报数据"}

        idx = dates.index(target_str)
        weathercode = daily["weathercode"][idx]
        precip = daily["precipitation_sum"][idx]

        return {
            "city": coords["name"],
            "country": coords["country"],
            "date": target_str,
            "date_label": DATE_LABELS.get(date_key, target_str),
            "temperature_max": daily["temperature_2m_max"][idx],
            "temperature_min": daily["temperature_2m_min"][idx],
            "precipitation_mm": precip,
            "weather": _weather_desc(weathercode),
            "need_umbrella": _need_umbrella(weathercode, precip),
        }
    except requests.Timeout:
        return {"error": "天气服务超时，请稍后重试"}
    except requests.RequestException as exc:
        return {"error": f"天气请求失败：{exc}"}
