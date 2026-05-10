import os
import shutil
import yaml
import re
import socket
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from collections import defaultdict
from datetime import datetime

yaml_file_tmp = "./File/tmp_go.yaml"
yaml_file_dst = "./File/go.yaml"

class ClashProxyRenamer:
    def __init__(self):
        # 国家代码到名称和国旗的映射
        self.country_info = {
            'US': {'name': '美国', 'flag': '🇺🇸', 'emoji': '🇺🇸', 'cn': '美国'},
            'JP': {'name': '日本', 'flag': '🇯🇵', 'emoji': '🇯🇵', 'cn': '日本'},
            'HK': {'name': '香港', 'flag': '🇭🇰', 'emoji': '🇭🇰', 'cn': '香港'},
            'SG': {'name': '新加坡', 'flag': '🇸🇬', 'emoji': '🇸🇬', 'cn': '新加坡'},
            'KR': {'name': '韩国', 'flag': '🇰🇷', 'emoji': '🇰🇷', 'cn': '韩国'},
            'UK': {'name': '英国', 'flag': '🇬🇧', 'emoji': '🇬🇧', 'cn': '英国'},
            'GB': {'name': '英国', 'flag': '🇬🇧', 'emoji': '🇬🇧', 'cn': '英国'},
            'DE': {'name': '德国', 'flag': '🇩🇪', 'emoji': '🇩🇪', 'cn': '德国'},
            'FR': {'name': '法国', 'flag': '🇫🇷', 'emoji': '🇫🇷', 'cn': '法国'},
            'CA': {'name': '加拿大', 'flag': '🇨🇦', 'emoji': '🇨🇦', 'cn': '加拿大'},
            'AU': {'name': '澳大利亚', 'flag': '🇦🇺', 'emoji': '🇦🇺', 'cn': '澳大利亚'},
            'RU': {'name': '俄罗斯', 'flag': '🇷🇺', 'emoji': '🇷🇺', 'cn': '俄罗斯'},
            'NL': {'name': '荷兰', 'flag': '🇳🇱', 'emoji': '🇳🇱', 'cn': '荷兰'},
            'TW': {'name': '台湾', 'flag': '🇨🇳', 'emoji': '🇨🇳', 'cn': '台湾'},
            'IN': {'name': '印度', 'flag': '🇮🇳', 'emoji': '🇮🇳', 'cn': '印度'},
            'BR': {'name': '巴西', 'flag': '🇧🇷', 'emoji': '🇧🇷', 'cn': '巴西'},
            'IT': {'name': '意大利', 'flag': '🇮🇹', 'emoji': '🇮🇹', 'cn': '意大利'},
            'ES': {'name': '西班牙', 'flag': '🇪🇸', 'emoji': '🇪🇸', 'cn': '西班牙'},
            'SE': {'name': '瑞典', 'flag': '🇸🇪', 'emoji': '🇸🇪', 'cn': '瑞典'},
            'NO': {'name': '挪威', 'flag': '🇳🇴', 'emoji': '🇳🇴', 'cn': '挪威'},
            'DK': {'name': '丹麦', 'flag': '🇩🇰', 'emoji': '🇩🇰', 'cn': '丹麦'},
            'FI': {'name': '芬兰', 'flag': '🇫🇮', 'emoji': '🇫🇮', 'cn': '芬兰'},
            'PL': {'name': '波兰', 'flag': '🇵🇱', 'emoji': '🇵🇱', 'cn': '波兰'},
            'CZ': {'name': '捷克', 'flag': '🇨🇿', 'emoji': '🇨🇿', 'cn': '捷克'},
            'MY': {'name': '马来西亚', 'flag': '🇲🇾', 'emoji': '🇲🇾', 'cn': '马来西亚'},
            'TH': {'name': '泰国', 'flag': '🇹🇭', 'emoji': '🇹🇭', 'cn': '泰国'},
            'VN': {'name': '越南', 'flag': '🇻🇳', 'emoji': '🇻🇳', 'cn': '越南'},
            'ID': {'name': '印度尼西亚', 'flag': '🇮🇩', 'emoji': '🇮🇩', 'cn': '印度尼西亚'},
            'PH': {'name': '菲律宾', 'flag': '🇵🇭', 'emoji': '🇵🇭', 'cn': '菲律宾'},
            'TR': {'name': '土耳其', 'flag': '🇹🇷', 'emoji': '🇹🇷', 'cn': '土耳其'},
            'AE': {'name': '阿联酋', 'flag': '🇦🇪', 'emoji': '🇦🇪', 'cn': '阿联酋'},
            'SA': {'name': '沙特阿拉伯', 'flag': '🇸🇦', 'emoji': '🇸🇦', 'cn': '沙特阿拉伯'},
            'CH': {'name': '瑞士', 'flag': '🇨🇭', 'emoji': '🇨🇭', 'cn': '瑞士'},
            'AT': {'name': '奥地利', 'flag': '🇦🇹', 'emoji': '🇦🇹', 'cn': '奥地利'},
            'BE': {'name': '比利时', 'flag': '🇧🇪', 'emoji': '🇧🇪', 'cn': '比利时'},
            'IE': {'name': '爱尔兰', 'flag': '🇮🇪', 'emoji': '🇮🇪', 'cn': '爱尔兰'},
            'NZ': {'name': '新西兰', 'flag': '🇳🇿', 'emoji': '🇳🇿', 'cn': '新西兰'},
            'ZA': {'name': '南非', 'flag': '🇿🇦', 'emoji': '🇿🇦', 'cn': '南非'},
        }
        
        # IP缓存，避免重复查询
        self.ip_cache = {}
        
        # 离线IP数据库文件路径（可选，如果有GeoLite2数据库）
        self.geoip_reader = None
        try:
            import geoip2.database
            # 如果有GeoLite2数据库文件，请设置路径
            # self.geoip_reader = geoip2.database.Reader('./GeoLite2-Country.mmdb')
            pass
        except:
            pass
    
    def download_config(self, url, timeout=15):
        """下载单个YAML配置文件"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/x-yaml,text/yaml,text/plain,*/*'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # 尝试解析YAML
            config = yaml.safe_load(response.text)
            return config
        except Exception as e:
            print(f"❌ 下载失败 {url}: {str(e)}")
            return None
    
    def extract_proxies_from_config(self, config, source_url):
        """从配置中提取proxies节点"""
        if not config:
            return []
        
        proxies = []
        
        # 直接包含proxies字段
        if 'proxies' in config and isinstance(config['proxies'], list):
            proxies = config['proxies']
        # 整个文件就是proxies列表
        elif isinstance(config, list):
            proxies = config
        # 其他格式尝试查找
        else:
            for key in ['Proxy', 'proxy', 'servers', 'nodes', 'proxys']:
                if key in config and isinstance(config[key], list):
                    proxies = config[key]
                    break
        
        # 为每个代理添加来源标记
        #for proxy in proxies:
            #proxy['_source'] = source_url
        
        return proxies
    
    def download_all_configs(self, urls, max_workers=5):
        """并发下载多个配置文件"""
        all_proxies = []
        
        print(f"\n📥 开始下载 {len(urls)} 个配置文件...\n")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.download_config, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    config = future.result()
                    if config:
                        proxies = self.extract_proxies_from_config(config, url)
                        all_proxies.extend(proxies)
                        print(f"✅ 成功: {url[:60]}... -> 获取 {len(proxies)} 个节点")
                    else:
                        print(f"⚠️  失败: {url[:60]}...")
                except Exception as e:
                    print(f"❌ 错误: {url[:60]}... -> {str(e)}")
        
        return all_proxies
    
    def parse_server_to_ip(self, server):
        """将server字段解析为IP地址"""
        if not server or not isinstance(server, str):
            return None
        
        # 处理纯IP
        ip_pattern = r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        match = re.match(ip_pattern, server)
        if match:
            return match.group(1)
        
        # 处理IP:端口格式
        match = re.match(ip_pattern + r'(?::\d+)?$', server)
        if match:
            return match.group(1)
        
        # 处理URL格式
        if server.startswith(('http://', 'https://')):
            try:
                parsed = urlparse(server)
                hostname = parsed.hostname
                if hostname:
                    if re.match(ip_pattern, hostname):
                        return hostname
                    # 解析域名
                    ip = socket.gethostbyname(hostname)
                    return ip
            except:
                pass
        
        # 处理普通域名
        if '.' in server:
            domain = server.split(':')[0]
            try:
                ip = socket.gethostbyname(domain)
                return ip
            except:
                pass
        
        return None
    
    def get_country_by_ip_online_precise(self, ip):
        """使用多个在线API精确查询IP国家（更精确）"""
        if ip in self.ip_cache:
            return self.ip_cache[ip]
        
        # API列表（按优先级排序）
        apis = [
            # ip-api.com - 免费，准确率高
            lambda: self._query_ip_api(ip),
            # ipinfo.io - 需要token但免费额度高
            lambda: self._query_ipinfo(ip),
            # ipwhois.io - 免费
            lambda: self._query_ipwhois(ip),
            # freeipapi.com - 免费
            lambda: self._query_freeipapi(ip),
        ]
        
        for api_func in apis:
            try:
                country_code = api_func()
                if country_code:
                    self.ip_cache[ip] = country_code
                    return country_code
            except:
                continue
            
            # 避免请求过快
            time.sleep(0.1)
        
        self.ip_cache[ip] = None
        return None
    
    def _query_ip_api(self, ip):
        """查询 ip-api.com"""
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode", timeout=3)
            data = response.json()
            if data.get('status') == 'success':
                return data.get('countryCode')
        except:
            pass
        return None
    
    def _query_ipinfo(self, ip):
        """查询 ipinfo.io（需要token，但免费版也有一定额度）"""
        try:
            # 免费版不需要token，但有速率限制
            response = requests.get(f"https://ipinfo.io/{ip}/country", timeout=3)
            if response.status_code == 200:
                code = response.text.strip()
                if code and len(code) == 2:
                    return code
        except:
            pass
        return None
    
    def _query_ipwhois(self, ip):
        """查询 ipwhois.io"""
        try:
            response = requests.get(f"http://ipwhois.app/json/{ip}", timeout=3)
            data = response.json()
            if data.get('success') != False:
                return data.get('country_code')
        except:
            pass
        return None
    
    def _query_freeipapi(self, ip):
        """查询 freeipapi.com"""
        try:
            response = requests.get(f"https://freeipapi.com/api/json/{ip}", timeout=3)
            data = response.json()
            return data.get('countryCode')
        except:
            pass
        return None
    
    def get_country_by_geoip2(self, ip):
        """使用本地GeoIP2数据库查询（最精确）"""
        if self.geoip_reader:
            try:
                response = self.geoip_reader.country(ip)
                return response.country.iso_code
            except:
                pass
        return None
    
    def get_country_from_domain(self, server):
        """从域名提取国家代码"""
        if '.' in server:
            # 常见国家域名后缀
            domain_map = {
                '.us': 'US', '.jp': 'JP', '.hk': 'HK', '.sg': 'SG',
                '.kr': 'KR', '.uk': 'GB', '.de': 'DE', '.fr': 'FR',
                '.ca': 'CA', '.au': 'AU', '.ru': 'RU', '.nl': 'NL',
                '.it': 'IT', '.es': 'ES', '.br': 'BR', '.in': 'IN',
            }
            server_lower = server.lower()
            for suffix, code in domain_map.items():
                if server_lower.endswith(suffix) or f'.{suffix}' in server_lower:
                    return code
            
            # 从子域名提取
            parts = server_lower.split('.')
            for part in parts:
                if part.upper() in self.country_info:
                    return part.upper()
                # 匹配国家代码（2字母）
                if len(part) == 2 and part.upper() in self.country_info:
                    return part.upper()
        return None
    
    def get_country_code_precise(self, server):
        """精确获取server对应的国家代码"""
        if not server:
            return 'UN'
        
        # 1. 先从域名提取（最快）
        code = self.get_country_from_domain(server)
        if code:
            return code
        
        # 2. 解析IP
        ip = self.parse_server_to_ip(server)
        if ip:
            # 3. 使用本地GeoIP2数据库（最精确）
            code = self.get_country_by_geoip2(ip)
            if code:
                return code
            
            # 4. 使用在线API精确查询
            code = self.get_country_by_ip_online_precise(ip)
            if code:
                return code
        
        # 5. 尝试从原始名称中提取
        return 'UN'
    
    def get_country_display(self, code):
        """获取国家显示名称（含国旗）"""
        if code in self.country_info:
            info = self.country_info[code]
            return f"{info['flag']}{info['name']}"
        return f"🌍未知"
    
    def extract_number_from_name(self, name):
        """从原始名称中提取数字后缀"""
        if not name:
            return ''
        match = re.search(r'(\d+)$', str(name))
        return match.group(1) if match else ''
    
    def group_and_number_nodes(self, proxies):
        """按国家分组并为每个国家的节点添加编号（保留原始顺序）"""
        # 按国家分组，保持原始顺序
        country_groups = defaultdict(list)
        
        for proxy in proxies:
            server = proxy.get('server', '')
            code = self.get_country_code_precise(server)
            proxy['_country_code'] = code
            
            # 保留原始名称中的数字后缀
            original_name = proxy.get('name', '')
            suffix = self.extract_number_from_name(original_name)
            proxy['_suffix'] = suffix
            
            country_groups[code].append(proxy)
        
        # 为每个节点添加编号
        all_processed = []
        
        for code, nodes in country_groups.items():
            country_display = self.get_country_display(code)
            
            for idx, node in enumerate(nodes, 1):
                # 格式：国旗+国家名+编号
                if node.get('_suffix'):
                    # 如果原名称有数字后缀，使用原后缀而不是序号
                    node['name'] = f"{country_display}{node['_suffix']}"
                else:
                    node['name'] = f"{country_display}{idx}"
                
                # 删除临时字段
                if '_country_code' in node:
                    del node['_country_code']
                if '_suffix' in node:
                    del node['_suffix']
                if '_source' in node:
                    # 保留来源作为备注
                    pass
                
                all_processed.append(node)
        
        return all_processed
    
    def process_urls(self, urls, output_path='proxies_only.yaml', max_workers=5):
        """从多个URL下载配置，处理并输出代理节点"""
        
        print("="*70)
        print("🚀 Clash节点合并工具 - 精确IP识别版")
        print("="*70)
        
        # 1. 下载所有配置
        all_proxies = self.download_all_configs(urls, max_workers)
        
        if not all_proxies:
            print("\n❌ 未能获取任何节点，请检查URL是否有效")
            return
        
        print(f"\n📊 共获取 {len(all_proxies)} 个原始节点")
        
        # 2. 不去重，不过滤，直接处理
        print(f"\n🔄 正在识别节点国家并添加编号...")
        print(f"   (使用多个IP数据库，确保精确识别)\n")
        
        # 显示识别进度
        for i, proxy in enumerate(all_proxies, 1):
            server = proxy.get('server', '无')
            if i % 50 == 0:
                print(f"   进度: {i}/{len(all_proxies)}")
        
        processed_proxies = self.group_and_number_nodes(all_proxies)
        
        # 3. 只输出proxies部分
        output_data = {'proxies': processed_proxies}
        
        # 4. 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(output_data, f, allow_unicode=True, sort_keys=False, 
                     default_flow_style=False, indent=2, width=1000)
        
        # 5. 统计信息
        print("\n" + "="*70)
        print("✅ 处理完成！")
        print("="*70)
        print(f"📊 原始节点总数: {len(all_proxies)}")
        print(f"📊 处理后节点数: {len(processed_proxies)}")
        print(f"📊 去重处理: 无（保留所有节点）")
        print(f"📊 过滤处理: 无（保留所有节点）")
        
        # 统计IP缓存命中率
        cache_hits = len([v for v in self.ip_cache.values() if v is not None])
        print(f"📊 IP缓存命中: {cache_hits} 个")
        
        print(f"\n📋 节点分组统计:")
        country_count = defaultdict(int)
        for proxy in processed_proxies:
            # 提取国家名（去掉编号）
            name = proxy['name']
            country = re.sub(r'\d+$', '', name)
            country_count[country] += 1
        
        for country, count in sorted(country_count.items(), key=lambda x: x[1], reverse=True):
            print(f"   {country}: {count}个节点")
        
        print(f"\n📁 输出文件: {output_path}")
        print(f"📝 文件内容: 仅包含 proxies 节点（带国旗和编号）")
        
        # 显示前15个节点作为预览
        print(f"\n📋 节点预览（前15个）:")
        for i, proxy in enumerate(processed_proxies[:15], 1):
            proxy_type = proxy.get('type', 'unknown')
            server = proxy.get('server', '')[:35]
            print(f"   {i:2}. {proxy['name']:20} | {proxy_type:12} | {server}")
        
        if len(processed_proxies) > 15:
            print(f"   ... 还有 {len(processed_proxies) - 15} 个节点")

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
def compare_files(file1, file2):
    # 获取文件信息
    date1, size1, err1 = get_file_info(file1)
    date2, size2, err2 = get_file_info(file2)
    
    # 处理错误情况
    if err1:
        print(f"文件1错误: {err1}")
        return 1

    if size1 < 3000 : # 文件太小 
        print(f"文件太小: {size1}")
        return 1
    
    print(f"文件时间 {date1}, {date2}")
    return 2
    #if date1 != date2:
    #    return 2
    #else: # date1 == date2
    #    return 3

if __name__ == "__main__":
    renamer = ClashProxyRenamer()
    
    # 多个YAML配置文件的URL列表
    urls = [
        "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/quick/1/config.yaml",
        "https://gitlab.com/free9999/ipupdate/-/raw/master/backup/img/1/2/ipp/quick/1/config.yaml",
        "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/quick/2/config.yaml",
        "https://gitlab.com/free9999/ipupdate/-/raw/master/backup/img/1/2/ipp/quick/2/config.yaml",  
        "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/quick/3/config.yaml",
        "https://gitlab.com/free9999/ipupdate/-/raw/master/backup/img/1/2/ipp/quick/3/config.yaml",
        "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/quick/4/config.yaml",
        "https://gitlab.com/free9999/ipupdate/-/raw/master/backup/img/1/2/ipp/quick/4/config.yaml",   
        #
        "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/clash.meta2/1/config.yaml",
        "https://gitlab.com/free9999/ipupdate/-/raw/master/backup/img/1/2/ipp/clash.meta2/1/config.yaml",   
        "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/clash.meta2/2/config.yaml",
        "https://gitlab.com/free9999/ipupdate/-/raw/master/backup/img/1/2/ipp/clash.meta2/2/config.yaml",   
        "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/clash.meta2/3/config.yaml",
        "https://gitlab.com/free9999/ipupdate/-/raw/master/backup/img/1/2/ipp/clash.meta2/3/config.yaml",   
        "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/clash.meta2/4/config.yaml",
        "https://gitlab.com/free9999/ipupdate/-/raw/master/backup/img/1/2/ipp/clash.meta2/4/config.yaml",   
        "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/clash.meta2/5/config.yaml",
        "https://gitlab.com/free9999/ipupdate/-/raw/master/backup/img/1/2/ipp/clash.meta2/5/config.yaml",   
        "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/clash.meta2/6/config.yaml",
        "https://gitlab.com/free9999/ipupdate/-/raw/master/backup/img/1/2/ipp/clash.meta2/6/config.yaml",      
   ]

    sourceFile = yaml_file_tmp
    destinationFile = yaml_file_dst
    # 处理所有URL
    renamer.process_urls(
        urls=urls,
        output_path=sourceFile,
        max_workers=3  # 并发下载数量
    )

    if compare_files(sourceFile, destinationFile) ==2 :#文件不相同，复制
        # 复制文件
        try:
            shutil.copy(sourceFile, destinationFile)
            print("文件复制成功", destinationFile)
        except Exception as e:
            print("复制失败:", e)