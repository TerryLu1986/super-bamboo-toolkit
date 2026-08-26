"""通用工具函数：配置加载与面积单位换算"""
import yaml
from pathlib import Path


def load_config(config_path=None):
    """加载默认参数配置（YAML）

    未指定路径时自动读取项目 config/default_params.yaml；
    文件不存在或格式非法时抛出 OSError / yaml.YAMLError。

    Args:
        config_path: 配置文件路径（str 或 pathlib.Path），None 时使用项目默认配置文件

    Returns:
        dict: 解析后的配置字典（嵌套结构：biomass / carbon / economics / seedling）
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "default_params.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def mu_to_hectare(area_mu):
    """亩转公顷：1 亩 = 0.0667 公顷

    Args:
        area_mu: 面积（亩）

    Returns:
        float: 面积（公顷）
    """
    return area_mu * 0.0667


def hectare_to_mu(area_ha):
    """公顷转亩：1 公顷 = 15 亩

    Args:
        area_ha: 面积（公顷）

    Returns:
        float: 面积（亩）
    """
    return area_ha * 15
