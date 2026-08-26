# 🎋 Super Bamboo Toolkit

**开源超级芦竹全产业链计算工具箱**

一站式计算超级芦竹（及其他能源草）的生物量产量、碳汇价值、经济效益和种苗规划。适用于政府招商方案、可研报告、投资分析等场景。

## ✨ 功能模块

| 模块 | 功能 |
|------|------|
| 🌱 产量计算 | 基于面积、品种、气候区估算年生物量，含达产曲线 |
| 🌍 碳汇测算 | 地上生物量固碳 + 地下根盘土壤固碳，碳资产价值估算 |
| 💰 经济模型 | 原料销售/颗粒加工/供热/甲醇多级收益，ROI分析，敏感性分析 |
| 🌿 种苗规划 | 种苗需求量、定植密度、分批种植计划、成本估算 |
| 📊 综合报告 | 一键生成可研报告摘要（Markdown/可导出PDF） |

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/YOUR_USERNAME/super-bamboo-toolkit.git
cd super-bamboo-toolkit
pip install -r requirements.txt
```

### 运行

```bash
streamlit run app/streamlit_app.py
```

浏览器自动打开 http://localhost:8501

### 命令行使用

```python
from src.biomass_yield import annual_yield, yield_curve
from src.carbon_sequestration import annual_co2_sequestration, carbon_asset_value
from src.economic_model import total_annual_revenue, roi_analysis

# 10000亩，品种亩产30吨干基/公顷
result = annual_yield(area_mu=10000, variety_yield_t_ha=30)
print(f"年湿料产量: {result['wet_tons']:.0f} 吨")

co2 = annual_co2_sequestration(area_mu=10000, biomass_t_dry=result['dry_tons'])
print(f"年固碳量: {co2:.0f} 吨CO₂")

value = carbon_asset_value(co2, price_per_ton=100)
print(f"碳资产价值: {value:.0f} 元")
```

## ⚙️ 参数说明

所有参数均可通过侧边栏或函数参数自定义，无硬编码值。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `area_mu` | 10000 | 种植面积（亩） |
| `variety_yield_t_ha` | 30 | 品种亩产（吨干基/公顷/年，丰产期） |
| `moisture_pct` | 30 | 采收含水率（%） |
| `peak_year` | 3 | 达产年数 |
| `carbon_content` | 0.45 | 干物质碳含量 |
| `soil_c_rate` | 2.0 | 土壤年固碳（吨碳/公顷/年） |
| `co2_price` | 100 | 碳价（元/吨CO₂） |
| `wet_price` | 300 | 湿料单价（元/吨） |
| `seedling_density` | 800 | 定植密度（株/亩） |
| `seedling_price` | 3.0 | 种苗单价（元/株） |

## 📐 计算依据

- 生物量产量：基于公开学术文献中的芦竹/能源草产量数据范围
- 碳含量：IPCC默认值45%（木质纤维素类）
- 碳转CO₂系数：44/12 ≈ 3.67
- 土壤固碳：多年生深根草本的文献报道值（1.5-3.0吨碳/公顷/年）
- 碳价：参考全国碳市场交易价格区间

## 📋 数据声明

⚠️ **本工具所有计算参数均为可配置的默认值，不包含任何特定企业的内部数据。**

参考数据来源：
- IPCC 国家温室气体清单指南
- 中国碳市场公开交易数据
- 学术期刊发表的能源草产量研究
- 国家能源局/林草局公开发布的行业规划

## 📄 许可证

MIT License - 自由使用、修改和分发。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。

## 📧 联系

如有行业合作或技术咨询需求，欢迎通过 GitHub Issues 联系。
