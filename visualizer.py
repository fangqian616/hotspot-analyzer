#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""网络热点舆情分析 - PDF报告生成引擎"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from datetime import datetime
from collections import Counter

# 中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Micro Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 配色
COLORS = {
    'B站': '#fb7299', '抖音': '#00f2ea', '微博': '#ff8200',
    '知乎': '#0066ff', '小红书': '#ff2442', '今日头条': '#d42d26',
    '其他': '#818cf8',
    '正面': '#34d399', '负面': '#f87171', '中性': '#60a5fa',
}
PIE_COLORS = ['#4C72B0', '#DD8452', '#55A868', '#C44E52', '#8172B3',
              '#937860', '#64B5CD', '#8C564B', '#E377C2', '#7F7F7F',
              '#BCBD22', '#17BECF', '#AEC7E8', '#FFD700']


def _safe_text(text, max_len=60):
    """安全截断文本用于图表标签"""
    if not text:
        return ''
    text = str(text).strip()
    if len(text) > max_len:
        text = text[:max_len - 1] + '…'
    return text


def generate_pdf_report(results, analysis, output_path, ai_report_text=None):
    """生成完整PDF报告（图表+文字）"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Image, PageBreak, Table, TableStyle)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # 注册中文字体
    font_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    ]
    cn_font = 'Helvetica'
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont('WQY', fp))
                cn_font = 'WQY'
                break
            except Exception:
                continue

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CnTitle', parent=styles['Title'],
                                  fontName=cn_font, fontSize=20, spaceAfter=12)
    heading_style = ParagraphStyle('CnHeading', parent=styles['Heading2'],
                                    fontName=cn_font, fontSize=14, spaceAfter=8)
    body_style = ParagraphStyle('CnBody', parent=styles['Normal'],
                                 fontName=cn_font, fontSize=9, leading=14)

    # 生成图表
    chart_files = []
    tmp_dir = os.path.dirname(output_path) or '/tmp'

    try:
        chart_files.append(_chart_platform_dist(analysis, tmp_dir))
        chart_files.append(_chart_category_dist(analysis, tmp_dir))
        chart_files.append(_chart_sentiment(analysis, tmp_dir))
        chart_files.append(_chart_platform_neg_rate(analysis, tmp_dir))
        chart_files.append(_chart_keyword_dist(analysis, tmp_dir))
        chart_files.append(_chart_word_freq(analysis, tmp_dir))
        chart_files.append(_chart_hotspot_rank(results, analysis, tmp_dir))
    except Exception as e:
        print(f"图表生成异常: {e}")

    # 构建PDF
    elements = []

    # 封面
    elements.append(Spacer(1, 60 * mm))
    elements.append(Paragraph("网络热点舆情分析报告", title_style))
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
    elements.append(Paragraph(f"数据量: {analysis.get('total', 0)} 条搜索结果", body_style))

    # KPI概览
    elements.append(Spacer(1, 10 * mm))
    kpi_data = [
        ['搜索结果数', '覆盖平台数', '内容分类数', '负面内容数'],
        [str(analysis.get('total', 0)),
         str(len(analysis.get('platform_dist', {}))),
         str(len(analysis.get('category_dist', {}))),
         str(len(analysis.get('negative_results', [])))]
    ]
    kpi_table = Table(kpi_data, colWidths=[40 * mm] * 4)
    kpi_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, 1), 16),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#4C72B0')),
        ('FONTNAME', (0, 0), (-1, -1), cn_font),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))
    elements.append(kpi_table)
    elements.append(PageBreak())

    # 图表页
    for i, chart_path in enumerate(chart_files):
        if chart_path and os.path.exists(chart_path):
            chart_titles = [
                '平台数据分布', '内容分类分布', '情感分析', '平台负面率对比',
                '关键词搜索结果数', '高频词排行', '热点内容排行',
            ]
            title = chart_titles[i] if i < len(chart_titles) else f'图表{i + 1}'
            elements.append(Paragraph(title, heading_style))
            try:
                img = Image(chart_path, width=160 * mm, height=85 * mm)
                elements.append(img)
            except Exception:
                elements.append(Paragraph("[图表生成失败]", body_style))
            elements.append(Spacer(1, 5 * mm))

            # 每2个图表换页
            if (i + 1) % 2 == 0 and i < len(chart_files) - 1:
                elements.append(PageBreak())

    # AI分析文字
    if ai_report_text:
        elements.append(PageBreak())
        elements.append(Paragraph("深度分析", title_style))
        elements.append(Spacer(1, 5 * mm))
        # 清理markdown标记
        clean = ai_report_text.replace('**', '').replace('##', '').replace('#', '')
        clean = clean.replace('***', '').replace('* ', '- ')
        for para in clean.split('\n\n'):
            para = para.strip()
            if para:
                try:
                    elements.append(Paragraph(para, body_style))
                    elements.append(Spacer(1, 3 * mm))
                except Exception:
                    elements.append(Paragraph(para.encode('utf-8', errors='replace').decode('utf-8'), body_style))
                    elements.append(Spacer(1, 3 * mm))

    doc.build(elements)

    # 清理临时图表
    for f in chart_files:
        try:
            if f and os.path.exists(f):
                os.unlink(f)
        except Exception:
            pass


def _chart_platform_dist(analysis, tmp_dir):
    """平台分布饼图"""
    data = analysis.get('platform_dist', {})
    if not data:
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # 饼图
    labels = list(data.keys())
    values = list(data.values())
    clrs = [COLORS.get(l, '#818cf8') for l in labels]
    ax1.pie(values, labels=labels, colors=clrs, autopct='%1.1f%%', startangle=140)
    ax1.set_title('平台内容分布', fontsize=13)

    # 柱状图
    ax2.bar(labels, values, color=clrs, alpha=0.85)
    ax2.set_title('平台内容数量', fontsize=13)
    ax2.set_ylabel('条数')
    for i, v in enumerate(values):
        ax2.text(i, v + 0.3, str(v), ha='center', fontsize=9)
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    path = os.path.join(tmp_dir, '_chart_platform.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def _chart_category_dist(analysis, tmp_dir):
    """分类分布"""
    data = analysis.get('category_dist', {})
    if not data:
        return None

    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    labels = [k for k, v in sorted_data]
    values = [v for k, v in sorted_data]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.barh(labels[::-1], values[::-1], color=PIE_COLORS[:len(labels)], alpha=0.85, height=0.6)
    ax1.set_title('内容分类排行', fontsize=13)
    for i, v in enumerate(values[::-1]):
        ax1.text(v + 0.2, i, str(v), va='center', fontsize=9)
    ax1.grid(axis='x', alpha=0.3)

    ax2.pie(values, labels=labels, colors=PIE_COLORS[:len(labels)], autopct='%1.1f%%', startangle=140)
    ax2.set_title('分类占比', fontsize=13)

    plt.tight_layout()
    path = os.path.join(tmp_dir, '_chart_category.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def _chart_sentiment(analysis, tmp_dir):
    """情感分析"""
    data = analysis.get('sentiment_dist', {})
    if not data:
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    labels = ['正面', '中性', '负面']
    values = [data.get(l, 0) for l in labels]
    clrs = [COLORS[l] for l in labels]

    ax1.pie(values, labels=labels, colors=clrs, autopct='%1.1f%%', startangle=140,
            textprops={'fontsize': 11})
    ax1.set_title('整体情感分布', fontsize=13)

    # 各平台情感对比
    ps = analysis.get('platform_sentiment', {})
    if ps:
        platforms = list(ps.keys())
        x = np.arange(len(platforms))
        w = 0.25
        pos_v = [ps[p].get('正面', 0) for p in platforms]
        neu_v = [ps[p].get('中性', 0) for p in platforms]
        neg_v = [ps[p].get('负面', 0) for p in platforms]

        ax2.bar(x - w, pos_v, w, label='正面', color=COLORS['正面'], alpha=0.85)
        ax2.bar(x, neu_v, w, label='中性', color=COLORS['中性'], alpha=0.85)
        ax2.bar(x + w, neg_v, w, label='负面', color=COLORS['负面'], alpha=0.85)
        ax2.set_xticks(x)
        ax2.set_xticklabels(platforms, fontsize=10)
        ax2.set_title('各平台情感对比', fontsize=13)
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    path = os.path.join(tmp_dir, '_chart_sentiment.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def _chart_platform_neg_rate(analysis, tmp_dir):
    """平台负面率对比"""
    data = analysis.get('platform_neg_rate', {})
    if not data:
        return None

    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    labels = [k for k, v in sorted_data]
    values = [v for k, v in sorted_data]

    fig, ax = plt.subplots(figsize=(12, 5))

    bar_colors = []
    for v in values:
        if v >= 20:
            bar_colors.append('#f87171')
        elif v >= 10:
            bar_colors.append('#fbbf24')
        else:
            bar_colors.append('#60a5fa')

    ax.bar(labels, values, color=bar_colors, alpha=0.85, width=0.5)
    ax.set_title('各平台负面率排行', fontsize=13)
    ax.set_ylabel('负面率 (%)')
    for i, v in enumerate(values):
        ax.text(i, v + 0.3, f'{v:.1f}%', ha='center', fontsize=10, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(y=15, color='#f87171', linestyle='--', alpha=0.5, label='高风险线(15%)')
    ax.legend()

    plt.tight_layout()
    path = os.path.join(tmp_dir, '_chart_neg_rate.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def _chart_keyword_dist(analysis, tmp_dir):
    """关键词搜索结果数"""
    data = analysis.get('keyword_dist', {})
    if not data:
        return None

    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    labels = [k for k, v in sorted_data]
    values = [v for k, v in sorted_data]

    fig, ax = plt.subplots(figsize=(12, max(5, len(labels) * 0.5)))

    ax.barh(labels[::-1], values[::-1], color='#818cf8', alpha=0.85, height=0.6)
    ax.set_title('关键词搜索结果数', fontsize=13)
    for i, v in enumerate(values[::-1]):
        ax.text(v + 0.2, i, str(v), va='center', fontsize=9)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    path = os.path.join(tmp_dir, '_chart_keyword.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def _chart_word_freq(analysis, tmp_dir):
    """高频词排行"""
    data = analysis.get('word_freq', {})
    if not data:
        return None

    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:20]
    labels = [k for k, v in sorted_data]
    values = [v for k, v in sorted_data]

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.barh(labels[::-1], values[::-1], color='#DD8452', alpha=0.85, height=0.6)
    ax.set_title('高频词 TOP20', fontsize=13)
    for i, v in enumerate(values[::-1]):
        ax.text(v + 0.2, i, str(v), va='center', fontsize=8)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    path = os.path.join(tmp_dir, '_chart_wordfreq.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def _chart_hotspot_rank(results, analysis, tmp_dir):
    """热点内容排行（按关键词+情感）"""
    if not results:
        return None

    # 按关键词聚合
    kw_data = {}
    for r in results:
        kw = r['keyword']
        if kw not in kw_data:
            kw_data[kw] = {'total': 0, 'negative': 0, 'positive': 0, 'neutral': 0}
        kw_data[kw]['total'] += 1
        if r['sentiment'] == '负面':
            kw_data[kw]['negative'] += 1
        elif r['sentiment'] == '正面':
            kw_data[kw]['positive'] += 1
        else:
            kw_data[kw]['neutral'] += 1

    sorted_kw = sorted(kw_data.items(), key=lambda x: x[1]['total'], reverse=True)
    labels = [k for k, v in sorted_kw]
    totals = [v['total'] for k, v in sorted_kw]
    negs = [v['negative'] for k, v in sorted_kw]
    neg_rates = [round(v['negative'] / v['total'] * 100, 1) if v['total'] > 0 else 0 for k, v in sorted_kw]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, max(5, len(labels) * 0.5)))

    # 内容量
    ax1.barh(labels[::-1], totals[::-1], color='#4C72B0', alpha=0.85, height=0.6)
    ax1.set_title('关键词内容量排行', fontsize=13)
    for i, v in enumerate(totals[::-1]):
        ax1.text(v + 0.2, i, str(v), va='center', fontsize=9)
    ax1.grid(axis='x', alpha=0.3)

    # 负面率
    bar_colors = ['#f87171' if v >= 20 else '#fbbf24' if v >= 10 else '#60a5fa' for v in neg_rates]
    ax2.barh(labels[::-1], neg_rates[::-1], color=bar_colors[::-1], alpha=0.85, height=0.6)
    ax2.set_title('关键词负面率 (%)', fontsize=13)
    for i, v in enumerate(neg_rates[::-1]):
        ax2.text(v + 0.3, i, f'{v}%', va='center', fontsize=9)
    ax2.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    path = os.path.join(tmp_dir, '_chart_hotspot.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path
