import yaml
from pathlib import Path

def load_config_from_yaml(config_file):
    """从 YAML 文件加载配置"""
    try:
        with Path(config_file).open('r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        return {}