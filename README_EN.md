English | [中文](README.md)

# 🌐 Internet Hot Topic Sentiment Analysis System

Enter keywords to automatically search the internet, perform platform identification, content classification, and sentiment analysis, then export a one-click PDF report.

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
streamlit run app.py
```

## Features

- **Multi-platform data collection**: Search content from Bilibili, Douyin, Weibo, Zhihu, Xiaohongshu, and more via DuckDuckGo
- **6 content categories**: International politics, Tech/AI, Social issues, Sports/Esports, Entertainment, Business/Consumer
- **Sentiment analysis**: Positive/Neutral/Negative classification with per-platform negative rate ranking
- **Risk alerts**: Auto-identify high/medium risk levels based on negative rates and categories
- **PDF report export**: 7-page data visualization, optional DeepSeek AI in-depth analysis
- **Platform-specific search**: Filter by Bilibili/Douyin/Weibo/Zhihu/Xiaohongshu
- **AI prompt customization**: Custom analysis modules, multi-round analysis, extra instructions
- **Built-in sample dataset**: 589 pre-loaded records for demo
- **CSV upload mode**: Import your own collected data for analysis

## Usage

1. Enter keywords (comma-separated) in the text box, e.g. `DeepSeek, AI, ChatGPT`
2. Click "Start Search" — the system automatically searches and analyzes
3. Browse 6 tabs for analysis results:
   - 📊 Platform Comparison
   - 🔥 Hot Topic Rankings
   - 😐 Sentiment Analysis
   - ⚠️ Risk Alerts
   - 📥 Export Report
   - 🔧 Collection Guide
4. Generate PDF in the "Export Report" tab

## Optional: DeepSeek AI Analysis

Enter your DeepSeek API Key in the sidebar to generate AI-powered in-depth analysis text, merged with data charts into a complete report.

- Get API Key: https://platform.deepseek.com/
- Cost: ~$0.001/request

### AI Prompt Configuration (Sidebar)

- **Analysis rounds**: 1-10 rounds, each round deepens the previous conclusions
- **Custom analysis modules**: Add, edit, delete, or restore default modules
- **Extra instructions**: Append custom requirements to guide AI analysis direction

## Advanced: Chromium Browser Collection

DuckDuckGo has limited coverage for Chinese social platforms. For richer data, use Playwright/Selenium with Chromium.

### Playwright (Recommended)

```bash
pip install playwright
playwright install chromium
```

After collecting content from Bilibili/Weibo/Zhihu, save results as CSV and import via the "Upload CSV/Excel" mode.

See the built-in "🔧 Collection Guide" tab for detailed code examples.

### CSV Format for Collected Data

| Column | Required | Description |
|--------|----------|-------------|
| title | Yes | Content title / first 100 chars of text |
| url | No | Original link |
| content | No | Full text / summary |
| platform | No | Platform name (auto-detected if empty) |
| keyword | No | Search keyword |

### Notes

- First-time collection from Bilibili/Weibo requires manual QR code login; use `headless=False` mode
- Control crawl rate: ≥1 second between requests to avoid anti-bot triggers
- Bilibili search API has WBI signature verification; Playwright rendering bypasses this
- Only collect publicly available content; respect each platform's robots.txt

## Limitations

- Search results come from DuckDuckGo public search; no comment/interaction data
- Full data from Bilibili, Douyin, etc. requires login or dedicated APIs
- Sentiment analysis is keyword-based; cannot detect sarcasm or memes
- Recommended: ≤10 keywords, 5-50 results per keyword
