#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadowrocket AntiLeak & AdBlock 规则自动构建与合并脚本
数据源:
- 广告过滤: Johnshall/Shadowrocket-ADBlock-Rules-Forever (sr_ad_only.conf)
- 防 DNS 泄露分流模板: Mini-AntiLeak.conf (基于 xiaolin-007 与 ACL4SSR 最佳实践)
- Android/跨平台: 同步输出 Clash Meta (Mihomo) 配置与转换后的广告规则集
  (模板 clash/Meta-AntiLeak.yaml -> output/clash/, 与 iOS 版同源同日构建)

失败策略 (fail loudly, 不静默降级):
- 上游全部拉取源失败、规则数超出上下限、任一 ACL4SSR 列表拉取失败、
  自检不通过, 一律非零退出, 不写任何输出文件, CI 不提交。
  历史上这里曾静默回退到 18 条内置规则还照常出包, 已删除该回退。
- 所有输出文件均原子写 (临时文件 + os.replace), 生成后立即自检。
- 用法: python3 scripts/build.py            # 完整构建
        python3 scripts/build.py --check    # 只校验已有 output/, 不联网

DNS 说明 (国内直连路径没有因为防泄露而变慢):
- Shadowrocket 与 Clash 的 DNS 均用 IP 字面量 DoH, 不再用主机名,
  因此不需要先用明文 DNS 解析 DoH 主机名本身。
- 国内域名 (geosite:cn / ChinaDomain / Apple 等) 仍走国内 DoH 直连
  (阿里 223.5.5.5 IP 字面量 / 腾讯 doh.pub, 无 #PROXY), 不经过代理、
  不走国外 DoH; 只有国外域名才走国外 DoH 经代理发出 / 远端解析。
"""

import argparse
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# 通用 UA, 不带任何可识别本仓库的特征串
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
FETCH_TIMEOUT = 30
FETCH_RETRIES = 2

UPSTREAM_AD_URLS = [
    "https://raw.githubusercontent.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever/release/sr_ad_only.conf",
    "https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever/sr_ad_only.conf",
    # jsDelivr 镜像, 2026-11-24 实测 200 且与 Raw 内容一致 (2,088,992 字节)
    "https://cdn.jsdelivr.net/gh/Johnshall/Shadowrocket-ADBlock-Rules-Forever@release/sr_ad_only.conf",
]

# Johnshall 规则数上下限 (2026-11-23 实测 52,655 条; 超出即视为上游异常)
AD_RULES_MIN = 1000
AD_RULES_MAX = 200000

# ACL4SSR 10 个列表: 由本脚本自托管到 output/clash/acl4ssr/,
# 模板与 JS 覆写改引本仓地址, 客户端不再直连原仓拉取。
ACL4SSR_NAMES = [
    "BanAD", "BanProgramAD", "LocalAreaNetwork", "UnBan",
    "GoogleCN", "ChinaDomain", "ChinaMedia", "Apple",
    "ChinaCompanyIp", "ChinaIp",
]

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "../rules/Mini-AntiLeak.conf")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../output/sr_ad_antileak.conf")
OUTPUT_MINI_FILE = os.path.join(os.path.dirname(__file__), "../output/Mini-AntiLeak.conf")
CLASH_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "../clash/Meta-AntiLeak.yaml")
CLASH_OVERRIDE_DIR = os.path.join(os.path.dirname(__file__), "../clash/override")
CLASH_OVERRIDE_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../output/clash/override")
CLASH_OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../output/clash/Meta-AntiLeak.yaml")
CLASH_AD_OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "../output/clash/ad_johnshall_clash.list")
CLASH_AD_DOMAIN_FILE = os.path.join(os.path.dirname(__file__), "../output/clash/ad_johnshall_domain.yaml")
CLASH_AD_IPCIDR_FILE = os.path.join(os.path.dirname(__file__), "../output/clash/ad_johnshall_ipcidr.list")
ACL4SSR_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../output/clash/acl4ssr")

def fetch_text(urls, label):
    """按顺序尝试多个源, 每个源重试 FETCH_RETRIES 次, 全部失败则抛错。

    不返回任何兜底内容: 调用方必须让构建失败, 而不是用旧数据/假数据出包。
    """
    last_error = None
    for url in urls:
        for attempt in range(1, FETCH_RETRIES + 1):
            try:
                print(f"正在拉取 {label}: {url} (第 {attempt} 次) ...")
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
                    if resp.status == 200:
                        content = resp.read().decode("utf-8")
                        print(f"成功获取 {label}, 大小: {len(content)} 字节, 来源: {url}")
                        return content, url
                    last_error = RuntimeError(f"HTTP {resp.status}")
            except Exception as e:
                last_error = e
                print(f"拉取失败 ({url}, 第 {attempt} 次): {e}")
    raise RuntimeError(f"拉取 {label} 全部失败, 最后一个错误: {last_error}")


def fetch_upstream_ad_rules():
    content, _url = fetch_text(UPSTREAM_AD_URLS, "Johnshall 去广告规则")
    return content


def fetch_acl4ssr_list(name):
    urls = [
        f"https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/{name}.list",
        f"https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/{name}.list",
    ]
    content, _url = fetch_text(urls, f"ACL4SSR {name}")
    # 至少要有若干条有效规则行, 否则视为上游返回了错误页
    rule_lines = [l for l in content.splitlines()
                  if l.strip() and not l.strip().startswith("#")]
    if len(rule_lines) < 5:
        raise RuntimeError(f"ACL4SSR {name} 内容异常: 有效行只有 {len(rule_lines)} 条")
    return content


def atomic_write(path, content):
    """原子写: 先写同目录临时文件再 os.replace, 避免构建中断留下半个文件。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp.{os.getpid()}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_path, path)


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
    if not AD_RULES_MIN <= len(ad_rules) <= AD_RULES_MAX:
        raise RuntimeError(
            f"Johnshall 规则数 {len(ad_rules)} 超出上下限 "
            f"[{AD_RULES_MIN}, {AD_RULES_MAX}], 疑似上游异常, 构建失败")
    return ad_rules

def build_combined_config(ad_rules):
    """结合防 DNS 泄露模板构建完整规则文件。

    [General] 段直接取自 rules/Mini-AntiLeak.conf 模板 (含 IP 字面量
    DoH 的 dns-server), 不再像旧版那样在脚本里硬编码一份
    dns-server = system 的 [General]。Johnshall 规则插在 [Rule] 段最前,
    其后是模板原有的分流规则, 再接模板的 [Host] / [URL Rewrite] 段。
    """
    beijing_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    rule_idx = template.index("[Rule]")
    host_idx = template.index("[Host]")
    general_section = template[:rule_idx]
    rule_body_template = template[rule_idx + len("[Rule]"):host_idx]
    tail_section = template[host_idx:]

    header = f"""# =================================================================
# Shadowrocket AntiLeak + ADBlock 整合规则 (防 DNS 泄露 + 强效广告过滤)
#
# 构建时间: {beijing_time} (UTC+8)
# 去广告来源: Johnshall/Shadowrocket-ADBlock-Rules-Forever
# 防 DNS 泄露模型: xiaolin-007 / ACL4SSR 架构
#
# 【防 DNS 泄露关键机制】
# 1. ipv6 = false & prefer-ipv6 = false: 彻底封堵运营商 IPv6 DNS 劫持与泄漏
# 2. dns-server = 国内加密 DoH (IP 字面量, 阿里 + 腾讯), 不再用 system 明文 DNS;
#    dns-direct-system = false: 禁用直连请求直接泄露至系统本地 DNS
# 3. dns-direct-fallback-proxy = true: 直连解析异常自动降级至代理安全查询
# 4. 所有 IP-CIDR 与 GEOIP 规则强制添加 no-resolve: 严防域名预解析
# 5. FINAL,PROXY: 未命中白名单的境外请求全部远端代理代理解析, 杜绝本地查询
# 注意: Shadowrocket 只有一个 dns-server, 国外域名也会先经这组国内 DoH
# 解析, 不如 Clash 版 (国内 DoH 直连 / 国外 DoH 经代理) 分得干净,
# 但查询本身是加密 DoH、连接仍走代理, 详见 rules/Mini-AntiLeak.conf 注释。
# =================================================================

"""

    rules_body = "\n".join(ad_rules)

    return (header + general_section + "[Rule]\n"
            "# -------------------------------------------------------------\n"
            "# 1. 强力去广告与隐私追踪拦截规则集 (来自 Johnshall 规则库)\n"
            "# -------------------------------------------------------------\n"
            + rules_body + "\n"
            + rule_body_template + tail_section)


# Clash classical 规则集支持的规则类型 (与 Shadowrocket 的交集)
CLASH_SUPPORTED_TYPES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
    "IP-CIDR", "IP-CIDR6", "GEOIP",
}

def convert_ad_rules_to_clash(ad_rules):
    """把 Shadowrocket 格式的去广告规则转换为 Clash classical 规则集格式。

    仅作过渡期兼容 (旧配置仍引用 JohnshallAD 时可用), 模板与覆写
    已改用下面 split_ad_rules_to_clash 的 domain + ipcidr 拆分版。
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
    return clash_rules, skipped

def split_ad_rules_to_clash(ad_rules):
    """把 Johnshall 规则拆成 domain + ipcidr 两类, 供 Mihomo 高效匹配。

    - domain (yaml payload): DOMAIN-SUFFIX -> `+.域名`, DOMAIN -> `域名`
      (2026-11-24 实测: Mihomo v1.19.33 加载 behavior:domain + format:yaml
      无警告; format:text + behavior:domain 同样能加载, 这里按任务要求用 yaml)
    - ipcidr (纯 CIDR 文本): IP-CIDR / IP-CIDR6 -> 只有 CIDR 本身, 不带
      `IP-CIDR,` 前缀、不带 no-resolve 后缀 (实测: 带前缀会被报
      `invalid Ipcidr`, 纯 CIDR 加载无警告)
    - DOMAIN-KEYWORD / GEOIP 无法放进这两类, 只留在 classical 过渡版里,
      并计数返回, 自检时用 domain + ipcidr + skipped == classical 核对。
    """
    domain_entries = []
    ipcidr_entries = []
    seen_domain = set()
    seen_ip = set()
    skipped = 0
    for line in ad_rules:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            skipped += 1
            continue
        rule_type = parts[0].upper()
        value = parts[1]
        if rule_type == "DOMAIN-SUFFIX" and value:
            entry = f"+.{value}"
            if entry not in seen_domain:
                seen_domain.add(entry)
                domain_entries.append(entry)
        elif rule_type == "DOMAIN" and value:
            if value not in seen_domain:
                seen_domain.add(value)
                domain_entries.append(value)
        elif rule_type in ("IP-CIDR", "IP-CIDR6") and value:
            if value not in seen_ip:
                seen_ip.add(value)
                ipcidr_entries.append(value)
        else:
            skipped += 1
    print(f"Clash 拆分完成: domain {len(domain_entries)} 条, "
          f"ipcidr {len(ipcidr_entries)} 条, 未拆分 {skipped} 条")
    return domain_entries, ipcidr_entries, skipped


def build_clash_outputs(ad_rules):
    """生成 Android/跨平台 Clash Meta (Mihomo) 输出:
    1. 复制 clash/Meta-AntiLeak.yaml 模板到 output/clash/
    2. 把 Johnshall 去广告规则拆成 domain (yaml) + ipcidr (纯 CIDR),
       另保留一份 classical 过渡版 (已废弃, 模板不再引用)
    3. 把 ACL4SSR 10 个列表自托管到 output/clash/acl4ssr/
    """
    os.makedirs(os.path.dirname(CLASH_OUTPUT_FILE), exist_ok=True)

    if os.path.exists(CLASH_TEMPLATE_PATH):
        with open(CLASH_TEMPLATE_PATH, "r", encoding="utf-8") as f_in:
            atomic_write(CLASH_OUTPUT_FILE, f_in.read())
        print(f"已同步生成 Clash Meta 配置: {CLASH_OUTPUT_FILE}")
    else:
        raise RuntimeError(f"未找到 Clash 模板 {CLASH_TEMPLATE_PATH}, 构建失败")

    # 同步覆写文件 (模式 B: FlClash JS 脚本 / Clash Verge Merge) 到 output
    if os.path.isdir(CLASH_OVERRIDE_DIR):
        os.makedirs(CLASH_OVERRIDE_OUTPUT_DIR, exist_ok=True)
        for name in sorted(os.listdir(CLASH_OVERRIDE_DIR)):
            src = os.path.join(CLASH_OVERRIDE_DIR, name)
            if os.path.isfile(src):
                with open(src, "r", encoding="utf-8") as f_in:
                    atomic_write(os.path.join(CLASH_OVERRIDE_OUTPUT_DIR, name), f_in.read())
                print(f"已同步覆写文件: {name}")

    beijing_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    clash_rules, _skipped_classical = convert_ad_rules_to_clash(ad_rules)
    domain_entries, ipcidr_entries, skipped_split = split_ad_rules_to_clash(ad_rules)

    # 拆分核对: domain + ipcidr + 未拆分 == classical 总数
    if len(domain_entries) + len(ipcidr_entries) + skipped_split != len(clash_rules):
        raise RuntimeError(
            f"拆分核对失败: domain {len(domain_entries)} + ipcidr "
            f"{len(ipcidr_entries)} + 未拆分 {skipped_split} != "
            f"classical {len(clash_rules)}")

    header_classical = f"""# Johnshall 去广告规则 (Clash classical 格式, 由 scripts/build.py 自动转换)
# 来源: Johnshall/Shadowrocket-ADBlock-Rules-Forever (sr_ad_only.conf)
# 构建时间: {beijing_time} (UTC+8), 共 {len(clash_rules)} 条
# 注意: 本文件已废弃 (DEPRECATED), 仅作过渡期兼容, 模板与覆写已改用
# ad_johnshall_domain.yaml (behavior:domain) + ad_johnshall_ipcidr.list
# (behavior:ipcidr)。新配置请勿再引用 JohnshallAD。
# 用法 (旧): RULE-SET,JohnshallAD,REJECT (策略由引用处指定, 本文件不带策略)
"""
    atomic_write(CLASH_AD_OUTPUT_FILE, header_classical + "\n".join(clash_rules) + "\n")
    print(f"已生成 Clash 广告规则集 (过渡版): {CLASH_AD_OUTPUT_FILE} (共 {len(clash_rules)} 条)")

    header_domain = f"""# Johnshall 去广告规则 (Clash domain 格式, 由 scripts/build.py 自动拆分)
# 来源: Johnshall/Shadowrocket-ADBlock-Rules-Forever (sr_ad_only.conf)
# 构建时间: {beijing_time} (UTC+8), 共 {len(domain_entries)} 条
# 用法: rule-provider behavior:domain, format:yaml; RULE-SET,JohnshallDomain,REJECT
payload:
"""
    atomic_write(CLASH_AD_DOMAIN_FILE,
                 header_domain + "\n".join(f"  - '{e}'" for e in domain_entries) + "\n")
    print(f"已生成 Clash 广告规则集 (domain): {CLASH_AD_DOMAIN_FILE} (共 {len(domain_entries)} 条)")

    header_ipcidr = f"""# Johnshall 去广告规则 (Clash ipcidr 格式, 由 scripts/build.py 自动拆分)
# 来源: Johnshall/Shadowrocket-ADBlock-Rules-Forever (sr_ad_only.conf)
# 构建时间: {beijing_time} (UTC+8), 共 {len(ipcidr_entries)} 条
# 注意: 本文件是纯 CIDR 文本, 不带 IP-CIDR, 前缀与 no-resolve 后缀
# (behavior:ipcidr + format:text 要求纯 CIDR, 带前缀会被 Mihomo 报 invalid Ipcidr)
# 用法: rule-provider behavior:ipcidr, format:text; RULE-SET,JohnshallIP,REJECT
"""
    atomic_write(CLASH_AD_IPCIDR_FILE,
                 header_ipcidr + "\n".join(ipcidr_entries) + "\n")
    print(f"已生成 Clash 广告规则集 (ipcidr): {CLASH_AD_IPCIDR_FILE} (共 {len(ipcidr_entries)} 条)")

    # ACL4SSR 自托管: 原文照搬 (只在文件头加一行来源注释), 失败即整 build 失败
    os.makedirs(ACL4SSR_OUTPUT_DIR, exist_ok=True)
    for name in ACL4SSR_NAMES:
        content = fetch_acl4ssr_list(name)
        out_path = os.path.join(ACL4SSR_OUTPUT_DIR, f"{name}.list")
        header = (f"# ACL4SSR {name} (由 scripts/build.py 自托管, 来源 "
                  f"ACL4SSR/ACL4SSR master/Clash/{name}.list, 构建时间 {beijing_time} UTC+8)\n")
        atomic_write(out_path, header + content)
        print(f"已自托管 ACL4SSR 列表: {out_path}")


def self_check():
    """生成后自检: 只读已有 output/, 不联网。返回错误列表 (空表示通过)。"""
    errors = []

    def read(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # --- Shadowrocket 生成物 ---
    for path in (OUTPUT_FILE, OUTPUT_MINI_FILE):
        if not os.path.exists(path):
            errors.append(f"缺失文件: {path}")
            continue
        text = read(path)
        if "dns-server = system" in text:
            errors.append(f"{path}: 仍含明文 dns-server = system")
        if "dns-server = https://" not in text:
            errors.append(f"{path}: 未找到加密 DoH 的 dns-server")
        final_lines = [l for l in text.splitlines() if l.strip() == "FINAL,PROXY"]
        if len(final_lines) != 1:
            errors.append(f"{path}: FINAL,PROXY 规则行应恰好 1 行, 实际 {len(final_lines)} 行 (注释里的提及不算)")
        for line in text.splitlines():
            sline = line.strip()
            if sline.startswith(("IP-CIDR,", "IP-CIDR6,", "GEOIP,")) and "no-resolve" not in sline.lower():
                errors.append(f"{path}: IP 规则缺 no-resolve: {sline[:80]}")
            if sline.startswith("RULE-SET,") and ("ChinaCompanyIp" in sline or "ChinaIp" in sline) \
                    and "no-resolve" not in sline.lower():
                errors.append(f"{path}: 国内 IP 规则集缺 no-resolve: {sline[:100]}")
        if "http://" in text:
            errors.append(f"{path}: 含明文 http:// 链接")

    # --- Clash 拆分核对 ---
    try:
        classical = [l for l in read(CLASH_AD_OUTPUT_FILE).splitlines()
                     if l and not l.startswith("#")]
        domain_text = read(CLASH_AD_DOMAIN_FILE)
        domain_entries = [l.strip()[3:-1] for l in domain_text.splitlines()
                          if l.strip().startswith("- '")]
        ipcidr_entries = [l for l in read(CLASH_AD_IPCIDR_FILE).splitlines()
                          if l and not l.startswith("#")]
        if len(domain_entries) + len(ipcidr_entries) > len(classical):
            errors.append(
                f"拆分核对失败: domain {len(domain_entries)} + ipcidr "
                f"{len(ipcidr_entries)} > classical {len(classical)}")
        if len(domain_entries) < 1000:
            errors.append(f"domain 规则过少: {len(domain_entries)} 条")
        if any(e.startswith("IP-CIDR") or "no-resolve" in e for e in ipcidr_entries):
            errors.append("ipcidr 文件含 IP-CIDR 前缀或 no-resolve 后缀 (应为纯 CIDR)")
    except FileNotFoundError as e:
        errors.append(f"缺失 Clash 拆分文件: {e}")

    # --- Clash 三文件 DNS 同步 ---
    clash_files = [
        CLASH_OUTPUT_FILE,
        os.path.join(CLASH_OVERRIDE_OUTPUT_DIR, "AntiLeak-Override.js"),
        os.path.join(CLASH_OVERRIDE_OUTPUT_DIR, "AntiLeak-Merge.yaml"),
    ]
    for path in clash_files:
        if not os.path.exists(path):
            errors.append(f"缺失文件: {path}")
            continue
        text = read(path)
        # 只检查正文行: 注释里提及旧主机名 (解释"不再用某某") 不算违规
        code_text = "\n".join(
            l for l in text.splitlines()
            if not l.strip().startswith(("#", "//")))
        text = code_text
        for needle in ("tls://223.5.5.5", "tls://119.29.29.29",
                       "https://223.5.5.5/dns-query", "https://doh.pub/dns-query",
                       "https://1.1.1.1/dns-query", "https://8.8.8.8/dns-query",
                       "tcp://any:853", "3478-3481", "19302-19309"):
            if needle not in text:
                errors.append(f"{path}: 缺少 DNS/拦截关键项: {needle}")
        for bad in ("dns.alidns.com", "cloudflare-dns.com",
                    "dns.google/dns-query",
                    "    - 223.5.5.5", "    - 119.29.29.29",
                    '"223.5.5.5"', '"119.29.29.29"'):
            if bad in text:
                errors.append(f"{path}: 仍含旧主机名/明文 DoH: {bad!r}")
        if "http://" in text:
            errors.append(f"{path}: 含明文 http:// 链接")

    # 模板版独有: fallback 组与拆分 provider
    if os.path.exists(CLASH_OUTPUT_FILE):
        text = read(CLASH_OUTPUT_FILE)
        for needle in ("AUTO-FALLBACK", "JohnshallDomain", "JohnshallIP",
                       "proxy: PROXY", "ad_johnshall_domain.yaml",
                       "output/clash/acl4ssr/BanAD.list"):
            if needle not in text:
                errors.append(f"{CLASH_OUTPUT_FILE}: 缺少关键项: {needle}")
        if "JohnshallAD:" in text:
            errors.append(f"{CLASH_OUTPUT_FILE}: 仍引用已废弃的 JohnshallAD")

    return errors


def main():
    parser = argparse.ArgumentParser(description="AntiLeak-AdBlock 规则构建脚本")
    parser.add_argument("--check", action="store_true",
                        help="只校验已有 output/, 不联网, 不写文件")
    args = parser.parse_args()

    if args.check:
        errors = self_check()
        if errors:
            print("自检失败:")
            for e in errors:
                print(f"  - {e}")
            return 1
        print("自检通过: output/ 全部检查项合格")
        return 0

    start = time.time()
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # 复制基础 Mini-AntiLeak.conf 到 output (原子写, 模板原文照搬)
    if os.path.exists(TEMPLATE_PATH):
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f_in:
            atomic_write(OUTPUT_MINI_FILE, f_in.read())
        print(f"已同步生成极简防泄露配置: {OUTPUT_MINI_FILE}")
    else:
        raise RuntimeError(f"未找到模板 {TEMPLATE_PATH}, 构建失败")

    # 拉取并合并去广告规则 (全部失败即抛错退出, 不写输出)
    raw_ad_conf = fetch_upstream_ad_rules()
    ad_rules = extract_ad_rules(raw_ad_conf)
    combined_content = build_combined_config(ad_rules)
    atomic_write(OUTPUT_FILE, combined_content)
    print(f"构建完成! 完整规则文件输出至: {OUTPUT_FILE} (共包含广告规则 {len(ad_rules)} 条)")

    # 同步生成 Android/跨平台 Clash Meta 配置、拆分规则集与 ACL4SSR 自托管
    build_clash_outputs(ad_rules)

    errors = self_check()
    if errors:
        print("生成后自检失败, 输出文件可能有问题:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("生成后自检通过")
    print(f"总耗时: {time.time() - start:.1f} 秒")
    return 0


if __name__ == "__main__":
    sys.exit(main())
