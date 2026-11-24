// =================================================================
// AntiLeak 覆写脚本 (FlClash 脚本覆写专用)
// 作用: 保留你已导入的机场订阅配置原样, 只在其上叠加与本仓库
// 模板版相同的防 DNS 泄露体系 + 广告拦截:
//   - DNS 改为 fake-ip + respect-rules: 国外域名经代理远端解析,
//     国内域名走国内加密 DoH 直连解析, 绝不走系统明文 DNS。
//     国内直连路径没有因为防泄露而变慢: 国内域名仍走国内 DoH
//     直连, 不经过代理、不走国外 DoH), 只有国外域名才走代理 DoH /
//     远端解析。国外与阿里 DoH 用 IP 字面量, 腾讯 DoH 用 doh.pub
//     主机名 (119.29.29.29 裸 IP 不提供 DoH, 实测服务端断开);
//     该主机名只由加密 DoT 解析, 不需要先用明文 DNS 解析 DoH 主机名。
//   - 全局关闭 IPv6; TUN strict-route + dns-hijack 接管全部查询
//     (53 明文 DNS + 853 DoT); UDP 443/8443 (QUIC) 拦截强制走
//     TCP/TLS; STUN/TURN 端口段拦截 (防 WebRTC 泄露)
//   - 前置 STUN 拦截与三层去广告规则; Johnshall 拆成 domain +
//     ipcidr 两类 (与模板版同源), ACL4SSR 两列表改走本仓自托管
//   - 机场原有的分流规则、策略组、节点全部保留, 不做任何改动
// 新增策略组 AntiLeak (include-all 自动包含你的全部节点), 仅供
// 本覆写的加密 DNS 指定出口使用, 不影响你在机场组里的选择。
// 注意: 本覆写不新增 fallback 策略组。机场配置自带的分流与
// 策略组 (含其自身的 url-test / fallback) 全部保留, 再叠加
// 一个 fallback 组会与机场组打架; 自动容灾只在模板版
// (Meta-AntiLeak.yaml 的 AUTO-FALLBACK 组) 里做。
//
// 用法 (FlClash): 打开机场配置 -> 覆写 -> 脚本 -> 新建/编辑,
// 把本文件全部内容粘贴进去 -> 保存 -> 对该配置启用此覆写 ->
// 断开重连一次生效。
// 校验: Mihomo v1.19.33, 模拟机场配置 + 本脚本合并后 mihomo -t 通过;
// domain yaml / ipcidr 纯 CIDR 文本两种 provider 格式均经该版本
// 实测加载无警告。
// =================================================================

function main(config) {
  config = config || {};

  // ---------- 基础 ----------
  config["ipv6"] = false;
  config["profile"] = Object.assign({}, config["profile"], {
    "store-selected": true,
    "store-fake-ip": true
  });
  config["hosts"] = Object.assign({}, config["hosts"], {
    "localhost": "127.0.0.1"
  });

  // ---------- 域名嗅探: 还原被应用自带 DNS 绕开的域名 ----------
  config["sniffer"] = {
    "enable": true,
    "force-dns-mapping": true,
    "parse-pure-ip": true,
    "override-destination": true,
    "sniff": {
      "HTTP": { "ports": [80, "8080-8880"], "override-destination": true },
      "TLS": { "ports": [443, 8443] },
      "QUIC": { "ports": [443, 8443] }
    }
  };

  // ---------- TUN 接管 ----------
  config["tun"] = Object.assign({}, config["tun"], {
    "enable": true,
    "stack": "mixed",
    // 53 明文 DNS + 853 DoT 一并劫持
    "dns-hijack": ["any:53", "tcp://any:53", "tcp://any:853"],
    "auto-route": true,
    "auto-detect-interface": true,
    "strict-route": true,
    "route-exclude-address": [
      "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16",
      "172.16.0.0/12", "192.0.0.0/24", "192.0.2.0/24", "192.168.0.0/16",
      "198.51.100.0/24", "203.0.113.0/24", "224.0.0.0/4", "255.255.255.255/32"
    ]
  });

  // ---------- DNS 防泄露 (核心) ----------
  // 国内 / 国外分流不变: 国内域名走国内 DoH 直连 (无 #AntiLeak),
  // 国外域名走国外 DoH 经 AntiLeak 组发出。DoH 端点:
  // 223.5.5.5 = 阿里 AliDNS (IP 字面量, 实测可用),
  // doh.pub = 腾讯 DoH (主机名, 裸 IP 不提供 DoH),
  // 1.1.1.1 = Cloudflare, 8.8.8.8 = Google (均为 IP 字面量)。
  config["dns"] = {
    "enable": true,
    "listen": "0.0.0.0:1053",
    "ipv6": false,
    "respect-rules": true,
    "enhanced-mode": "fake-ip",
    "fake-ip-range": "198.18.0.1/16",
    "fake-ip-filter": [
      "*.lan", "*.local", "localhost",
      "time.*.com", "time.*.gov", "time.*.edu.cn", "time.*.apple.com",
      "time-ios.apple.com",
      "time1.*.com", "time2.*.com", "time3.*.com", "time4.*.com",
      "time5.*.com", "time6.*.com", "time7.*.com",
      "ntp.*.com", "ntp1.*.com", "ntp2.*.com", "ntp3.*.com",
      "ntp4.*.com", "ntp5.*.com", "ntp6.*.com", "ntp7.*.com",
      "*.ntp.org.cn", "+.pool.ntp.org", "+.stun.*.*", "+.stun.*.*.*",
      "connectivitycheck.gstatic.com", "www.msftconnecttest.com",
      "www.msftncsi.com", "dns.msftncsi.com"
    ],
    // bootstrap 专用, 只做 DoT 加密解析, 不处理普通查询
    "default-nameserver": ["tls://223.5.5.5", "tls://119.29.29.29"],
    "proxy-server-nameserver": [
      "https://223.5.5.5/dns-query",
      "https://doh.pub/dns-query"
    ],
    "nameserver": [
      "https://1.1.1.1/dns-query#AntiLeak",
      "https://8.8.8.8/dns-query#AntiLeak"
    ],
    "direct-nameserver": [
      "https://223.5.5.5/dns-query",
      "https://doh.pub/dns-query"
    ],
    "direct-nameserver-follow-policy": true,
    "nameserver-policy": {
      "geosite:cn,private": [
        "https://223.5.5.5/dns-query",
        "https://doh.pub/dns-query"
      ]
    }
  };

  // ---------- DNS 出口策略组: 自动包含机场全部节点 ----------
  var groups = Array.isArray(config["proxy-groups"]) ? config["proxy-groups"] : [];
  if (!groups.some(function (g) { return g && g.name === "AntiLeak"; })) {
    groups.unshift({ "name": "AntiLeak", "type": "select", "include-all": true });
  }
  config["proxy-groups"] = groups;

  // ---------- 广告规则集 (与模板版同源) ----------
  var classical = { "type": "http", "interval": 86400, "behavior": "classical", "format": "text" };
  var domain = { "type": "http", "interval": 86400, "behavior": "domain", "format": "yaml" };
  var ipcidr = { "type": "http", "interval": 86400, "behavior": "ipcidr", "format": "text" };
  function provider(url, path, kind) {
    // 显式指定经 AntiLeak 组拉取, 不受机场兜底规则 (如 MATCH,DIRECT) 影响
    var p = { "url": url, "path": path, "proxy": "AntiLeak" };
    var base = kind === "domain" ? domain : (kind === "ipcidr" ? ipcidr : classical);
    for (var k in base) p[k] = base[k];
    return p;
  }
  config["rule-providers"] = Object.assign({}, config["rule-providers"], {
    // Johnshall 拆分版: domain (yaml payload, 52,527 条) + ipcidr (纯 CIDR, 128 条)
    "JohnshallDomain": provider(
      "https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/clash/ad_johnshall_domain.yaml",
      "./ruleset/ad_johnshall_domain.yaml", "domain"),
    "JohnshallIP": provider(
      "https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/clash/ad_johnshall_ipcidr.list",
      "./ruleset/ad_johnshall_ipcidr.list", "ipcidr"),
    // ACL4SSR 两列表改走本仓自托管 (build.py 生成)
    "BanAD": provider(
      "https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/clash/acl4ssr/BanAD.list",
      "./ruleset/BanAD.list"),
    "BanProgramAD": provider(
      "https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/clash/acl4ssr/BanProgramAD.list",
      "./ruleset/BanProgramAD.list")
  });

  // ---------- 前置规则: QUIC + STUN 拦截 + 去广告 (机场规则保留在后) ----------
  // QUIC 在最前: UDP 443/8443 一律 REJECT 强制 TCP/TLS, 原因见模板版
  // rules 第 0 节 (UDP 限流环境下更稳, SNI 可嗅探; 代价是 HTTP/3 不可用)。
  // 广告在国内 DIRECT 之前: 既在广告名单又在国内名单的域名必须是 REJECT。
  // IP 规则只有 128 条, 放域名规则前面。
  var prepend = [
    "AND,((NETWORK,udp),(DST-PORT,443)),REJECT",
    "AND,((NETWORK,udp),(DST-PORT,8443)),REJECT",
    "AND,((NETWORK,udp),(DST-PORT,3478-3481)),REJECT",
    "AND,((NETWORK,udp),(DST-PORT,5349)),REJECT",
    "AND,((NETWORK,udp),(DST-PORT,5350)),REJECT",
    "AND,((NETWORK,udp),(DST-PORT,19302-19309)),REJECT",
    "DOMAIN-SUFFIX,stun.l.google.com,REJECT",
    "RULE-SET,JohnshallIP,REJECT",
    "RULE-SET,JohnshallDomain,REJECT",
    "RULE-SET,BanAD,REJECT",
    "RULE-SET,BanProgramAD,REJECT",
    "GEOSITE,category-ads-all,REJECT"
  ];
  var oldRules = Array.isArray(config["rules"]) ? config["rules"] : [];
  config["rules"] = prepend.concat(oldRules.filter(function (r) {
    return prepend.indexOf(r) === -1;
  }));

  return config;
}
