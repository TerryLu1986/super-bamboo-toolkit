"""单元测试 - 全部计算模块"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from src.biomass_yield import annual_yield, yield_curve
from src.carbon_sequestration import annual_co2_sequestration, carbon_asset_value, comparison_with_forestry, soil_carbon_accumulation
from src.economic_model import npv_analysis, raw_material_revenue, pellet_processing_revenue, roi_analysis, sensitivity_analysis, total_annual_revenue
from src.seedling_planner import seedling_demand, seedling_demand_detail, planting_schedule, seedling_cost, full_plan


# === biomass_yield ===

def test_annual_yield_basic():
    """10000亩×30吨/公顷，丰产期干基=20000吨（10000/15×30）"""
    r = annual_yield(10000, 30, year=3)
    assert abs(r["dry_tons"] - 20000.0) < 1e-6
    assert r["wet_tons"] > r["dry_tons"]

def test_annual_yield_year1():
    """第1年应为丰产期的30%（文献经验值）"""
    r1 = annual_yield(10000, 30, year=1)
    r_peak = annual_yield(10000, 30, year=3)
    assert abs(r1["dry_tons"] / r_peak["dry_tons"] - 0.3) < 1e-9

def test_annual_yield_ramp_exact():
    """默认peak_year=3时达产系数精确为 0.3/0.6/1.0——第三年即满产"""
    peak = annual_yield(10000, 30, year=3)["dry_tons"]
    for year, ratio in [(1, 0.3), (2, 0.6), (3, 1.0), (4, 1.0)]:
        assert abs(annual_yield(10000, 30, year=year)["dry_tons"] / peak - ratio) < 1e-9

def test_annual_yield_peak_year_generalized():
    """peak_year=5时：第5年即100%丰产（锚点插值30/45/60/80/100）"""
    curve = yield_curve(10000, 30, peak_year=5, years=8)
    assert curve[4]["dry_tons"] == pytest.approx(20000.0)   # 第5年满产
    assert curve[5]["dry_tons"] == pytest.approx(curve[6]["dry_tons"])  # 之后保持
    assert curve[3]["dry_tons"] == pytest.approx(16000.0)   # 第4年=80%锚点插值
    for i in range(1, 5):
        assert curve[i]["dry_tons"] > curve[i - 1]["dry_tons"]

def test_annual_yield_peak_year_one():
    """peak_year=1：种植当年即满产，不除零"""
    assert annual_yield(10000, 30, year=1, peak_year=1)["dry_tons"] == pytest.approx(20000.0)

def test_yield_curve_length():
    """25年应返回25条记录"""
    curve = yield_curve(10000, 30, years=25)
    assert len(curve) == 25

def test_yield_curve_monotonic():
    """达产前产量递增；第3年即达丰产并保持稳定"""
    curve = yield_curve(10000, 30, peak_year=3, years=10)
    for i in range(1, 3):
        assert curve[i]["dry_tons"] > curve[i-1]["dry_tons"]
    for i in range(3, 10):
        assert curve[i]["dry_tons"] == curve[2]["dry_tons"]  # 第3年起恒为丰产期

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


def test_seedling_demand_detail():
    """净定植+补栽余量=采购总量；成活率1.0时余量为0"""
    d = seedling_demand_detail(10000, 800, 0.9)
    assert d["net_demand"] == 800_0000
    assert d["total_demand"] == 888_8889
    assert d["replant_reserve"] == d["total_demand"] - d["net_demand"]
    d2 = seedling_demand_detail(10000, 800, 1.0)
    assert d2["replant_reserve"] == 0
    assert d2["total_demand"] == d2["net_demand"] == 8_000_000


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


def test_cli_new_flags_flow_through(capsys):
    """--survival-rate/--discount-rate 应真实作用于种苗需求与NPV折现率"""
    from src.cli import main
    rc = main(["--area", "1000", "--survival-rate", "0.8", "--discount-rate", "0.10"])
    assert rc == 0
    out = capsys.readouterr().out
    # 1000亩×800株/亩÷0.8 = 1,000,000 株
    assert "1,000,000 株" in out
    # 折现率10%应体现在NPV行
    assert "10%" in out


def test_cli_invalid_area_exits():
    """非法参数（负面积）应通过argparse报错退出而非静默计算"""
    from src.cli import main
    with pytest.raises(SystemExit) as ei:
        main(["--area", "-5"])
    assert ei.value.code == 2  # argparse error 约定退出码


def test_cli_help_no_crash(capsys):
    """--help 应正常输出（回归测试：help含裸%曾致ValueError）"""
    from src.cli import build_parser
    with pytest.raises(SystemExit) as ei:
        build_parser().parse_args(["--help"])
    assert ei.value.code == 0
    assert "折现率" in capsys.readouterr().out


# === project_calculator ===

from src.project_calculator import build_report, compute_all, fmt, tornado_npv


def test_fmt():
    """千分位格式化：整数与指定小数位"""
    assert fmt(1234567) == "1,234,567"
    assert fmt(0) == "0"
    assert fmt(1234.567, 2) == "1,234.57"


def test_compute_all_default_keys():
    """默认参数应返回完整结果字典，收益=原料+碳资产"""
    r = compute_all()
    for key in ("y_peak", "curve", "co2", "cv", "cf", "soil_c",
                "raw_rev", "carbon_rev", "total_rev", "pellet_rev", "plan"):
        assert key in r, f"缺少键: {key}"
    assert r["total_rev"] == r["raw_rev"] + r["carbon_rev"]
    assert r["raw_rev"] > 0 and r["carbon_rev"] > 0


def test_compute_all_curve_length():
    """达产曲线长度应等于项目周期年数"""
    r = compute_all(project_years=10)
    assert len(r["curve"]) == 10
    assert r["curve"][0]["year"] == 1
    assert r["curve"][-1]["year"] == 10


def test_compute_all_area_scaling():
    """面积翻倍，丰产期干基产量应精确翻倍（线性模型）"""
    small = compute_all(area_mu=10000)["y_peak"]["dry_tons"]
    big = compute_all(area_mu=20000)["y_peak"]["dry_tons"]
    assert big == pytest.approx(2 * small)


def test_compute_all_config_fallback():
    """soil_c_rate/discount_rate 传 None 时应回退配置文件值"""
    r = compute_all()
    assert r["soil_c_rate"] == 2.0
    assert r["discount_rate"] == 0.08
    # 显式传参优先于配置
    r2 = compute_all(discount_rate=0.10)
    assert r2["discount_rate"] == 0.10


def test_build_report_sections():
    """报告应包含全部章节标题与碳汇口径免责声明"""
    text = build_report(compute_all())
    for kw in ("超级芦竹全产业链项目测算报告", "产量测算", "碳汇价值", "经济效益",
               "投资回报", "种苗规划", "NPV", "IRR", "碳汇口径说明"):
        assert kw in text, f"报告缺少: {kw}"


def test_build_report_custom_params():
    """自定义投资额应体现在报告文本中"""
    text = build_report(compute_all(area_mu=1000), investment=80_000_000, annual_cost=8_000_000)
    assert "80,000,000" in text
    assert "8,000,000" in text


def test_tornado_npv_shape():
    """龙卷风数据：六因素、按影响幅度降序、delta自洽"""
    t = tornado_npv(compute_all(), 50_000_000, 5_000_000)
    assert len(t["factors"]) == 6
    impacts = [f["impact"] for f in t["factors"]]
    assert impacts == sorted(impacts, reverse=True)
    for f in t["factors"]:
        assert f["low_delta"] == pytest.approx(f["low"] - t["base_npv"])
        assert f["high_delta"] == pytest.approx(f["high"] - t["base_npv"])
        assert f["impact"] == pytest.approx(max(abs(f["low_delta"]), abs(f["high_delta"])))


def test_tornado_npv_direction():
    """方向检验：亩产+20%→NPV升；总投资+20%→NPV降；折现率+20%→NPV降"""
    t = tornado_npv(compute_all(), 50_000_000, 5_000_000)
    by_name = {f["name"]: f for f in t["factors"]}
    assert set(by_name) == {"亩产", "湿料单价", "碳价", "折现率", "总投资", "年运营成本"}
    assert by_name["亩产"]["high_delta"] > 0
    assert by_name["湿料单价"]["high_delta"] > 0
    assert by_name["碳价"]["high_delta"] > 0
    assert by_name["总投资"]["high_delta"] < 0
    assert by_name["年运营成本"]["high_delta"] < 0
    assert by_name["折现率"]["high_delta"] < 0


def test_tornado_npv_base_matches_npv_analysis():
    """基准NPV应与直接调用 npv_analysis 一致"""
    r = compute_all()
    t = tornado_npv(r, 50_000_000, 5_000_000)
    direct = npv_analysis(50_000_000, r["total_rev"], 5_000_000, 25, 0.08)["npv"]
    assert t["base_npv"] == pytest.approx(direct)


# === utils ===

from src.utils import hectare_to_mu, load_config, mu_to_hectare


def test_mu_hectare_conversion():
    """亩↔公顷互转：1公顷=15亩精确值"""
    assert mu_to_hectare(15) == 1.0
    assert hectare_to_mu(1) == 15
    assert mu_to_hectare(100) == pytest.approx(100 / 15)
    # 往返一致
    assert hectare_to_mu(mu_to_hectare(12345)) == pytest.approx(12345)


def test_load_config_sections():
    """默认配置应含四大节及关键字段"""
    cfg = load_config()
    for sec in ("biomass", "carbon", "economics", "seedling"):
        assert sec in cfg, f"配置缺少节: {sec}"
    assert cfg["economics"]["discount_rate"] == 0.08
    assert cfg["biomass"]["peak_year"] == 3


def test_load_config_missing_file():
    """配置文件不存在应抛OSError而非静默返回"""
    with pytest.raises(OSError):
        load_config("/nonexistent/params.yaml")
