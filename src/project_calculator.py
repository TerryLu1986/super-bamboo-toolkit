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
from src.economic_model import pellet_processing_revenue, raw_material_revenue, roi_analysis
from src.seedling_planner import full_plan


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
    # ---- 产量：以 peak_year+1 年计算丰产期产量（此时达产系数=1.0）----
    y_peak = annual_yield(area_mu, variety_yield, moisture_pct, year=peak_year + 1)

    # ---- 碳汇测算 ----
    co2 = annual_co2_sequestration(area_mu, y_peak["dry_tons"])
    cv = carbon_asset_value(co2, co2_price)
    cf = comparison_with_forestry(area_mu, y_peak["dry_tons"])
    soil_c = soil_carbon_accumulation(area_mu, project_years)

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


def build_report(r, investment=None, annual_cost=None):
    """生成 Markdown 格式的综合项目报告（命令行与前端 Tab5 共用）

    Args:
        r: compute_all() 返回的结果字典
        investment: 总投资额（元），None 时使用默认 5000 万元
        annual_cost: 年运营成本（元），None 时使用默认 500 万元

    Returns:
        str: Markdown 格式的完整报告文本（可直接复制或写入文件）
    """
    if investment is None:
        investment = 50_000_000
    if annual_cost is None:
        annual_cost = 5_000_000

    roi = roi_analysis(investment, r["total_rev"], annual_cost, r["project_years"])
    y_peak = r["y_peak"]
    plan = r["plan"]

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
- 年固碳量：{fmt(r['co2'])} 吨CO₂
- 碳资产价值：{fmt(r['cv'])} 元/年（碳价 {r['co2_price']} 元/吨）
- {r['project_years']} 年土壤固碳：{fmt(r['soil_c'])} 吨CO₂
- vs 传统林业碳汇：{r['cf']['ratio']:.1f} 倍

## 经济效益
- 原料销售收入：{fmt(r['raw_rev'])} 元/年（湿料 {r['wet_price']} 元/吨）
- 碳资产收益：{fmt(r['carbon_rev'])} 元/年
- 综合年收益：{fmt(r['total_rev'])} 元/年
- 颗粒加工净收益（可选深加工）：{fmt(r['pellet_rev'])} 元/年

## 投资回报
- 总投资额：{fmt(investment)} 元
- 年运营成本：{fmt(annual_cost)} 元
- 年净收益：{fmt(roi['annual_net'])} 元
- 回本周期：{roi['payback_years']:.1f} 年
- {r['project_years']} 年累计净利：{fmt(roi['net_profit_25y'])} 元

## 种苗规划
- 种苗需求：{fmt(plan['total_demand'])} 株（密度 {r['seedling_density']} 株/亩）
- 种苗成本：{fmt(plan['total_cost'])} 元
- 种植批次：{plan['total_batches']} 批

---
*数据来源：IPCC指南、学术期刊、碳市场公开数据*
*计算工具：Super Bamboo Toolkit*
"""
    return report
