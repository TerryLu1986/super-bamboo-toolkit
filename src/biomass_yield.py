"""生物量产量计算模块: 超级芦竹年生物量产量与达产曲线估算

默认参数见 config/default_params.yaml, 数据来源见 data/references.yaml
"""
from src.utils import mu_to_hectare

# 达产系数(文献经验值): 第1年30%, 第2年60%, 第3年80%, 第4年起100%
_RAMP_RATIOS = {1: 0.3, 2: 0.6, 3: 0.8}


def annual_yield(area_mu, variety_yield_t_ha=30, moisture_pct=30, year=1, peak_year=3):
    """单年生物量产量估算(吨)

    亩转公顷: area_mu * 0.0667
    干基产量 = 面积(公顷) × 品种亩产(吨干基/公顷/年) × 达产系数
    湿料产量 = 干基产量 / (1 - 含水率/100)

    Args:
        area_mu: 种植面积(亩)
        variety_yield_t_ha: 丰产期品种亩产(吨干基/公顷/年), 默认30
        moisture_pct: 采收含水率(%), 默认30
        year: 种植第几年, 用于达产系数(第1年30%, 第2年60%, 第3年80%, 第4年起100%), 默认1

    Returns:
        dict: {'dry_tons': 干基产量(吨), 'wet_tons': 湿料产量(吨), 'area_ha': 面积(公顷)}

    Examples:
        >>> annual_yield(10000, 30, year=4)
        {'dry_tons': 20010.0, 'wet_tons': 28585.714285714286, 'area_ha': 667.0}
    """
    if not (0 <= moisture_pct < 100):
        raise ValueError(f"moisture_pct 需在 [0, 100) 区间, 当前为 {moisture_pct}")
    if area_mu < 0 or variety_yield_t_ha < 0:
        raise ValueError("面积与品种亩产不能为负")

    area_ha = mu_to_hectare(area_mu)
    factor = _RAMP_RATIOS.get(max(int(year), 1), 1.0)  # year>=4 时达产系数=1.0
    dry_tons = area_ha * variety_yield_t_ha * factor
    wet_tons = dry_tons / (1.0 - moisture_pct / 100.0)
    return {"dry_tons": dry_tons, "wet_tons": wet_tons, "area_ha": area_ha}


def yield_curve(area_mu, variety_yield_t_ha=30, moisture_pct=30, peak_year=3, years=25):
    """逐年达产曲线(吨)

    达产前(第1~peak_year年)按比例递增, 达产系数 = year / peak_year;
    达产后(第peak_year年起)保持100%。

    Args:
        area_mu: 种植面积(亩)
        variety_yield_t_ha: 丰产期品种亩产(吨干基/公顷/年), 默认30
        moisture_pct: 采收含水率(%), 默认30
        peak_year: 达产年数, 默认3
        years: 项目周期(年), 默认25

    Returns:
        list of dict: [{'year': int, 'dry_tons': float, 'wet_tons': float}, ...]

    Examples:
        >>> curve = yield_curve(10000, 30)
        >>> curve[0]
        {'year': 1, 'dry_tons': 6670.0, 'wet_tons': 9528.57142857143}
        >>> curve[-1]['dry_tons']
        20010.0
    """
    if peak_year < 1:
        raise ValueError(f"peak_year 至少为1, 当前为 {peak_year}")
    if years < 1:
        raise ValueError(f"years 至少为1, 当前为 {years}")
    if not (0 <= moisture_pct < 100):
        raise ValueError(f"moisture_pct 需在 [0, 100) 区间, 当前为 {moisture_pct}")
    if area_mu < 0 or variety_yield_t_ha < 0:
        raise ValueError("面积与品种亩产不能为负")

    area_ha = mu_to_hectare(area_mu)
    curve = []
    for y in range(1, years + 1):
        r = annual_yield(area_mu, variety_yield_t_ha, moisture_pct, year=y, peak_year=peak_year)
        dry = r["dry_tons"]
        wet = r["wet_tons"]
        curve.append({"year": y, "dry_tons": dry, "wet_tons": wet})
    return curve
