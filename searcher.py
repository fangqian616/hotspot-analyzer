#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""网络热点舆情分析 - 数据采集引擎"""

import re
import time
from datetime import datetime
from typing import List, Dict, Optional
from collections import Counter


# ── 平台识别规则 ──
PLATFORM_RULES = {
    'B站': ['bilibili.com', 'b23.tv'],
    '抖音': ['douyin.com', 'iesdouyin.com'],
    '微博': ['weibo.com', 'weibo.cn'],
    '知乎': ['zhihu.com'],
    '小红书': ['xiaohongshu.com', 'xhslink.com'],
    '今日头条': ['toutiao.com'],
    '微信公众号': ['mp.weixin.qq.com'],
}

# ── 内容分类关键词库 ──
CATEGORY_KEYWORDS = {
    '国际政治': ['国际', '外交', '战争', '冲突', '总统', '联合国', '制裁', '谈判', '俄乌', '中美', '欧盟', '北约'],
    '科技AI': ['AI', '人工智能', '芯片', '大模型', 'deepseek', 'openai', '科技', '算法', '机器人',
               '英伟达', 'NVIDIA', 'GPT', 'Claude', '自动驾驶', '量子'],
    '社会民生': ['教育', '高考', '就业', '房价', '医疗', '养老', '食品安全', '社会', '特训学校',
               '天气', '灾害', '疫情', '裁员', '内卷'],
    '体育电竞': ['比赛', '世界杯', '奥运', '电竞', '足球', '篮球', '选手', '冠军', 'NBA',
               'FIFA', '中超', 'LOL', '王者荣耀'],
    '文娱': ['电影', '电视剧', '综艺', '明星', '偶像', '动漫', '游戏', '原神', '崩铁', '绝区零',
            'PV', '番剧', '演唱会', '塌房'],
    '商业消费': ['品牌', '消费', '直播', '电商', '价格', '产品', '投诉', '售后', '李佳琦',
               '带货', '翻车', '618', '双11', '退款'],
}

# ── 情感分析词库 ──
POSITIVE_WORDS = [
    '好评', '支持', '推荐', '优秀', '厉害', '突破', '创新', '感动', '暖心', '点赞',
    '成功', '惊喜', '里程碑', '期待', '认可', '自豪', '进步', '榜样',
]
NEGATIVE_WORDS = [
    '争议', '批评', '质疑', '问题', '投诉', '不满', '愤怒', '失望', '骂', '坑',
    '烂', '差', '骗', '翻车', '塌房', '暴雷', '危机', '造假', '欺诈', '崩盘',
    '封杀', '抵制', '抗议', '剥削', '腐败', '诈骗', '怒斥', '声讨',
]


def detect_platform(url: str) -> str:
    """从URL识别平台"""
    for platform, domains in PLATFORM_RULES.items():
        if any(d in url for d in domains):
            return platform
    return '其他'


def categorize_content(title: str, snippet: str) -> str:
    """自动分类内容"""
    text = (title + ' ' + snippet).lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[cat] = score
    if scores:
        return max(scores, key=scores.get)
    return '其他'


def simple_sentiment(text: str) -> str:
    """简单情感分析"""
    neg_count = sum(1 for w in NEGATIVE_WORDS if w in text)
    pos_count = sum(1 for w in POSITIVE_WORDS if w in text)
    if neg_count > pos_count + 1:
        return '负面'
    elif pos_count > neg_count + 1:
        return '正面'
    return '中性'


def search_hotspots(keywords: List[str], max_results: int = 15,
                    platform_filter: str = '全部') -> List[Dict]:
    """搜索热点内容（使用ddgs/DuckDuckGo）"""
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            raise ImportError("请安装搜索库: pip install ddgs")

    results = []
    seen_urls = set()
    ddgs = DDGS()

    for kw in keywords:
        try:
            term = kw
            site_map = {
                'B站': 'site:bilibili.com',
                '抖音': 'site:douyin.com',
                '微博': 'site:weibo.com',
                '知乎': 'site:zhihu.com',
                '小红书': 'site:xiaohongshu.com',
            }
            if platform_filter in site_map:
                term = f"{kw} {site_map[platform_filter]}"

            try:
                search_results = ddgs.text(term, region='cn-zh', max_results=max_results)
            except Exception:
                # region参数不支持时回退
                search_results = ddgs.text(term, max_results=max_results)

            if search_results:
                for item in search_results:
                    url = item.get('href', '') or item.get('url', '')
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    title = item.get('title', '')
                    snippet = item.get('body', '') or item.get('snippet', '')

                    results.append({
                        'keyword': kw,
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'platform': detect_platform(url),
                        'category': categorize_content(title, snippet),
                        'sentiment': simple_sentiment(title + ' ' + snippet),
                        'search_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    })

            time.sleep(0.3)

        except Exception as e:
            print(f"搜索关键词 '{kw}' 时出错: {e}")
            continue

    return results


def parse_uploaded_csv(df) -> List[Dict]:
    """解析用户上传的CSV/Excel数据
    
    期望列：title, url (或 link), content (或 snippet 或 body)
    可选列：platform, category, sentiment, keyword
    """
    results = []
    col_map = {}
    
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in ('title', '标题'):
            col_map['title'] = col
        elif col_lower in ('url', 'link', '链接'):
            col_map['url'] = col
        elif col_lower in ('content', 'snippet', 'body', '内容', '摘要'):
            col_map['snippet'] = col
        elif col_lower in ('platform', '平台'):
            col_map['platform'] = col
        elif col_lower in ('category', '分类'):
            col_map['category'] = col
        elif col_lower in ('sentiment', '情感'):
            col_map['sentiment'] = col
        elif col_lower in ('keyword', '关键词'):
            col_map['keyword'] = col
    
    for _, row in df.iterrows():
        title = str(row.get(col_map.get('title', 'title'), ''))
        url = str(row.get(col_map.get('url', 'url'), ''))
        snippet = str(row.get(col_map.get('snippet', 'snippet'), ''))
        
        if not title or title == 'nan':
            continue
        
        # 如果CSV已有平台/分类/情感字段则直接用，否则自动识别
        platform = str(row.get(col_map.get('platform', 'platform'), '')) if 'platform' in col_map else detect_platform(url)
        category = str(row.get(col_map.get('category', 'category'), '')) if 'category' in col_map else categorize_content(title, snippet)
        sentiment = str(row.get(col_map.get('sentiment', 'sentiment'), '')) if 'sentiment' in col_map else simple_sentiment(title + ' ' + snippet)
        keyword = str(row.get(col_map.get('keyword', 'keyword'), '上传数据')) if 'keyword' in col_map else '上传数据'
        
        if platform == 'nan': platform = detect_platform(url)
        if category == 'nan': category = categorize_content(title, snippet)
        if sentiment == 'nan': sentiment = simple_sentiment(title + ' ' + snippet)
        if keyword == 'nan': keyword = '上传数据'
        
        results.append({
            'keyword': keyword,
            'title': title,
            'url': url if url != 'nan' else '',
            'snippet': snippet if snippet != 'nan' else '',
            'platform': platform,
            'category': category,
            'sentiment': sentiment,
            'search_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
        })
    
    return results


def analyze_results(results: List[Dict]) -> Dict:
    """对搜索结果进行统计分析"""
    if not results:
        return {}

    platform_dist = Counter(r['platform'] for r in results)
    category_dist = Counter(r['category'] for r in results)
    sentiment_dist = Counter(r['sentiment'] for r in results)
    keyword_dist = Counter(r['keyword'] for r in results)

    platform_sentiment = {}
    for r in results:
        p = r['platform']
        if p not in platform_sentiment:
            platform_sentiment[p] = Counter()
        platform_sentiment[p][r['sentiment']] += 1

    category_sentiment = {}
    for r in results:
        c = r['category']
        if c not in category_sentiment:
            category_sentiment[c] = Counter()
        category_sentiment[c][r['sentiment']] += 1

    all_text = ' '.join(r['title'] + ' ' + r['snippet'] for r in results)
    word_freq = extract_word_frequency(all_text)

    negative_results = [r for r in results if r['sentiment'] == '负面']

    platform_neg_rate = {}
    for p, counts in platform_sentiment.items():
        total = sum(counts.values())
        neg = counts.get('负面', 0)
        platform_neg_rate[p] = round(neg / total * 100, 1) if total > 0 else 0

    category_neg_rate = {}
    for c, counts in category_sentiment.items():
        total = sum(counts.values())
        neg = counts.get('负面', 0)
        category_neg_rate[c] = round(neg / total * 100, 1) if total > 0 else 0

    return {
        'total': len(results),
        'platform_dist': dict(platform_dist),
        'category_dist': dict(category_dist),
        'sentiment_dist': dict(sentiment_dist),
        'keyword_dist': dict(keyword_dist),
        'platform_sentiment': {k: dict(v) for k, v in platform_sentiment.items()},
        'category_sentiment': {k: dict(v) for k, v in category_sentiment.items()},
        'word_freq': word_freq,
        'negative_results': negative_results,
        'platform_neg_rate': platform_neg_rate,
        'category_neg_rate': category_neg_rate,
    }


def extract_word_frequency(text: str, top_n: int = 30) -> Dict[str, int]:
    """简单中文词频统计（按2-4字切分）"""
    text = re.sub(r'[^\u4e00-\u9fff]', '', text)
    stopwords = set('的了是在我有和就不人都一上也很到说要去你会着没有看好自己这那他她它们什么怎么哪里为什么可以已经'.split())
    freq = Counter()
    for length in [4, 3, 2]:
        for i in range(len(text) - length + 1):
            word = text[i:i + length]
            if all(c not in stopwords for c in word):
                freq[word] += 1
    return {k: v for k, v in freq.most_common(top_n) if v >= 2}
