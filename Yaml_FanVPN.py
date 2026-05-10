#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import configparser
import requests
import re
import chardet
import time
import base64
import json
import yaml
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA1

from bs4 import BeautifulSoup
from datetime import datetime

yaml_file_tmp = "./File/tmp_fanvpn.yaml"
yaml_file_dst = "./File/fanvpn.yaml"

# ---------- 1. 配置参数 ----------
BACKGROUND_JS_PATH = "./background.js"   # background.js 
CONFIG_URLS = [
    'https://gitlab.com/zhifan999/fq/-/raw/main/config.json',
    'https://www.githubip.xyz/config.json'
]


# ---------- 密文（从你提供的 config.json 复制）----------
#envelope = {
#    "key": "",
#    "iv": "",
#    "data": ""
#}

# ---------- 2. 从地址拉取密文 ----------
def extract_private_key_from_js(js_path):
    """从 background.js 中提取 PRIVATE_KEY_PEM 的内容"""
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # 匹配 const PRIVATE_KEY_PEM = ` ... `; 或 let PRIVATE_KEY_PEM = `...`;
    pattern = r'(?:const|let)\s+PRIVATE_KEY_PEM\s*=\s*`([^`]+)`'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise Exception("未能在文件中找到 PRIVATE_KEY_PEM 的定义")
    private_key = match.group(1).strip()
    # 确保开头和结尾有正确标记
    if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
        private_key = '-----BEGIN PRIVATE KEY-----\n' + private_key
    if not private_key.endswith('-----END PRIVATE KEY-----'):
        private_key = private_key + '\n-----END PRIVATE KEY-----'
    return private_key


def fetch_envelope(urls):
    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            resp.encoding = 'utf-8'
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"请求失败 {url}: {e}")
    raise Exception("所有备用地址均无法获取配置文件")


# ---------- 工具函数 ----------
def b64_to_bytes(b64):
    return base64.b64decode(b64)

# ---------- 解密 ----------
def decrypt_config(envelope, private_key_pem):
    key_bytes = b64_to_bytes(envelope['key'])
    iv_bytes = b64_to_bytes(envelope['iv'])
    data_bytes = b64_to_bytes(envelope['data'])

    rsa_key = RSA.import_key(private_key_pem)
    cipher_rsa = PKCS1_OAEP.new(rsa_key, hashAlgo=SHA1)   # 注意：使用 SHA1
    aes_key = cipher_rsa.decrypt(key_bytes)

    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv_bytes)
    decrypted = cipher_aes.decrypt(data_bytes)
    # 去除 PKCS#7 填充
    pad_len = decrypted[-1]
    decrypted = decrypted[:-pad_len]

    config = json.loads(decrypted.decode('utf-8'))
    return config
    
    
    



COUNTRY_FLAGS = {
    # ========== 亚洲 ==========
    'cn': '🇨🇳', 'china': '🇨🇳', 'chinese': '🇨🇳',
    'hk': '🇭🇰', 'hongkong': '🇭🇰', 'hong kong': '🇭🇰',
    'mo': '🇲🇴', 'macau': '🇲🇴', 'macao': '🇲🇴',
    #'tw': '🇹🇼', 'taiwan': '🇹🇼',
    'tw': '🇨🇳', 'taiwan': '🇨🇳',
    'jp': '🇯🇵', 'japan': '🇯🇵', 'tokyo': '🇯🇵', 'osaka': '🇯🇵',
    'kr': '🇰🇷', 'south korea': '🇰🇷', 'korea': '🇰🇷', 'seoul': '🇰🇷',
    'kp': '🇰🇵', 'north korea': '🇰🇵',
    'sg': '🇸🇬', 'singapore': '🇸🇬',
    'my': '🇲🇾', 'malaysia': '🇲🇾', 'kuala lumpur': '🇲🇾',
    'th': '🇹🇭', 'thailand': '🇹🇭', 'bangkok': '🇹🇭',
    'vn': '🇻🇳', 'vietnam': '🇻🇳', 'ho chi minh': '🇻🇳', 'hanoi': '🇻🇳',
    'ph': '🇵🇭', 'philippines': '🇵🇭', 'manila': '🇵🇭',
    'id': '🇮🇩', 'indonesia': '🇮🇩', 'jakarta': '🇮🇩', 'bali': '🇮🇩',
    'in': '🇮🇳', 'india': '🇮🇳', 'mumbai': '🇮🇳', 'delhi': '🇮🇳',
    'bd': '🇧🇩', 'bangladesh': '🇧🇩',
    'pk': '🇵🇰', 'pakistan': '🇵🇰',
    'lk': '🇱🇰', 'sri lanka': '🇱🇰',
    'np': '🇳🇵', 'nepal': '🇳🇵',
    'bt': '🇧🇹', 'bhutan': '🇧🇹',
    'mm': '🇲🇲', 'myanmar': '🇲🇲', 'burma': '🇲🇲',
    'kh': '🇰🇭', 'cambodia': '🇰🇭',
    'la': '🇱🇦', 'laos': '🇱🇦',
    'mn': '🇲🇳', 'mongolia': '🇲🇳',
    'ge': '🇬🇪', 'georgia': '🇬🇪',
    'am': '🇦🇲', 'armenia': '🇦🇲',
    'az': '🇦🇿', 'azerbaijan': '🇦🇿',
    'kz': '🇰🇿', 'kazakhstan': '🇰🇿',
    'uz': '🇺🇿', 'uzbekistan': '🇺🇿',
    'tr': '🇹🇷', 'turkey': '🇹🇷', 'istanbul': '🇹🇷',
    'il': '🇮🇱', 'israel': '🇮🇱',
    'ps': '🇵🇸', 'palestine': '🇵🇸',
    'sa': '🇸🇦', 'saudi arabia': '🇸🇦', 'riyadh': '🇸🇦',
    'ae': '🇦🇪', 'uae': '🇦🇪', 'dubai': '🇦🇪', 'abu dhabi': '🇦🇪',
    'qa': '🇶🇦', 'qatar': '🇶🇦',
    'om': '🇴🇲', 'oman': '🇴🇲',
    'kw': '🇰🇼', 'kuwait': '🇰🇼',
    'bh': '🇧🇭', 'bahrain': '🇧🇭',
    'ye': '🇾🇪', 'yemen': '🇾🇪',
    'ir': '🇮🇷', 'iran': '🇮🇷',
    'iq': '🇮🇶', 'iraq': '🇮🇶',

    # ========== 欧洲 ==========
    'ru': '🇷🇺', 'russia': '🇷🇺', 'moscow': '🇷🇺',
    'de': '🇩🇪', 'germany': '🇩🇪', 'berlin': '🇩🇪', 'frankfurt': '🇩🇪',
    'uk': '🇬🇧', 'gb': '🇬🇧', 'united kingdom': '🇬🇧', 'britain': '🇬🇧', 'london': '🇬🇧',
    'fr': '🇫🇷', 'france': '🇫🇷', 'paris': '🇫🇷',
    'it': '🇮🇹', 'italy': '🇮🇹', 'rome': '🇮🇹', 'milan': '🇮🇹',
    'es': '🇪🇸', 'spain': '🇪🇸', 'madrid': '🇪🇸', 'barcelona': '🇪🇸',
    'pt': '🇵🇹', 'portugal': '🇵🇹', 'lisbon': '🇵🇹',
    'nl': '🇳🇱', 'netherlands': '🇳🇱', 'holland': '🇳🇱', 'amsterdam': '🇳🇱',
    'be': '🇧🇪', 'belgium': '🇧🇪', 'brussels': '🇧🇪',
    'ch': '🇨🇭', 'switzerland': '🇨🇭', 'zurich': '🇨🇭',
    'at': '🇦🇹', 'austria': '🇦🇹', 'vienna': '🇦🇹',
    'se': '🇸🇪', 'sweden': '🇸🇪', 'stockholm': '🇸🇪',
    'no': '🇳🇴', 'norway': '🇳🇴', 'oslo': '🇳🇴',
    'dk': '🇩🇰', 'denmark': '🇩🇰', 'copenhagen': '🇩🇰',
    'fi': '🇫🇮', 'finland': '🇫🇮', 'helsinki': '🇫🇮',
    'ie': '🇮🇪', 'ireland': '🇮🇪', 'dublin': '🇮🇪',
    'pl': '🇵🇱', 'poland': '🇵🇱', 'warsaw': '🇵🇱',
    'cz': '🇨🇿', 'czech republic': '🇨🇿', 'prague': '🇨🇿',
    'hu': '🇭🇺', 'hungary': '🇭🇺', 'budapest': '🇭🇺',
    'ro': '🇷🇴', 'romania': '🇷🇴',
    'bg': '🇧🇬', 'bulgaria': '🇧🇬',
    'gr': '🇬🇷', 'greece': '🇬🇷', 'athens': '🇬🇷',
    'hr': '🇭🇷', 'croatia': '🇭🇷',
    'rs': '🇷🇸', 'serbia': '🇷🇸',
    'ua': '🇺🇦', 'ukraine': '🇺🇦', 'kyiv': '🇺🇦',
    'by': '🇧🇾', 'belarus': '🇧🇾',
    'md': '🇲🇩', 'moldova': '🇲🇩',
    'ee': '🇪🇪', 'estonia': '🇪🇪',
    'lv': '🇱🇻', 'latvia': '🇱🇻',
    'lt': '🇱🇹', 'lithuania': '🇱🇹',
    'sk': '🇸🇰', 'slovakia': '🇸🇰',
    'si': '🇸🇮', 'slovenia': '🇸🇮',
    'lu': '🇱🇺', 'luxembourg': '🇱🇺',
    'mt': '🇲🇹', 'malta': '🇲🇹',
    'cy': '🇨🇾', 'cyprus': '🇨🇾',
    'is': '🇮🇸', 'iceland': '🇮🇸',
    'li': '🇱🇮', 'liechtenstein': '🇱🇮',
    'mc': '🇲🇨', 'monaco': '🇲🇨',
    'sm': '🇸🇲', 'san marino': '🇸🇲',
    'va': '🇻🇦', 'vatican': '🇻🇦',

    # 英国构成国（非 ISO，但常用）
    'england': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    'scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
    'wales': '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
    'northern ireland': '🇬🇧',  # 无独立旗帜 emoji，用英国

    # ========== 美洲 ==========
    'us': '🇺🇸', 'usa': '🇺🇸', 'america': '🇺🇸', 'united states': '🇺🇸', 'los angeles': '🇺🇸', 'new york': '🇺🇸', 'chicago': '🇺🇸', 'miami': '🇺🇸', 'ashburn': '🇺🇸', 'silicon valley': '🇺🇸',
    'ca': '🇨🇦', 'canada': '🇨🇦', 'toronto': '🇨🇦', 'vancouver': '🇨🇦', 'montreal': '🇨🇦',
    'mx': '🇲🇽', 'mexico': '🇲🇽', 'mexico city': '🇲🇽',
    'br': '🇧🇷', 'brazil': '🇧🇷', 'sao paulo': '🇧🇷', 'rio': '🇧🇷',
    'ar': '🇦🇷', 'argentina': '🇦🇷', 'buenos aires': '🇦🇷',
    'cl': '🇨🇱', 'chile': '🇨🇱', 'santiago': '🇨🇱',
    'co': '🇨🇴', 'colombia': '🇨🇴', 'bogota': '🇨🇴',
    'pe': '🇵🇪', 'peru': '🇵🇪', 'lima': '🇵🇪',
    've': '🇻🇪', 'venezuela': '🇻🇪',
    'ec': '🇪🇨', 'ecuador': '🇪🇨',
    'bo': '🇧🇴', 'bolivia': '🇧🇴',
    'py': '🇵🇾', 'paraguay': '🇵🇾',
    'uy': '🇺🇾', 'uruguay': '🇺🇾',
    'gy': '🇬🇾', 'guyana': '🇬🇾',
    'sr': '🇸🇷', 'suriname': '🇸🇷',
    'gf': '🇬🇫', 'french guiana': '🇬🇫',  # 法属，但常单独列出

    # 中美洲 & 加勒比
    'cr': '🇨🇷', 'costa rica': '🇨🇷',
    'pa': '🇵🇦', 'panama': '🇵🇦',
    'gt': '🇬🇹', 'guatemala': '🇬🇹',
    'sv': '🇸🇻', 'el salvador': '🇸🇻',
    'hn': '🇭🇳', 'honduras': '🇭🇳',
    'ni': '🇳🇮', 'nicaragua': '🇳🇮',
    'bz': '🇧🇿', 'belize': '🇧🇿',
    'jm': '🇯🇲', 'jamaica': '🇯🇲',
    'cu': '🇨🇺', 'cuba': '🇨🇺',
    'do': '🇩🇴', 'dominican republic': '🇩🇴',
    'ht': '🇭🇹', 'haiti': '🇭🇹',
    'bs': '🇧🇸', 'bahamas': '🇧🇸',
    'bb': '🇧🇧', 'barbados': '🇧🇧',
    'tt': '🇹🇹', 'trinidad and tobago': '🇹🇹',

    # ========== 非洲 ==========
    'za': '🇿🇦', 'south africa': '🇿🇦',
    'ng': '🇳🇬', 'nigeria': '🇳🇬',
    'eg': '🇪🇬', 'egypt': '🇪🇬', 'cairo': '🇪🇬',
    'ke': '🇰🇪', 'kenya': '🇰🇪', 'nairobi': '🇰🇪',
    'gh': '🇬🇭', 'ghana': '🇬🇭',
    'tz': '🇹🇿', 'tanzania': '🇹🇿',
    'ug': '🇺🇬', 'uganda': '🇺🇬',
    'dz': '🇩🇿', 'algeria': '🇩🇿',
    'ma': '🇲🇦', 'morocco': '🇲🇦',
    'tn': '🇹🇳', 'tunisia': '🇹🇳',
    'et': '🇪🇹', 'ethiopia': '🇪🇹',
    'zm': '🇿🇲', 'zambia': '🇿🇲',
    'zw': '🇿🇼', 'zimbabwe': '🇿🇼',
    'mw': '🇲🇼', 'malawi': '🇲🇼',
    'ao': '🇦🇴', 'angola': '🇦🇴',
    'mg': '🇲🇬', 'madagascar': '🇲🇬',
    'ci': '🇨🇮', 'cote divoire': "🇨🇮", 'ivory coast': '🇨🇮',
    'sn': '🇸🇳', 'senegal': '🇸🇳',
    'cm': '🇨🇲', 'cameroon': '🇨🇲',
    'bj': '🇧🇯', 'benin': '🇧🇯',
    'tg': '🇹🇬', 'togo': '🇹🇬',
    'ga': '🇬🇦', 'gabon': '🇬🇦',
    'cg': '🇨🇬', 'congo': '🇨🇬',
    'cd': '🇨🇩', 'dr congo': '🇨🇩', 'democratic republic of the congo': '🇨🇩',
    'rw': '🇷🇼', 'rwanda': '🇷🇼',
    'bi': '🇧🇮', 'burundi': '🇧🇮',
    'so': '🇸🇴', 'somalia': '🇸🇴',
    #'ss': '🇸🇸', 'south sudan': '🇸🇸',
    'ly': '🇱🇾', 'libya': '🇱🇾',
    'sd': '🇸🇩', 'sudan': '🇸🇩',
    'mr': '🇲🇷', 'mauritania': '🇲🇷',
    'gn': '🇬🇳', 'guinea': '🇬🇳',
    'gw': '🇬🇼', 'guinea-bissau': '🇬🇼',
    'lr': '🇱🇷', 'liberia': '🇱🇷',
    'sl': '🇸🇱', 'sierra leone': '🇸🇱',
    'gm': '🇬🇲', 'gambia': '🇬🇲',
    'mu': '🇲🇺', 'mauritius': '🇲🇺',
    'sc': '🇸🇨', 'seychelles': '🇸🇨',
    'km': '🇰🇲', 'comoros': '🇰🇲',
    'cv': '🇨🇻', 'cape verde': '🇨🇻',
    'st': '🇸🇹', 'sao tome and principe': '🇸🇹',
    'td': '🇹🇩', 'chad': '🇹🇩',
    'ne': '🇳🇪', 'niger': '🇳🇪',
    'bf': '🇧🇫', 'burkina faso': '🇧🇫',
    'ml': '🇲🇱', 'mali': '🇲🇱',

    # ========== 大洋洲 ==========
    'au': '🇦🇺', 'australia': '🇦🇺', 'sydney': '🇦🇺', 'melbourne': '🇦🇺',
    'nz': '🇳🇿', 'new zealand': '🇳🇿', 'auckland': '🇳🇿',
    'fj': '🇫🇯', 'fiji': '🇫🇯',
    'pg': '🇵🇬', 'papua new guinea': '🇵🇬',
    'sb': '🇸🇧', 'solomon islands': '🇸🇧',
    'vu': '🇻🇺', 'vanuatu': '🇻🇺',
    'to': '🇹🇴', 'tonga': '🇹🇴',
    'ws': '🇼🇸', 'samoa': '🇼🇸',
    'ki': '🇰🇮', 'kiribati': '🇰🇮',
    'fm': '🇫🇲', 'micronesia': '🇫🇲',
    'mh': '🇲🇭', 'marshall islands': '🇲🇭',
    'nr': '🇳🇷', 'nauru': '🇳🇷',
    'pw': '🇵🇼', 'palau': '🇵🇼',
    'tv': '🇹🇻', 'tuvalu': '🇹🇻',

    # ========== 其他 / 特殊 ==========
    'global': '🌍',
    'international': '🌐',
    'unknown': '❓',
    'private': '🔒',
    'backup': '🔄',
    'auto': '🤖',
    'direct': '➡️',
    'reject': '🚫',

    # ========== 新增中文名称映射 ==========
    # 亚洲
    '中国': '🇨🇳', '中国大陆': '🇨🇳', '中华': '🇨🇳',
    '香港': '🇭🇰', '香港特别行政区': '🇭🇰',
    '澳门': '🇲🇴', '澳门特别行政区': '🇲🇴',
    #'台湾': '🇹🇼', '台湾地区': '🇹🇼',
    '台湾': '🇨🇳', '台湾地区': '🇨🇳',
    '日本': '🇯🇵', '东京': '🇯🇵', '大阪': '🇯🇵',
    '韩国': '🇰🇷', '南韩': '🇰🇷', '首尔': '🇰🇷',
    '朝鲜': '🇰🇵', '北韩': '🇰🇵',
    '新加坡': '🇸🇬',
    '马来西亚': '🇲🇾', '吉隆坡': '🇲🇾',
    '泰国': '🇹🇭', '曼谷': '🇹🇭',
    '越南': '🇻🇳', '胡志明': '🇻🇳', '河内': '🇻🇳',
    '菲律宾': '🇵🇭', '马尼拉': '🇵🇭',
    '印度尼西亚': '🇮🇩', '印尼': '🇮🇩', '雅加达': '🇮🇩', '巴厘岛': '🇮🇩',
    '印度': '🇮🇳', '孟买': '🇮🇳', '德里': '🇮🇳',
    '孟加拉国': '🇧🇩', '孟加拉': '🇧🇩',
    '巴基斯坦': '🇵🇰',
    '斯里兰卡': '🇱🇰',
    '尼泊尔': '🇳🇵',
    '不丹': '🇧🇹',
    '缅甸': '🇲🇲',
    '柬埔寨': '🇰🇭',
    '老挝': '🇱🇦',
    '蒙古': '🇲🇳',
    '格鲁吉亚': '🇬🇪',
    '亚美尼亚': '🇦🇲',
    '阿塞拜疆': '🇦🇿',
    '哈萨克斯坦': '🇰🇿',
    '乌兹别克斯坦': '🇺🇿',
    '土耳其': '🇹🇷', '伊斯坦布尔': '🇹🇷',
    '以色列': '🇮🇱',
    '巴勒斯坦': '🇵🇸',
    '沙特阿拉伯': '🇸🇦', '沙特': '🇸🇦', '利雅得': '🇸🇦',
    '阿联酋': '🇦🇪', '阿拉伯联合酋长国': '🇦🇪', '迪拜': '🇦🇪', '阿布扎比': '🇦🇪',
    '卡塔尔': '🇶🇦',
    '阿曼': '🇴🇲',
    '科威特': '🇰🇼',
    '巴林': '🇧🇭',
    '也门': '🇾🇪',
    '伊朗': '🇮🇷',
    '伊拉克': '🇮🇶',

    # 欧洲
    '俄罗斯': '🇷🇺', '俄国': '🇷🇺', '莫斯科': '🇷🇺',
    '德国': '🇩🇪', '柏林': '🇩🇪', '法兰克福': '🇩🇪',
    '英国': '🇬🇧', '联合王国': '🇬🇧', '伦敦': '🇬🇧',
    '法国': '🇫🇷', '巴黎': '🇫🇷',
    '意大利': '🇮🇹', '罗马': '🇮🇹', '米兰': '🇮🇹',
    '西班牙': '🇪🇸', '马德里': '🇪🇸', '巴塞罗那': '🇪🇸',
    '葡萄牙': '🇵🇹', '里斯本': '🇵🇹',
    '荷兰': '🇳🇱', '阿姆斯特丹': '🇳🇱',
    '比利时': '🇧🇪', '布鲁塞尔': '🇧🇪',
    '瑞士': '🇨🇭', '苏黎世': '🇨🇭',
    '奥地利': '🇦🇹', '维也纳': '🇦🇹',
    '瑞典': '🇸🇪', '斯德哥尔摩': '🇸🇪',
    '挪威': '🇳🇴', '奥斯陆': '🇳🇴',
    '丹麦': '🇩🇰', '哥本哈根': '🇩🇰',
    '芬兰': '🇫🇮', '赫尔辛基': '🇫🇮',
    '爱尔兰': '🇮🇪', '都柏林': '🇮🇪',
    '波兰': '🇵🇱', '华沙': '🇵🇱',
    '捷克': '🇨🇿', '捷克共和国': '🇨🇿', '布拉格': '🇨🇿',
    '匈牙利': '🇭🇺', '布达佩斯': '🇭🇺',
    '罗马尼亚': '🇷🇴',
    '保加利亚': '🇧🇬',
    '希腊': '🇬🇷', '雅典': '🇬🇷',
    '克罗地亚': '🇭🇷',
    '塞尔维亚': '🇷🇸',
    '乌克兰': '🇺🇦', '基辅': '🇺🇦',
    '白俄罗斯': '🇧🇾',
    '摩尔多瓦': '🇲🇩',
    '爱沙尼亚': '🇪🇪',
    '拉脱维亚': '🇱🇻',
    '立陶宛': '🇱🇹',
    '斯洛伐克': '🇸🇰',
    '斯洛文尼亚': '🇸🇮',
    '卢森堡': '🇱🇺',
    '马耳他': '🇲🇹',
    '塞浦路斯': '🇨🇾',
    '冰岛': '🇮🇸',
    '列支敦士登': '🇱🇮',
    '摩纳哥': '🇲🇨',
    '圣马力诺': '🇸🇲',
    '梵蒂冈': '🇻🇦',
    '英格兰': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    '苏格兰': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
    '威尔士': '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
    '北爱尔兰': '🇬🇧',

    # 美洲
    '美国': '🇺🇸', '美利坚合众国': '🇺🇸', '洛杉矶': '🇺🇸', '纽约': '🇺🇸', '芝加哥': '🇺🇸', '迈阿密': '🇺🇸',
    '加拿大': '🇨🇦', '多伦多': '🇨🇦', '温哥华': '🇨🇦', '蒙特利尔': '🇨🇦',
    '墨西哥': '🇲🇽', '墨西哥城': '🇲🇽',
    '巴西': '🇧🇷', '圣保罗': '🇧🇷', '里约': '🇧🇷',
    '阿根廷': '🇦🇷', '布宜诺斯艾利斯': '🇦🇷',
    '智利': '🇨🇱', '圣地亚哥': '🇨🇱',
    '哥伦比亚': '🇨🇴', '波哥大': '🇨🇴',
    '秘鲁': '🇵🇪', '利马': '🇵🇪',
    '委内瑞拉': '🇻🇪',
    '厄瓜多尔': '🇪🇨',
    '玻利维亚': '🇧🇴',
    '巴拉圭': '🇵🇾',
    '乌拉圭': '🇺🇾',
    '圭亚那': '🇬🇾',
    '苏里南': '🇸🇷',
    '法属圭亚那': '🇬🇫',
    '哥斯达黎加': '🇨🇷',
    '巴拿马': '🇵🇦',
    '危地马拉': '🇬🇹',
    '萨尔瓦多': '🇸🇻',
    '洪都拉斯': '🇭🇳',
    '尼加拉瓜': '🇳🇮',
    '伯利兹': '🇧🇿',
    '牙买加': '🇯🇲',
    '古巴': '🇨🇺',
    '多米尼加共和国': '🇩🇴', '多米尼加': '🇩🇴',
    '海地': '🇭🇹',
    '巴哈马': '🇧🇸',
    '巴巴多斯': '🇧🇧',
    '特立尼达和多巴哥': '🇹🇹',

    # 非洲
    '南非': '🇿🇦',
    '尼日利亚': '🇳🇬',
    '埃及': '🇪🇬', '开罗': '🇪🇬',
    '肯尼亚': '🇰🇪', '内罗毕': '🇰🇪',
    '加纳': '🇬🇭',
    '坦桑尼亚': '🇹🇿',
    '乌干达': '🇺🇬',
    '阿尔及利亚': '🇩🇿',
    '摩洛哥': '🇲🇦',
    '突尼斯': '🇹🇳',
    '埃塞俄比亚': '🇪🇹',
    '赞比亚': '🇿🇲',
    '津巴布韦': '🇿🇼',
    '马拉维': '🇲🇼',
    '安哥拉': '🇦🇴',
    '马达加斯加': '🇲🇬',
    '科特迪瓦': '🇨🇮', '象牙海岸': '🇨🇮',
    '塞内加尔': '🇸🇳',
    '喀麦隆': '🇨🇲',
    '贝宁': '🇧🇯',
    '多哥': '🇹🇬',
    '加蓬': '🇬🇦',
    '刚果': '🇨🇬', '刚果共和国': '🇨🇬',
    '刚果民主共和国': '🇨🇩', '民主刚果': '🇨🇩',
    '卢旺达': '🇷🇼',
    '布隆迪': '🇧🇮',
    '索马里': '🇸🇴',
    '利比亚': '🇱🇾',
    '苏丹': '🇸🇩',
    '毛里塔尼亚': '🇲🇷',
    '几内亚': '🇬🇳',
    '几内亚比绍': '🇬🇼',
    '利比里亚': '🇱🇷',
    '塞拉利昂': '🇸🇱',
    '冈比亚': '🇬🇲',
    '毛里求斯': '🇲🇺',
    '塞舌尔': '🇸🇨',
    '科摩罗': '🇰🇲',
    '佛得角': '🇨🇻',
    '圣多美和普林西比': '🇸🇹',
    '乍得': '🇹🇩',
    '尼日尔': '🇳🇪',
    '布基纳法索': '🇧🇫',
    '马里': '🇲🇱',

    # 大洋洲
    '澳大利亚': '🇦🇺', '澳洲': '🇦🇺', '悉尼': '🇦🇺', '墨尔本': '🇦🇺',
    '新西兰': '🇳🇿', '奥克兰': '🇳🇿',
    '斐济': '🇫🇯',
    '巴布亚新几内亚': '🇵🇬',
    '所罗门群岛': '🇸🇧',
    '瓦努阿图': '🇻🇺',
    '汤加': '🇹🇴',
    '萨摩亚': '🇼🇸',
    '基里巴斯': '🇰🇮',
    '密克罗尼西亚': '🇫🇲',
    '马绍尔群岛': '🇲🇭',
    '瑙鲁': '🇳🇷',
    '帕劳': '🇵🇼',
    '图瓦卢': '🇹🇻',

    # 特殊
    '全球': '🌍', '世界': '🌍',
    '国际': '🌐',
    '未知': '❓',
    '私有': '🔒', '私人': '🔒',
    '备份': '🔄',
    '自动': '🤖',
    '直连': '➡️', '直接': '➡️',
    '拒绝': '🚫',
}

COUNTRY_KEYWORDS = {}
for k, v in COUNTRY_FLAGS.items():
    if k not in ('global', 'unknown'):
        COUNTRY_KEYWORDS[k.lower()] = v



def get_flag_emoji(name: str) -> str:
    """
    根据国家/地区名称（中文、英文、代码、城市等）返回对应国旗 emoji。
    - 优先匹配中文名称（如“美国”）
    - 其次匹配完整英文名称或长关键词
    - 最后匹配两字母国家代码
    - 若无法识别，返回空字符串
    """
    if not name or not isinstance(name, str):
        return ''

    name = name.strip()
    # 如果输入已经是国旗 emoji（两个区域指示符），直接返回
    if re.match(r'[\U0001F1E6-\U0001F1FF]{2}', name):
        return name

    name_lower = name.lower()

    # 1. 精确匹配（原始字符串和全小写）
    if name in COUNTRY_FLAGS:
        return COUNTRY_FLAGS[name]
    if name_lower in COUNTRY_FLAGS:
        return COUNTRY_FLAGS[name_lower]

    # 2. 提取连续中文字符串并匹配（优先处理中文，避免“CN2”里的“CN”干扰）
    chinese_parts = re.findall(r'[\u4e00-\u9fff]+', name)
    for ch in chinese_parts:
        if ch in COUNTRY_FLAGS:
            return COUNTRY_FLAGS[ch]

    # 3. 匹配两字母国家代码（如 us, jp, cn），需单词边界（避免 CN2 中的 CN）
    words = re.findall(r'\b[a-z]{2}\b', name_lower)
    for word in words:
        if word in COUNTRY_FLAGS:
            return COUNTRY_FLAGS[word]

    # 4. 长关键词子串匹配（按长度降序，优先匹配更长的关键词，减少误匹配）
    keywords = sorted([k for k in COUNTRY_FLAGS.keys() if len(k) >= 2], key=len, reverse=True)
    for keyword in keywords:
        if keyword in name_lower:
            return COUNTRY_FLAGS[keyword]

    return ''

def add_flags_to_proxies(data: dict) -> dict:
    """遍历 proxies，为每个节点 name 添加国旗"""
    proxies = data.get('proxies', [])
    updated_proxies = []

    for proxy in proxies:
        original_name = proxy.get('name', '')
        flag = get_flag_emoji(original_name)
        if flag and not original_name.startswith(flag):
            proxy['name'] = flag + ' ' + original_name
        updated_proxies.append(proxy)

    data['proxies'] = updated_proxies
    return data

def output_file(input_file: str, output_file: str):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    updated_data = add_flags_to_proxies(data)

    #with open(output_file, 'w', encoding='utf-8') as f:
    #    yaml.dump(updated_data, f, allow_unicode=True, sort_keys=False, default_flow_style=True)
    # 手动控制 proxies 的缩进和格式
    with open(output_file, 'w', encoding='utf-8') as f:

        f.write('proxies:\n')
        for proxy in updated_data['proxies']:
            f.write(f"  - {proxy}\n")

    print(f"✅ 已生成带国旗的配置文件：{output_file}")    
    

# ---------- 生成 Clash YAML ----------
def generate_clash_yaml(config, output_file='tmp_fanvpn.yaml'):
    nodes = config['nodes']

    # 构建 proxies
    proxies = []
    for node in nodes:
        name = node.get('name', f"{node['server']}:{node['port']}")
        proxies.append({
            'name': name,
            'type': 'http',
            'server': node['server'],
            'port': node['port'],
            'tls': True,
            'skip-cert-verify': True
        })

    # 策略组
    proxy_names = [p['name'] for p in proxies]
    proxy_groups = [
        {
            'name': 'PROXY',
            'type': 'select',
            'proxies': proxy_names + ['DIRECT']
        },
        {
            'name': 'DIRECT',
            'type': 'select',
            'proxies': ['DIRECT']
        }
    ]

    # 国内直连域名（来自 PAC 脚本）
    direct_domains = [
        ".cn", ".baidu.com", ".qq.com", ".weixin.qq.com",
        ".taobao.com", ".tmall.com", ".jd.com", ".alipay.com",
        ".aliyun.com", ".tencent.com", ".163.com", ".126.com",
        ".sina.com.cn", ".weibo.com", ".bilibili.com", ".iqiyi.com",
        ".youku.com", ".meituan.com", ".dianping.com", ".ctrip.com",
        ".zhihu.com", ".douban.com", ".xiaohongshu.com", ".toutiao.com",
        ".bytedance.com", ".douyin.com", ".kuaishou.com"
    ]

    rules = []
    for d in direct_domains:
        if d.startswith('.'):
            rules.append(f"DOMAIN-SUFFIX,{d[1:]},DIRECT")
        else:
            rules.append(f"DOMAIN,{d},DIRECT")
    rules.extend([
        "IP-CIDR,127.0.0.0/8,DIRECT",
        "IP-CIDR,192.168.0.0/16,DIRECT",
        "IP-CIDR,10.0.0.0/8,DIRECT",
        "GEOIP,CN,DIRECT",
        "MATCH,PROXY"
    ])

    clash_config = {
        'port': 7890,
        'socks-port': 7891,
        'allow-lan': False,
        'mode': 'rule',
        'log-level': 'info',
        'proxies': proxies,
        'proxy-groups': proxy_groups,
        'rules': rules
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(clash_config, f, allow_unicode=True, sort_keys=False)

    print(f"✅ Clash 配置文件已生成: {output_file}")
    print(f"📡 共 {len(nodes)} 个节点")
    return clash_config
    
# 获取文件的修改时间和大小
def get_file_info(file_path):
    try:
        if not os.path.exists(file_path):
            return None, None, f"文件不存在: {file_path}"
        
        # 获取修改时间（时间戳）
        mod_time = os.path.getmtime(file_path)
        # 转换为年月日格式
        mod_date = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d")
        
        # 获取文件大小（字节）
        file_size = os.path.getsize(file_path)
        
        return mod_date, file_size, None
    
    except Exception as e:
        return None, None, f"读取文件失败: {str(e)}"
        
#对比两个文件信息
def compare_files(file1, file2) :
    # 获取文件信息
    date1, size1, err1 = get_file_info(file1)
    date2, size2, err2 = get_file_info(file2)
    
    # 处理错误情况
    if err1:
        print(f"文件1错误: {err1}")
        return 1

    if size1 < 1000 : # 文件太小 
        print(f"文件太小: {size1}")
        return 1
    
    print(f"文件时间 {date1}, {date2}")
    return 2
    #if date1 != date2:
    #    return 2
    #else: # date1 == date2
    #    return 3 
    

# ---------- 主程序 ----------
if __name__ == '__main__':
    try:
        print("📂 从 background.js 提取私钥...")
        private_key_pem = extract_private_key_from_js(BACKGROUND_JS_PATH)
        print("✅ 私钥提取成功")

        print("🌍 正在从备用地址获取加密配置...")
        envelope = fetch_envelope(CONFIG_URLS)
        print("✅ 密文获取成功")

        print("🔐 正在解密配置...")
        config = decrypt_config(envelope, private_key_pem)

        print("✅ 解密成功，节点列表：")
        for idx, node in enumerate(config['nodes'], 1):
            print(f"  {idx}. {node.get('name', '未命名')}: {node['server']}:{node['port']}")
        print("\n📝 生成 Clash YAML...")

        sourceFile= yaml_file_tmp
        destinationFile = yaml_file_dst
        generate_clash_yaml(config, sourceFile)
        if compare_files(sourceFile, destinationFile) == 2 :#文件不相同，复制
            # 复制文件
            try:
                #生成带国旗的配置文件
                input_path = sourceFile     
                output_path = sourceFile

                if not os.path.exists(input_path):
                    print(f"❌ 文件 {input_path} 不存在！")
                else:
                    output_file(input_path, output_path)

                shutil.copy(sourceFile, destinationFile)
                print("文件复制成功", destinationFile)
            except Exception as e:
                print("复制失败:", e)
        else:
            print("不用复制文件")
    except Exception as e:
        print(f"❌ 发生错误: {e}")