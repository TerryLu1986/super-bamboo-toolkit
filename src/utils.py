"""通用工具函数"""
import yaml
from pathlib import Path


def load_config(config_path=None):
    """加载默认参数配置"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "default_params.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def mu_to_hectare(area_mu):
    """亩转公顷: 1亩 = 0.0667公顷"""
    return area_mu * 0.0667


def hectare_to_mu(area_ha):
    """公顷转亩: 1公顷 = 15亩"""
    return area_ha * 15
