"""🎋 超级芦竹全产业链计算器 - Streamlit 前端

页面结构：
- 侧边栏：全部项目参数（面积、品种亩产、含水率、碳价、湿料单价、种苗参数等）
- 项目概览：Tab 上方的 4 张关键数据大卡片（面积 / 丰产期产量 / 年固碳 / 综合年收益）
- 五个功能 Tab：产量计算 / 碳汇测算 / 经济效益 / 种苗规划 / 综合报告

实现说明：
- 所有计算委托给 src.project_calculator.compute_all()，与命令行工具共用同一套逻辑
- 图表统一使用绿色系主题，中文标题，hover 展示详细数值
- 敏感性分析使用 Plotly 柱状图（替代原 st.table）
- main() 仅在作为主脚本运行时执行（streamlit run 亦满足），因此本模块可被安全 import
"""
import sys
from pathlib import Path

# 将项目根目录插入模块搜索路径，保证从任意工作目录启动均可导入 src 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.economic_model import raw_material_revenue, roi_analysis
from src.project_calculator import build_report, compute_all, fmt

# ==================== 绿色系主题色板 ====================
GREEN_THEME = {
    "primary": "#2E7D32",    # 主色：深绿
    "secondary": "#66BB6A",  # 次色：中绿
    "light": "#A5D6A7",      # 浅绿（对比 / 辅助）
    "dark": "#1B5E20",       # 强调：墨绿
    "fill": "rgba(46,125,50,0.12)",  # 面积填充：半透明绿
}


def apply_green_theme(fig, title, x_title="", y_title="", height=420, hovermode="x unified"):
    """为 Plotly 图表统一套用绿色系主题（中文标题 + 布局 + hover 模式）

    Args:
        fig: plotly.graph_objects.Figure 图表对象（原地修改）
        title: 图表标题（中文）
        x_title: X 轴标题（中文），默认空字符串
        y_title: Y 轴标题（中文），默认空字符串
        height: 图表高度（像素），默认 420
        hovermode: hover 模式，默认 "x unified"（按 X 轴统一展示）；饼图传 False

    Returns:
        plotly.graph_objects.Figure: 应用主题后的图表对象
    """
    fig.update_layout(
        title=dict(text=title, x=0.02, font=dict(size=18, color=GREEN_THEME["dark"])),
        xaxis_title=x_title,
        yaxis_title=y_title,
        hovermode=hovermode,
        height=height,
        margin=dict(l=60, r=30, t=60, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        plot_bgcolor="rgba(0,0,0,0)",   # 透明绘图区
        paper_bgcolor="rgba(0,0,0,0)",  # 透明画布
        font=dict(family="Microsoft YaHei, PingFang SC, Noto Sans CJK SC, sans-serif"),
    )
    return fig


# ==================== 各 Tab 渲染函数 ====================

def render_yield_tab(r):
    """Tab1 渲染：生物量产量计算与达产曲线

    Args:
        r: compute_all() 返回的结果字典
    """
    st.header("🌱 生物量产量计算")

    # 关键数据卡片
    col1, col2, col3 = st.columns(3)
    col1.metric("丰产期年干基产量", f"{fmt(r['y_peak']['dry_tons'])} 吨")
    col2.metric("丰产期年湿料产量", f"{fmt(r['y_peak']['wet_tons'])} 吨")
    col3.metric("种植面积", f"{fmt(r['area_mu'])} 亩（{fmt(r['y_peak']['area_ha'], 1)} 公顷）")

    # 达产曲线（绿色系折线图，带 hover 信息）
    st.subheader("📈 达产曲线")
    df_curve = pd.DataFrame(r["curve"])
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_curve["year"],
            y=df_curve["dry_tons"],
            name="干基产量",
            mode="lines+markers",
            line=dict(color=GREEN_THEME["primary"], width=3),
            marker=dict(size=5, color=GREEN_THEME["primary"]),
            fill="tozeroy",
            fillcolor=GREEN_THEME["fill"],
            hovertemplate="第 %{x} 年<br>干基产量：%{y:,.0f} 吨<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_curve["year"],
            y=df_curve["wet_tons"],
            name="湿料产量",
            mode="lines+markers",
            line=dict(color=GREEN_THEME["secondary"], width=2, dash="dash"),
            marker=dict(size=5, color=GREEN_THEME["secondary"]),
            hovertemplate="第 %{x} 年<br>湿料产量：%{y:,.0f} 吨<extra></extra>",
        )
    )
    apply_green_theme(fig, "丰产期达产曲线（逐年产量）", "种植年份", "产量（吨）", height=420)
    st.plotly_chart(fig, use_container_width=True)


def render_carbon_tab(r):
    """Tab2 渲染：碳汇测算（固碳量、碳资产价值、与林业对比、碳汇构成）

    Args:
        r: compute_all() 返回的结果字典
    """
    st.header("🌍 碳汇价值测算")

    # 关键数据卡片
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("年固碳量", f"{fmt(r['co2'])} 吨CO₂")
    col2.metric("碳资产价值", f"{fmt(r['cv'])} 元/年")
    col3.metric("vs 传统林业碳汇", f"{r['cf']['ratio']:.1f} 倍")
    col4.metric(f"{r['project_years']}年土壤固碳", f"{fmt(r['soil_c'])} 吨CO₂")

    # 芦竹 vs 传统林业 分组柱状图
    st.subheader("📊 芦竹 vs 传统林业碳汇对比")
    categories = ["年固碳量（吨CO₂）", "碳资产价值（万元）"]
    fig2 = go.Figure()
    fig2.add_trace(
        go.Bar(
            name="超级芦竹",
            x=categories,
            y=[r["co2"], r["cv"] / 10000],
            marker_color=GREEN_THEME["primary"],
            hovertemplate="%{x}<br>超级芦竹：%{y:,.0f}<extra></extra>",
        )
    )
    fig2.add_trace(
        go.Bar(
            name="传统林业碳汇",
            x=categories,
            y=[r["cf"]["forestry_co2"], r["cf"]["forestry_co2"] * r["co2_price"] / 10000],
            marker_color=GREEN_THEME["light"],
            hovertemplate="%{x}<br>传统林业：%{y:,.0f}<extra></extra>",
        )
    )
    fig2.update_layout(barmode="group")
    apply_green_theme(fig2, "芦竹与传统林业年固碳量对比", "", "", height=400)
    st.plotly_chart(fig2, use_container_width=True)

    # 碳汇构成环形图（生物量固碳 vs 年均土壤固碳）
    st.subheader("🥧 碳汇构成分析")
    soil_annual = r["soil_c"] / r["project_years"]  # 年均土壤固碳（吨CO₂/年）
    fig3 = go.Figure(
        go.Pie(
            labels=["地上生物量固碳", "土壤固碳（年均）"],
            values=[r["co2"], soil_annual],
            hole=0.45,
            marker=dict(colors=[GREEN_THEME["primary"], GREEN_THEME["light"]]),
            textinfo="label+percent",
            hovertemplate="%{label}<br>%{value:,.0f} 吨CO₂/年（%{percent:.1%}）<extra></extra>",
        )
    )
    apply_green_theme(fig3, "年固碳量构成（吨CO₂/年）", "", "", height=380, hovermode=False)
    st.plotly_chart(fig3, use_container_width=True)


def render_economic_tab(r):
    """Tab3 渲染：经济效益（收益构成、投资回报、敏感性分析柱状图）

    Args:
        r: compute_all() 返回的结果字典

    Returns:
        tuple: (investment, annual_cost) 投资额与年成本（元），供综合报告复用
    """
    st.header("💰 经济效益分析")

    # 收益构成卡片
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("原料销售收入", f"{fmt(r['raw_rev'])} 元/年")
    col2.metric("碳资产收益", f"{fmt(r['carbon_rev'])} 元/年")
    col3.metric("综合年收益", f"{fmt(r['total_rev'])} 元/年")
    col4.metric("颗粒加工净收益", f"{fmt(r['pellet_rev'])} 元/年")

    # 投资回报分析
    st.subheader("📉 投资回报分析")
    c1, c2 = st.columns(2)
    investment = c1.number_input("总投资额（万元）", value=5000, step=100) * 10000
    annual_cost = c2.number_input("年运营成本（万元）", value=500, step=50) * 10000

    roi = roi_analysis(investment, r["total_rev"], annual_cost, r["project_years"])
    m1, m2, m3 = st.columns(3)
    m1.metric("年净收益", f"{fmt(roi['annual_net'])} 元")
    m2.metric("回本周期", f"{roi['payback_years']:.1f} 年")
    m3.metric(f"{r['project_years']}年累计净利", f"{fmt(roi['net_profit_25y'])} 元")

    # 敏感性分析（Plotly 柱状图，替代原 st.table）
    st.subheader("🔍 敏感性分析：湿料单价 ±20% 对综合年收益的影响")
    sens = []
    for pct in [-20, -10, 0, 10, 20]:
        price = r["wet_price"] * (1 + pct / 100)
        # 综合年收益 = 变动单价下的原料收入 + 碳资产收益
        rev = raw_material_revenue(r["y_peak"]["wet_tons"], price) + r["carbon_rev"]
        sens.append({"pct": pct, "price": price, "rev": rev})

    # 柱色：基准值用墨绿强调，正向变动用主绿，负向变动用浅绿
    bar_colors = []
    for s in sens:
        if s["pct"] == 0:
            bar_colors.append(GREEN_THEME["dark"])
        elif s["pct"] < 0:
            bar_colors.append(GREEN_THEME["light"])
        else:
            bar_colors.append(GREEN_THEME["primary"])

    fig4 = go.Figure(
        go.Bar(
            x=[f"{s['pct']:+d}%" for s in sens],
            y=[s["rev"] / 10000 for s in sens],
            marker_color=bar_colors,
            text=[f"{s['rev'] / 10000:,.0f} 万元" for s in sens],
            textposition="outside",
            customdata=[f"{s['price']:.0f}" for s in sens],
            hovertemplate=(
                "价格变动：%{x}<br>"
                "湿料单价：%{customdata} 元/吨<br>"
                "综合年收益：%{y:,.0f} 万元<extra></extra>"
            ),
        )
    )
    # 基准收益参考线
    fig4.add_hline(
        y=r["total_rev"] / 10000,
        line_dash="dot",
        line_color=GREEN_THEME["dark"],
        annotation_text=f"基准收益 {r['total_rev'] / 10000:,.0f} 万元",
        annotation_position="top left",
    )
    apply_green_theme(fig4, "湿料单价敏感性分析（综合年收益）", "价格变动幅度", "综合年收益（万元）", height=420)
    st.plotly_chart(fig4, use_container_width=True)

    return investment, annual_cost


def render_seedling_tab(r):
    """Tab4 渲染：种苗规划（需求、成本、分批计划与图表）

    Args:
        r: compute_all() 返回的结果字典
    """
    st.header("🌿 种苗需求规划")

    # 关键数据卡片
    col1, col2, col3 = st.columns(3)
    col1.metric("种苗总需求", f"{fmt(r['plan']['total_demand'])} 株")
    col2.metric("种苗总成本", f"{fmt(r['plan']['total_cost'])} 元")
    col3.metric("种植批次数", f"{r['plan']['total_batches']} 批")

    # 分批种植计划表
    st.subheader("📋 分批种植计划")
    df_batch = pd.DataFrame(r["plan"]["batches"])
    df_batch.columns = ["批次", "面积（亩）", "种苗（株）", "起始天"]
    st.dataframe(df_batch, use_container_width=True, hide_index=True)

    # 各批次种苗需求柱状图（绿色系）
    fig5 = go.Figure(
        go.Bar(
            x=df_batch["批次"],
            y=df_batch["种苗（株）"],
            marker_color=GREEN_THEME["secondary"],
            text=[f"{v:,.0f}" for v in df_batch["种苗（株）"]],
            textposition="outside",
            customdata=df_batch["面积（亩）"],
            hovertemplate=(
                "第 %{x} 批<br>"
                "种植面积：%{customdata:.0f} 亩<br>"
                "种苗需求：%{y:,.0f} 株<extra></extra>"
            ),
        )
    )
    apply_green_theme(fig5, "各批次种苗需求", "批次", "种苗需求（株）", height=380)
    st.plotly_chart(fig5, use_container_width=True)


def render_report_tab(r, investment, annual_cost):
    """Tab5 渲染：综合报告（Markdown 可复制 / 可下载）

    Args:
        r: compute_all() 返回的结果字典
        investment: 总投资额（元）
        annual_cost: 年运营成本（元）
    """
    st.header("📊 综合报告（可复制 Markdown）")

    report = build_report(r, investment, annual_cost)
    st.code(report, language="markdown")
    st.download_button("📥 下载报告", report, "super_bamboo_report.md", "text/markdown")


# ==================== 应用主入口 ====================

def main():
    """应用主入口：搭建侧边栏参数、项目概览与五个功能 Tab"""
    st.set_page_config(page_title="超级芦竹全产业链计算器", page_icon="🎋", layout="wide")
    st.title("🎋 超级芦竹全产业链计算器")
    st.caption("开源能源草全产业链计算工具 | 参数全部可配置 | 数据来源：公开学术文献")

    # ---------- 侧边栏：项目参数 ----------
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

    # ---------- 核心计算（前端与 CLI 共用同一套逻辑）----------
    r = compute_all(
        area_mu=area_mu,
        variety_yield=variety_yield,
        moisture_pct=moisture_pct,
        peak_year=peak_year,
        project_years=project_years,
        co2_price=co2_price,
        wet_price=wet_price,
        seedling_density=seedling_density,
        seedling_price=seedling_price,
    )

    # ---------- 项目概览（Tab 上方的 4 张大数字卡片）----------
    st.subheader("📌 项目概览")
    with st.container(border=True):
        oc1, oc2, oc3, oc4 = st.columns(4)
        oc1.metric(
            "种植面积",
            f"{fmt(r['area_mu'])} 亩",
            help=f"折合约 {fmt(r['y_peak']['area_ha'], 1)} 公顷",
        )
        oc2.metric(
            "丰产期产量（干基）",
            f"{fmt(r['y_peak']['dry_tons'])} 吨/年",
            help=f"折合湿料 {fmt(r['y_peak']['wet_tons'])} 吨/年",
        )
        oc3.metric(
            "年固碳量",
            f"{fmt(r['co2'])} 吨CO₂/年",
            help=f"碳资产价值约 {fmt(r['cv'])} 元/年",
        )
        oc4.metric(
            "综合年收益",
            f"{fmt(r['total_rev'] / 10000)} 万元/年",
            help=f"折合 {fmt(r['total_rev'])} 元/年（原料销售 + 碳资产）",
        )

    # ---------- 五个功能 Tab ----------
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🌱 产量计算", "🌍 碳汇测算", "💰 经济效益", "🌿 种苗规划", "📊 综合报告"]
    )

    with tab1:
        render_yield_tab(r)

    with tab2:
        render_carbon_tab(r)

    with tab3:
        investment, annual_cost = render_economic_tab(r)

    with tab4:
        render_seedling_tab(r)

    with tab5:
        render_report_tab(r, investment, annual_cost)


# 仅在作为主脚本运行时执行（streamlit run 满足该条件），保证模块可被安全 import
if __name__ == "__main__":
    main()
