"""碳汇核算模块: 芦竹生物量固碳、土壤固碳与碳资产价值估算

⚠️ 方法学说明: 地上生物量碳属年度循环固碳——原料收获能源化利用后,
其中的碳会以CO2形式重新排回大气, 不能计入长期净碳汇;
净碳汇仅由地下根系/根盘与土壤固碳构成。本模块的生物量固碳量
应理解为"年碳固定通量"(毛固碳), 用于对比展示; 碳资产的可交易性
以官方认可的方法学(如CCER)审定结果为准。
"""
from src.utils import mu_to_hectare


def annual_co2_sequestration(area_mu, biomass_t_dry, carbon_content=0.45, c_to_co2=3.67):
    """生物量年固碳量(吨CO2) —— 毛固碳通量

    固碳CO2 = 干基生物量(吨) × 碳含量(默认0.45, IPCC木质纤维素默认值) × 碳转CO2系数(44/12≈3.67)

    注意: 收获利用后生物量碳会重新排放, 该值不代表净碳汇(见模块docstring)。

    Args:
        area_mu: 种植面积(亩)。保留该参数仅为接口兼容, 计算不使用
            (固碳量仅取决于生物量绝对值, 与面积无关)
        biomass_t_dry: 年干基生物量(吨)
        carbon_content: 生物质碳含量比例, 默认0.45
        c_to_co2: 碳转CO2质量系数(44/12), 默认3.67

    Returns:
        float: 年固碳量(吨CO2)
    """
    return biomass_t_dry * carbon_content * c_to_co2


def soil_carbon_accumulation(area_mu, years, annual_soil_c_t_ha=2.0):
    """累积土壤固碳量(吨CO2)

    面积(公顷) × 年土壤固碳率(吨CO2/公顷/年) × 年数

    单位说明: annual_soil_c_t_ha 以 CO2 计(非碳计)。
    文献报道多年生能源草土壤有机碳积累约 0.3~0.8 吨碳/公顷/年,
    折合约 1~3 吨CO2/公顷/年; 默认值 2.0 吨CO2/公顷/年 取中值偏保守。

    Args:
        area_mu: 种植面积(亩)
        years: 累积年数(>=0)
        annual_soil_c_t_ha: 年土壤固碳率(吨CO2/公顷/年), 默认2.0

    Returns:
        float: 累积土壤固碳量(吨CO2)
    """
    if years < 0:
        raise ValueError(f"years 需 >= 0, 当前为 {years}")
    if annual_soil_c_t_ha < 0:
        raise ValueError(f"年土壤固碳率不能为负, 当前为 {annual_soil_c_t_ha}")
    area_ha = mu_to_hectare(area_mu)
    return area_ha * annual_soil_c_t_ha * years


def carbon_asset_value(co2_tons, price_per_ton=100):
    """碳资产价值(元)

    价值 = 固碳量(吨CO2) × 碳价(元/吨)

    Args:
        co2_tons: CO2吨数
        price_per_ton: 碳价(元/吨), 默认100

    Returns:
        float: 碳资产价值(元)
    """
    return co2_tons * price_per_ton


def comparison_with_forestry(area_mu, biomass_t_dry, forestry_c_rate_t_mu=0.5):
    """芦竹年毛固碳 vs 传统林业碳汇对比

    传统林业参考基准: forestry_c_rate_t_mu 吨CO2/亩/年。
    中国森林碳汇多为 0.2~0.7 吨CO2/亩/年(约3~10吨CO2/公顷/年,
    中幼龄林偏高、成熟林偏低), 默认取 0.5 (≈7.5吨CO2/公顷/年)。
    对比口径为"年固碳速率", 且芦竹侧为毛固碳通量(见模块docstring),
    该比值用于量级感知, 不构成碳汇项目开发承诺。

    Args:
        area_mu: 种植面积(亩)
        biomass_t_dry: 年干基生物量(吨)
        forestry_c_rate_t_mu: 传统林业年固碳率(吨CO2/亩/年), 默认0.5

    Returns:
        dict: {'bamboo_co2': float, 'forestry_co2': float, 'ratio': float}
    """
    if forestry_c_rate_t_mu < 0:
        raise ValueError(f"林业固碳率不能为负, 当前为 {forestry_c_rate_t_mu}")
    bamboo_co2 = annual_co2_sequestration(area_mu, biomass_t_dry)
    forestry_co2 = area_mu * forestry_c_rate_t_mu
    ratio = bamboo_co2 / forestry_co2 if forestry_co2 else float("inf")
    return {
        "bamboo_co2": bamboo_co2,
        "forestry_co2": forestry_co2,
        "ratio": ratio,
    }
