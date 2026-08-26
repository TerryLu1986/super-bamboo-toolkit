"""经济效益模型: 原料销售、颗粒加工、综合年收益、投资回报(NPV/IRR)与敏感性分析"""
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

    口径说明: 适用于"自种原料自行加工"场景, 只扣加工成本,
    不扣原料机会成本(即未与直接售卖原料做对比); 若外购原料需自行加入原料成本。

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


def total_annual_revenue(area_mu, config=None, year=None):
    """综合年收益(元): 原料销售 + 碳资产

    Args:
        area_mu: 种植面积(亩)
        config: 参数配置dict, 不传则加载 config/default_params.yaml
        year: 计算年份(种植第几年); None 时取丰产期(第 peak_year+1 年,
            达产系数=1.0), 默认None

    Returns:
        dict: {'raw_revenue': float, 'carbon_revenue': float, 'total': float}
    """
    if config is None:
        config = load_config()

    biomass = config.get("biomass", {})
    carbon = config.get("carbon", {})
    economics = config.get("economics", {})
    peak_year = biomass.get("peak_year", 3)
    if year is None:
        year = peak_year + 1  # 丰产期

    _yield = annual_yield(
        area_mu,
        biomass.get("variety_yield_t_ha", 30),
        moisture_pct=biomass.get("moisture_pct", 30),
        year=year,
        peak_year=peak_year,
    )
    tons_wet = _yield["wet_tons"]
    tons_dry = _yield["dry_tons"]

    raw_revenue = raw_material_revenue(
        tons_wet, economics.get("wet_price_per_ton", 300)
    )

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
    """投资回报分析(静态, 不折现)

    年净收益 = 年收入 - 年成本
    静态回本年数 = 总投资 / 年净收益
    累计净利(years年) = 年净收益 × years - 总投资

    注意: 本函数为静态指标(不含资金时间价值),
    动态指标请用 npv_analysis()。

    Args:
        total_investment: 总投资(元)
        annual_revenue: 年收入(元)
        annual_cost: 年成本(元)
        years: 项目周期(年), 默认25

    Returns:
        dict: {'payback_years': float, 'net_profit_total': float, 'annual_net': float}
    """
    if years < 1:
        raise ValueError(f"years 至少为1, 当前为 {years}")
    annual_net = annual_revenue - annual_cost
    payback_years = total_investment / annual_net if annual_net > 0 else float("inf")
    net_profit = annual_net * years - total_investment
    return {
        "payback_years": float(payback_years),
        "net_profit_total": float(net_profit),
        "annual_net": float(annual_net),
    }


def npv_analysis(total_investment, annual_revenue, annual_cost, years=25, discount_rate=0.08):
    """净现值(NPV)与内部收益率(IRR)分析

    现金流假设: 期初一次性投入总投资, 此后每年年末产生等额净现金流
    (年收入-年成本), 持续 years 年。

    NPV = -总投资 + Σ 年净现金流 / (1+折现率)^t,  t = 1..years
    IRR = 使 NPV = 0 的折现率(二分法求解)

    Args:
        total_investment: 总投资(元)
        annual_revenue: 年收入(元)
        annual_cost: 年成本(元)
        years: 项目周期(年), 默认25
        discount_rate: 折现率, 默认0.08(8%)

    Returns:
        dict: {'npv': float, 'irr': float, 'discount_rate': float, 'annual_net': float}
            IRR 无解(如年净现金流<=0或投资为0)时为 float('nan')

    Examples:
        >>> res = npv_analysis(60, 30, 0, years=3, discount_rate=0.1)
        >>> round(res['npv'], 2)
        14.61
        >>> round(res['irr'], 3)
        0.234
    """
    if years < 1:
        raise ValueError(f"years 至少为1, 当前为 {years}")
    if discount_rate <= -1.0:
        raise ValueError(f"discount_rate 需 > -1, 当前为 {discount_rate}")
    annual_net = annual_revenue - annual_cost

    def _npv_at(rate):
        return -total_investment + sum(
            annual_net / (1 + rate) ** t for t in range(1, years + 1)
        )

    npv = _npv_at(discount_rate)

    # IRR: 二分法, 搜索区间 [-99%, 1000%]
    if total_investment <= 0 or annual_net <= 0:
        irr = float("nan")
    else:
        lo, hi = -0.99, 10.0
        f_lo, f_hi = _npv_at(lo), _npv_at(hi)
        if f_lo * f_hi > 0:
            irr = float("nan")
        else:
            mid = (lo + hi) / 2
            for _ in range(200):
                f_mid = _npv_at(mid)
                if abs(f_mid) < 1e-9 * max(1.0, abs(total_investment)):
                    break
                if f_lo * f_mid < 0:
                    hi, f_hi = mid, f_mid
                else:
                    lo, f_lo = mid, f_mid
                mid = (lo + hi) / 2
            irr = mid

    return {
        "npv": float(npv),
        "irr": float(irr),
        "discount_rate": float(discount_rate),
        "annual_net": float(annual_net),
    }


def sensitivity_analysis(base_value, param_range=0.2, steps=5):
    """单参数 ±% 变动下的结果情景表(等比例缩放)

    结果 = base_value × (1 + 参数变动比例), 即假设结果与参数线性相关
    (弹性=1)。适用于收入对单价/产量、成本对单价等线性关系;
    非线性关系(如IRR对投资额)请直接改变参数重新计算。

    Args:
        base_value: 基准结果值(参数取基准值时的结果)
        param_range: 参数变动幅度(比例), 默认0.2(±20%)
        steps: 取样点数, 默认5

    Returns:
        list: [{'param_change': float, 'result': float}, ...]

    Examples:
        >>> sensitivity_analysis(100, 0.2, 3)
        [{'param_change': -0.2, 'result': 80.0}, {'param_change': 0.0, 'result': 100.0}, {'param_change': 0.2, 'result': 120.0}]
    """
    if steps < 1:
        raise ValueError(f"steps 至少为1, 当前为 {steps}")
    if param_range < 0:
        raise ValueError(f"param_range 不能为负, 当前为 {param_range}")
    results = []
    if steps == 1:
        return [{"param_change": 0.0, "result": float(base_value)}]
    for i in range(steps):
        change = -param_range + 2 * param_range * i / (steps - 1)
        results.append({
            "param_change": round(change, 6),
            "result": float(base_value * (1 + change)),
        })
    return results
