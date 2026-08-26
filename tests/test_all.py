"""单元测试 - 全部计算模块"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from src.biomass_yield import annual_yield, yield_curve
from src.carbon_sequestration import annual_co2_sequestration, carbon_asset_value, comparison_with_forestry, soil_carbon_accumulation
from src.economic_model import npv_analysis, raw_material_revenue, pellet_processing_revenue, roi_analysis, sensitivity_analysis, total_annual_revenue
from src.seedling_planner import seedling_demand, planting_schedule, seedling_cost, full_plan


# === biomass_yield ===

def test_annual_yield_basic():
    """10000亩×30吨/公顷，丰产期干基=20000吨（10000/15×30）"""
    r = annual_yield(10000, 30, year=4)
    assert abs(r["dry_tons"] - 20000.0) < 1e-6
    assert r["wet_tons"] > r["dry_tons"]

def test_annual_yield_year1():
    """第1年应为丰产期的30%（文献经验值）"""
    r1 = annual_yield(10000, 30, year=1)
    r4 = annual_yield(10000, 30, year=4)
    assert abs(r1["dry_tons"] / r4["dry_tons"] - 0.3) < 1e-9

def test_annual_yield_ramp_exact():
    """默认peak_year=3时达产系数精确为 0.3/0.6/0.8/1.0"""
    peak = annual_yield(10000, 30, year=4)["dry_tons"]
    for year, ratio in [(1, 0.3), (2, 0.6), (3, 0.8), (4, 1.0)]:
        assert abs(annual_yield(10000, 30, year=year)["dry_tons"] / peak - ratio) < 1e-9

def test_annual_yield_peak_year_generalized():
    """peak_year=5时：第6年起100%丰产，且逐年递增"""
    curve = yield_curve(10000, 30, peak_year=5, years=8)
    assert curve[5]["dry_tons"] == pytest.approx(curve[6]["dry_tons"])  # 第6、7年相等
    assert curve[7]["dry_tons"] == pytest.approx(20000.0)
    for i in range(1, 6):
        assert curve[i]["dry_tons"] > curve[i - 1]["dry_tons"]

def test_yield_curve_length():
    """25年应返回25条记录"""
    curve = yield_curve(10000, 30, years=25)
    assert len(curve) == 25

def test_yield_curve_monotonic():
    """达产前产量递增，达产后稳定"""
    curve = yield_curve(10000, 30, peak_year=3, years=10)
    for i in range(1, 4):
        assert curve[i]["dry_tons"] >= curve[i-1]["dry_tons"]
    for i in range(4, 10):
        assert curve[i]["dry_tons"] == curve[3]["dry_tons"]

def test_yield_validation():
    """非法参数应抛ValueError"""
    with pytest.raises(ValueError):
        annual_yield(10000, 30, moisture_pct=100)   # 含水率=100
    with pytest.raises(ValueError):
        annual_yield(-1, 30)                        # 负面积
    with pytest.raises(ValueError):
        annual_yield(10000, 30, year=0)             # 年份<1
    with pytest.raises(ValueError):
        annual_yield(10000, 30, peak_year=0)        # 达产年数<1
    with pytest.raises(ValueError):
        yield_curve(10000, 30, years=0)             # 周期<1


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
    """默认林业基准0.5吨CO2/亩/年时，芦竹毛固碳应为林业的6倍以上"""
    cf = comparison_with_forestry(10000, 20000)
    assert cf["ratio"] > 6

def test_soil_carbon():
    """10000亩×10年应有正向土壤固碳（666.7公顷×2.0×10≈13333吨CO2）"""
    sc = soil_carbon_accumulation(10000, 10)
    assert sc == pytest.approx(10000 / 15 * 2.0 * 10)

def test_soil_carbon_validation():
    with pytest.raises(ValueError):
        soil_carbon_accumulation(10000, -1)


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
    assert roi["net_profit_total"] > 0

def test_npv_known_value():
    """投资60、年净流30、3年、10%折现：NPV=14.61、IRR≈23.4%（手算基准）"""
    res = npv_analysis(60, 30, 0, years=3, discount_rate=0.1)
    assert res["npv"] == pytest.approx(14.6056, abs=0.001)
    assert res["irr"] == pytest.approx(0.2338, abs=0.001)

def test_npv_no_payback():
    """年净现金流为负时IRR无解(nan)"""
    res = npv_analysis(1000, 100, 200, years=25)
    assert res["irr"] != res["irr"]  # NaN
    assert res["npv"] < 0

def test_sensitivity():
    """±20%、5点：首尾为0.8x/1.2x，中点为基准"""
    s = sensitivity_analysis(100, 0.2, 5)
    assert s[0]["result"] == pytest.approx(80.0)
    assert s[-1]["result"] == pytest.approx(120.0)
    assert s[2]["result"] == pytest.approx(100.0)

def test_total_annual_revenue_default_peak():
    """不传year时默认按丰产期（100%达产）计算综合年收益"""
    rev = total_annual_revenue(10000)
    # 丰产期湿料 20000/0.7≈28571吨 ×300元 ≈ 857万元（原料部分）
    assert rev["raw_revenue"] == pytest.approx(20000 / 0.7 * 300, rel=1e-6)


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

def test_seedling_validation():
    """非法参数应抛ValueError而非除零/静默错误"""
    with pytest.raises(ValueError):
        seedling_demand(10000, survival_rate=0)      # 成活率=0
    with pytest.raises(ValueError):
        seedling_demand(10000, survival_rate=1.5)    # 成活率>1
    with pytest.raises(ValueError):
        seedling_demand(10000, density_per_mu=-1)    # 负密度
    with pytest.raises(ValueError):
        planting_schedule(10000, batch_size_mu=0)    # 每批面积=0


# === cli smoke ===

def test_cli_smoke(tmp_path, capsys):
    """CLI默认参数应成功生成报告并可写入文件"""
    from src.cli import main
    out = tmp_path / "report.md"
    rc = main(["--area", "1000", "--output", str(out)])
    assert rc == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "超级芦竹全产业链项目测算报告" in content
    assert "IRR" in content  # 报告含NPV/IRR章节
