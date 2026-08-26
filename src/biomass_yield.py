"""生物量产量计算模块: 超级芦竹年生物量产量与达产曲线估算

默认参数见 config/default_params.yaml, 数据来源见 data/references.yaml
"""
from src.utils import mu_to_hectare

# 达产曲线锚点(文献经验值, 以"达产进度 p=(年份-1)/(达产年数-1)"为横轴):
#   p=0(第1年)→30%, p=0.5→60%, p=1(达产当年)→100%
# 默认 peak_year=3 时即 30% / 60% / 100%: 第三年达到满产;
# 其他达产年数按锚点线性插值泛化。
_RAMP_ANCHORS = ((0.0, 0.3), (0.5, 0.6), (1.0, 1.0))


def _ramp_factor(year, peak_year):
    """达产系数: 按达产进度 p=(year-1)/(peak_year-1) 在锚点间线性插值

    Args:
        year: 种植第几年(>=1)
        peak_year: 达产年数(>=1), 第 peak_year 年系数即 1.0(当年满产);
                   peak_year=1 表示种植当年即满产

    Returns:
        float: (0, 1] 之间的达产系数
    """
    if peak_year <= 1:
        return 1.0  # 种植当年即满产
    p = (year - 1) / (peak_year - 1)
    if p >= 1.0:
        return 1.0
    for (p0, v0), (p1, v1) in zip(_RAMP_ANCHORS, _RAMP_ANCHORS[1:]):
        if p <= p1:
            return v0 + (v1 - v0) * (p - p0) / (p1 - p0)
    return 1.0


def annual_yield(area_mu, variety_yield_t_ha=30, moisture_pct=30, year=1, peak_year=3):
    """单年生物量产量估算(吨)

    亩转公顷: area_mu / 15 (1公顷=15亩)
    干基产量 = 面积(公顷) × 品种亩产(吨干基/公顷/年) × 达产系数
    湿料产量 = 干基产量 / (1 - 含水率/100)

    达产系数随 peak_year 泛化: 默认 peak_year=3 时为文献经验值
    (第1年30%, 第2年60%, 第3年即满产100%); 其他达产年数按锚点插值。

    Args:
        area_mu: 种植面积(亩)
        variety_yield_t_ha: 丰产期品种亩产(吨干基/公顷/年), 默认30
        moisture_pct: 采收含水率(%), 默认30
        year: 种植第几年(>=1), 用于达产系数, 默认1
        peak_year: 达产年数(>=1), 第 peak_year 年达产系数=1.0, 默认3

    Returns:
        dict: {'dry_tons': 干基产量(吨), 'wet_tons': 湿料产量(吨), 'area_ha': 面积(公顷)}

    Raises:
        ValueError: 参数越界(面积/亩产为负, 含水率不在[0,100), year/peak_year<1)

    Examples:
        >>> annual_yield(10000, 30, year=3)  # 第三年即满产
        {'dry_tons': 20000.0, 'wet_tons': 28571.428571428572, 'area_ha': 666.6666666666666}
    """
    if not (0 <= moisture_pct < 100):
        raise ValueError(f"moisture_pct 需在 [0, 100) 区间, 当前为 {moisture_pct}")
    if area_mu < 0 or variety_yield_t_ha < 0:
        raise ValueError("面积与品种亩产不能为负")
    year = int(year)
    peak_year = int(peak_year)
    if year < 1:
        raise ValueError(f"year 需 >= 1, 当前为 {year}")
    if peak_year < 1:
        raise ValueError(f"peak_year 需 >= 1, 当前为 {peak_year}")

    area_ha = mu_to_hectare(area_mu)
    factor = _ramp_factor(year, peak_year)
    dry_tons = area_ha * variety_yield_t_ha * factor
    wet_tons = dry_tons / (1.0 - moisture_pct / 100.0)
    return {"dry_tons": dry_tons, "wet_tons": wet_tons, "area_ha": area_ha}


def yield_curve(area_mu, variety_yield_t_ha=30, moisture_pct=30, peak_year=3, years=25):
    """逐年达产曲线(吨)

    每年产量由 annual_yield(year=y, peak_year=peak_year) 计算:
    达产进度 p=(y-1)/(peak_year-1) 在锚点(30%/60%/100%)间线性插值,
    第 peak_year 年即达 100% 丰产并保持。

    Args:
        area_mu: 种植面积(亩)
        variety_yield_t_ha: 丰产期品种亩产(吨干基/公顷/年), 默认30
        moisture_pct: 采收含水率(%), 默认30
        peak_year: 达产年数(>=1), 默认3
        years: 项目周期(年, >=1), 默认25

    Returns:
        list of dict: [{'year': int, 'dry_tons': float, 'wet_tons': float}, ...]

    Raises:
        ValueError: 参数越界(同 annual_yield, 另含 years<1)

    Examples:
        >>> curve = yield_curve(10000, 30)
        >>> curve[0]
        {'year': 1, 'dry_tons': 6000.0, 'wet_tons': 8571.428571428572}
        >>> curve[-1]['dry_tons']
        20000.0
    """
    if peak_year < 1:
        raise ValueError(f"peak_year 至少为1, 当前为 {peak_year}")
    if years < 1:
        raise ValueError(f"years 至少为1, 当前为 {years}")
    if not (0 <= moisture_pct < 100):
        raise ValueError(f"moisture_pct 需在 [0, 100) 区间, 当前为 {moisture_pct}")
    if area_mu < 0 or variety_yield_t_ha < 0:
        raise ValueError("面积与品种亩产不能为负")

    curve = []
    for y in range(1, int(years) + 1):
        r = annual_yield(area_mu, variety_yield_t_ha, moisture_pct, year=y, peak_year=peak_year)
        curve.append({"year": y, "dry_tons": r["dry_tons"], "wet_tons": r["wet_tons"]})
    return curve
