#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadowrocket AntiLeak & AdBlock 规则自动构建与合并脚本
数据源:
- 广告过滤: Johnshall/Shadowrocket-ADBlock-Rules-Forever (sr_ad_only.conf)
- 防 DNS 泄露分流模板: Mini-AntiLeak.conf (基于 xiaolin-007 与 ACL4SSR 最佳实践)
- Android/跨平台: 同步输出 Clash Meta (Mihomo) 配置与转换后的广告规则集
  (模板 clash/Meta-AntiLeak.yaml -> output/clash/, 与 iOS 版同源同日构建)
"""

import os
import sys
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

UPSTREAM_AD_URLS = [
    "https://raw.githubusercontent.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever/release/sr_ad_only.conf",
    "https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever/sr_ad_only.conf"
]

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "../rules/Mini-AntiLeak.conf")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../output/sr_ad_antileak.conf")
OUTPUT_MINI_FILE = os.path.join(os.path.dirname(__file__), "../output/Mini-AntiLeak.conf")
CLASH_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "../clash/Meta-AntiLeak.yaml")
CLASH_OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../output/clash/Meta-AntiLeak.yaml")
CLASH_AD_OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../output/clash/ad_johnshall_clash.list")

def fetch_upstream_ad_rules():
    """从上游仓库拉取最新的仅去广告规则"""
    content = ""
    for url in UPSTREAM_AD_URLS:
        try:
            print(f"正在从上游拉取去广告规则: {url} ...")
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Shadowrocket-Rule-Builder/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    content = resp.read().decode("utf-8")
                    print(f"成功获取上游规则，大小: {len(content)} 字节")
                    break
        except Exception as e:
            print(f"拉取失败 ({url}): {e}")
            continue

    if not content:
        print("警告: 无法从网络获取最新上游规则，使用内置回退基础广告规则集。")
        content = get_fallback_ad_rules()
    return content

def get_fallback_ad_rules():
    """网络不可达时的基础兜底广告过滤规则"""
    return """
# 基础通用广告与追踪拦截
DOMAIN-KEYWORD,adservice,REJECT
DOMAIN-KEYWORD,telemetry,REJECT
DOMAIN-KEYWORD,analytics,REJECT
DOMAIN-SUFFIX,adcolony.com,REJECT
DOMAIN-SUFFIX,adjust.com,REJECT
DOMAIN-SUFFIX,admob.com,REJECT
DOMAIN-SUFFIX,ads.youtube.com,REJECT
DOMAIN-SUFFIX,applovin.com,REJECT
DOMAIN-SUFFIX,appsflyer.com,REJECT
DOMAIN-SUFFIX,unityads.unity3d.com,REJECT
DOMAIN-SUFFIX,vungle.com,REJECT
DOMAIN-SUFFIX,umeng.com,REJECT
DOMAIN-SUFFIX,pangolin-sdk-toutiao.com,REJECT
DOMAIN-SUFFIX,pglstatp-toutiao.com,REJECT
DOMAIN-SUFFIX,e.qq.com,REJECT
DOMAIN-SUFFIX,gdt.qq.com,REJECT
DOMAIN-SUFFIX,baidustatic.com,REJECT
DOMAIN-SUFFIX,pos.baidu.com,REJECT
"""

def extract_ad_rules(raw_conf):
    """从去广告配置文件中提取所有 REJECT 规则行并去重优化"""
    ad_rules = []
    seen = set()

    for line in raw_conf.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//") or line.startswith("["):
            continue
        
        # 匹配 Shadowrocket 规则指令
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2:
            action = parts[-1].upper()
            if action in ("REJECT", "REJECT-DROP", "REJECT-TINYGIF"):
                # 如果是 IP-CIDR 类规则，强制附加 no-resolve 防止本地 DNS 泄漏
                if parts[0].upper() in ("IP-CIDR", "IP-CIDR6", "GEOIP"):
                    if "no-resolve" not in [p.lower() for p in parts]:
                        line = f"{line},no-resolve"
                
                if line not in seen:
                    seen.add(line)
                    ad_rules.append(line)

    print(f"已提取去广告规则: {len(ad_rules)} 条")
    return ad_rules

def build_combined_config(ad_rules):
    """结合防 DNS 泄露模板构建完整规则文件"""
    beijing_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")

    header = f"""# =================================================================
# Shadowrocket AntiLeak + ADBlock 整合规则 (防 DNS 泄露 + 强效广告过滤)
#
# 构建时间: {beijing_time} (UTC+8)
# 去广告来源: Johnshall/Shadowrocket-ADBlock-Rules-Forever
# 防 DNS 泄露模型: xiaolin-007 / ACL4SSR 架构
#
# 【防 DNS 泄露关键机制】
# 1. ipv6 = false & prefer-ipv6 = false: 彻底封堵运营商 IPv6 DNS 劫持与泄漏
# 2. dns-direct-system = false: 禁用直连请求直接泄露至系统本地 DNS
# 3. dns-direct-fallback-proxy = true: 直连解析异常自动降级至代理安全查询
# 4. 所有 IP-CIDR 与 GEOIP 规则强制添加 no-resolve: 严防域名预解析
# 5. FINAL,PROXY: 未命中白名单的境外请求全部远端代理代理解析，杜绝本地查询
# =================================================================

[General]
bypass-system = true
skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com
tun-excluded-routes = 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.0.0.0/24, 192.0.2.0/24, 192.88.99.0/24, 192.168.0.0/16, 198.51.100.0/24, 203.0.113.0/24, 224.0.0.0/4, 255.255.255.255/32, 239.255.255.250/32
dns-server = system
ipv6 = false
prefer-ipv6 = false
dns-fallback-system = false
dns-direct-system = false
icmp-auto-reply = true
always-reject-url-rewrite = false
private-ip-answer = true
dns-direct-fallback-proxy = true

[Rule]
# -------------------------------------------------------------
# 1. 强力去广告与隐私追踪拦截规则集 (来自 Johnshall 规则库)
# -------------------------------------------------------------
"""

    rules_body = "\n".join(ad_rules)

    middle = """

# -------------------------------------------------------------
# 2. 局域网与本地直连规则
# -------------------------------------------------------------
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/LocalAreaNetwork.list,DIRECT
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/UnBan.list,DIRECT

# -------------------------------------------------------------
# 3. 国内直连域名名单 (直接根据域名走直连，无需预解析其他域名)
# -------------------------------------------------------------
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/GoogleCN.list,DIRECT
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaDomain.list,DIRECT
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaMedia.list,DIRECT
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Apple.list,DIRECT

# -------------------------------------------------------------
# 4. 国内 IP 与 GEOIP 规则 (必须保持 no-resolve，避免域名反查泄露)
# -------------------------------------------------------------
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaCompanyIp.list,DIRECT,no-resolve
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaIp.list,DIRECT,no-resolve
GEOIP,CN,DIRECT,no-resolve

# -------------------------------------------------------------
# 5. 兜底策略: 所有非大陆域名直接交由境外代理节点远端解析
# -------------------------------------------------------------
FINAL,PROXY

[Host]
localhost = 127.0.0.1

[URL Rewrite]
^https?://(www.)?g.cn https://www.google.com 302
^https?://(www.)?google.cn https://www.google.com 302
"""

    return header + rules_body + middle

# Clash classical 规则集支持的规则类型 (与 Shadowrocket 的交集)
CLASH_SUPPORTED_TYPES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
    "IP-CIDR", "IP-CIDR6", "GEOIP",
}

def convert_ad_rules_to_clash(ad_rules):
    """把 Shadowrocket 格式的去广告规则转换为 Clash classical 规则集格式。

    转换规则: 去掉行尾的策略 (REJECT 等, 统一由引用处的 RULE-SET,...,REJECT
    指定); IP 类规则保留/补齐 no-resolve; Clash 不支持的规则类型跳过并计数。
    """
    clash_rules = []
    seen = set()
    skipped = 0
    for line in ad_rules:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            skipped += 1
            continue
        rule_type = parts[0].upper()
        value = parts[1]
        if rule_type not in CLASH_SUPPORTED_TYPES or not value:
            skipped += 1
            continue
        converted = f"{rule_type},{value}"
        if rule_type in ("IP-CIDR", "IP-CIDR6", "GEOIP"):
            converted += ",no-resolve"
        if converted not in seen:
            seen.add(converted)
            clash_rules.append(converted)
    print(f"Clash 广告规则转换完成: {len(clash_rules)} 条 (跳过不支持类型 {skipped} 条)")
    return clash_rules

def build_clash_outputs(ad_rules):
    """生成 Android/跨平台 Clash Meta (Mihomo) 输出:
    1. 复制 clash/Meta-AntiLeak.yaml 模板到 output/clash/
    2. 把 Johnshall 去广告规则转换为 Clash classical 规则集, 供模板以
       RULE-SET,JohnshallAD,REJECT 远程引用, 与 iOS 版每日同步更新
    """
    os.makedirs(os.path.dirname(CLASH_OUTPUT_FILE), exist_ok=True)

    if os.path.exists(CLASH_TEMPLATE_PATH):
        with open(CLASH_TEMPLATE_PATH, "r", encoding="utf-8") as f_in:
            with open(CLASH_OUTPUT_FILE, "w", encoding="utf-8") as f_out:
                f_out.write(f_in.read())
        print(f"已同步生成 Clash Meta 配置: {CLASH_OUTPUT_FILE}")
    else:
        print(f"警告: 未找到 Clash 模板 {CLASH_TEMPLATE_PATH}, 跳过 Clash 配置同步")

    beijing_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    clash_rules = convert_ad_rules_to_clash(ad_rules)
    header = f"""# Johnshall 去广告规则 (Clash classical 格式, 由 scripts/build.py 自动转换)
# 来源: Johnshall/Shadowrocket-ADBlock-Rules-Forever (sr_ad_only.conf)
# 构建时间: {beijing_time} (UTC+8), 共 {len(clash_rules)} 条
# 用法: RULE-SET,JohnshallAD,REJECT (策略由引用处指定, 本文件不带策略)
"""
    with open(CLASH_AD_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(clash_rules) + "\n")
    print(f"已生成 Clash 广告规则集: {CLASH_AD_OUTPUT_FILE} (共 {len(clash_rules)} 条)")

def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # 复制基础 Mini-AntiLeak.conf 到 output
    if os.path.exists(TEMPLATE_PATH):
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f_in:
            with open(OUTPUT_MINI_FILE, "w", encoding="utf-8") as f_out:
                f_out.write(f_in.read())
        print(f"已同步生成极简防泄露配置: {OUTPUT_MINI_FILE}")

    # 拉取并合并去广告规则
    raw_ad_conf = fetch_upstream_ad_rules()
    ad_rules = extract_ad_rules(raw_ad_conf)
    combined_content = build_combined_config(ad_rules)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(combined_content)

    print(f"构建完成! 完整规则文件输出至: {OUTPUT_FILE} (共包含广告规则 {len(ad_rules)} 条)")

    # 同步生成 Android/跨平台 Clash Meta 配置与规则集
    build_clash_outputs(ad_rules)

if __name__ == "__main__":
    main()
