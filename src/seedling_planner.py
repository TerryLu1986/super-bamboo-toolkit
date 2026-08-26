"""种苗规划模块: 种苗需求量、分批种植计划与种苗成本估算

默认参数从 config/default_params.yaml 的 seedling 段读取,
文件缺失或键缺失时回退到内置默认值, 保证模块可独立运行。
"""
import math

from src.utils import load_config

# 内置默认值(config 缺失时的回退)
_BUILTIN_DEFAULTS = {
    "density_per_mu": 800,
    "survival_rate": 0.9,
    "price_per_seedling": 3.0,
    "batch_size_mu": 5000,
    "batch_interval_days": 30,
}


def _param(key, override=None):
    """解析种苗参数: 显式传参 > config/default_params.yaml > 内置默认值"""
    if override is not None:
        return override
    try:
        cfg = load_config().get("seedling", {})
    except Exception:
        cfg = {}
    return cfg.get(key, _BUILTIN_DEFAULTS[key])


def seedling_demand_detail(area_mu, density_per_mu=None, survival_rate=None):
    """种苗需求明细：净定植需求 / 补栽余量 / 采购总量

    - 净定植需求 = 面积(亩) × 定植密度(株/亩)：按设计密度实际栽植的株数
    - 采购总量 = 净定植需求 / 首年成活率, 向上取整：含补栽余量,
      保证按成活率折损后存苗数仍达到设计密度
    - 补栽余量 = 采购总量 - 净定植需求

    Args:
        area_mu: 种植面积(亩, >=0)
        density_per_mu: 定植密度(株/亩), 默认取配置(内置800)
        survival_rate: 首年成活率(0, 1], 默认取配置(内置0.9)

    Returns:
        dict: {'net_demand': 净定植需求(株), 'replant_reserve': 补栽余量(株),
               'total_demand': 采购总量(株), 'density_per_mu': 定植密度,
               'survival_rate': 成活率}

    Raises:
        ValueError: 面积/密度为负或零、成活率不在(0,1]区间

    Example:
        >>> d = seedling_demand_detail(10000)
        >>> d['net_demand']
        8000000
        >>> d['total_demand']
        8888889
    """
    density_per_mu = _param("density_per_mu", density_per_mu)
    survival_rate = _param("survival_rate", survival_rate)
    if area_mu < 0:
        raise ValueError(f"面积不能为负, 当前为 {area_mu}")
    if density_per_mu <= 0:
        raise ValueError(f"定植密度需 > 0, 当前为 {density_per_mu}")
    if not (0 < survival_rate <= 1):
        raise ValueError(f"成活率需在 (0, 1] 区间, 当前为 {survival_rate}")
    net = math.ceil(area_mu * density_per_mu)
    total = math.ceil(area_mu * density_per_mu / survival_rate)
    return {
        "net_demand": net,
        "replant_reserve": total - net,
        "total_demand": total,
        "density_per_mu": density_per_mu,
        "survival_rate": survival_rate,
    }


def seedling_demand(area_mu, density_per_mu=None, survival_rate=None):
    """种苗采购总量(株)——含成活率补栽余量

    总需求量 = 面积(亩) × 定植密度(株/亩) / 成活率, 向上取整预留补栽余量;
    净定植需求与补栽余量的分项明细见 seedling_demand_detail()。

    Args:
        area_mu: 种植面积(亩, >=0)
        density_per_mu: 定植密度(株/亩), 默认取配置(内置800)
        survival_rate: 首年成活率(0, 1], 默认取配置(内置0.9)

    Returns:
        int: 种苗采购总量(株)

    Raises:
        ValueError: 面积/密度为负或零、成活率不在(0,1]区间
    """
    return seedling_demand_detail(area_mu, density_per_mu, survival_rate)["total_demand"]


def planting_schedule(area_mu, batch_size_mu=None, batch_interval_days=None):
    """分批种植计划

    批次数 = ceil(面积 / 每批面积), 每批需求量按 seedling_demand 计算,
    最后一批面积不足 batch_size_mu 时按实际剩余面积计算。

    Args:
        area_mu: 种植面积(亩, >=0)
        batch_size_mu: 每批种植面积(亩), 默认取配置(内置5000)
        batch_interval_days: 批次间隔天数, 默认取配置(内置30)

    Returns:
        list[dict]: [{'batch': int, 'area_mu': float, 'seedlings': int, 'start_day': int}, ...]

    Raises:
        ValueError: 面积为负或每批面积<=0
    """
    batch_size_mu = _param("batch_size_mu", batch_size_mu)
    batch_interval_days = _param("batch_interval_days", batch_interval_days)
    if area_mu < 0:
        raise ValueError(f"面积不能为负, 当前为 {area_mu}")
    if batch_size_mu <= 0:
        raise ValueError(f"每批种植面积需 > 0, 当前为 {batch_size_mu}")
    if batch_interval_days < 0:
        raise ValueError(f"批次间隔天数不能为负, 当前为 {batch_interval_days}")
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


def seedling_cost(total_seedlings, price_per_seedling=None):
    """种苗总成本(元)

    总成本 = 种苗总量(株) × 种苗单价(元/株)

    Args:
        total_seedlings: 种苗总需求量(株, >=0)
        price_per_seedling: 种苗单价(元/株), 默认取配置(内置3.0)

    Returns:
        float: 种苗总成本(元)

    Raises:
        ValueError: 数量为负或单价为负
    """
    price_per_seedling = _param("price_per_seedling", price_per_seedling)
    if total_seedlings < 0:
        raise ValueError(f"种苗数量不能为负, 当前为 {total_seedlings}")
    if price_per_seedling < 0:
        raise ValueError(f"种苗单价不能为负, 当前为 {price_per_seedling}")
    return total_seedlings * price_per_seedling


def full_plan(
    area_mu,
    density_per_mu=None,
    survival_rate=None,
    price_per_seedling=None,
    batch_size_mu=None,
):
    """综合规划: 种苗需求 + 分批计划 + 成本

    Args:
        area_mu: 种植面积(亩, >=0)
        density_per_mu: 定植密度(株/亩), 默认取配置(内置800)
        survival_rate: 首年成活率(0,1], 默认取配置(内置0.9)
        price_per_seedling: 种苗单价(元/株), 默认取配置(内置3.0)
        batch_size_mu: 每批种植面积(亩), 默认取配置(内置5000)

    Returns:
        dict: {'net_demand': 净定植需求(株), 'replant_reserve': 补栽余量(株),
               'total_demand': 采购总量(株), 'total_cost': float,
               'batches': list, 'total_batches': int,
               'density_per_mu': int, 'survival_rate': float}
    """
    detail = seedling_demand_detail(area_mu, density_per_mu, survival_rate)
    total_demand = detail["total_demand"]
    total_cost = seedling_cost(total_demand, price_per_seedling)
    batches = planting_schedule(area_mu, batch_size_mu)
    return {
        "net_demand": detail["net_demand"],
        "replant_reserve": detail["replant_reserve"],
        "total_demand": total_demand,
        "total_cost": total_cost,
        "batches": batches,
        "total_batches": len(batches),
        "density_per_mu": detail["density_per_mu"],
        "survival_rate": detail["survival_rate"],
    }
