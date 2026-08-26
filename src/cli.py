"""命令行计算器入口（argparse）

用法示例：
    python3 -m src.cli --area 10000 --yield 30 --moisture 30
    python3 -m src.cli --area 10000                          # 其余参数使用默认值
    python3 -m src.cli --area 20000 --years 20 --co2-price 120 --output report.md

输出：与 Streamlit「综合报告」Tab 一致的 Markdown 格式文本报告；
指定 --output 时同时将报告写入 UTF-8 文件。
"""
import argparse
import sys
from pathlib import Path

# 将项目根目录插入模块搜索路径，保证从任意工作目录执行均可导入 src 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.project_calculator import build_report, compute_all
from src.utils import load_config


def load_defaults():
    """读取 config/default_params.yaml 中的默认参数

    Returns:
        dict: 参数名到默认值的映射（area_mu / variety_yield / moisture_pct /
              peak_year / project_years / co2_price / wet_price /
              seedling_density / seedling_price）；读取失败或键缺失时回退到内置默认值
    """
    defaults = {
        "area_mu": 10000,
        "variety_yield": 30,
        "moisture_pct": 30,
        "peak_year": 3,
        "project_years": 25,
        "co2_price": 100,
        "wet_price": 300,
        "seedling_density": 800,
        "seedling_price": 3.0,
    }
    try:
        cfg = load_config()
        defaults["area_mu"] = cfg["biomass"].get("area_mu", defaults["area_mu"])
        defaults["variety_yield"] = cfg["biomass"].get(
            "variety_yield_t_ha", defaults["variety_yield"]
        )
        defaults["moisture_pct"] = cfg["biomass"].get("moisture_pct", defaults["moisture_pct"])
        defaults["peak_year"] = cfg["biomass"].get("peak_year", defaults["peak_year"])
        defaults["project_years"] = cfg["biomass"].get("project_years", defaults["project_years"])
        defaults["co2_price"] = cfg["carbon"].get("co2_price_per_ton", defaults["co2_price"])
        defaults["wet_price"] = cfg["economics"].get("wet_price_per_ton", defaults["wet_price"])
        defaults["seedling_density"] = cfg["seedling"].get(
            "density_per_mu", defaults["seedling_density"]
        )
        defaults["seedling_price"] = cfg["seedling"].get(
            "price_per_seedling", defaults["seedling_price"]
        )
    except Exception:
        # 配置文件缺失或格式异常时静默回退到内置默认值
        pass
    return defaults


def build_parser():
    """构建命令行参数解析器

    Returns:
        argparse.ArgumentParser: 配置好全部参数、默认值与帮助信息的解析器
    """
    d = load_defaults()
    parser = argparse.ArgumentParser(
        prog="src.cli",
        description="超级芦竹全产业链命令行计算器：计算产量、碳汇、经济与种苗指标并输出 Markdown 报告",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--area", type=float, default=d["area_mu"], help="种植面积（亩）")
    parser.add_argument(
        "--yield",
        dest="yield_t_ha",
        type=float,
        default=d["variety_yield"],
        help="品种亩产（吨干基/公顷/年）",
    )
    parser.add_argument(
        "--moisture",
        dest="moisture_pct",
        type=float,
        default=d["moisture_pct"],
        help="采收含水率（%%）",
    )
    parser.add_argument(
        "--peak-year", dest="peak_year", type=int, default=d["peak_year"], help="达产年数"
    )
    parser.add_argument(
        "--years", dest="project_years", type=int, default=d["project_years"], help="项目周期（年）"
    )
    parser.add_argument(
        "--co2-price", dest="co2_price", type=float, default=d["co2_price"], help="碳价（元/吨CO2）"
    )
    parser.add_argument(
        "--wet-price", dest="wet_price", type=float, default=d["wet_price"], help="湿料单价（元/吨）"
    )
    parser.add_argument(
        "--density",
        dest="seedling_density",
        type=float,
        default=d["seedling_density"],
        help="定植密度（株/亩）",
    )
    parser.add_argument(
        "--seedling-price",
        dest="seedling_price",
        type=float,
        default=d["seedling_price"],
        help="种苗单价（元/株）",
    )
    parser.add_argument(
        "--survival-rate",
        dest="survival_rate",
        type=float,
        default=0.9,
        help="首年成活率（0-1）",
    )
    parser.add_argument(
        "--discount-rate",
        dest="discount_rate",
        type=float,
        default=0.08,
        help="折现率（用于NPV/IRR，如0.08表示8%%）",
    )
    parser.add_argument("--investment", type=float, default=5000, help="总投资额（万元）")
    parser.add_argument(
        "--annual-cost", dest="annual_cost", type=float, default=500, help="年运营成本（万元）"
    )
    parser.add_argument(
        "--output", type=str, default=None, help="将报告写入指定文件路径（UTF-8 编码）"
    )
    return parser


def main(argv=None):
    """命令行入口：解析参数、执行计算并输出 Markdown 报告

    Args:
        argv: 命令行参数列表，None 时取 sys.argv[1:]

    Returns:
        int: 退出码（0 表示成功；1 表示参数非法或计算失败）
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # ---------- 参数合法性校验 ----------
    if args.area <= 0:
        parser.error("--area 必须大于 0")
    if args.yield_t_ha <= 0:
        parser.error("--yield 必须大于 0")
    if not (0 <= args.moisture_pct < 100):
        parser.error("--moisture 需在 [0, 100) 区间")

    # ---------- 执行计算 ----------
    try:
        r = compute_all(
            area_mu=args.area,
            variety_yield=args.yield_t_ha,
            moisture_pct=args.moisture_pct,
            peak_year=args.peak_year,
            project_years=args.project_years,
            co2_price=args.co2_price,
            wet_price=args.wet_price,
            seedling_density=args.seedling_density,
            seedling_price=args.seedling_price,
            survival_rate=args.survival_rate,
            discount_rate=args.discount_rate,
        )
        # 投资额与年成本：万元 -> 元
        report = build_report(
            r,
            investment=args.investment * 10000,
            annual_cost=args.annual_cost * 10000,
        )
    except ValueError as exc:
        print(f"❌ 计算失败：{exc}", file=sys.stderr)
        return 1

    # ---------- 输出报告 ----------
    print(report)
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report, encoding="utf-8")
        print(f"\n✅ 报告已写入：{output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
