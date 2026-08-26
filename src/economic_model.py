"""经济效益模型: 原料销售、颗粒加工、综合年收益、投资回报与敏感性分析"""
from src.biomass_yield import annual_yield
from src.carbon_sequestration import annual_co2_sequestration, carbon_asset_value
from src.utils import load_config


def raw_material_revenue(tons_wet, price_per_ton=300):
    """原料直接销售收入(元)

    收入 = 湿料吨数 × 单价(元/吨)

    Args:
        tons_wet: 湿料产量(吨)
        price_per_ton: 原料单价(元/吨), 默认300

    Returns:
        float: 原料销售收入(元)
    """
    return float(tons_wet * price_per_ton)


def pellet_processing_revenue(tons_wet, pellet_price=800, conversion_rate=0.4, processing_cost=200):
    """生物质颗粒加工净收益(元)

    颗粒产量 = 湿料吨数 × 转化率
    净收益 = 颗粒产量 × 颗粒单价 - 湿料吨数 × 加工成本

    Args:
        tons_wet: 湿料产量(吨)
        pellet_price: 颗粒销售单价(元/吨), 默认800
        conversion_rate: 湿料→颗粒转化率, 默认0.4
        processing_cost: 颗粒加工成本(元/吨湿料), 默认200

    Returns:
        float: 颗粒加工净收益(元)
    """
    pellet_tons = tons_wet * conversion_rate
    net = pellet_tons * pellet_price - tons_wet * processing_cost
    return float(net)


def total_annual_revenue(area_mu, config=None):
    """综合年收益(元): 原料销售 + 碳资产

    Args:
        area_mu: 种植面积(亩)
        config: 参数配置dict, 不传则加载 config/default_params.yaml

    Returns:
        dict: {'raw_revenue': float, 'carbon_revenue': float, 'total': float}
    """
    if config is None:
        config = load_config()

    biomass = config.get("biomass", {})
    carbon = config.get("carbon", {})
    economics = config.get("economics", {})

    # 年产量: 湿料 + 干基
    _yield = annual_yield(
        area_mu,
        biomass.get("variety_yield_t_ha", 30),
        moisture_pct=biomass.get("moisture_pct", 30),
    )
    tons_wet = _yield["wet_tons"]
    tons_dry = _yield["dry_tons"]

    # 原料收益
    raw_revenue = raw_material_revenue(
        tons_wet, economics.get("wet_price_per_ton", 300)
    )

    # 碳资产收益: 固碳量(吨CO2) × 碳价
    co2_tons = annual_co2_sequestration(
        area_mu,
        tons_dry,
        carbon_content=carbon.get("carbon_content", 0.45),
        c_to_co2=carbon.get("c_to_co2", 3.67),
    )
    carbon_revenue = carbon_asset_value(
        co2_tons, carbon.get("co2_price_per_ton", 100)
    )

    return {
        "raw_revenue": float(raw_revenue),
        "carbon_revenue": float(carbon_revenue),
        "total": float(raw_revenue + carbon_revenue),
    }


def roi_analysis(total_investment, annual_revenue, annual_cost, years=25):
    """投资回报分析

    年净收益 = 年收入 - 年成本
    回本年数 = 总投资 / 年净收益
    累计收益(years年) = 年净收益 × years - 总投资

    Args:
        total_investment: 总投资(元)
        annual_revenue: 年收入(元)
        annual_cost: 年成本(元)
        years: 项目周期(年), 默认25

    Returns:
        dict: {'payback_years': float, 'net_profit_25y': float, 'annual_net': float}
    """
    annual_net = annual_revenue - annual_cost
    payback_years = total_investment / annual_net if annual_net > 0 else float("inf")
    net_profit = annual_net * years - total_investment
    return {
        "payback_years": float(payback_years),
        "net_profit_25y": float(net_profit),
        "annual_net": float(annual_net),
    }


def sensitivity_analysis(base_value, param_range=0.2, steps=5):
    """单参数敏感性分析: 以base_value为基准做±param_range等步长变动

    Args:
        base_value: 基准结果值(参数取基准值时的结果)
        param_range: 参数变动幅度(比例), 默认0.2(±20%)
        steps: 取样步数, 默认5

    Returns:
        list: [{'param_change': float, 'result': float}, ...]
    """
    results = []
    if steps < 1:
        raise ValueError(f"steps 至少为1, 当前为 {steps}")
    if steps == 1:
        return [{"param_change": 0.0, "result": float(base_value)}]
    for i in range(steps):
        change = -param_range + 2 * param_range * i / (steps - 1)
        results.append({
            "param_change": round(change, 6),
            "result": float(base_value * (1 + change)),
        })
    return results
