# AntiLeak-AdBlock 🛡️

> **Shadowrocket (iOS) × Clash Meta (Android / 跨平台)** —— 防 DNS 泄露 + 广告拦截双平台整合规则

提供针对 iOS **Shadowrocket (小火箭)** 与 Android **Clash Meta (Mihomo)** 的**防 DNS 泄露**与**全能广告拦截**整合规则配置，两端同源同防护模型，支持 GitHub Actions 每日北京时间 09:15 自动定时构建更新。

---

## 🌟 项目特性

- **彻底封堵 DNS 泄露**：
  - 基于 [xiaolin-007](https://github.com/xiaolin-007) 的 `Mini-AntiLeak.conf` 与业界成熟防泄露方案。
  - **强制 `no-resolve`**：所有国内 `IP-CIDR` 与 `GEOIP,CN` 规则均附加 `no-resolve` 属性，彻底防止分流规则在匹配 IP 时向本地运营商 DNS 发起域名预解析。
  - **境外域名远端代理解析**：未命中直连白名单的请求通过 `FINAL,PROXY` 直接将原始域名封装进代理隧道，在境外节点端完成远端 DNS 查询，本地零记录。
  - **切断 IPv6 泄露通道**：默认关闭 IPv6 解析 (`ipv6 = false`)，严防双栈环境下运营商 IPv6 DNS 劫持。
  - **安全 DNS 回退机制**：设置 `dns-direct-system = false` 与 `dns-direct-fallback-proxy = true`，避免直连请求走系统默认明文 DNS。
  - **加密 DNS，不走明文**：Clash 版国内 DoH 直连、国外 DoH 经代理发出，全部用 IP 字面量 DoH（阿里 `223.5.5.5`、Cloudflare `1.1.1.1`、Google `8.8.8.8`；腾讯 DoH 用 `doh.pub` 主机名，因其裸 IP 不提供 DoH，该主机名只由加密 DoT 解析）；`default-nameserver` 用 DoT（`tls://223.5.5.5` / `tls://119.29.29.29`）作 bootstrap，不再用明文 IP。TUN 劫持 `53` + `853`（DoT），UDP `443/8443`（QUIC）拦截强制走 TCP/TLS，STUN/TURN 端口段拦截。Shadowrocket 版 `dns-server` 改为国内加密 DoH，不再用 `system`（见下文 DNS 一节的折中说明）。
- **强效广告与追踪过滤**：
  - 上游自动同步 [Johnshall/Shadowrocket-ADBlock-Rules-Forever](https://github.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever) 的 `仅去广告规则 (sr_ad_only.conf)`。
  - 覆盖 iOS 常见 App 开屏广告、SDK 追踪（穿山甲、优量汇、友盟等）以及视频/网页广告。
- **Android / 跨平台 Clash Meta 版**：
  - 与 iOS 版一一对应的 Mihomo 配置 `Meta-AntiLeak.yaml`：`fake-ip` + `respect-rules` 实现境外域名远端解析、国内域名加密 DoH 直连解析；`strict-route` + `dns-hijack` 接管全部 DNS；STUN 规则拦截封堵 WebRTC 泄露；国内 IP 规则同样强制 `no-resolve`。
  - 广告规则同源：Johnshall 规则每日由构建脚本自动拆成 domain（52,758 条，yaml）+ ipcidr（128 条，纯 CIDR）两类，比原来 52,886 条 classical 文本匹配更快；ACL4SSR 10 个列表由构建脚本自托管到本仓 `output/clash/acl4ssr/`，客户端不再直连原仓拉取，全部规则集均经代理拉取。主策略组默认先走 `AUTO`（自动选延迟最低），全挂时走 `AUTO-FALLBACK`，再走 `DIRECT`，节点挂了不用手动切。适用于 FlClash、Clash Meta for Android，桌面端 Clash Verge / Mihomo Party 亦可使用。

- **自动化免维护**：
  - 内置 GitHub Actions 工作流，每天自动拉取上游最新规则并合并构建发布。

---

## 📥 规则订阅地址

> 直接复制下面的 Raw 订阅地址导入即可。本仓库已去掉第三方二维码服务（原先的二维码由 `api.qrserver.com` 生成，订阅地址会经过第三方服务器），如需扫码请在 Shadowrocket 里用「扫描」功能直接扫订阅链接，或复制链接手动导入。

| 规则类型 | 说明 | 订阅地址 (Raw) |
| :--- | :--- | :---: |
| **整合强效版<br>(推荐)** | 防 DNS 泄露 + Johnshall 每日同步去广告 | `https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/sr_ad_antileak.conf` |
| **极简防泄露版** | 纯粹防 DNS 泄露与基础分流，不含庞大广告规则 | `https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/Mini-AntiLeak.conf` |

### 镜像订阅（国内 Raw 地址报 TLS 错误时用）

> `raw.githubusercontent.com` 在国内直连时有时 TLS 握手会被干扰，Shadowrocket 导入会报 TLS 错误。下面是同一份文件的 jsDelivr 镜像，内容与 Raw 一致，复制链接导入即可；镜像的日常更新可能比 Raw 慢一点。

| 规则类型 | 镜像订阅地址 (jsDelivr) |
| :--- | :--- |
| **整合强效版<br>(推荐)** | `https://cdn.jsdelivr.net/gh/shankangk/AntiLeak-AdBlock@main/output/sr_ad_antileak.conf` |
| **极简防泄露版** | `https://cdn.jsdelivr.net/gh/shankangk/AntiLeak-AdBlock@main/output/Mini-AntiLeak.conf` |

### 一键导入 Shadowrocket（iOS）

> 在 iPhone / iPad 上点下面的链接，会先打开跳转页，点「点击一键安装」并在弹出窗口点「允许」后唤醒 Shadowrocket 导入对应配置。GitHub 会过滤 `shadowrocket://` 这类自定义协议链接，所以这里经跳转页中转；镜像版国内更稳，Raw 版与上方二维码是同一地址。

- **整合强效版**：[一键导入（镜像）](https://shankangk.github.io/AntiLeak-AdBlock/redirect.html?url=https://cdn.jsdelivr.net/gh/shankangk/AntiLeak-AdBlock@main/output/sr_ad_antileak.conf) · [一键导入（Raw）](https://shankangk.github.io/AntiLeak-AdBlock/redirect.html?url=https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/sr_ad_antileak.conf)
- **极简防泄露版**：[一键导入（镜像）](https://shankangk.github.io/AntiLeak-AdBlock/redirect.html?url=https://cdn.jsdelivr.net/gh/shankangk/AntiLeak-AdBlock@main/output/Mini-AntiLeak.conf) · [一键导入（Raw）](https://shankangk.github.io/AntiLeak-AdBlock/redirect.html?url=https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/Mini-AntiLeak.conf)

> 一键导入走本仓库自托管的跳转页（`docs/redirect.html`），不再经过第三方 `lowertop.github.io`。跳转页只显示目标地址、点按钮才唤醒 Shadowrocket，不自动跳转、不收集信息、不加载第三方脚本。**需要先在仓库 Settings → Pages → Deploy from branch（选 main 分支、`/docs` 目录）开启 GitHub Pages，否则上面的一键导入链接打不开**；不开 Pages 也不影响复制链接手动导入。

---

## 🔒 DNS 是怎么分的（国内直连不绕代理）

防 DNS 泄露不等于把所有 DNS 都绕到代理上——那样国内网站会变慢。本仓库的分流是：

| 域名 | 解析方式 | 走不走代理 |
| :--- | :--- | :---: |
| 国内域名（`geosite:cn`、`ChinaDomain`、`Apple` 等规则命中的域名） | 国内加密 DoH 直连：阿里 `https://223.5.5.5/dns-query`（IP 字面量）+ 腾讯 `https://doh.pub/dns-query` | 不走代理，直连 |
| 国外域名 | 国外加密 DoH 经代理发出：Cloudflare `https://1.1.1.1/dns-query#PROXY` + Google `https://8.8.8.8/dns-query#PROXY`，或由节点远端解析（fake-ip） | 走代理 |
| DoH 主机名本身（仅 `doh.pub` 一个） | 由 `default-nameserver` 的加密 DoT（`tls://223.5.5.5` / `tls://119.29.29.29`）解析，只作 bootstrap | 不走明文 DNS |

- 为什么腾讯 DoH 用主机名而不用 IP 字面量：`119.29.29.29` 裸 IP 不提供 DoH（2026-11-24 实测：服务端直接断开连接，3 次均超时），而 `doh.pub` 主机名 DoH 实测可用；阿里、Cloudflare、Google 的 IP 字面量 DoH 均实测可用。
- 国内直连没有变慢（直接 DoH 端点实测，`www.baidu.com`，各 3 次取中位；绝对毫秒含测试环境的出口代理开销，只看相对值）：阿里 IP 字面量 1001ms vs 阿里主机名（旧方案）1564ms；腾讯 `doh.pub` 518ms；Cloudflare IP 字面量 324ms vs 主机名 379ms；Google IP 字面量 468ms vs 主机名 567ms。IP 字面量与旧主机名方案相当或更快，因为少了一次 bootstrap 主机名查询。
- Shadowrocket 的折中（Clash 版没有这个问题）：Shadowrocket 只有一个 `dns-server`，国外域名也会先经这组国内 DoH 解析，不如 Clash 版分得干净；但查询本身是加密 DoH、连接仍走代理、直连绝不走系统明文 DNS，且 `dns-direct-fallback-proxy = true` 会在直连解析失败时降级到代理。

---

## 📲 在 Shadowrocket 中使用

### 方法一：一键导入（最便捷）
1. 在 iPhone / iPad 上点上方「一键导入」链接，在跳转页点「点击一键安装」，弹出窗口点「允许」。
2. Shadowrocket 被唤醒后完成导入，在配置列表里选中该配置并选择 **使用配置**。

### 方法二：复制 URL 手动导入
1. 复制上方表格中的 **Raw 订阅地址**。
2. 打开 **Shadowrocket**，进入底部的 **配置** (Config) 页面。
3. 点击右上角的 **➕** 号，将链接粘贴至 **URL** 处，点击 **下载**。
4. 轻点已下载的配置文件，选择 **使用配置**。

### 关键设置：封堵 WebRTC 泄露
- 进入 Shadowrocket **设置** -> **UDP** -> 开启 **禁用 STUN** (Disable STUN 开关)。
- 断开并重新连接 Shadowrocket 开关以使新规则全面生效。

---

## 🤖 在 Android 上使用 (Clash Meta / Mihomo)

| 规则类型 | 说明 | 配置地址 (Raw) |
| :--- | :--- | :--- | :---: |
| **Clash Meta 完整版 (推荐)** | 防 DNS 泄露 + 去广告完整 Mihomo 配置，与 iOS 版同源 | `https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/clash/Meta-AntiLeak.yaml` |

> 本仓库不提供任何节点。配置里有**一处必改**：`proxy-providers` 中 `MySubscribe` 的 `url`，换成你自己的订阅链接即可（机场订阅链接可直接填，只取其中节点部分）；也可以删掉 `proxy-providers`，把节点手写进 `proxies:`。

### 导入步骤 (FlClash 为例)

1. 打开上方 Raw 地址，复制全文，把 `MySubscribe` 的 `url` 改成你的订阅链接，保存为 `.yaml` 文件。
2. FlClash → **配置** → 右上角 **➕** → **从文件导入**，选择该文件并启用。
3. Clash Meta for Android 同理：**Profiles** → **New profile** → **File** 导入；在桌面端 Clash Verge / Mihomo Party 中作为本地配置导入亦可。

### ❓ Clash 的用法和 Shadowrocket 不一样

Shadowrocket 是「节点订阅 + 规则配置」两层分开添加的；**Clash / Mihomo 没有独立的规则配置层**，一份 YAML 同时管节点、DNS 与规则，所以不能像小火箭那样在已有订阅上再叠一个规则文件。Clash 版对应有两种用法：

- **模式 A（模板模式，推荐，即上表这份配置）**：把 `Meta-AntiLeak.yaml` 导入为**唯一配置**，你的机场订阅链接只填到 `proxy-providers` 一处。之后节点由模板按 `interval` 每日自动拉取更新，效果等同于直接订阅机场，**不需要再单独导入机场配置**，两边也不会打架。
- **模式 B（覆写模式）**：保留你已导入的机场配置，在支持「覆写 / Override」的客户端上叠加一层，只改 DNS / TUN 并前置防泄露与去广告规则，机场原有分流与策略组全部保留。本仓库提供两个覆写文件（见下节）：JS 脚本版（FlClash、Clash Verge Rev 的 Script 模式通用，全量规则）与 Merge 版（Clash Verge Rev 专用，去广告仅内置 GEOSITE 分类）。Clash Meta for Android 不支持完整覆写，请用模式 A。

### 模式 B：覆写文件与用法

| 文件 | 适用客户端 | 地址 (Raw) |
| :--- | :--- | :--- |
| **AntiLeak-Override.js**（推荐） | FlClash（脚本覆写）、Clash Verge Rev（Script 覆写） | `https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/clash/override/AntiLeak-Override.js` |
| **AntiLeak-Merge.yaml** | Clash Verge Rev（Merge 覆写） | `https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/clash/override/AntiLeak-Merge.yaml` |

- **FlClash**：打开机场配置 → **覆写** → **脚本** → 把 JS 文件全文粘贴进去 → 保存并启用该覆写 → 断开重连一次。
- **Clash Verge Rev**：新建覆写并绑定到机场订阅：选 **Script** 类型时用上面的 JS 文件（与 FlClash 同一份，全量 Johnshall 去广告规则）；选 **Merge** 类型时用 Merge 版 YAML。注意 Merge 机制对 `rule-providers` 是整段替换、无法安全叠加远程规则集，所以 Merge 版的去广告只有内核内置的 `GEOSITE category-ads-all`，其余防泄露部分（fake-ip DNS、TUN、STUN/QUIC 拦截、853 劫持）与 JS 版一致。
- 两种覆写都会新增一个 **AntiLeak** 策略组（`include-all` 自动包含你的全部节点），仅作为加密 DNS 的指定出口，不影响你在机场策略组里的任何选择；随时关掉覆写即可完整还原机场配置。

### Android 关键设置

1. **关闭系统「私人 DNS」**：设置 → 网络和互联网 → 私人 DNS，选「关闭」或「自动」，不要指定第三方 DoT 服务器，否则 DNS 会绕过本配置的接管。
2. **关闭浏览器自带安全 DNS**：Chrome → 设置 → 隐私和安全 → 使用安全 DNS，选「使用当前服务提供商」或关闭，避免浏览器 DoH 绕行。
3. **确认 TUN/VPN 模式已开启**（FlClash 默认开启）。WebRTC 的 STUN 探测已由配置内规则拦截，无需像 iOS 版那样再找开关。
4. 断开重连一次使配置全面生效，泄露检测方法见下一节（用 Chrome 访问即可）。

---

## 🌐 网络不通畅怎么办（UDP 限流）

如果你所在的网络对 UDP 有限流（表现为 HY2 / QUIC 经常超时、节点时通时断，但 TCP 线路正常），本配置已经做了三件事：

1. **QUIC 拦截**：Clash 版拦截 UDP `443/8443`，强制走 TCP/TLS。QUIC 走 UDP 会绕过 TLS SNI 嗅探与代理分流，在 UDP 限流的网络下常超时；强制 TCP 后 SNI 可被嗅探还原、分流更准，网速反而更稳。代价是 HTTP/3 不可用，部分 Google 服务可能变慢。
2. **优先 TCP 线路**：选节点时优先用 TCP 线路（VLESS / Trojan / VMess over WS over TLS 443），不要只盯着 HY2（UDP）节点。`AUTO` 策略组会自动选延迟最低的节点，全挂时 `AUTO-FALLBACK` 按顺序选第一个可用节点。
3. **不要只换节点重试**：如果所有 UDP 节点都超时、TCP 节点正常，问题在 UDP 限流不在节点，换更多 UDP 节点没用；切到 TCP 线路才是对的。

---

## 🧪 DNS / WebRTC 泄露检测

连接节点并启用本规则后，建议使用 Safari 访问以下专业隐私检测平台验证防护效果：

1. **[IPPure](https://www.ippure.com)**：
   - 检查「DNS 泄漏检测」：结果中**不应出现中国大陆地区旗帜或国内运营商 DNS**。
   - 检查「WebRTC 泄漏检测」：应显示“未检测到 WebRTC 泄露”。
2. **[BrowserLeaks](https://browserleaks.com/ip)**：
   - 检查 DNS Leak 与 WebRTC Leak 页面。
3. **[IPLeak.net](https://ipleak.net)**：
   - 检查 DNS Address Detection 检测出的 DNS 服务器归属地。

---

## ⚠️ 本配置不保证什么

如实写在前面，避免过度承诺：

- **节点运营方仍能看到你的流量**：配置只能保证本地运营商看不到 DNS 查询和明文流量，不能保证代理节点本身不记录、不分析你的流量。选节点要选你信任的服务方。
- **配置本身不提供 ECH / 流量混淆**：本配置只做到强制 TLS、拦截 QUIC、嗅探还原 SNI 分流；ECH 需要节点与客户端同时支持，流量特征混淆需要节点侧开启 REALITY / VLESS+TLS 443 等（仅作指引，不写具体节点）。
- **广告拦截不等于反追踪全覆盖**：去广告规则拦截的是已知广告与追踪域名，App 内嵌 SDK、第一方追踪、指纹识别不在拦截范围内。
- **防泄露依赖客户端正确开启**：Shadowrocket 须开启「禁用 STUN」，Android 须关闭系统「私人 DNS」与浏览器自带安全 DNS，TUN/VPN 模式须开启；任一处没开都可能漏。

---

## 🚀 如何部署到您自己的 GitHub 仓库

您可以按照以下 3 步在您的 GitHub 上一键部署此开源项目：

### 第一步：在 GitHub 上创建新仓库
1. 登录您的 GitHub 账号，访问 [https://github.com/new](https://github.com/new)。
2. 仓库名称填写：`AntiLeak-AdBlock`。
3. 设置为 **Public**（公开仓库）。
4. **不要勾选** "Add a README file"（保持空仓库）。

### 第二步：推送代码至 GitHub
在本地终端中进入该项目目录，执行：

```bash
git init
git add .
git commit -m "feat: initial commit with AntiLeak and AdBlock automation"
git branch -M main
git remote add origin [https://github.com/shankangk/AntiLeak-AdBlock.git](https://github.com/shankangk/AntiLeak-AdBlock.git)
git push -u origin main
