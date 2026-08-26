"""项目级计算编排模块：汇总产量、碳汇、经济、种苗四大子模块并生成综合报告

本模块是整个工具箱的「计算中枢」，同时被 Streamlit 前端（app/streamlit_app.py）
与命令行工具（src/cli.py）复用，保证两端的计算结果与报告格式完全一致。

主要公开函数：
- compute_all(): 一次完成全部指标计算，返回统一结果字典
- build_report(): 基于结果字典生成 Markdown 格式的综合报告（与前端 Tab5 一致）
- fmt(): 千分位数字格式化工具
"""
from src.biomass_yield import annual_yield, yield_curve
from src.carbon_sequestration import (
    annual_co2_sequestration,
    carbon_asset_value,
    comparison_with_forestry,
    soil_carbon_accumulation,
)
from src.economic_model import (
    npv_analysis,
    pellet_processing_revenue,
    raw_material_revenue,
    roi_analysis,
)
from src.seedling_planner import full_plan
from src.utils import load_config


def fmt(n, decimals=0):
    """千分位格式化数字

    Args:
        n: 待格式化的数值（int 或 float）
        decimals: 保留的小数位数，默认 0（输出整数千分位）

    Returns:
        str: 千分位分组后的数字字符串，例如 fmt(1234567) -> "1,234,567"
    """
    if decimals == 0:
        return f"{n:,.0f}"
    return f"{n:,.{decimals}f}"


def _cfg_value(section, key, fallback):
    """从 config/default_params.yaml 读取参数, 失败回退内置默认值"""
    try:
        return load_config().get(section, {}).get(key, fallback)
    except Exception:
        return fallback


def compute_all(
    area_mu=10000,
    variety_yield=30,
    moisture_pct=30,
    peak_year=3,
    project_years=25,
    co2_price=100,
    wet_price=300,
    seedling_density=800,
    seedling_price=3.0,
    survival_rate=0.9,
    soil_c_rate=None,
    forestry_c_rate=None,
    discount_rate=None,
):
    """汇总计算全产业链核心指标（产量 / 碳汇 / 经济 / 种苗）

    Args:
        area_mu: 种植面积（亩），默认 10000
        variety_yield: 品种亩产（吨干基/公顷/年），默认 30
        moisture_pct: 采收含水率（%），默认 30
        peak_year: 达产年数，默认 3
        project_years: 项目周期（年），默认 25
        co2_price: 碳价（元/吨CO₂），默认 100
        wet_price: 湿料单价（元/吨），默认 300
        seedling_density: 定植密度（株/亩），默认 800
        seedling_price: 种苗单价（元/株），默认 3.0
        survival_rate: 首年成活率，默认 0.9
        soil_c_rate: 年土壤固碳率（吨CO2/公顷/年），None 时读配置（缺省2.0）
        forestry_c_rate: 对比用林业年固碳率（吨CO2/亩/年），None 时读配置（缺省0.5）
        discount_rate: 折现率，None 时读配置（缺省0.08）

    Returns:
        dict: 统一结果字典，包含以下键：
            - 参数回显: area_mu, variety_yield, moisture_pct, peak_year,
              project_years, co2_price, wet_price, seedling_density, seedling_price
            - 产量: y_peak(dict: dry_tons/wet_tons/area_ha), curve(逐年产量列表)
            - 碳汇: co2(年固碳吨数), cv(碳资产价值), cf(与林业对比字典), soil_c(土壤固碳)
            - 经济: raw_rev(原料收入), carbon_rev(碳资产收益), total_rev(综合年收益),
              pellet_rev(颗粒加工净收益)
            - 种苗: plan(种苗综合规划字典)
    """
    if soil_c_rate is None:
        soil_c_rate = _cfg_value("carbon", "soil_c_rate_t_ha", 2.0)
    if forestry_c_rate is None:
        forestry_c_rate = _cfg_value("carbon", "forestry_c_rate_t_mu", 0.5)
    if discount_rate is None:
        discount_rate = _cfg_value("economics", "discount_rate", 0.08)

    # ---- 产量：以 peak_year+1 年计算丰产期产量（此时达产系数=1.0）----
    y_peak = annual_yield(area_mu, variety_yield, moisture_pct, year=peak_year + 1)

    # ---- 碳汇测算 ----
    co2 = annual_co2_sequestration(area_mu, y_peak["dry_tons"])
    cv = carbon_asset_value(co2, co2_price)
    cf = comparison_with_forestry(area_mu, y_peak["dry_tons"], forestry_c_rate)
    soil_c = soil_carbon_accumulation(area_mu, project_years, soil_c_rate)

    # ---- 经济效益 ----
    raw_rev = raw_material_revenue(y_peak["wet_tons"], wet_price)
    carbon_rev = cv
    total_rev = raw_rev + carbon_rev
    pellet_rev = pellet_processing_revenue(y_peak["wet_tons"])

    # ---- 种苗规划 ----
    plan = full_plan(area_mu, seedling_density, survival_rate, seedling_price)

    # ---- 达产曲线（逐年产量）----
    curve = yield_curve(area_mu, variety_yield, moisture_pct, peak_year, project_years)

    return {
        # 参数回显（供报告与图表标题使用）
        "area_mu": area_mu,
        "variety_yield": variety_yield,
        "moisture_pct": moisture_pct,
        "peak_year": peak_year,
        "project_years": project_years,
        "co2_price": co2_price,
        "wet_price": wet_price,
        "seedling_density": seedling_density,
        "seedling_price": seedling_price,
        "soil_c_rate": soil_c_rate,
        "forestry_c_rate": forestry_c_rate,
        "discount_rate": discount_rate,
        # 产量
        "y_peak": y_peak,
        "curve": curve,
        # 碳汇
        "co2": co2,
        "cv": cv,
        "cf": cf,
        "soil_c": soil_c,
        # 经济
        "raw_rev": raw_rev,
        "carbon_rev": carbon_rev,
        "total_rev": total_rev,
        "pellet_rev": pellet_rev,
        # 种苗
        "plan": plan,
    }


def build_report(r, investment=None, annual_cost=None, discount_rate=None):
    """生成 Markdown 格式的综合项目报告（命令行与前端 Tab5 共用）

    Args:
        r: compute_all() 返回的结果字典
        investment: 总投资额（元），None 时使用默认 5000 万元
        annual_cost: 年运营成本（元），None 时使用默认 500 万元
        discount_rate: 折现率，None 时使用 r['discount_rate']

    Returns:
        str: Markdown 格式的完整报告文本（可直接复制或写入文件）
    """
    if investment is None:
        investment = 50_000_000
    if annual_cost is None:
        annual_cost = 5_000_000
    if discount_rate is None:
        discount_rate = r.get("discount_rate", 0.08)

    roi = roi_analysis(investment, r["total_rev"], annual_cost, r["project_years"])
    npv = npv_analysis(
        investment, r["total_rev"], annual_cost, r["project_years"], discount_rate
    )
    y_peak = r["y_peak"]
    plan = r["plan"]
    irr_pct = f"{npv['irr']:.1%}" if npv["irr"] == npv["irr"] else "无解"

    report = f"""# 超级芦竹全产业链项目测算报告

## 项目基本参数
- 种植面积：{fmt(r['area_mu'])} 亩（{fmt(y_peak['area_ha'], 1)} 公顷）
- 品种亩产：{r['variety_yield']} 吨干基/公顷/年
- 采收含水率：{r['moisture_pct']}%
- 达产年数：{r['peak_year']} 年
- 项目周期：{r['project_years']} 年

## 产量测算（丰产期）
- 年干基产量：{fmt(y_peak['dry_tons'])} 吨
- 年湿料产量：{fmt(y_peak['wet_tons'])} 吨

## 碳汇价值
- 年固碳量（毛固碳通量）：{fmt(r['co2'])} 吨CO₂
- 碳资产价值：{fmt(r['cv'])} 元/年（碳价 {r['co2_price']} 元/吨）
- {r['project_years']} 年土壤固碳：{fmt(r['soil_c'])} 吨CO₂
- vs 传统林业碳汇：{r['cf']['ratio']:.1f} 倍（对比基准 {r.get('forestry_c_rate', 0.5)} 吨CO₂/亩/年）

## 经济效益
- 原料销售收入：{fmt(r['raw_rev'])} 元/年（湿料 {r['wet_price']} 元/吨）
- 碳资产收益：{fmt(r['carbon_rev'])} 元/年
- 综合年收益：{fmt(r['total_rev'])} 元/年
- 颗粒加工净收益（可选深加工）：{fmt(r['pellet_rev'])} 元/年

## 投资回报
- 总投资额：{fmt(investment)} 元
- 年运营成本：{fmt(annual_cost)} 元
- 年净收益：{fmt(roi['annual_net'])} 元
- 静态回本周期：{roi['payback_years']:.1f} 年
- 净现值 NPV（折现率 {discount_rate:.0%}）：{fmt(npv['npv'])} 元
- 内部收益率 IRR：{irr_pct}
- {r['project_years']} 年累计净利（静态）：{fmt(roi['net_profit_total'])} 元

## 种苗规划
- 种苗需求：{fmt(plan['total_demand'])} 株（密度 {r['seedling_density']} 株/亩）
- 种苗成本：{fmt(plan['total_cost'])} 元
- 种植批次：{plan['total_batches']} 批

---
*数据来源：IPCC指南、学术期刊、碳市场公开数据*
*计算工具：Super Bamboo Toolkit*

⚠️ **碳汇口径说明**：地上生物量固碳为年度循环碳通量，原料能源化利用后将重新排放；
长期净碳汇以地下根系与土壤固碳为主。碳资产可交易性以官方方法学（如CCER）审定为准。
本报告为参数化估算，不构成投资建议。
"""
    return report


def tornado_npv(r, investment=50_000_000.0, annual_cost=5_000_000.0, swing=0.2):
    """多因素敏感性分析（龙卷风图数据源）

    对六个关键参数分别施加 ±swing 扰动（其余保持基准值），重算全链条 NPV，
    返回各因素对 NPV 的影响幅度，按影响大小降序排列：

    - 亩产（variety_yield）：影响产量 → 原料收入 + 碳资产收益
    - 湿料单价（wet_price）：影响原料收入
    - 碳价（co2_price）：影响碳资产收益
    - 折现率（discount_rate）：影响资金时间价值
    - 总投资（investment）：影响初始现金流
    - 年运营成本（annual_cost）：影响逐年净现金流

    Args:
        r: compute_all() 返回的基准结果字典（基准参数取其中的回显值）
        investment: 基准总投资额（元）
        annual_cost: 基准年运营成本（元）
        swing: 扰动幅度，默认 0.2（即 ±20%）

    Returns:
        dict: {"base_npv": 基准NPV(元),
               "factors": [{"name", "low", "high", "low_delta", "high_delta", "impact"}, ...]}
              low/high 为该参数取 -swing/+swing 时的 NPV，delta 为相对基准的变化量，
              impact = max(|low_delta|, |high_delta|)，factors 按 impact 降序。

    Example:
        >>> t = tornado_npv(compute_all(area_mu=1000), 5_000_000, 500_000)
        >>> len(t["factors"])
        6
        >>> t["factors"][0]["impact"] >= t["factors"][-1]["impact"]
        True
    """
    years = r["project_years"]
    dr = r["discount_rate"]
    base_rev = r["total_rev"]

    def npv_of(rev, inv=investment, cost=annual_cost, rate=dr):
        return npv_analysis(inv, rev, cost, years, rate)["npv"]

    def rev_with(**over):
        """在基准参数上覆盖个别参数后重算综合年收益"""
        base = dict(
            area_mu=r["area_mu"],
            variety_yield=r["variety_yield"],
            moisture_pct=r["moisture_pct"],
            peak_year=r["peak_year"],
            project_years=years,
        )
        base.update(over)
        return compute_all(**base)["total_rev"]

    base_npv = npv_of(base_rev)
    factors = []

    # 产量侧参数：扰动后需重算收益链
    for name, key in (("亩产", "variety_yield"), ("湿料单价", "wet_price"), ("碳价", "co2_price")):
        v = r[key]
        low = npv_of(rev_with(**{key: v * (1 - swing)}))
        high = npv_of(rev_with(**{key: v * (1 + swing)}))
        factors.append((name, low, high))

    # 折现率：收益不变，只改资金时间价值
    low = npv_of(base_rev, rate=dr * (1 - swing))
    high = npv_of(base_rev, rate=dr * (1 + swing))
    factors.append(("折现率", low, high))

    # 投资与运营成本：直接作用于 NPV 输入
    factors.append(("总投资",
                    npv_of(base_rev, inv=investment * (1 - swing)),
                    npv_of(base_rev, inv=investment * (1 + swing))))
    factors.append(("年运营成本",
                    npv_of(base_rev, cost=annual_cost * (1 - swing)),
                    npv_of(base_rev, cost=annual_cost * (1 + swing))))

    rows = [
        {
            "name": name,
            "low": low,
            "high": high,
            "low_delta": low - base_npv,
            "high_delta": high - base_npv,
            "impact": max(abs(low - base_npv), abs(high - base_npv)),
        }
        for name, low, high in factors
    ]
    rows.sort(key=lambda x: x["impact"], reverse=True)
    return {"base_npv": base_npv, "factors": rows}
