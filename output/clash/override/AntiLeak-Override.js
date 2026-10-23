// =================================================================
// AntiLeak 覆写脚本 (FlClash 脚本覆写专用)
// 作用: 保留你已导入的机场订阅配置原样, 只在其上叠加与本仓库
// 模板版相同的防 DNS 泄露体系 + 广告拦截:
//   - DNS 改为 fake-ip + respect-rules: 国外域名经代理远端解析,
//     国内域名走国内加密 DoH, 绝不走系统明文 DNS
//   - 全局关闭 IPv6; TUN strict-route + dns-hijack 接管全部查询
//   - 前置 STUN 拦截 (防 WebRTC 泄露) 与三层去广告规则
//   - 机场原有的分流规则、策略组、节点全部保留, 不做任何改动
// 新增策略组 AntiLeak (include-all 自动包含你的全部节点), 仅供
// 本覆写的加密 DNS 指定出口使用, 不影响你在机场组里的选择。
//
// 用法 (FlClash): 打开机场配置 -> 覆写 -> 脚本 -> 新建/编辑,
// 把本文件全部内容粘贴进去 -> 保存 -> 对该配置启用此覆写 ->
// 断开重连一次生效。
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
    "dns-hijack": ["any:53", "tcp://any:53"],
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
    "default-nameserver": ["223.5.5.5", "119.29.29.29"],
    "proxy-server-nameserver": [
      "https://dns.alidns.com/dns-query",
      "https://doh.pub/dns-query"
    ],
    "nameserver": [
      "https://cloudflare-dns.com/dns-query#AntiLeak",
      "https://dns.google/dns-query#AntiLeak"
    ],
    "direct-nameserver": [
      "https://dns.alidns.com/dns-query",
      "https://doh.pub/dns-query"
    ],
    "direct-nameserver-follow-policy": true,
    "nameserver-policy": {
      "geosite:cn,private": [
        "https://dns.alidns.com/dns-query",
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
  function provider(url, path) {
    // 显式指定经 AntiLeak 组拉取, 不受机场兜底规则 (如 MATCH,DIRECT) 影响
    var p = { "url": url, "path": path, "proxy": "AntiLeak" };
    for (var k in classical) p[k] = classical[k];
    return p;
  }
  config["rule-providers"] = Object.assign({}, config["rule-providers"], {
    "JohnshallAD": provider(
      "https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/clash/ad_johnshall_clash.list",
      "./ruleset/ad_johnshall_clash.list"),
    "BanAD": provider(
      "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanAD.list",
      "./ruleset/BanAD.list"),
    "BanProgramAD": provider(
      "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanProgramAD.list",
      "./ruleset/BanProgramAD.list")
  });

  // ---------- 前置规则: STUN 拦截 + 去广告 (机场规则保留在后) ----------
  var prepend = [
    "AND,((NETWORK,udp),(DST-PORT,3478)),REJECT",
    "AND,((NETWORK,udp),(DST-PORT,19302)),REJECT",
    "DOMAIN-SUFFIX,stun.l.google.com,REJECT",
    "RULE-SET,JohnshallAD,REJECT",
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
