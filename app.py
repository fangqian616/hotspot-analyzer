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

# ── 页面配置 ──
st.set_page_config(
    page_title="网络热点舆情分析",
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
    st.image("https://img.icons8.com/fluency/96/globe-earth.png", width=60)
    st.title("网络热点分析")
    st.caption("搜索互联网或上传数据，一键生成舆情分析报告")
    
    st.divider()
    
    # DeepSeek API（可选）
    st.subheader("AI分析（可选）")
    deepseek_key = st.text_input("DeepSeek API Key", type="password",
                                  help="填入后可生成AI深度分析文本，留空则仅生成数据报告")
    deepseek_base = st.text_input("API Base URL", value="https://api.deepseek.com/v1",
                                   help="默认使用DeepSeek官方，也可替换为兼容接口")
    
    st.divider()
    
    # 搜索参数
    st.subheader("搜索参数")
    max_results = st.number_input("每个关键词搜索条数", min_value=5, max_value=50,
                                   value=15, step=5)
    platform_filter = st.selectbox("平台限定",
                                    ['全部', 'B站', '抖音', '微博', '知乎', '小红书'],
                                    index=0)
    
    st.divider()
    
    # ── 提示词自定义 ──
    st.subheader("AI提示词配置")
    
    # 分析轮次
    analysis_rounds = st.number_input("分析轮次", min_value=1, max_value=10,
                                       value=1, step=1,
                                       help="每轮AI会基于上一轮结论深化分析，轮次越多越深入但耗时越长")
    
    # 分析模块管理
    st.markdown("**分析模块**")
    
    default_modules = [
        "整体舆情态势",
        "平台舆论差异",
        "核心风险点TOP5",
        "情感分布判断",
        "舆情走势预判",
        "应对建议",
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
            if st.button("🗑", key=f"del_mod_{i}", help="删除此模块"):
                modules_to_remove.append(i)
    
    # 删除标记的模块
    for idx in reversed(modules_to_remove):
        st.session_state['custom_modules'].pop(idx)
        st.rerun()
    
    # 新增模块
    new_module = st.text_input("新增模块名称", key="new_module_input", placeholder="输入后按回车添加")
    if new_module and new_module not in st.session_state['custom_modules']:
        st.session_state['custom_modules'].append(new_module)
        st.rerun()
    
    # 额外指令
    extra_instructions = st.text_area("额外指令", value="", height=80,
                                       placeholder="如：重点关注游戏行业、需对比上期数据、强调品牌影响...",
                                       help="追加到提示词末尾的额外要求，会指导AI的分析方向")
    
    # 恢复默认
    if st.button("恢复默认模块"):
        st.session_state['custom_modules'] = default_modules.copy()
        st.rerun()

# ── 主区域 ──
st.markdown('<p class="main-title">🌐 网络热点舆情分析系统</p>', unsafe_allow_html=True)
st.markdown("输入关键词搜索互联网，或上传CSV数据，自动完成平台识别、内容分类、情感分析，一键导出PDF报告。")

# ── 数据输入区 ──
data_mode = st.radio("数据来源", ["🔍 关键词搜索", "📤 上传CSV/Excel"], horizontal=True)

results = None
analysis = None

if data_mode == "🔍 关键词搜索":
    kw_input = st.text_area(
        "输入关键词（逗号分隔，如：DeepSeek, 高考, 俄乌冲突）",
        height=80,
        placeholder="多个关键词用英文逗号或中文逗号分隔..."
    )
    
    search_col1, search_col2 = st.columns([1, 4])
    with search_col1:
        search_btn = st.button("🔍 开始搜索", type="primary", use_container_width=True)
    
    if search_btn and kw_input.strip():
        keywords = [k.strip() for k in kw_input.replace('，', ',').split(',') if k.strip()]
        if not keywords:
            st.warning("请输入至少一个关键词")
        elif len(keywords) > 10:
            st.warning(f"关键词最多10个，当前输入了 {len(keywords)} 个")
        else:
            with st.spinner(f"正在搜索 {len(keywords)} 个关键词..."):
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
                    
                    st.success(f"搜索完成！耗时 {search_time:.1f}s，共 {len(results)} 条结果")
                    if len(results) == 0:
                        st.warning("未搜到结果。可能原因：①关键词太生僻 ②DuckDuckGo无法访问 ③平台限定太严格。试试换个关键词或选'全部'平台。")
                except Exception as e:
                    st.error(f"搜索失败：{e}")
                    if 'ddgs' in str(e).lower() or 'duckduckgo' in str(e).lower():
                        st.info("请安装搜索库: pip install ddgs")
                    st.stop()

else:  # 上传模式
    uploaded_csv = st.file_uploader(
        "上传CSV或Excel文件",
        type=["csv", "xlsx", "xls"],
        help="CSV需含 title 列，可选 url/content/platform/category/sentiment/keyword 列"
    )
    
    if uploaded_csv is not None:
        try:
            import pandas as pd
            
            if uploaded_csv.name.endswith('.csv'):
                df = pd.read_csv(uploaded_csv)
            else:
                df = pd.read_excel(uploaded_csv)
            
            st.info(f"读取到 {len(df)} 行数据，列名: {list(df.columns)}")
            
            if 'title' not in df.columns and '标题' not in df.columns:
                st.error("CSV必须包含 title 或 标题 列")
            else:
                if st.button("📊 开始分析", type="primary"):
                    with st.spinner("正在解析数据..."):
                        results = parse_uploaded_csv(df)
                        analysis = analyze_results(results)
                        
                        st.session_state['results'] = results
                        st.session_state['analysis'] = analysis
                        st.session_state['keywords'] = list(set(r['keyword'] for r in results))
                        
                        st.success(f"解析完成！共 {len(results)} 条有效数据")
        except Exception as e:
            st.error(f"文件解析失败: {e}")

# ── 显示分析结果 ──
if 'analysis' in st.session_state and st.session_state['analysis']:
    analysis = st.session_state['analysis']
    results = st.session_state.get('results', [])
    keywords = st.session_state.get('keywords', [])
    
    # ── 概览指标 ──
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("数据总量", f"{analysis.get('total', 0):,}")
    with col2:
        st.metric("覆盖平台", f"{len(analysis.get('platform_dist', {}))}")
    with col3:
        st.metric("内容分类", f"{len(analysis.get('category_dist', {}))}")
    with col4:
        neg_count = len(analysis.get('negative_results', []))
        neg_rate = round(neg_count / max(analysis.get('total', 1), 1) * 100, 1)
        st.metric("负面内容", f"{neg_count} ({neg_rate}%)")
    
    # ── Tab区域 ──
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 平台对比", "🔥 热点排行", "😐 情感分析",
        "⚠️ 风险预警", "📥 导出报告", "🔧 采集指引"
    ])
    
    # ═══ Tab1: 平台对比 ═══
    with tab1:
        st.subheader("平台数据分布与对比")
        
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
            ax1.set_title('平台内容分布', fontsize=13)
            
            if ps:
                plat_list = list(ps.keys())
                x = np.arange(len(plat_list))
                w = 0.25
                pos_v = [ps[p].get('正面', 0) for p in plat_list]
                neu_v = [ps[p].get('中性', 0) for p in plat_list]
                neg_v = [ps[p].get('负面', 0) for p in plat_list]
                
                ax2.bar(x - w, pos_v, w, label='正面', color='#34d399', alpha=0.85)
                ax2.bar(x, neu_v, w, label='中性', color='#60a5fa', alpha=0.85)
                ax2.bar(x + w, neg_v, w, label='负面', color='#f87171', alpha=0.85)
                ax2.set_xticks(x)
                ax2.set_xticklabels(plat_list, fontsize=10)
                ax2.set_title('各平台情感对比', fontsize=13)
                ax2.legend()
                ax2.grid(axis='y', alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
        
        # 平台详情表
        if pd_data:
            st.subheader("平台数据详情")
            rows = []
            for p, count in sorted(pd_data.items(), key=lambda x: x[1], reverse=True):
                p_sent = ps.get(p, {})
                total = sum(p_sent.values()) if p_sent else count
                neg = p_sent.get('负面', 0)
                neg_r = round(neg / total * 100, 1) if total > 0 else 0
                rows.append({
                    '平台': p, '内容数': count,
                    '正面': p_sent.get('正面', 0), '中性': p_sent.get('中性', 0), '负面': neg,
                    '负面率': f"{neg_r}%",
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)
    
    # ═══ Tab2: 热点排行 ═══
    with tab2:
        st.subheader("内容分类与热点排行")
        
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
            ax1.set_title('内容分类排行', fontsize=13)
            for i, v in enumerate(cat_vals[::-1]):
                ax1.text(v + 0.2, i, str(v), va='center', fontsize=9)
            ax1.grid(axis='x', alpha=0.3)
            
            ax2.pie(cat_vals, labels=cat_labels, colors=cat_colors, autopct='%1.1f%%', startangle=140)
            ax2.set_title('分类占比', fontsize=13)
            plt.tight_layout()
            st.pyplot(fig)
        
        if kd:
            st.subheader("关键词搜索结果数排行")
            import matplotlib.pyplot as plt
            
            sorted_kw = sorted(kd.items(), key=lambda x: x[1], reverse=True)
            kw_labels = [k for k, v in sorted_kw]
            kw_vals = [v for k, v in sorted_kw]
            
            fig, ax = plt.subplots(figsize=(12, max(4, len(kw_labels) * 0.5)))
            ax.barh(kw_labels[::-1], kw_vals[::-1], color='#818cf8', alpha=0.85, height=0.6)
            ax.set_title('关键词搜索结果数', fontsize=13)
            for i, v in enumerate(kw_vals[::-1]):
                ax.text(v + 0.2, i, str(v), va='center', fontsize=9)
            ax.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
        
        wf = analysis.get('word_freq', {})
        if wf:
            st.subheader("高频词 TOP20")
            import matplotlib.pyplot as plt
            
            sorted_wf = sorted(wf.items(), key=lambda x: x[1], reverse=True)[:20]
            wf_labels = [k for k, v in sorted_wf]
            wf_vals = [v for k, v in sorted_wf]
            
            fig, ax = plt.subplots(figsize=(12, 7))
            ax.barh(wf_labels[::-1], wf_vals[::-1], color='#DD8452', alpha=0.85, height=0.6)
            ax.set_title('高频词排行', fontsize=13)
            for i, v in enumerate(wf_vals[::-1]):
                ax.text(v + 0.1, i, str(v), va='center', fontsize=8)
            ax.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
    
    # ═══ Tab3: 情感分析 ═══
    with tab3:
        st.subheader("情感分析详情")
        
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
            labels = ['正面', '中性', '负面']
            vals = [sd.get(l, 0) for l in labels]
            clrs = ['#34d399', '#60a5fa', '#f87171']
            axes[idx].pie(vals, labels=labels, colors=clrs, autopct='%1.1f%%', startangle=140)
            axes[idx].set_title('整体情感分布', fontsize=13)
            idx += 1
            
            # 平台负面率
            if pnr:
                sorted_pnr = sorted(pnr.items(), key=lambda x: x[1], reverse=True)
                p_names = [k for k, v in sorted_pnr]
                p_vals = [v for k, v in sorted_pnr]
                bar_c = ['#f87171' if v >= 20 else '#fbbf24' if v >= 10 else '#60a5fa' for v in p_vals]
                axes[idx].bar(p_names, p_vals, color=bar_c, alpha=0.85, width=0.5)
                axes[idx].set_title('平台负面率排行', fontsize=13)
                axes[idx].set_ylabel('负面率 (%)')
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
                axes[idx].set_title('分类负面率排行', fontsize=13)
                axes[idx].set_xlabel('负面率 (%)')
                axes[idx].grid(axis='x', alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
        
        # 负面内容样本
        neg_results = analysis.get('negative_results', [])
        if neg_results:
            st.subheader("负面内容样本")
            for i, r in enumerate(neg_results[:15]):
                title_preview = r['title'][:60] if r['title'] else '(无标题)'
                with st.expander(f"[{r['platform']}] {title_preview}"):
                    st.markdown(f"**关键词:** {r['keyword']}")
                    st.markdown(f"**分类:** {r['category']}")
                    if r['snippet']:
                        st.markdown(f"**摘要:** {r['snippet']}")
                    if r['url']:
                        st.markdown(f"**链接:** [打开]({r['url']})")
    
    # ═══ Tab4: 风险预警 ═══
    with tab4:
        st.subheader("舆情风险预警")
        
        risks = []
        
        # 高负面率平台
        for p, rate in pnr.items():
            if rate >= 20:
                risks.append({
                    'level': '高危', 'title': f'{p} 负面率达 {rate}%',
                    'detail': f'该平台搜索结果中负面内容占比超过20%，需重点关注',
                })
            elif rate >= 10:
                risks.append({
                    'level': '中危', 'title': f'{p} 负面率 {rate}%',
                    'detail': f'该平台搜索结果中负面内容占比达{rate}%，建议持续关注',
                })
        
        # 高负面率分类
        for c, rate in cnr.items():
            if rate >= 20:
                risks.append({
                    'level': '高危', 'title': f'{c}领域负面率达 {rate}%',
                    'detail': f'{c}相关内容负面情绪集中，可能引发舆论发酵',
                })
            elif rate >= 10:
                risks.append({
                    'level': '中危', 'title': f'{c}领域负面率 {rate}%',
                    'detail': f'{c}相关内容存在一定负面情绪',
                })
        
        # 负面内容关键词
        neg_kws = Counter(r['keyword'] for r in analysis.get('negative_results', []))
        for kw, count in neg_kws.most_common(5):
            if count >= 3:
                risks.append({
                    'level': '中危', 'title': f'关键词"{kw}"负面内容集中({count}条)',
                    'detail': '该关键词下的搜索结果负面内容较多，建议重点关注相关舆情',
                })
        
        if risks:
            level_order = {'高危': 0, '中危': 1}
            risks.sort(key=lambda x: level_order.get(x['level'], 3))
            
            high = [r for r in risks if r['level'] == '高危']
            mid = [r for r in risks if r['level'] == '中危']
            
            if high:
                st.markdown("### 🔴 高危预警")
                for r in high:
                    st.error(f"**{r['title']}**  \n{r['detail']}")
            
            if mid:
                st.markdown("### 🟡 中危预警")
                for r in mid[:10]:
                    st.warning(f"**{r['title']}**  \n{r['detail']}")
            
            if not high and not mid:
                st.success("当前未检测到高/中危舆情风险")
        else:
            st.success("✅ 当前未检测到明显舆情风险，整体态势平稳")
        
        st.divider()
        st.markdown("""
        ### ⚠️ 分析局限性
        
        ① 数据来源为搜索引擎公开结果，不含评论区互动数据（点赞/评论/转发），情感分析仅基于标题和摘要
        ② B站、抖音等平台需登录或专用API才能获取完整互动数据，本工具受此限制
        ③ 简单情感分析无法识别"玩梗""反讽"等复杂语用场景，负面率可能低估
        ④ 搜索结果排序受搜索引擎算法影响，不代表全平台真实声量排序
        ⑤ 如需更精确的分析，建议上传自行采集的CSV数据（含完整评论内容）
        """)
    
    # ═══ Tab5: 导出报告 ═══
    with tab5:
        st.subheader("导出PDF报告")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 数据可视化报告")
            st.markdown("包含7页图表：封面、平台分布、分类分布、情感分析、负面率对比、关键词排行、热点排行")
            
            if st.button("生成数据报告", key="gen_data"):
                with st.spinner("正在生成PDF..."):
                    try:
                        pdf_tmp = tempfile.mktemp(suffix='.pdf')
                        generate_pdf_report(results, analysis, pdf_tmp)
                        with open(pdf_tmp, 'rb') as f:
                            st.download_button(
                                label="📥 下载数据报告",
                                data=f.read(),
                                file_name=f"网络热点舆情分析_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"生成失败: {e}")
        
        with col2:
            st.markdown("#### 📊+📝 完整分析报告")
            st.markdown("数据图表 + AI深度分析文本（需要DeepSeek API Key）")
            
            if not deepseek_key:
                st.warning("请先在侧边栏填入DeepSeek API Key")
            
            if st.button("生成完整报告", key="gen_full", disabled=not deepseek_key):
                round_hint = f"，{analysis_rounds}轮分析" if analysis_rounds > 1 else ""
                with st.spinner(f"正在调用AI分析{round_hint}，预计{1*analysis_rounds}-{2*analysis_rounds}分钟..."):
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
                                label="📥 下载完整报告",
                                data=f.read(),
                                file_name=f"网络热点舆情分析_完整报告_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"生成失败: {e}")

    # ═══ Tab6: 采集指引 ═══
    with tab6:
        st.subheader("进阶数据采集指引")
        st.markdown("""
本系统默认使用DuckDuckGo搜索公开网页，但中文社交平台（B站、抖音、微博等）的搜索覆盖有限。  
如需更丰富的数据，可使用浏览器自动化工具（Chromium + Playwright/Selenium）进行采集，然后将结果上传到本系统分析。

---
### 📦 方案一：Playwright（推荐）

**1. 安装**
```bash
pip install playwright
playwright install chromium
```

**2. B站搜索采集示例**
```python
from playwright.sync_api import sync_playwright
import json, time

def search_bilibili(keyword, max_scroll=5):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 首次建议有界面，方便扫码登录
        context = browser.new_context()
        page = context.new_page()
        
        # 先访问B站首页，手动扫码登录一次（cookie会自动保存）
        page.goto('https://www.bilibili.com')
        input('登录后按回车继续...')
        
        # 搜索
        page.goto(f'https://search.bilibili.com/all?keyword={keyword}')
        time.sleep(2)
        
        # 滚动加载更多
        for _ in range(max_scroll):
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(1)
        
        # 提取视频标题和链接
        items = page.query_selector_all('.video-item.card')
        for item in items:
            title_el = item.query_selector('a.title')
            if title_el:
                results.append({
                    'title': title_el.inner_text(),
                    'url': 'https:' + title_el.get_attribute('href') if title_el.get_attribute('href') else '',
                    'platform': 'B站',
                    'keyword': keyword,
                })
        
        browser.close()
    return results

# 使用
data = search_bilibili('原神4.7')
with open('bilibili_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

**3. 微博搜索采集示例**
```python
def search_weibo(keyword, max_scroll=3):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto('https://s.weibo.com/weibo?q=' + keyword)
        input('登录微博后按回车继续...')
        
        for _ in range(max_scroll):
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(1.5)
        
        items = page.query_selector_all('.card-wrap .content')
        for item in items:
            text = item.inner_text().strip()
            if text:
                results.append({
                    'title': text[:100],
                    'url': '',
                    'platform': '微博',
                    'keyword': keyword,
                })
        browser.close()
    return results
```

---
### 📦 方案二：Selenium

```bash
pip install selenium
```

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time

def search_zhihu(keyword):
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(options=options)
    
    driver.get(f'https://www.zhihu.com/search?type=content&q={keyword}')
    time.sleep(3)
    
    results = []
    items = driver.find_elements(By.CSS_SELECTOR, '.SearchResult-Card')
    for item in items:
        title_el = item.find_elements(By.CSS_SELECTOR, 'h2 a')
        if title_el:
            results.append({
                'title': title_el[0].text,
                'url': title_el[0].get_attribute('href'),
                'platform': '知乎',
                'keyword': keyword,
            })
    
    driver.quit()
    return results
```

---
### 📋 采集数据格式

采集完成后，将数据整理为CSV文件上传到本系统，要求：

| 列名 | 必填 | 说明 |
|------|------|------|
| title | ✅ | 内容标题/正文前100字 |
| url | ❌ | 原文链接 |
| content | ❌ | 正文/摘要 |
| platform | ❌ | 平台名（不填则自动识别） |
| keyword | ❌ | 搜索关键词 |

示例CSV：
```
title,url,content,platform,keyword
原神4.7版本评测,https://bilibili.com/xxx,纳塔版本...,B站,原神4.7
```

---
### ⚠️ 注意事项

① **首次运行需手动登录**：B站/微博需扫码登录才能搜索，建议首次用`headless=False`有界面模式登录
② **保存Cookie复用**：登录后可导出`context.storage_state()`保存Cookie，后续免登录
③ **控制频率**：每次请求间隔≥1秒，滚动间隔≥1.5秒，避免触发反爬
④ **B站WBI签名**：B站搜索API有WBI签名校验，直接请求API会返回-799，用Playwright渲染页面可绕过
⑤ **采集量建议**：每个关键词采集20-50条即可，数据量过大会降低分析效率
⑥ **合法性**：仅采集公开内容，不采集用户隐私数据，遵守各平台robots.txt

---
### 🔄 完整工作流

```
1. 用Playwright/Selenium采集 → 得到JSON/CSV数据
2. 在本系统选择"上传CSV/Excel"模式 → 上传采集数据
3. 系统自动完成平台识别 + 内容分类 + 情感分析
4. 查看分析结果 → 导出PDF报告
```
        """)

else:
    # 没有搜索时的引导
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("""
        ### 🌐 使用说明
        
        **方式一：关键词搜索**
        1. 选择"关键词搜索"模式
        2. 输入关键词（逗号分隔），如 "DeepSeek, 高考, 俄乌冲突"
        3. 点击"开始搜索"，系统自动搜索互联网内容
        
        **方式二：上传数据**
        1. 选择"上传CSV/Excel"模式
        2. 上传含 title 列的CSV文件
        3. 系统自动识别平台、分类和情感
        
        **两种模式均支持：**
        - 📊 平台对比分析
        - 🔥 热点排行与高频词
        - 😐 情感分析与负面率
        - ⚠️ 舆情风险预警
        - 📥 一键导出PDF报告
        - 可选DeepSeek AI深度分析
        """)
    
    # ── 示例数据加载 ──
    st.divider()
    st.subheader("💡 快速体验")
    st.markdown("没有数据？点击下方按钮加载内置示例数据集（589条B站+抖音真实用户评论，覆盖9大分类），即刻体验完整分析流程。")
    
    if st.button("📂 加载示例数据集", type="primary"):
        sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_data.csv')
        if os.path.exists(sample_path):
            try:
                import pandas as pd
                df = pd.read_csv(sample_path)
                
                with st.spinner(f"正在加载 {len(df)} 条示例数据..."):
                    results = parse_uploaded_csv(df)
                    analysis = analyze_results(results)
                    
                    st.session_state['results'] = results
                    st.session_state['analysis'] = analysis
                    st.session_state['keywords'] = list(set(r['keyword'] for r in results if r.get('keyword')))
                    
                    st.success(f"示例数据加载完成！共 {len(results)} 条数据，覆盖 {len(analysis.get('platform_dist', {}))} 个平台、{len(analysis.get('category_dist', {}))} 个分类")
                    st.rerun()
            except Exception as e:
                st.error(f"加载示例数据失败: {e}")
        else:
            st.warning("示例数据文件不存在，请确认 sample_data.csv 在同一目录下")


def _call_deepseek(api_key, api_base, results, analysis, custom_modules=None, analysis_rounds=1, extra_instructions=""):
    """调用DeepSeek API生成分析文本，支持自定义模块、多轮分析和额外指令"""
    import requests
    
    platform_str = "\n".join(f"  {k}: {v}条" for k, v in sorted(analysis['platform_dist'].items(), key=lambda x: x[1], reverse=True))
    category_str = "\n".join(f"  {k}: {v}条" for k, v in sorted(analysis['category_dist'].items(), key=lambda x: x[1], reverse=True))
    sentiment_str = "\n".join(f"  {k}: {v}条" for k, v in analysis['sentiment_dist'].items())
    neg_rate_str = "\n".join(f"  {k}: {v}%" for k, v in sorted(analysis.get('platform_neg_rate', {}).items(), key=lambda x: x[1], reverse=True))
    
    neg_samples = ""
    for i, r in enumerate(analysis.get('negative_results', [])[:10]):
        neg_samples += f"\n--- 样本{i+1} [{r['platform']}] ---\n标题: {r['title']}\n摘要: {r['snippet'][:200]}\n"
    
    # 构建模块列表
    if not custom_modules:
        custom_modules = ["整体舆情态势", "平台舆论差异", "核心风险点TOP5", "情感分布判断", "舆情走势预判", "应对建议"]
    
    modules_text = "\n".join(f"### {i+1}. {mod}" for i, mod in enumerate(custom_modules))
    
    # 轮次说明
    round_instruction = ""
    if analysis_rounds > 1:
        round_instruction = f"\n\n【多轮分析要求】共需进行{analysis_rounds}轮分析。每轮在前一轮结论基础上深化，第1轮为初步分析，后续轮次需指出前轮的不足并补充新视角。最终输出合并所有轮次的综合结论。"
    
    # 额外指令
    extra_text = ""
    if extra_instructions.strip():
        extra_text = f"\n\n【额外要求】{extra_instructions.strip()}"
    
    prompt = f"""你是数据分析专家，基于以下网络热点搜索数据生成舆情分析报告。直接输出报告正文，不要自我介绍，不要写AI助手相关内容。

数据概况:
  搜索结果总数: {analysis['total']}
  搜索关键词: {', '.join(st.session_state.get('keywords', []))}

平台分布:
{platform_str}

内容分类:
{category_str}

情感分布:
{sentiment_str}

各平台负面率:
{neg_rate_str}

负面内容样本:
{neg_samples}

请输出{len(custom_modules)}个模块的分析：
{modules_text}
{round_instruction}{extra_text}"""

    messages = [{"role": "user", "content": prompt}]
    
    # 多轮分析
    for round_idx in range(analysis_rounds):
        if round_idx > 0:
            # 后续轮次：让AI基于前一轮结论深化
            deepen_prompt = f"请基于你上一轮的分析结论，进行第{round_idx+1}轮深化分析。要求：①指出前轮分析的不足或遗漏 ②补充新的数据视角或跨维度关联 ③更新风险判断和结论。保持原有模块结构，输出完整深化版报告。"
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
            raise Exception(f"API调用失败(第{round_idx+1}轮): {resp.status_code} - {resp.text}")
        
        ai_reply = resp.json()['choices'][0]['message']['content']
        messages.append({"role": "assistant", "content": ai_reply})
    
    # 如果多轮，在最终结果前加说明
    if analysis_rounds > 1:
        return f"（经{analysis_rounds}轮深化分析）\n\n{ai_reply}"
    return ai_reply
