import yaml
from pathlib import Path
import requests
from requests import RequestException


def load_config_from_yaml(config_file):
    """从 YAML 文件加载配置"""
    try:
        with Path(config_file).open('r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        return {}


def send_request(
        method: str,
        url: str,
        function: str,
        headers: dict = None,
        params: dict = None,
        data: dict = None,
        json: dict = None,
        timeout: int = 60
) -> dict | str:
    valid_methods = ['GET', 'POST']
    if method.upper() not in valid_methods:
        return "错误请求"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            json=json,
            timeout=timeout
        )
        print(response.json())

    except RequestException:
        return function + "接口异常，请稍后重试"

    return response.json()