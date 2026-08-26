"""种苗规划模块: 种苗需求量、分批种植计划与种苗成本估算"""
import math

from src.utils import load_config


def _seedling_defaults():
    """从 config/default_params.yaml 读取种苗默认参数

    读取失败或键缺失时回退到内置默认值，保证模块可独立运行。

    Returns:
        dict: 种苗默认参数字典，键为 density_per_mu / survival_rate /
              price_per_seedling / batch_size_mu / batch_interval_days
    """
    defaults = {
        "density_per_mu": 800,
        "survival_rate": 0.9,
        "price_per_seedling": 3.0,
        "batch_size_mu": 5000,
        "batch_interval_days": 30,
    }
    try:
        seedling_cfg = load_config().get("seedling", {})
        defaults.update(
            {key: value for key, value in seedling_cfg.items() if key in defaults}
        )
    except Exception:
        pass
    return defaults


_DEFAULTS = _seedling_defaults()


def seedling_demand(
    area_mu,
    density_per_mu=_DEFAULTS["density_per_mu"],
    survival_rate=_DEFAULTS["survival_rate"],
):
    """种苗总需求量(株)

    总需求量 = 面积(亩) × 定植密度(株/亩) / 成活率, 向上取整预留补栽余量。

    Args:
        area_mu: 种植面积(亩)
        density_per_mu: 定植密度(株/亩), 默认800
        survival_rate: 首年成活率, 默认0.9

    Returns:
        int: 种苗总需求量(株)
    """
    demand = area_mu * density_per_mu / survival_rate
    return math.ceil(demand)


def planting_schedule(
    area_mu,
    batch_size_mu=_DEFAULTS["batch_size_mu"],
    batch_interval_days=_DEFAULTS["batch_interval_days"],
):
    """分批种植计划

    批次数 = ceil(面积 / 每批面积), 每批需求量按 seedling_demand 计算,
    最后一批面积不足 batch_size_mu 时按实际剩余面积计算。

    Args:
        area_mu: 种植面积(亩)
        batch_size_mu: 每批种植面积(亩), 默认5000
        batch_interval_days: 批次间隔天数, 默认30

    Returns:
        list[dict]: [{'batch': int, 'area_mu': float, 'seedlings': int, 'start_day': int}, ...]
    """
    total_batches = math.ceil(area_mu / batch_size_mu)
    schedule = []
    remaining = area_mu
    for batch in range(1, total_batches + 1):
        batch_area = min(batch_size_mu, remaining)
        schedule.append(
            {
                "batch": batch,
                "area_mu": batch_area,
                "seedlings": seedling_demand(batch_area),
                "start_day": (batch - 1) * batch_interval_days,
            }
        )
        remaining -= batch_area
    return schedule


def seedling_cost(
    total_seedlings,
    price_per_seedling=_DEFAULTS["price_per_seedling"],
):
    """种苗总成本(元)

    总成本 = 种苗总量(株) × 种苗单价(元/株)

    Args:
        total_seedlings: 种苗总需求量(株)
        price_per_seedling: 种苗单价(元/株), 默认3.0

    Returns:
        float: 种苗总成本(元)
    """
    return total_seedlings * price_per_seedling


def full_plan(
    area_mu,
    density_per_mu=_DEFAULTS["density_per_mu"],
    survival_rate=_DEFAULTS["survival_rate"],
    price_per_seedling=_DEFAULTS["price_per_seedling"],
    batch_size_mu=_DEFAULTS["batch_size_mu"],
):
    """综合规划: 种苗需求 + 分批计划 + 成本

    Args:
        area_mu: 种植面积(亩)
        density_per_mu: 定植密度(株/亩), 默认800
        survival_rate: 首年成活率, 默认0.9
        price_per_seedling: 种苗单价(元/株), 默认3.0
        batch_size_mu: 每批种植面积(亩), 默认5000

    Returns:
        dict: {'total_demand': int, 'total_cost': float, 'batches': list, 'total_batches': int}
    """
    total_demand = seedling_demand(area_mu, density_per_mu, survival_rate)
    total_cost = seedling_cost(total_demand, price_per_seedling)
    batches = planting_schedule(area_mu, batch_size_mu)
    return {
        "total_demand": total_demand,
        "total_cost": total_cost,
        "batches": batches,
        "total_batches": len(batches),
    }
