"""🎋 超级芦竹全产业链计算器 - Streamlit前端"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.biomass_yield import annual_yield, yield_curve
from src.carbon_sequestration import (
    annual_co2_sequestration,
    carbon_asset_value,
    comparison_with_forestry,
    soil_carbon_accumulation,
)
from src.economic_model import (
    raw_material_revenue,
    pellet_processing_revenue,
    roi_analysis,
)
from src.seedling_planner import seedling_demand, full_plan


def fmt(n, decimals=0):
    """千分位格式化"""
    if decimals == 0:
        return f"{n:,.0f}"
    return f"{n:,.{decimals}f}"


st.set_page_config(page_title="超级芦竹全产业链计算器", page_icon="🎋", layout="wide")
st.title("🎋 超级芦竹全产业链计算器")
st.caption("开源能源草全产业链计算工具 | 参数全部可配置 | 数据来源：公开学术文献")

# === 侧边栏参数 ===
st.sidebar.header("⚙️ 项目参数")

area_mu = st.sidebar.slider("种植面积（亩）", 1000, 100000, 10000, 1000)
variety_yield = st.sidebar.slider("品种亩产（吨干基/公顷/年）", 15, 45, 30)
moisture_pct = st.sidebar.slider("采收含水率（%）", 20, 50, 30)
peak_year = st.sidebar.slider("达产年数", 1, 5, 3)
project_years = st.sidebar.slider("项目周期（年）", 10, 30, 25)
co2_price = st.sidebar.slider("碳价（元/吨CO₂）", 50, 200, 100)
wet_price = st.sidebar.slider("湿料单价（元/吨）", 100, 500, 300)
seedling_density = st.sidebar.slider("定植密度（株/亩）", 400, 1200, 800)
seedling_price = st.sidebar.slider("种苗单价（元/株）", 1.0, 5.0, 3.0, 0.1)

st.sidebar.divider()
st.sidebar.markdown("📖 数据来源：IPCC指南、学术期刊、碳市场公开数据")
st.sidebar.markdown("🔗 [GitHub仓库](https://github.com/)")

# === 主页面 Tabs ===
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🌱 产量计算", "🌍 碳汇测算", "💰 经济效益", "🌿 种苗规划", "📊 综合报告"]
)

# --- Tab1: 产量计算 ---
with tab1:
    st.header("生物量产量计算")

    y_peak = annual_yield(area_mu, variety_yield, moisture_pct, year=peak_year + 1)

    col1, col2, col3 = st.columns(3)
    col1.metric("丰产期年干基产量", f"{fmt(y_peak['dry_tons'])} 吨")
    col2.metric("丰产期年湿料产量", f"{fmt(y_peak['wet_tons'])} 吨")
    col3.metric("种植面积", f"{fmt(area_mu)} 亩（{fmt(y_peak['area_ha'], 1)} 公顷）")

    st.subheader("达产曲线")
    curve = yield_curve(area_mu, variety_yield, moisture_pct, peak_year, project_years)
    df_curve = pd.DataFrame(curve)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_curve["year"],
            y=df_curve["dry_tons"],
            name="干基产量",
            line=dict(color="green", width=3),
            fill="tozeroy",
            fillcolor="rgba(0,128,0,0.1)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_curve["year"],
            y=df_curve["wet_tons"],
            name="湿料产量",
            line=dict(color="orange", width=2, dash="dash"),
        )
    )
    fig.update_layout(
        xaxis_title="种植年份",
        yaxis_title="产量（吨）",
        hovermode="x unified",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Tab2: 碳汇测算 ---
with tab2:
    st.header("碳汇价值测算")

    co2 = annual_co2_sequestration(area_mu, y_peak["dry_tons"])
    cv = carbon_asset_value(co2, co2_price)
    cf = comparison_with_forestry(area_mu, y_peak["dry_tons"])
    soil_c = soil_carbon_accumulation(area_mu, project_years)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("年固碳量", f"{fmt(co2)} 吨CO₂")
    col2.metric("碳资产价值", f"{fmt(cv)} 元/年")
    col3.metric("vs 林业碳汇", f"{cf['ratio']:.1f} 倍")
    col4.metric(f"{project_years}年土壤固碳", f"{fmt(soil_c)} 吨CO₂")

    st.subheader("芦竹 vs 传统林业碳汇对比")
    fig2 = go.Figure()
    fig2.add_trace(
        go.Bar(
            name="超级芦竹",
            x=["年固碳量（吨CO₂）", "碳资产价值（万元）"],
            y=[co2, cv / 10000],
            marker_color="green",
        )
    )
    fig2.add_trace(
        go.Bar(
            name="传统林业碳汇",
            x=["年固碳量（吨CO₂）", "碳资产价值（万元）"],
            y=[cf["forestry_co2"], cf["forestry_co2"] * co2_price / 10000],
            marker_color="brown",
        )
    )
    fig2.update_layout(barmode="group", height=400)
    st.plotly_chart(fig2, use_container_width=True)

# --- Tab3: 经济效益 ---
with tab3:
    st.header("经济效益分析")

    raw_rev = raw_material_revenue(y_peak["wet_tons"], wet_price)
    carbon_rev = carbon_asset_value(co2, co2_price)
    total_rev = raw_rev + carbon_rev

    col1, col2, col3 = st.columns(3)
    col1.metric("原料销售收入", f"{fmt(raw_rev)} 元/年")
    col2.metric("碳资产收益", f"{fmt(carbon_rev)} 元/年")
    col3.metric("综合年收益", f"{fmt(total_rev)} 元/年")

    st.subheader("投资回报分析")
    c1, c2 = st.columns(2)
    investment = c1.number_input("总投资额（万元）", value=5000, step=100) * 10000
    annual_cost = c2.number_input("年运营成本（万元）", value=500, step=50) * 10000

    roi = roi_analysis(investment, total_rev, annual_cost, project_years)

    col1, col2, col3 = st.columns(3)
    col1.metric("年净收益", f"{fmt(roi['annual_net'])} 元")
    col2.metric("回本周期", f"{roi['payback_years']:.1f} 年")
    col3.metric(f"{project_years}年累计净利", f"{fmt(roi['net_profit_25y'])} 元")

    st.subheader("敏感性分析（湿料单价 ±20%）")
    sens = []
    for pct in [-20, -10, 0, 10, 20]:
        price = wet_price * (1 + pct / 100)
        rev = raw_material_revenue(y_peak["wet_tons"], price) + carbon_rev
        sens.append({"价格变动": f"{pct:+d}%", "湿料单价": f"{price:.0f}元", "年收益（万元）": f"{rev/10000:.0f}"})
    st.table(pd.DataFrame(sens))

# --- Tab4: 种苗规划 ---
with tab4:
    st.header("种苗需求规划")

    plan = full_plan(area_mu, seedling_density, 0.9, seedling_price)

    col1, col2, col3 = st.columns(3)
    col1.metric("种苗总需求", f"{fmt(plan['total_demand'])} 株")
    col2.metric("种苗总成本", f"{fmt(plan['total_cost'])} 元")
    col3.metric("种植批次数", f"{plan['total_batches']} 批")

    st.subheader("分批种植计划")
    df_batch = pd.DataFrame(plan["batches"])
    df_batch.columns = ["批次", "面积（亩）", "种苗（株）", "起始天"]
    st.dataframe(df_batch, use_container_width=True, hide_index=True)

# --- Tab5: 综合报告 ---
with tab5:
    st.header("综合报告（可复制Markdown）")

    report = f"""# 超级芦竹全产业链项目测算报告

## 项目基本参数
- 种植面积：{fmt(area_mu)} 亩（{fmt(y_peak['area_ha'], 1)} 公顷）
- 品种亩产：{variety_yield} 吨干基/公顷/年
- 采收含水率：{moisture_pct}%
- 达产年数：{peak_year} 年
- 项目周期：{project_years} 年

## 产量测算（丰产期）
- 年干基产量：{fmt(y_peak['dry_tons'])} 吨
- 年湿料产量：{fmt(y_peak['wet_tons'])} 吨

## 碳汇价值
- 年固碳量：{fmt(co2)} 吨CO₂
- 碳资产价值：{fmt(cv)} 元/年（碳价{co2_price}元/吨）
- {project_years}年土壤固碳：{fmt(soil_c)} 吨CO₂
- vs传统林业碳汇：{cf['ratio']:.1f}倍

## 经济效益
- 原料销售收入：{fmt(raw_rev)} 元/年（湿料{wet_price}元/吨）
- 碳资产收益：{fmt(carbon_rev)} 元/年
- 综合年收益：{fmt(total_rev)} 元/年

## 投资回报
- 总投资额：{fmt(investment)} 元
- 年运营成本：{fmt(annual_cost)} 元
- 年净收益：{fmt(roi['annual_net'])} 元
- 回本周期：{roi['payback_years']:.1f} 年
- {project_years}年累计净利：{fmt(roi['net_profit_25y'])} 元

## 种苗规划
- 种苗需求：{fmt(plan['total_demand'])} 株（密度{seedling_density}株/亩）
- 种苗成本：{fmt(plan['total_cost'])} 元
- 种植批次：{plan['total_batches']} 批

---
*数据来源：IPCC指南、学术期刊、碳市场公开数据*
*计算工具：Super Bamboo Toolkit*
"""
    st.code(report, language="markdown")
    st.download_button("📥 下载报告", report, "super_bamboo_report.md", "text/markdown")
