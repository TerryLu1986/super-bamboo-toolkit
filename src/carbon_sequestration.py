"""碳汇核算模块: 芦竹生物量固碳、土壤固碳与碳资产价值估算"""
from src.utils import mu_to_hectare


def annual_co2_sequestration(area_mu, biomass_t_dry, carbon_content=0.45, c_to_co2=3.67):
    """生物量年固碳量(吨CO2)

    固碳CO2 = 干基生物量(吨) × 碳含量(默认0.45) × 碳转CO2系数(默认3.67)

    Args:
        area_mu: 种植面积(亩)
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

    Args:
        area_mu: 种植面积(亩)
        years: 累积年数
        annual_soil_c_t_ha: 年土壤固碳率(吨CO2/公顷/年), 默认2.0

    Returns:
        float: 累积土壤固碳量(吨CO2)
    """
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


def comparison_with_forestry(area_mu, biomass_t_dry, forestry_c_rate_t_mu=1.0):
    """芦竹年固碳 vs 传统林业碳汇对比

    传统林业碳汇参考: 1万吨CO2/万亩/年, 即 forestry_c_rate_t_mu 吨CO2/亩/年(默认1.0)

    Args:
        area_mu: 种植面积(亩)
        biomass_t_dry: 年干基生物量(吨)
        forestry_c_rate_t_mu: 传统林业年固碳率(吨CO2/亩/年), 默认1.0

    Returns:
        dict: {'bamboo_co2': float, 'forestry_co2': float, 'ratio': float}
    """
    bamboo_co2 = annual_co2_sequestration(area_mu, biomass_t_dry)
    forestry_co2 = area_mu * forestry_c_rate_t_mu
    ratio = bamboo_co2 / forestry_co2 if forestry_co2 else float("inf")
    return {
        "bamboo_co2": bamboo_co2,
        "forestry_co2": forestry_co2,
        "ratio": ratio,
    }
