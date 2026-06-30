#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络热点舆情分析系统 - Streamlit Web应用
输入关键词搜索互联网，或上传CSV数据，完成平台识别、分类、情感分析，一键导出PDF报告。
"""

import streamlit as st
import sys
import os
import json
import tempfile
import time
from datetime import datetime
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from searcher import (search_hotspots, analyze_results, parse_uploaded_csv,
                       CATEGORY_KEYWORDS, POSITIVE_WORDS, NEGATIVE_WORDS)
from visualizer import generate_pdf_report


# ── i18n 翻译字典 ──
LANG = {
    "zh": {
        # Sidebar
        "app_title": "网络热点分析",
        "app_caption": "搜索互联网或上传数据，一键生成舆情分析报告",
        "ai_analysis": "AI分析（可选）",
        "api_key_help": "填入后可生成AI深度分析文本，留空则仅生成数据报告",
        "api_base_help": "默认使用DeepSeek官方，也可替换为兼容接口",
        "search_params": "搜索参数",
        "max_results_label": "每个关键词搜索条数",
        "platform_filter_label": "平台限定",
        "platform_all": "全部",
        "ai_prompt_config": "AI提示词配置",
        "analysis_rounds_label": "分析轮次",
        "analysis_rounds_help": "每轮AI会基于上一轮结论深化分析，轮次越多越深入但耗时越长",
        "analysis_modules": "**分析模块**",
        "new_module_label": "新增模块名称",
        "new_module_placeholder": "输入后按回车添加",
        "extra_instructions_label": "额外指令",
        "extra_instructions_placeholder": "如：重点关注游戏行业、需对比上期数据、强调品牌影响...",
        "extra_instructions_help": "追加到提示词末尾的额外要求，会指导AI的分析方向",
        "reset_modules": "恢复默认模块",
        "delete_module_help": "删除此模块",
        # Main
        "page_title": "网络热点舆情分析",
        "main_title": "🌐 网络热点舆情分析系统",
        "main_desc": "输入关键词搜索互联网，或上传CSV数据，自动完成平台识别、内容分类、情感分析，一键导出PDF报告。",
        "data_source": "数据来源",
        "search_mode": "🔍 关键词搜索",
        "upload_mode": "📤 上传CSV/Excel",
        "kw_input_label": "输入关键词（逗号分隔，如：DeepSeek, 高考, 俄乌冲突）",
        "kw_input_placeholder": "多个关键词用英文逗号或中文逗号分隔...",
        "search_btn": "🔍 开始搜索",
        "warn_no_keyword": "请输入至少一个关键词",
        "warn_too_many_kw": "关键词最多10个，当前输入了 {} 个",
        "spinner_searching": "正在搜索 {} 个关键词...",
        "search_success": "搜索完成！耗时 {:.1f}s，共 {} 条结果",
        "warn_no_results": "未搜到结果。可能原因：①关键词太生僻 ②DuckDuckGo无法访问 ③平台限定太严格。试试换个关键词或选'全部'平台。",
        "error_search": "搜索失败：{}",
        "info_install_ddgs": "请安装搜索库: pip install ddgs",
        # Upload
        "upload_label": "上传CSV或Excel文件",
        "upload_help": "CSV需含 title 列，可选 url/content/platform/category/sentiment/keyword 列",
        "info_rows": "读取到 {} 行数据，列名: {}",
        "error_no_title": "CSV必须包含 title 或 标题 列",
        "analyze_btn": "📊 开始分析",
        "spinner_parsing": "正在解析数据...",
        "parse_success": "解析完成！共 {} 条有效数据",
        "error_parse": "文件解析失败: {}",
        # Metrics
        "metric_total": "数据总量",
        "metric_platforms": "覆盖平台",
        "metric_categories": "内容分类",
        "metric_negative": "负面内容",
        # Tabs
        "tab_platform": "📊 平台对比",
        "tab_hotspot": "🔥 热点排行",
        "tab_sentiment": "😐 情感分析",
        "tab_risk": "⚠️ 风险预警",
        "tab_export": "📥 导出报告",
        "tab_guide": "🔧 采集指引",
        # Tab1
        "platform_sub": "平台数据分布与对比",
        "chart_platform_dist": "平台内容分布",
        "chart_sentiment_compare": "各平台情感对比",
        "platform_detail": "平台数据详情",
        "col_platform": "平台",
        "col_count": "内容数",
        "col_positive": "正面",
        "col_neutral": "中性",
        "col_negative": "负面",
        "col_neg_rate": "负面率",
        # Tab2
        "hotspot_sub": "内容分类与热点排行",
        "chart_category_rank": "内容分类排行",
        "chart_category_pie": "分类占比",
        "kw_rank_sub": "关键词搜索结果数排行",
        "chart_kw_results": "关键词搜索结果数",
        "word_freq_sub": "高频词 TOP20",
        "chart_word_freq": "高频词排行",
        # Tab3
        "sentiment_sub": "情感分析详情",
        "chart_sentiment_overall": "整体情感分布",
        "chart_platform_neg_rate": "平台负面率排行",
        "chart_category_neg_rate": "分类负面率排行",
        "neg_rate_ylabel": "负面率 (%)",
        "neg_samples_sub": "负面内容样本",
        "no_title": "(无标题)",
        "label_keyword": "**关键词:**",
        "label_category": "**分类:**",
        "label_snippet": "**摘要:**",
        "label_link": "**链接:**",
        "link_open": "打开",
        # Tab4
        "risk_sub": "舆情风险预警",
        "risk_high": "高危",
        "risk_mid": "中危",
        "risk_high_plat_title": "{} 负面率达 {}%",
        "risk_high_plat_detail": "该平台搜索结果中负面内容占比超过20%，需重点关注",
        "risk_mid_plat_title": "{} 负面率 {}%",
        "risk_mid_plat_detail": "该平台搜索结果中负面内容占比达{}%，建议持续关注",
        "risk_high_cat_title": "{}领域负面率达 {}%",
        "risk_high_cat_detail": "{}相关内容负面情绪集中，可能引发舆论发酵",
        "risk_mid_cat_title": "{}领域负面率 {}%",
        "risk_mid_cat_detail": "{}相关内容存在一定负面情绪",
        "risk_kw_title": '关键词"{}"负面内容集中({}条)',
        "risk_kw_detail": "该关键词下的搜索结果负面内容较多，建议重点关注相关舆情",
        "high_alert": "### 🔴 高危预警",
        "mid_alert": "### 🟡 中危预警",
        "no_high_mid_risk": "当前未检测到高/中危舆情风险",
        "no_risk": "✅ 当前未检测到明显舆情风险，整体态势平稳",
        # Limitations
        "limitations_title": "### ⚠️ 分析局限性",
        "limitations_content": (
            "① 数据来源为搜索引擎公开结果，不含评论区互动数据（点赞/评论/转发），情感分析仅基于标题和摘要\n"
            "② B站、抖音等平台需登录或专用API才能获取完整互动数据，本工具受此限制\n"
            "③ 简单情感分析无法识别"玩梗""反讽"等复杂语用场景，负面率可能低估\n"
            "④ 搜索结果排序受搜索引擎算法影响，不代表全平台真实声量排序\n"
            "⑤ 如需更精确的分析，建议上传自行采集的CSV数据（含完整评论内容）"
        ),
        # Tab5
        "export_sub": "导出PDF报告",
        "data_report_title": "#### 📊 数据可视化报告",
        "data_report_desc": "包含7页图表：封面、平台分布、分类分布、情感分析、负面率对比、关键词排行、热点排行",
        "gen_data_btn": "生成数据报告",
        "spinner_gen_pdf": "正在生成PDF...",
        "download_data_btn": "📥 下载数据报告",
        "data_report_filename": "网络热点舆情分析_{}",
        "full_report_title": "#### 📊+📝 完整分析报告",
        "full_report_desc": "数据图表 + AI深度分析文本（需要DeepSeek API Key）",
        "warn_no_api_key": "请先在侧边栏填入DeepSeek API Key",
        "gen_full_btn": "生成完整报告",
        "spinner_ai_analysis": "正在调用AI分析{}，预计{}-{}分钟...",
        "round_hint": "，{}轮分析",
        "download_full_btn": "📥 下载完整报告",
        "full_report_filename": "网络热点舆情分析_完整报告_{}",
        "error_gen": "生成失败: {}",
        # Tab6
        "guide_sub": "进阶数据采集指引",
        "guide_content": (
            "本系统默认使用DuckDuckGo搜索公开网页，但中文社交平台（B站、抖音、微博等）的搜索覆盖有限。  \n"
            "如需更丰富的数据，可使用浏览器自动化工具（Chromium + Playwright/Selenium）进行采集，然后将结果上传到本系统分析。\n\n"
            "---\n"
            "### 📦 方案一：Playwright（推荐）\n\n"
            "**1. 安装**\n"
            "```bash\n"
            "pip install playwright\n"
            "playwright install chromium\n"
            "```\n\n"
            "**2. B站搜索采集示例**\n"
            "```python\n"
            "from playwright.sync_api import sync_playwright\n"
            "import json, time\n\n"
            "def search_bilibili(keyword, max_scroll=5):\n"
            "    results = []\n"
            "    with sync_playwright() as p:\n"
            "        browser = p.chromium.launch(headless=False)\n"
            "        context = browser.new_context()\n"
            "        page = context.new_page()\n\n"
            "        page.goto('https://www.bilibili.com')\n"
            "        input('登录后按回车继续...')\n\n"
            "        page.goto(f'https://search.bilibili.com/all?keyword={keyword}')\n"
            "        time.sleep(2)\n\n"
            "        for _ in range(max_scroll):\n"
            "            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')\n"
            "            time.sleep(1)\n\n"
            "        items = page.query_selector_all('.video-item.card')\n"
            "        for item in items:\n"
            "            title_el = item.query_selector('a.title')\n"
            "            if title_el:\n"
            "                results.append({\n"
            "                    'title': title_el.inner_text(),\n"
            "                    'url': 'https:' + title_el.get_attribute('href') if title_el.get_attribute('href') else '',\n"
            "                    'platform': 'B站',\n"
            "                    'keyword': keyword,\n"
            "                })\n\n"
            "        browser.close()\n"
            "    return results\n\n"
            "data = search_bilibili('原神4.7')\n"
            "with open('bilibili_data.json', 'w', encoding='utf-8') as f:\n"
            "    json.dump(data, f, ensure_ascii=False, indent=2)\n"
            "```\n\n"
            "**3. 微博搜索采集示例**\n"
            "```python\n"
            "def search_weibo(keyword, max_scroll=3):\n"
            "    results = []\n"
            "    with sync_playwright() as p:\n"
            "        browser = p.chromium.launch(headless=False)\n"
            "        context = browser.new_context()\n"
            "        page = context.new_page()\n"
            "        page.goto('https://s.weibo.com/weibo?q=' + keyword)\n"
            "        input('登录微博后按回车继续...')\n\n"
            "        for _ in range(max_scroll):\n"
            "            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')\n"
            "            time.sleep(1.5)\n\n"
            "        items = page.query_selector_all('.card-wrap .content')\n"
            "        for item in items:\n"
            "            text = item.inner_text().strip()\n"
            "            if text:\n"
            "                results.append({\n"
            "                    'title': text[:100],\n"
            "                    'url': '',\n"
            "                    'platform': '微博',\n"
            "                    'keyword': keyword,\n"
            "                })\n"
            "        browser.close()\n"
            "    return results\n"
            "```\n\n"
            "---\n"
            "### 📦 方案二：Selenium\n\n"
            "```bash\n"
            "pip install selenium\n"
            "```\n\n"
            "```python\n"
            "from selenium import webdriver\n"
            "from selenium.webdriver.common.by import By\n"
            "from selenium.webdriver.chrome.service import Service\n"
            "import time\n\n"
            "def search_zhihu(keyword):\n"
            "    options = webdriver.ChromeOptions()\n"
            "    options.add_argument('--disable-blink-features=AutomationControlled')\n"
            "    driver = webdriver.Chrome(options=options)\n\n"
            "    driver.get(f'https://www.zhihu.com/search?type=content&q={keyword}')\n"
            "    time.sleep(3)\n\n"
            "    results = []\n"
            "    items = driver.find_elements(By.CSS_SELECTOR, '.SearchResult-Card')\n"
            "    for item in items:\n"
            "        title_el = item.find_elements(By.CSS_SELECTOR, 'h2 a')\n"
            "        if title_el:\n"
            "            results.append({\n"
            "                'title': title_el[0].text,\n"
            "                'url': title_el[0].get_attribute('href'),\n"
            "                'platform': '知乎',\n"
            "                'keyword': keyword,\n"
            "            })\n\n"
            "    driver.quit()\n"
            "    return results\n"
            "```\n\n"
            "---\n"
            "### 📋 采集数据格式\n\n"
            "采集完成后，将数据整理为CSV文件上传到本系统，要求：\n\n"
            "| 列名 | 必填 | 说明 |\n"
            "|------|------|------|\n"
            "| title | ✅ | 内容标题/正文前100字 |\n"
            "| url | ❌ | 原文链接 |\n"
            "| content | ❌ | 正文/摘要 |\n"
            "| platform | ❌ | 平台名（不填则自动识别） |\n"
            "| keyword | ❌ | 搜索关键词 |\n\n"
            "示例CSV：\n"
            "```\n"
            "title,url,content,platform,keyword\n"
            "原神4.7版本评测,https://bilibili.com/xxx,纳塔版本...,B站,原神4.7\n"
            "```\n\n"
            "---\n"
            "### ⚠️ 注意事项\n\n"
            "① **首次运行需手动登录**：B站/微博需扫码登录才能搜索，建议首次用`headless=False`有界面模式登录\n"
            "② **保存Cookie复用**：登录后可导出`context.storage_state()`保存Cookie，后续免登录\n"
            "③ **控制频率**：每次请求间隔≥1秒，滚动间隔≥1.5秒，避免触发反爬\n"
            "④ **B站WBI签名**：B站搜索API有WBI签名校验，直接请求API会返回-799，用Playwright渲染页面可绕过\n"
            "⑤ **采集量建议**：每个关键词采集20-50条即可，数据量过大会降低分析效率\n"
            "⑥ **合法性**：仅采集公开内容，不采集用户隐私数据，遵守各平台robots.txt\n\n"
            "---\n"
            "### 🔄 完整工作流\n\n"
            "```\n"
            "1. 用Playwright/Selenium采集 → 得到JSON/CSV数据\n"
            "2. 在本系统选择"上传CSV/Excel"模式 → 上传采集数据\n"
            "3. 系统自动完成平台识别 + 内容分类 + 情感分析\n"
            "4. 查看分析结果 → 导出PDF报告\n"
            "```"
        ),
        # Usage
        "usage_title": "### 🌐 使用说明",
        "usage_content": (
            "**方式一：关键词搜索**\n"
            "1. 选择"关键词搜索"模式\n"
            "2. 输入关键词（逗号分隔），如 "DeepSeek, 高考, 俄乌冲突"\n"
            "3. 点击"开始搜索"，系统自动搜索互联网内容\n\n"
            "**方式二：上传数据**\n"
            "1. 选择"上传CSV/Excel"模式\n"
            "2. 上传含 title 列的CSV文件\n"
            "3. 系统自动识别平台、分类和情感\n\n"
            "**两种模式均支持：**\n"
            "- 📊 平台对比分析\n"
            "- 🔥 热点排行与高频词\n"
            "- 😐 情感分析与负面率\n"
            "- ⚠️ 舆情风险预警\n"
            "- 📥 一键导出PDF报告\n"
            "- 可选DeepSeek AI深度分析"
        ),
        "quick_exp_sub": "💡 快速体验",
        "quick_exp_desc": "没有数据？点击下方按钮加载内置示例数据集（589条B站+抖音真实用户评论，覆盖9大分类），即刻体验完整分析流程。",
        "load_sample_btn": "📂 加载示例数据集",
        "spinner_loading": "正在加载 {} 条示例数据...",
        "sample_loaded": "示例数据加载完成！共 {} 条数据，覆盖 {} 个平台、{} 个分类",
        "error_load_sample": "加载示例数据失败: {}",
        "warn_no_sample": "示例数据文件不存在，请确认 sample_data.csv 在同一目录下",
        # Default modules
        "default_mod_1": "整体舆情态势",
        "default_mod_2": "平台舆论差异",
        "default_mod_3": "核心风险点TOP5",
        "default_mod_4": "情感分布判断",
        "default_mod_5": "舆情走势预判",
        "default_mod_6": "应对建议",
        # DeepSeek prompt
        "ds_role": "你是数据分析专家，基于以下网络热点搜索数据生成舆情分析报告。直接输出报告正文，不要自我介绍，不要写AI助手相关内容。",
        "ds_data_overview": "数据概况",
        "ds_total": "搜索结果总数",
        "ds_keywords": "搜索关键词",
        "ds_platform_dist": "平台分布",
        "ds_category": "内容分类",
        "ds_sentiment": "情感分布",
        "ds_platform_neg": "各平台负面率",
        "ds_neg_samples": "负面内容样本",
        "ds_sample": "样本",
        "ds_title_label": "标题",
        "ds_snippet_label": "摘要",
        "ds_output_modules": "请输出{}个模块的分析：",
        "ds_multi_round": "【多轮分析要求】共需进行{}轮分析。每轮在前一轮结论基础上深化，第1轮为初步分析，后续轮次需指出前轮的不足并补充新视角。最终输出合并所有轮次的综合结论。",
        "ds_extra": "【额外要求】{}",
        "ds_deepen": "请基于你上一轮的分析结论，进行第{}轮深化分析。要求：①指出前轮分析的不足或遗漏 ②补充新的数据视角或跨维度关联 ③更新风险判断和结论。保持原有模块结构，输出完整深化版报告。",
        "ds_api_fail": "API调用失败(第{}轮): {} - {}",
        "ds_round_result": "（经{}轮深化分析）",
        "item_suffix": "条",
    },
    "en": {
        # Sidebar
        "app_title": "Hotspot Analyzer",
        "app_caption": "Search the web or upload data to generate sentiment analysis reports",
        "ai_analysis": "AI Analysis (Optional)",
        "api_key_help": "Fill in to generate AI analysis; leave empty for data-only report",
        "api_base_help": "Default: DeepSeek official; replace with compatible endpoint",
        "search_params": "Search Parameters",
        "max_results_label": "Results per keyword",
        "platform_filter_label": "Platform Filter",
        "platform_all": "All",
        "ai_prompt_config": "AI Prompt Config",
        "analysis_rounds_label": "Analysis Rounds",
        "analysis_rounds_help": "Each round deepens analysis based on previous conclusions; more rounds = deeper but slower",
        "analysis_modules": "**Analysis Modules**",
        "new_module_label": "New module name",
        "new_module_placeholder": "Type and press Enter to add",
        "extra_instructions_label": "Extra Instructions",
        "extra_instructions_placeholder": "e.g., Focus on gaming industry, compare with previous period...",
        "extra_instructions_help": "Appended to prompt end; guides AI analysis direction",
        "reset_modules": "Reset to Default",
        "delete_module_help": "Delete this module",
        # Main
        "page_title": "Hotspot Sentiment Analyzer",
        "main_title": "🌐 Hotspot Sentiment Analyzer",
        "main_desc": "Enter keywords to search the web, or upload CSV data for automatic platform detection, content classification, and sentiment analysis. Export PDF reports with one click.",
        "data_source": "Data Source",
        "search_mode": "🔍 Keyword Search",
        "upload_mode": "📤 Upload CSV/Excel",
        "kw_input_label": "Enter keywords (comma-separated, e.g.: DeepSeek, AI, climate)",
        "kw_input_placeholder": "Separate multiple keywords with commas...",
        "search_btn": "🔍 Start Search",
        "warn_no_keyword": "Please enter at least one keyword",
        "warn_too_many_kw": "Max 10 keywords, you entered {}",
        "spinner_searching": "Searching {} keywords...",
        "search_success": "Search complete! {:.1f}s, {} results",
        "warn_no_results": "No results. Possible reasons: ①Niche keywords ②DuckDuckGo unavailable ③Platform filter too strict. Try different keywords or 'All' platforms.",
        "error_search": "Search failed: {}",
        "info_install_ddgs": "Install search library: pip install ddgs",
        # Upload
        "upload_label": "Upload CSV or Excel file",
        "upload_help": "CSV must have 'title' column; optional: url/content/platform/category/sentiment/keyword",
        "info_rows": "Read {} rows, columns: {}",
        "error_no_title": "CSV must contain 'title' or '标题' column",
        "analyze_btn": "📊 Start Analysis",
        "spinner_parsing": "Parsing data...",
        "parse_success": "Parsing complete! {} valid records",
        "error_parse": "File parsing failed: {}",
        # Metrics
        "metric_total": "Total Data",
        "metric_platforms": "Platforms",
        "metric_categories": "Categories",
        "metric_negative": "Negative Content",
        # Tabs
        "tab_platform": "📊 Platform",
        "tab_hotspot": "🔥 Hotspots",
        "tab_sentiment": "😐 Sentiment",
        "tab_risk": "⚠️ Risk Alert",
        "tab_export": "📥 Export",
        "tab_guide": "🔧 Guide",
        # Tab1
        "platform_sub": "Platform Data Distribution & Comparison",
        "chart_platform_dist": "Platform Content Distribution",
        "chart_sentiment_compare": "Sentiment Comparison by Platform",
        "platform_detail": "Platform Data Details",
        "col_platform": "Platform",
        "col_count": "Count",
        "col_positive": "Positive",
        "col_neutral": "Neutral",
        "col_negative": "Negative",
        "col_neg_rate": "Neg. Rate",
        # Tab2
        "hotspot_sub": "Content Category & Hotspot Rankings",
        "chart_category_rank": "Content Category Rankings",
        "chart_category_pie": "Category Proportion",
        "kw_rank_sub": "Keyword Search Result Rankings",
        "chart_kw_results": "Keyword Search Results",
        "word_freq_sub": "Top 20 Frequent Words",
        "chart_word_freq": "Word Frequency Rankings",
        # Tab3
        "sentiment_sub": "Sentiment Analysis Details",
        "chart_sentiment_overall": "Overall Sentiment Distribution",
        "chart_platform_neg_rate": "Platform Negative Rate Rankings",
        "chart_category_neg_rate": "Category Negative Rate Rankings",
        "neg_rate_ylabel": "Neg. Rate (%)",
        "neg_samples_sub": "Negative Content Samples",
        "no_title": "(No title)",
        "label_keyword": "**Keyword:**",
        "label_category": "**Category:**",
        "label_snippet": "**Snippet:**",
        "label_link": "**Link:**",
        "link_open": "Open",
        # Tab4
        "risk_sub": "Sentiment Risk Alerts",
        "risk_high": "High",
        "risk_mid": "Medium",
        "risk_high_plat_title": "{} negative rate reaches {}%",
        "risk_high_plat_detail": "Negative content exceeds 20% on this platform; requires close attention",
        "risk_mid_plat_title": "{} negative rate {}%",
        "risk_mid_plat_detail": "Negative content at {}% on this platform; monitor closely",
        "risk_high_cat_title": "{} category negative rate reaches {}%",
        "risk_high_cat_detail": "Concentrated negative sentiment in {}; may trigger public debate",
        "risk_mid_cat_title": "{} category negative rate {}%",
        "risk_mid_cat_detail": "Some negative sentiment in {}",
        "risk_kw_title": 'Keyword "{}" concentrated negative ({} items)',
        "risk_kw_detail": "High negative content for this keyword; monitor related sentiment",
        "high_alert": "### 🔴 High Risk Alerts",
        "mid_alert": "### 🟡 Medium Risk Alerts",
        "no_high_mid_risk": "No high/medium risk detected",
        "no_risk": "✅ No significant risks detected; overall sentiment is stable",
        # Limitations
        "limitations_title": "### ⚠️ Analysis Limitations",
        "limitations_content": (
            "① Data sourced from search engine public results, excluding comment interactions (likes/comments/shares); sentiment analysis based only on titles and snippets\n"
            "② Platforms like Bilibili & Douyin require login or dedicated APIs for full interaction data; this tool is limited by this\n"
            "③ Simple sentiment analysis cannot detect complex usage like memes or sarcasm; negative rate may be underestimated\n"
            "④ Search result ranking is influenced by search engine algorithms and does not represent true volume ranking across platforms\n"
            "⑤ For more accurate analysis, upload self-collected CSV data with full comment content"
        ),
        # Tab5
        "export_sub": "Export PDF Report",
        "data_report_title": "#### 📊 Data Visualization Report",
        "data_report_desc": "Includes 7 pages: cover, platform distribution, category distribution, sentiment analysis, negative rate comparison, keyword rankings, hotspot rankings",
        "gen_data_btn": "Generate Data Report",
        "spinner_gen_pdf": "Generating PDF...",
        "download_data_btn": "📥 Download Data Report",
        "data_report_filename": "Hotspot_Analysis_{}",
        "full_report_title": "#### 📊+📝 Full Analysis Report",
        "full_report_desc": "Data charts + AI deep analysis text (DeepSeek API Key required)",
        "warn_no_api_key": "Please enter DeepSeek API Key in the sidebar",
        "gen_full_btn": "Generate Full Report",
        "spinner_ai_analysis": "Calling AI analysis{}, estimated {}-{} min...",
        "round_hint": ", {} rounds",
        "download_full_btn": "📥 Download Full Report",
        "full_report_filename": "Hotspot_Analysis_Full_{}",
        "error_gen": "Generation failed: {}",
        # Tab6
        "guide_sub": "Advanced Data Collection Guide",
        "guide_content": (
            "This system uses DuckDuckGo by default to search public web pages, but coverage of Chinese social platforms (Bilibili, Douyin, Weibo, etc.) is limited.  \n"
            "For richer data, use browser automation tools (Chromium + Playwright/Selenium) for collection, then upload results to this system for analysis.\n\n"
            "---\n"
            "### 📦 Option 1: Playwright (Recommended)\n\n"
            "**1. Installation**\n"
            "```bash\n"
            "pip install playwright\n"
            "playwright install chromium\n"
            "```\n\n"
            "**2. Bilibili Search Example**\n"
            "```python\n"
            "from playwright.sync_api import sync_playwright\n"
            "import json, time\n\n"
            "def search_bilibili(keyword, max_scroll=5):\n"
            "    results = []\n"
            "    with sync_playwright() as p:\n"
            "        browser = p.chromium.launch(headless=False)\n"
            "        context = browser.new_context()\n"
            "        page = context.new_page()\n\n"
            "        page.goto('https://www.bilibili.com')\n"
            "        input('Login and press Enter to continue...')\n\n"
            "        page.goto(f'https://search.bilibili.com/all?keyword={keyword}')\n"
            "        time.sleep(2)\n\n"
            "        for _ in range(max_scroll):\n"
            "            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')\n"
            "            time.sleep(1)\n\n"
            "        items = page.query_selector_all('.video-item.card')\n"
            "        for item in items:\n"
            "            title_el = item.query_selector('a.title')\n"
            "            if title_el:\n"
            "                results.append({\n"
            "                    'title': title_el.inner_text(),\n"
            "                    'url': 'https:' + title_el.get_attribute('href') if title_el.get_attribute('href') else '',\n"
            "                    'platform': 'B站',\n"
            "                    'keyword': keyword,\n"
            "                })\n\n"
            "        browser.close()\n"
            "    return results\n\n"
            "data = search_bilibili('原神4.7')\n"
            "with open('bilibili_data.json', 'w', encoding='utf-8') as f:\n"
            "    json.dump(data, f, ensure_ascii=False, indent=2)\n"
            "```\n\n"
            "**3. Weibo Search Example**\n"
            "```python\n"
            "def search_weibo(keyword, max_scroll=3):\n"
            "    results = []\n"
            "    with sync_playwright() as p:\n"
            "        browser = p.chromium.launch(headless=False)\n"
            "        context = browser.new_context()\n"
            "        page = context.new_page()\n"
            "        page.goto('https://s.weibo.com/weibo?q=' + keyword)\n"
            "        input('Login to Weibo and press Enter to continue...')\n\n"
            "        for _ in range(max_scroll):\n"
            "            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')\n"
            "            time.sleep(1.5)\n\n"
            "        items = page.query_selector_all('.card-wrap .content')\n"
            "        for item in items:\n"
            "            text = item.inner_text().strip()\n"
            "            if text:\n"
            "                results.append({\n"
            "                    'title': text[:100],\n"
            "                    'url': '',\n"
            "                    'platform': '微博',\n"
            "                    'keyword': keyword,\n"
            "                })\n"
            "        browser.close()\n"
            "    return results\n"
            "```\n\n"
            "---\n"
            "### 📦 Option 2: Selenium\n\n"
            "```bash\n"
            "pip install selenium\n"
            "```\n\n"
            "```python\n"
            "from selenium import webdriver\n"
            "from selenium.webdriver.common.by import By\n"
            "from selenium.webdriver.chrome.service import Service\n"
            "import time\n\n"
            "def search_zhihu(keyword):\n"
            "    options = webdriver.ChromeOptions()\n"
            "    options.add_argument('--disable-blink-features=AutomationControlled')\n"
            "    driver = webdriver.Chrome(options=options)\n\n"
            "    driver.get(f'https://www.zhihu.com/search?type=content&q={keyword}')\n"
            "    time.sleep(3)\n\n"
            "    results = []\n"
            "    items = driver.find_elements(By.CSS_SELECTOR, '.SearchResult-Card')\n"
            "    for item in items:\n"
            "        title_el = item.find_elements(By.CSS_SELECTOR, 'h2 a')\n"
            "        if title_el:\n"
            "            results.append({\n"
            "                'title': title_el[0].text,\n"
            "                'url': title_el[0].get_attribute('href'),\n"
            "                'platform': '知乎',\n"
            "                'keyword': keyword,\n"
            "            })\n\n"
            "    driver.quit()\n"
            "    return results\n"
            "```\n\n"
            "---\n"
            "### 📋 Collected Data Format\n\n"
            "After collection, organize data into a CSV file and upload to this system. Requirements:\n\n"
            "| Column | Required | Description |\n"
            "|--------|----------|-------------|\n"
            "| title | ✅ | Content title / first 100 chars of text |\n"
            "| url | ❌ | Original link |\n"
            "| content | ❌ | Full text / snippet |\n"
            "| platform | ❌ | Platform name (auto-detected if empty) |\n"
            "| keyword | ❌ | Search keyword |\n\n"
            "Example CSV:\n"
            "```\n"
            "title,url,content,platform,keyword\n"
            "原神4.7版本评测,https://bilibili.com/xxx,纳塔版本...,B站,原神4.7\n"
            "```\n\n"
            "---\n"
            "### ⚠️ Important Notes\n\n"
            "① **First run requires manual login**: Bilibili/Weibo require QR code login for search; use `headless=False` on first run\n"
            "② **Save cookies for reuse**: After login, export `context.storage_state()` to save cookies for future sessions\n"
            "③ **Control frequency**: Keep ≥1s between requests, ≥1.5s between scrolls to avoid anti-bot triggers\n"
            "④ **Bilibili WBI signature**: Bilibili search API uses WBI signature verification; direct API calls return -799; use Playwright rendering to bypass\n"
            "⑤ **Collection volume**: 20-50 items per keyword is sufficient; too much data reduces analysis efficiency\n"
            "⑥ **Legality**: Only collect public content; do not collect user privacy data; comply with each platform's robots.txt\n\n"
            "---\n"
            "### 🔄 Complete Workflow\n\n"
            "```\n"
            "1. Collect with Playwright/Selenium → Get JSON/CSV data\n"
            '2. Select "Upload CSV/Excel" mode in this system → Upload collected data\n'
            "3. System auto-detects platforms + classifies content + analyzes sentiment\n"
            "4. View analysis results → Export PDF report\n"
            "```"
        ),
        # Usage
        "usage_title": "### 🌐 Usage Guide",
        "usage_content": (
            '**Option 1: Keyword Search**\n'
            '1. Select "Keyword Search" mode\n'
            '2. Enter keywords (comma-separated), e.g. "DeepSeek, AI, climate"\n'
            '3. Click "Start Search" to search the web automatically\n\n'
            '**Option 2: Upload Data**\n'
            '1. Select "Upload CSV/Excel" mode\n'
            '2. Upload a CSV file with a title column\n'
            '3. System auto-detects platforms, categories, and sentiment\n\n'
            '**Both modes support:**\n'
            '- 📊 Platform comparison analysis\n'
            '- 🔥 Hotspot rankings & frequent words\n'
            '- 😐 Sentiment analysis & negative rates\n'
            '- ⚠️ Sentiment risk alerts\n'
            '- 📥 One-click PDF report export\n'
            '- Optional DeepSeek AI deep analysis'
        ),
        "quick_exp_sub": "💡 Quick Start",
        "quick_exp_desc": "No data? Load the built-in sample dataset (589 real comments from Bilibili & Douyin, 9 categories) to experience the full analysis.",
        "load_sample_btn": "📂 Load Sample Dataset",
        "spinner_loading": "Loading {} sample records...",
        "sample_loaded": "Sample data loaded! {} records, {} platforms, {} categories",
        "error_load_sample": "Failed to load sample data: {}",
        "warn_no_sample": "Sample data file not found; ensure sample_data.csv is in the same directory",
        # Default modules
        "default_mod_1": "Overall Sentiment Landscape",
        "default_mod_2": "Platform Sentiment Differences",
        "default_mod_3": "Top 5 Core Risk Points",
        "default_mod_4": "Sentiment Distribution Assessment",
        "default_mod_5": "Sentiment Trend Prediction",
        "default_mod_6": "Response Recommendations",
        # DeepSeek prompt
        "ds_role": "You are a data analysis expert. Generate a sentiment analysis report based on the following web hotspot search data. Output the report body directly, no self-introduction, no AI assistant references.",
        "ds_data_overview": "Data Overview",
        "ds_total": "Total search results",
        "ds_keywords": "Search keywords",
        "ds_platform_dist": "Platform Distribution",
        "ds_category": "Content Categories",
        "ds_sentiment": "Sentiment Distribution",
        "ds_platform_neg": "Platform Negative Rates",
        "ds_neg_samples": "Negative Content Samples",
        "ds_sample": "Sample",
        "ds_title_label": "Title",
        "ds_snippet_label": "Snippet",
        "ds_output_modules": "Please analyze the following {} modules:",
        "ds_multi_round": "[Multi-round Analysis] {} rounds required. Each round deepens based on previous conclusions. Round 1 is initial analysis; subsequent rounds must point out gaps and add new perspectives. Final output combines all rounds.",
        "ds_extra": "[Extra Requirements] {}",
        "ds_deepen": "Based on your previous analysis, perform round {} deepened analysis. Requirements: ①Point out gaps from the previous round ②Add new data perspectives or cross-dimensional correlations ③Update risk judgments and conclusions. Maintain the original module structure and output the complete deepened report.",
        "ds_api_fail": "API call failed (round {}): {} - {}",
        "ds_round_result": "(After {} rounds of deep analysis)",
        "item_suffix": " items",
    },
}


# ── 翻译函数 ──
def t(key, *args):
    lang = st.session_state.get("lang", "zh")
    text = LANG.get(lang, LANG["zh"]).get(key, key)
    if args:
        text = text.format(*args)
    return text


# ── 工具函数 ──
def _call_deepseek(api_key, api_base, results, analysis, custom_modules=None, analysis_rounds=1, extra_instructions=""):
    """调用DeepSeek API生成分析文本，支持自定义模块、多轮分析和额外指令"""
    import requests

    item_sfx = t("item_suffix")
    platform_str = "\n".join(f"  {k}: {v}{item_sfx}" for k, v in sorted(analysis['platform_dist'].items(), key=lambda x: x[1], reverse=True))
    category_str = "\n".join(f"  {k}: {v}{item_sfx}" for k, v in sorted(analysis['category_dist'].items(), key=lambda x: x[1], reverse=True))
    sentiment_str = "\n".join(f"  {k}: {v}{item_sfx}" for k, v in analysis['sentiment_dist'].items())
    neg_rate_str = "\n".join(f"  {k}: {v}%" for k, v in sorted(analysis.get('platform_neg_rate', {}).items(), key=lambda x: x[1], reverse=True))

    neg_samples = ""
    for i, r in enumerate(analysis.get('negative_results', [])[:10]):
        neg_samples += f"\n--- {t('ds_sample')}{i+1} [{r['platform']}] ---\n{t('ds_title_label')}: {r['title']}\n{t('ds_snippet_label')}: {r['snippet'][:200]}\n"

    # 构建模块列表
    if not custom_modules:
        custom_modules = [t(f"default_mod_{i}") for i in range(1, 7)]

    modules_text = "\n".join(f"### {i+1}. {mod}" for i, mod in enumerate(custom_modules))

    # 轮次说明
    round_instruction = ""
    if analysis_rounds > 1:
        round_instruction = f"\n\n{t('ds_multi_round', analysis_rounds)}"

    # 额外指令
    extra_text = ""
    if extra_instructions.strip():
        extra_text = f"\n\n{t('ds_extra', extra_instructions.strip())}"

    prompt = f"""{t('ds_role')}

{t('ds_data_overview')}:
  {t('ds_total')}: {analysis['total']}
  {t('ds_keywords')}: {', '.join(st.session_state.get('keywords', []))}

{t('ds_platform_dist')}:
{platform_str}

{t('ds_category')}:
{category_str}

{t('ds_sentiment')}:
{sentiment_str}

{t('ds_platform_neg')}:
{neg_rate_str}

{t('ds_neg_samples')}:
{neg_samples}

{t('ds_output_modules', len(custom_modules))}
{modules_text}
{round_instruction}{extra_text}"""

    messages = [{"role": "user", "content": prompt}]

    # 多轮分析
    for round_idx in range(analysis_rounds):
        if round_idx > 0:
            # 后续轮次：让AI基于前一轮结论深化
            deepen_prompt = t("ds_deepen", round_idx + 1)
            messages.append({"role": "user", "content": deepen_prompt})

        resp = requests.post(
            f"{api_base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4000,
            },
            timeout=120,
        )

        if resp.status_code != 200:
            raise Exception(t("ds_api_fail", round_idx + 1, resp.status_code, resp.text))

        ai_reply = resp.json()['choices'][0]['message']['content']
        messages.append({"role": "assistant", "content": ai_reply})

    # 如果多轮，在最终结果前加说明
    if analysis_rounds > 1:
        return f"{t('ds_round_result', analysis_rounds)}\n\n{ai_reply}"
    return ai_reply


# ── 页面配置 ──
st.set_page_config(
    page_title=t("page_title"),
    page_icon="🌐",
    layout="wide",
)

# ── 自定义CSS ──
st.markdown("""
<style>
    .main-title { font-size: 2rem; font-weight: 700; color: #1a1a2e; }
</style>
""", unsafe_allow_html=True)

# ── 侧边栏 ──
with st.sidebar:
    # 语言切换
    lang_col1, lang_col2 = st.columns(2)
    with lang_col1:
        if st.button("🇨🇳 中文", use_container_width=True, disabled=st.session_state.get("lang", "zh") == "zh"):
            st.session_state["lang"] = "zh"
            st.rerun()
    with lang_col2:
        if st.button("🇬🇧 EN", use_container_width=True, disabled=st.session_state.get("lang", "zh") == "en"):
            st.session_state["lang"] = "en"
            st.rerun()
    st.divider()

    st.image("https://img.icons8.com/fluency/96/globe-earth.png", width=60)
    st.title(t("app_title"))
    st.caption(t("app_caption"))

    st.divider()

    # DeepSeek API（可选）
    st.subheader(t("ai_analysis"))
    deepseek_key = st.text_input("DeepSeek API Key", type="password",
                                  help=t("api_key_help"))
    deepseek_base = st.text_input("API Base URL", value="https://api.deepseek.com/v1",
                                   help=t("api_base_help"))

    st.divider()

    # 搜索参数
    st.subheader(t("search_params"))
    max_results = st.number_input(t("max_results_label"), min_value=5, max_value=50,
                                   value=15, step=5)
    platform_filter_display = st.selectbox(t("platform_filter_label"),
                                    [t("platform_all"), 'B站', '抖音', '微博', '知乎', '小红书'],
                                    index=0)
    platform_filter = '全部' if platform_filter_display == t("platform_all") else platform_filter_display

    st.divider()

    # ── 提示词自定义 ──
    st.subheader(t("ai_prompt_config"))

    # 分析轮次
    analysis_rounds = st.number_input(t("analysis_rounds_label"), min_value=1, max_value=10,
                                       value=1, step=1,
                                       help=t("analysis_rounds_help"))

    # 分析模块管理
    st.markdown(t("analysis_modules"))

    default_modules = [
        t("default_mod_1"),
        t("default_mod_2"),
        t("default_mod_3"),
        t("default_mod_4"),
        t("default_mod_5"),
        t("default_mod_6"),
    ]

    if 'custom_modules' not in st.session_state:
        st.session_state['custom_modules'] = default_modules.copy()

    # 显示并编辑现有模块
    modules_to_remove = []
    for i, mod in enumerate(st.session_state['custom_modules']):
        col_a, col_b = st.columns([5, 1])
        with col_a:
            new_val = st.text_input(f"模块{i+1}", value=mod, key=f"mod_{i}", label_visibility="collapsed")
            if new_val != mod:
                st.session_state['custom_modules'][i] = new_val
        with col_b:
            if st.button("🗑", key=f"del_mod_{i}", help=t("delete_module_help")):
                modules_to_remove.append(i)

    # 删除标记的模块
    for idx in reversed(modules_to_remove):
        st.session_state['custom_modules'].pop(idx)
        st.rerun()

    # 新增模块
    new_module = st.text_input(t("new_module_label"), key="new_module_input", placeholder=t("new_module_placeholder"))
    if new_module and new_module not in st.session_state['custom_modules']:
        st.session_state['custom_modules'].append(new_module)
        st.rerun()

    # 额外指令
    extra_instructions = st.text_area(t("extra_instructions_label"), value="", height=80,
                                       placeholder=t("extra_instructions_placeholder"),
                                       help=t("extra_instructions_help"))

    # 恢复默认
    if st.button(t("reset_modules")):
        st.session_state['custom_modules'] = default_modules.copy()
        st.rerun()

# ── 主区域 ──
st.markdown(f'<p class="main-title">{t("main_title")}</p>', unsafe_allow_html=True)
st.markdown(t("main_desc"))

# ── 数据输入区 ──
data_mode = st.radio(t("data_source"), [t("search_mode"), t("upload_mode")], horizontal=True)

results = None
analysis = None

if data_mode == t("search_mode"):
    kw_input = st.text_area(
        t("kw_input_label"),
        height=80,
        placeholder=t("kw_input_placeholder")
    )

    search_col1, search_col2 = st.columns([1, 4])
    with search_col1:
        search_btn = st.button(t("search_btn"), type="primary", use_container_width=True)

    if search_btn and kw_input.strip():
        keywords = [k.strip() for k in kw_input.replace('，', ',').split(',') if k.strip()]
        if not keywords:
            st.warning(t("warn_no_keyword"))
        elif len(keywords) > 10:
            st.warning(t("warn_too_many_kw", len(keywords)))
        else:
            with st.spinner(t("spinner_searching", len(keywords))):
                t0 = time.time()
                try:
                    results = search_hotspots(
                        keywords=keywords,
                        max_results=max_results,
                        platform_filter=platform_filter,
                    )
                    analysis = analyze_results(results)
                    search_time = time.time() - t0

                    st.session_state['results'] = results
                    st.session_state['analysis'] = analysis
                    st.session_state['keywords'] = keywords

                    st.success(t("search_success", search_time, len(results)))
                    if len(results) == 0:
                        st.warning(t("warn_no_results"))
                except Exception as e:
                    st.error(t("error_search", e))
                    if 'ddgs' in str(e).lower() or 'duckduckgo' in str(e).lower():
                        st.info(t("info_install_ddgs"))
                    st.stop()

else:  # 上传模式
    uploaded_csv = st.file_uploader(
        t("upload_label"),
        type=["csv", "xlsx", "xls"],
        help=t("upload_help")
    )

    if uploaded_csv is not None:
        try:
            import pandas as pd

            if uploaded_csv.name.endswith('.csv'):
                df = pd.read_csv(uploaded_csv)
            else:
                df = pd.read_excel(uploaded_csv)

            st.info(t("info_rows", len(df), list(df.columns)))

            if 'title' not in df.columns and '标题' not in df.columns:
                st.error(t("error_no_title"))
            else:
                if st.button(t("analyze_btn"), type="primary"):
                    with st.spinner(t("spinner_parsing")):
                        results = parse_uploaded_csv(df)
                        analysis = analyze_results(results)

                        st.session_state['results'] = results
                        st.session_state['analysis'] = analysis
                        st.session_state['keywords'] = list(set(r['keyword'] for r in results))

                        st.success(t("parse_success", len(results)))
        except Exception as e:
            st.error(t("error_parse", e))

# ── 显示分析结果 ──
if 'analysis' in st.session_state and st.session_state['analysis']:
    analysis = st.session_state['analysis']
    results = st.session_state.get('results', [])
    keywords = st.session_state.get('keywords', [])

    # ── 概览指标 ──
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t("metric_total"), f"{analysis.get('total', 0):,}")
    with col2:
        st.metric(t("metric_platforms"), f"{len(analysis.get('platform_dist', {}))}")
    with col3:
        st.metric(t("metric_categories"), f"{len(analysis.get('category_dist', {}))}")
    with col4:
        neg_count = len(analysis.get('negative_results', []))
        neg_rate = round(neg_count / max(analysis.get('total', 1), 1) * 100, 1)
        st.metric(t("metric_negative"), f"{neg_count} ({neg_rate}%)")

    # ── Tab区域 ──
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        t("tab_platform"), t("tab_hotspot"), t("tab_sentiment"),
        t("tab_risk"), t("tab_export"), t("tab_guide")
    ])

    # ═══ Tab1: 平台对比 ═══
    with tab1:
        st.subheader(t("platform_sub"))

        import matplotlib.pyplot as plt
        import numpy as np

        pd_data = analysis.get('platform_dist', {})
        ps = analysis.get('platform_sentiment', {})
        pnr = analysis.get('platform_neg_rate', {})

        if pd_data:
            platform_colors = {
                'B站': '#fb7299', '抖音': '#00f2ea', '微博': '#ff8200',
                '知乎': '#0066ff', '小红书': '#ff2442', '今日头条': '#d42d26',
                '微信公众号': '#07c160', '其他': '#818cf8'
            }

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            labels = list(pd_data.keys())
            values = list(pd_data.values())
            clrs = [platform_colors.get(l, '#818cf8') for l in labels]
            ax1.pie(values, labels=labels, colors=clrs, autopct='%1.1f%%', startangle=140)
            ax1.set_title(t("chart_platform_dist"), fontsize=13)

            if ps:
                plat_list = list(ps.keys())
                x = np.arange(len(plat_list))
                w = 0.25
                pos_v = [ps[p].get('正面', 0) for p in plat_list]
                neu_v = [ps[p].get('中性', 0) for p in plat_list]
                neg_v = [ps[p].get('负面', 0) for p in plat_list]

                ax2.bar(x - w, pos_v, w, label=t("col_positive"), color='#34d399', alpha=0.85)
                ax2.bar(x, neu_v, w, label=t("col_neutral"), color='#60a5fa', alpha=0.85)
                ax2.bar(x + w, neg_v, w, label=t("col_negative"), color='#f87171', alpha=0.85)
                ax2.set_xticks(x)
                ax2.set_xticklabels(plat_list, fontsize=10)
                ax2.set_title(t("chart_sentiment_compare"), fontsize=13)
                ax2.legend()
                ax2.grid(axis='y', alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)

        # 平台详情表
        if pd_data:
            st.subheader(t("platform_detail"))
            rows = []
            for p, count in sorted(pd_data.items(), key=lambda x: x[1], reverse=True):
                p_sent = ps.get(p, {})
                total = sum(p_sent.values()) if p_sent else count
                neg = p_sent.get('负面', 0)
                neg_r = round(neg / total * 100, 1) if total > 0 else 0
                rows.append({
                    t("col_platform"): p, t("col_count"): count,
                    t("col_positive"): p_sent.get('正面', 0), t("col_neutral"): p_sent.get('中性', 0), t("col_negative"): neg,
                    t("col_neg_rate"): f"{neg_r}%",
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

    # ═══ Tab2: 热点排行 ═══
    with tab2:
        st.subheader(t("hotspot_sub"))

        cd = analysis.get('category_dist', {})
        kd = analysis.get('keyword_dist', {})

        if cd:
            import matplotlib.pyplot as plt

            sorted_cat = sorted(cd.items(), key=lambda x: x[1], reverse=True)
            cat_labels = [k for k, v in sorted_cat]
            cat_vals = [v for k, v in sorted_cat]
            cat_colors = ['#4C72B0', '#DD8452', '#55A868', '#C44E52', '#8172B3', '#937860', '#64B5CD'][:len(cat_labels)]

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
            ax1.barh(cat_labels[::-1], cat_vals[::-1], color=cat_colors[::-1], alpha=0.85, height=0.6)
            ax1.set_title(t("chart_category_rank"), fontsize=13)
            for i, v in enumerate(cat_vals[::-1]):
                ax1.text(v + 0.2, i, str(v), va='center', fontsize=9)
            ax1.grid(axis='x', alpha=0.3)

            ax2.pie(cat_vals, labels=cat_labels, colors=cat_colors, autopct='%1.1f%%', startangle=140)
            ax2.set_title(t("chart_category_pie"), fontsize=13)
            plt.tight_layout()
            st.pyplot(fig)

        if kd:
            st.subheader(t("kw_rank_sub"))
            import matplotlib.pyplot as plt

            sorted_kw = sorted(kd.items(), key=lambda x: x[1], reverse=True)
            kw_labels = [k for k, v in sorted_kw]
            kw_vals = [v for k, v in sorted_kw]

            fig, ax = plt.subplots(figsize=(12, max(4, len(kw_labels) * 0.5)))
            ax.barh(kw_labels[::-1], kw_vals[::-1], color='#818cf8', alpha=0.85, height=0.6)
            ax.set_title(t("chart_kw_results"), fontsize=13)
            for i, v in enumerate(kw_vals[::-1]):
                ax.text(v + 0.2, i, str(v), va='center', fontsize=9)
            ax.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)

        wf = analysis.get('word_freq', {})
        if wf:
            st.subheader(t("word_freq_sub"))
            import matplotlib.pyplot as plt

            sorted_wf = sorted(wf.items(), key=lambda x: x[1], reverse=True)[:20]
            wf_labels = [k for k, v in sorted_wf]
            wf_vals = [v for k, v in sorted_wf]

            fig, ax = plt.subplots(figsize=(12, 7))
            ax.barh(wf_labels[::-1], wf_vals[::-1], color='#DD8452', alpha=0.85, height=0.6)
            ax.set_title(t("chart_word_freq"), fontsize=13)
            for i, v in enumerate(wf_vals[::-1]):
                ax.text(v + 0.1, i, str(v), va='center', fontsize=8)
            ax.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)

    # ═══ Tab3: 情感分析 ═══
    with tab3:
        st.subheader(t("sentiment_sub"))

        sd = analysis.get('sentiment_dist', {})
        cnr = analysis.get('category_neg_rate', {})

        if sd:
            import matplotlib.pyplot as plt

            chart_count = 1 + (1 if pnr else 0) + (1 if cnr else 0)
            fig, axes = plt.subplots(1, chart_count, figsize=(6 * chart_count, 5))
            if chart_count == 1:
                axes = [axes]

            idx = 0

            # 情感饼图
            sentiment_keys = ['正面', '中性', '负面']
            sentiment_display_labels = [t("col_positive"), t("col_neutral"), t("col_negative")]
            vals = [sd.get(l, 0) for l in sentiment_keys]
            clrs = ['#34d399', '#60a5fa', '#f87171']
            axes[idx].pie(vals, labels=sentiment_display_labels, colors=clrs, autopct='%1.1f%%', startangle=140)
            axes[idx].set_title(t("chart_sentiment_overall"), fontsize=13)
            idx += 1

            # 平台负面率
            if pnr:
                sorted_pnr = sorted(pnr.items(), key=lambda x: x[1], reverse=True)
                p_names = [k for k, v in sorted_pnr]
                p_vals = [v for k, v in sorted_pnr]
                bar_c = ['#f87171' if v >= 20 else '#fbbf24' if v >= 10 else '#60a5fa' for v in p_vals]
                axes[idx].bar(p_names, p_vals, color=bar_c, alpha=0.85, width=0.5)
                axes[idx].set_title(t("chart_platform_neg_rate"), fontsize=13)
                axes[idx].set_ylabel(t("neg_rate_ylabel"))
                axes[idx].tick_params(axis='x', rotation=30)
                for i, v in enumerate(p_vals):
                    axes[idx].text(i, v + 0.3, f'{v}%', ha='center', fontsize=9)
                axes[idx].grid(axis='y', alpha=0.3)
                idx += 1

            # 分类负面率
            if cnr:
                sorted_cnr = sorted(cnr.items(), key=lambda x: x[1], reverse=True)
                c_names = [k for k, v in sorted_cnr]
                c_vals = [v for k, v in sorted_cnr]
                bar_c2 = ['#f87171' if v >= 20 else '#fbbf24' if v >= 10 else '#60a5fa' for v in c_vals]
                axes[idx].barh(c_names[::-1], c_vals[::-1], color=bar_c2[::-1], alpha=0.85, height=0.6)
                axes[idx].set_title(t("chart_category_neg_rate"), fontsize=13)
                axes[idx].set_xlabel(t("neg_rate_ylabel"))
                axes[idx].grid(axis='x', alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)

        # 负面内容样本
        neg_results = analysis.get('negative_results', [])
        if neg_results:
            st.subheader(t("neg_samples_sub"))
            for i, r in enumerate(neg_results[:15]):
                title_preview = r['title'][:60] if r['title'] else t("no_title")
                with st.expander(f"[{r['platform']}] {title_preview}"):
                    st.markdown(f"{t('label_keyword')} {r['keyword']}")
                    st.markdown(f"{t('label_category')} {r['category']}")
                    if r['snippet']:
                        st.markdown(f"{t('label_snippet')} {r['snippet']}")
                    if r['url']:
                        st.markdown(f"{t('label_link')} [{t('link_open')}]({r['url']})")

    # ═══ Tab4: 风险预警 ═══
    with tab4:
        st.subheader(t("risk_sub"))

        risks = []

        # 高负面率平台
        for p, rate in pnr.items():
            if rate >= 20:
                risks.append({
                    'level': '高危',
                    'title': t("risk_high_plat_title", p, rate),
                    'detail': t("risk_high_plat_detail"),
                })
            elif rate >= 10:
                risks.append({
                    'level': '中危',
                    'title': t("risk_mid_plat_title", p, rate),
                    'detail': t("risk_mid_plat_detail", rate),
                })

        # 高负面率分类
        for c, rate in cnr.items():
            if rate >= 20:
                risks.append({
                    'level': '高危',
                    'title': t("risk_high_cat_title", c, rate),
                    'detail': t("risk_high_cat_detail", c),
                })
            elif rate >= 10:
                risks.append({
                    'level': '中危',
                    'title': t("risk_mid_cat_title", c, rate),
                    'detail': t("risk_mid_cat_detail", c),
                })

        # 负面内容关键词
        neg_kws = Counter(r['keyword'] for r in analysis.get('negative_results', []))
        for kw, count in neg_kws.most_common(5):
            if count >= 3:
                risks.append({
                    'level': '中危',
                    'title': t("risk_kw_title", kw, count),
                    'detail': t("risk_kw_detail"),
                })

        if risks:
            level_order = {'高危': 0, '中危': 1}
            risks.sort(key=lambda x: level_order.get(x['level'], 3))

            high = [r for r in risks if r['level'] == '高危']
            mid = [r for r in risks if r['level'] == '中危']

            if high:
                st.markdown(t("high_alert"))
                for r in high:
                    st.error(f"**{r['title']}**  \n{r['detail']}")

            if mid:
                st.markdown(t("mid_alert"))
                for r in mid[:10]:
                    st.warning(f"**{r['title']}**  \n{r['detail']}")

            if not high and not mid:
                st.success(t("no_high_mid_risk"))
        else:
            st.success(t("no_risk"))

        st.divider()
        st.markdown(t("limitations_title"))
        st.markdown(t("limitations_content"))

    # ═══ Tab5: 导出报告 ═══
    with tab5:
        st.subheader(t("export_sub"))

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(t("data_report_title"))
            st.markdown(t("data_report_desc"))

            if st.button(t("gen_data_btn"), key="gen_data"):
                with st.spinner(t("spinner_gen_pdf")):
                    try:
                        pdf_tmp = tempfile.mktemp(suffix='.pdf')
                        generate_pdf_report(results, analysis, pdf_tmp)
                        with open(pdf_tmp, 'rb') as f:
                            st.download_button(
                                label=t("download_data_btn"),
                                data=f.read(),
                                file_name=t("data_report_filename", datetime.now().strftime('%Y%m%d_%H%M')) + ".pdf",
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(t("error_gen", e))

        with col2:
            st.markdown(t("full_report_title"))
            st.markdown(t("full_report_desc"))

            if not deepseek_key:
                st.warning(t("warn_no_api_key"))

            if st.button(t("gen_full_btn"), key="gen_full", disabled=not deepseek_key):
                round_hint = t("round_hint", analysis_rounds) if analysis_rounds > 1 else ""
                with st.spinner(t("spinner_ai_analysis", round_hint, 1 * analysis_rounds, 2 * analysis_rounds)):
                    try:
                        ai_text = _call_deepseek(
                            deepseek_key, deepseek_base, results, analysis,
                            custom_modules=st.session_state.get('custom_modules'),
                            analysis_rounds=analysis_rounds,
                            extra_instructions=extra_instructions,
                        )

                        pdf_tmp = tempfile.mktemp(suffix='.pdf')
                        generate_pdf_report(results, analysis, pdf_tmp, ai_report_text=ai_text)

                        with open(pdf_tmp, 'rb') as f:
                            st.download_button(
                                label=t("download_full_btn"),
                                data=f.read(),
                                file_name=t("full_report_filename", datetime.now().strftime('%Y%m%d_%H%M')) + ".pdf",
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(t("error_gen", e))

    # ═══ Tab6: 采集指引 ═══
    with tab6:
        st.subheader(t("guide_sub"))
        st.markdown(t("guide_content"))

else:
    # 没有搜索时的引导
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info(f"""
        {t('usage_title')}

        {t('usage_content')}
        """)

    # ── 示例数据加载 ──
    st.divider()
    st.subheader(t("quick_exp_sub"))
    st.markdown(t("quick_exp_desc"))

    if st.button(t("load_sample_btn"), type="primary"):
        sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_data.csv')
        if os.path.exists(sample_path):
            try:
                import pandas as pd
                df = pd.read_csv(sample_path)

                with st.spinner(t("spinner_loading", len(df))):
                    results = parse_uploaded_csv(df)
                    analysis = analyze_results(results)

                    st.session_state['results'] = results
                    st.session_state['analysis'] = analysis
                    st.session_state['keywords'] = list(set(r['keyword'] for r in results if r.get('keyword')))

                    st.success(t("sample_loaded", len(results), len(analysis.get('platform_dist', {})), len(analysis.get('category_dist', {}))))
                    st.rerun()
            except Exception as e:
                st.error(t("error_load_sample", e))
        else:
            st.warning(t("warn_no_sample"))
