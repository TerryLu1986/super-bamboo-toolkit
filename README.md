# 🎋 Super Bamboo Toolkit

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**开源超级芦竹全产业链计算工具箱**

一站式计算超级芦竹（及其他能源草）的生物量产量、碳汇价值、经济效益和种苗规划。适用于政府招商方案、可研报告、投资分析等场景。

## ✨ 功能模块

| 模块 | 功能 |
|------|------|
| 🌱 产量计算 | 基于面积、品种、气候区估算年生物量，含任意达产年数的达产曲线 |
| 🌍 碳汇测算 | 生物量固碳 + 土壤固碳，碳资产价值估算，与林业碳汇对比 |
| 💰 经济模型 | 原料销售/颗粒加工多级收益，静态回本 + **NPV/IRR 动态分析**，敏感性分析 |
| 🌿 种苗规划 | 种苗需求量（含成活率补栽余量）、定植密度、分批种植计划、成本估算 |
| 📊 综合报告 | 一键生成可研报告摘要（Markdown/可导出PDF） |

## 🚀 快速开始

### 安装（Python 3.10+）

```bash
git clone https://github.com/TerryLu1986/super-bamboo-toolkit.git
cd super-bamboo-toolkit
pip install -r requirements.txt
```

### Web 界面（推荐）

```bash
streamlit run app/streamlit_app.py
```

浏览器自动打开 http://localhost:8501，侧边栏调参、五个功能Tab实时联动。

### 命令行

```bash
# 默认参数（10000亩）生成完整测算报告
python3 -m src.cli

# 自定义参数并导出报告文件
python3 -m src.cli --area 50000 --yield 25 --co2-price 80 \
    --investment 20000 --annual-cost 1500 --output report.md
```

全部参数见 `python3 -m src.cli --help`。

### Python API

```python
from src.biomass_yield import annual_yield
from src.carbon_sequestration import annual_co2_sequestration, carbon_asset_value
from src.economic_model import total_annual_revenue, roi_analysis, npv_analysis

# 10000亩，品种亩产30吨干基/公顷/年，第4年（丰产期）
result = annual_yield(area_mu=10000, variety_yield_t_ha=30, year=4)
print(f"年干基产量: {result['dry_tons']:.0f} 吨")   # 20000 吨
print(f"年湿料产量: {result['wet_tons']:.0f} 吨")   # 28571 吨

co2 = annual_co2_sequestration(area_mu=10000, biomass_t_dry=result['dry_tons'])
print(f"年毛固碳量: {co2:.0f} 吨CO₂")               # 33030 吨

value = carbon_asset_value(co2, price_per_ton=100)
print(f"碳资产价值: {value:.0f} 元/年")              # 330.3 万元/年

# 一步到位：综合年收益（默认按丰产期）+ 静态/动态回报指标
rev = total_annual_revenue(10000)
roi = roi_analysis(50_000_000, rev['total'], 5_000_000, years=25)
npv = npv_analysis(50_000_000, rev['total'], 5_000_000, years=25, discount_rate=0.08)
print(f"综合年收益 {rev['total']:,.0f} 元 | 静态回本 {roi['payback_years']:.1f} 年 | IRR {npv['irr']:.1%}")
```

### 运行测试

```bash
pip install pytest
python3 -m pytest tests/ --doctest-modules src/ -q
```

## ⚙️ 参数说明

所有参数均可通过侧边栏、CLI 标志、函数参数或 `config/default_params.yaml` 自定义，无硬编码值。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `area_mu` | 10000 | 种植面积（亩） |
| `variety_yield_t_ha` | 30 | 品种亩产（吨干基/公顷/年，丰产期） |
| `moisture_pct` | 30 | 采收含水率（%） |
| `peak_year` | 3 | 达产年数（第 peak_year+1 年起 100% 丰产） |
| `carbon_content` | 0.45 | 干物质碳含量（IPCC 默认值） |
| `soil_c_rate` | 2.0 | 土壤年固碳率（吨CO₂/公顷/年） |
| `forestry_c_rate_t_mu` | 0.5 | 对比用林业年固碳率（吨CO₂/亩/年） |
| `co2_price` | 100 | 碳价（元/吨CO₂） |
| `wet_price` | 300 | 湿料单价（元/吨） |
| `discount_rate` | 0.08 | 折现率（NPV/IRR 计算） |
| `seedling_density` | 800 | 定植密度（株/亩） |
| `survival_rate` | 0.9 | 首年成活率（自动放大种苗需求预留补栽） |
| `seedling_price` | 3.0 | 种苗单价（元/株） |

## 📐 计算依据

- **达产曲线**：文献经验值，第1~4年分别为丰产期的 30% / 60% / 80% / 100%；自定义达产年数按锚点线性插值
- **单位换算**：1 公顷 = 15 亩（精确值）
- **碳含量**：IPCC 默认值 45%（木质纤维素类）；碳转CO₂系数 44/12 ≈ 3.67
- **土壤固碳**：多年生深根草本文献报道 0.3~0.8 吨碳/公顷/年，折合约 1~3 吨CO₂/公顷/年，默认取 2.0（偏保守）
- **林业对比基准**：中国森林碳汇多为 0.2~0.7 吨CO₂/亩/年，默认取 0.5
- **碳价**：参考全国碳市场交易价格区间

## ⚠️ 碳汇口径说明（重要）

**地上生物量固碳是年度循环碳通量，不是永久净碳汇。** 芦竹原料收获后用于燃烧发电、制颗粒、制甲醇等能源化场景时，其中的碳会以CO₂形式重新排回大气。长期净碳汇主要由**地下根系/根盘与土壤固碳**构成。

因此本工具中的"年固碳量"应理解为**毛固碳通量**（年碳固定速率），用于量级对比展示；碳资产的可交易性与项目开发，须以官方认可的方法学（如 CCER）审定核证为准。将本工具输出直接用作碳汇交易预期属于误用。

## 📋 数据声明

⚠️ **本工具所有计算参数均为可配置的默认值，不包含任何特定企业的内部数据。**

参考数据来源（详见 `data/references.yaml`）：
- IPCC 国家温室气体清单指南
- 中国碳市场公开交易数据
- 学术期刊发表的能源草产量研究
- 国家能源局/林草局公开发布的行业规划

本工具为参数化估算工具，输出不构成投资建议。

## 📄 许可证

MIT License - 自由使用、修改和分发。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。提交前请跑通测试：`python3 -m pytest tests/ --doctest-modules src/ -q`

## 📧 联系

如有行业合作或技术咨询需求，欢迎通过 GitHub Issues 联系。
