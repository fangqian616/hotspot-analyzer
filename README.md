[English](README_EN.md) | 中文

# 网络热点舆情分析系统

输入关键词，自动搜索互联网内容，完成平台识别、内容分类、情感分析，一键导出PDF报告。

## 安装

```bash
pip install -r requirements.txt
```

## 启动

```bash
streamlit run app.py
```

## 功能

- **多平台数据采集**：通过DuckDuckGo搜索B站/抖音/微博/知乎/小红书等平台内容
- **6大内容分类**：国际政治、科技AI、社会民生、体育电竞、文娱、商业消费
- **情感分析**：正面/中性/负面分类，各平台负面率排行
- **舆情风险预警**：基于负面率和分类自动识别高危/中危风险
- **PDF报告导出**：7页数据图表，可选DeepSeek AI深度分析
- **平台限定搜索**：支持按B站/抖音/微博/知乎/小红书过滤

## 使用方法

1. 在文本框输入关键词（逗号分隔），如 `DeepSeek, 高考, 俄乌冲突`
2. 点击"开始搜索"，系统自动搜索并分析
3. 切换5个Tab查看分析结果：
   - 📊 平台对比
   - 🔥 热点排行
   - 😐 情感分析
   - ⚠️ 风险预警
   - 📥 导出报告
4. 在"导出报告"Tab生成PDF

## 可选：DeepSeek AI分析

在侧边栏填入DeepSeek API Key后，可生成AI深度分析文字，与数据图表合并为完整报告。

- API Key获取：https://platform.deepseek.com/
- 费用：约0.001元/次

## 进阶：Chromium浏览器采集

DuckDuckGo对中文社交平台覆盖有限，如需更丰富的数据，可使用Playwright/Selenium+Chromium进行采集。

### Playwright（推荐）

```bash
pip install playwright
playwright install chromium
```

采集B站/微博/知乎等内容后，将结果保存为CSV，在本系统选择"上传CSV/Excel"模式导入分析。

详细代码示例和使用说明见系统内"🔧 采集指引"Tab。

### 采集数据CSV格式

| 列名 | 必填 | 说明 |
|------|------|------|
| title | 是 | 内容标题/正文前100字 |
| url | 否 | 原文链接 |
| content | 否 | 正文/摘要 |
| platform | 否 | 平台名（不填则自动识别） |
| keyword | 否 | 搜索关键词 |

### 注意事项

- 首次采集B站/微博需手动扫码登录，建议用`headless=False`有界面模式
- 控制采集频率，每次请求间隔≥1秒，避免触发反爬
- B站搜索API有WBI签名校验，Playwright渲染页面可绕过
- 仅采集公开内容，遵守各平台robots.txt

## 注意事项

- 搜索结果来自DuckDuckGo公开搜索，不含评论区互动数据
- B站、抖音等平台的完整数据需登录或专用API
- 情感分析基于关键词匹配，无法识别"玩梗""反讽"等复杂场景
- 建议关键词不超过10个，每个关键词搜索5-50条
