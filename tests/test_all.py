"""单元测试 - 全部计算模块"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.biomass_yield import annual_yield, yield_curve
from src.carbon_sequestration import annual_co2_sequestration, carbon_asset_value, comparison_with_forestry, soil_carbon_accumulation
from src.economic_model import raw_material_revenue, pellet_processing_revenue, roi_analysis
from src.seedling_planner import seedling_demand, planting_schedule, seedling_cost, full_plan


# === biomass_yield ===

def test_annual_yield_basic():
    """10000亩×30吨/公顷，丰产期干基≈20000吨"""
    r = annual_yield(10000, 30, year=4)
    assert 19000 < r["dry_tons"] < 21000
    assert r["wet_tons"] > r["dry_tons"]

def test_annual_yield_year1():
    """第1年应为丰产期的30%"""
    r1 = annual_yield(10000, 30, year=1)
    r4 = annual_yield(10000, 30, year=4)
    assert abs(r1["dry_tons"] / r4["dry_tons"] - 0.3) < 0.05

def test_yield_curve_length():
    """25年应返回25条记录"""
    curve = yield_curve(10000, 30, years=25)
    assert len(curve) == 25

def test_yield_curve_monotonic():
    """达产前产量递增，达产后稳定（第4年起=丰产期100%）"""
    curve = yield_curve(10000, 30, peak_year=3, years=10)
    for i in range(1, 4):
        assert curve[i]["dry_tons"] >= curve[i-1]["dry_tons"]
    for i in range(4, 10):
        assert curve[i]["dry_tons"] == curve[3]["dry_tons"]


# === carbon_sequestration ===

def test_co2_sequestration():
    """20000吨干基×0.45×3.67≈33030吨CO2"""
    co2 = annual_co2_sequestration(10000, 20000)
    assert abs(co2 - 33030) < 100

def test_carbon_asset_value():
    """33030吨×100元/吨=3303000元"""
    v = carbon_asset_value(33030, 100)
    assert abs(v - 3303000) < 1000

def test_forestry_comparison():
    """芦竹固碳应为林业的3倍以上"""
    cf = comparison_with_forestry(10000, 20000)
    assert cf["ratio"] > 2.5

def test_soil_carbon():
    """10000亩×10年应有正向土壤固碳"""
    sc = soil_carbon_accumulation(10000, 10)
    assert sc > 0


# === economic_model ===

def test_raw_revenue():
    """857000吨湿料×300元=257100000元"""
    r = raw_material_revenue(857000, 300)
    assert abs(r - 257100000) < 1000

def test_pellet_revenue():
    """颗粒加工收益应为正"""
    r = pellet_processing_revenue(100000)
    assert r > 0

def test_roi_analysis():
    """投资5000万，年收益2.57亿，回本应<1年"""
    roi = roi_analysis(50000000, 257100000, 50000000)
    assert roi["payback_years"] < 1
    assert roi["net_profit_25y"] > 0


# === seedling_planner ===

def test_seedling_demand():
    """10000亩×800株÷0.9≈8888889株"""
    d = seedling_demand(10000)
    assert abs(d - 8888889) < 100

def test_planting_schedule():
    """10000亩÷5000亩/批=2批"""
    s = planting_schedule(10000)
    assert len(s) == 2

def test_seedling_cost():
    """8888889株×3元≈26666667元"""
    c = seedling_cost(8888889, 3.0)
    assert abs(c - 26666667) < 1000

def test_full_plan():
    """综合规划应包含所有字段"""
    fp = full_plan(10000)
    assert "total_demand" in fp
    assert "total_cost" in fp
    assert "batches" in fp
    assert fp["total_batches"] == 2
