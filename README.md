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
- **强效广告与追踪过滤**：
  - 上游自动同步 [Johnshall/Shadowrocket-ADBlock-Rules-Forever](https://github.com/Johnshall/Shadowrocket-ADBlock-Rules-Forever) 的 `仅去广告规则 (sr_ad_only.conf)`。
  - 覆盖 iOS 常见 App 开屏广告、SDK 追踪（穿山甲、优量汇、友盟等）以及视频/网页广告。
- **Android / 跨平台 Clash Meta 版**：
  - 与 iOS 版一一对应的 Mihomo 配置 `Meta-AntiLeak.yaml`：`fake-ip` + `respect-rules` 实现境外域名远端解析、国内域名加密 DoH 直连解析；`strict-route` + `dns-hijack` 接管全部 DNS；STUN 规则拦截封堵 WebRTC 泄露；国内 IP 规则同样强制 `no-resolve`。
  - 广告规则同源：Johnshall 规则每日由构建脚本自动转换为 Clash 格式，ACL4SSR 规则集与 iOS 版完全一致。适用于 FlClash、Clash Meta for Android，桌面端 Clash Verge / Mihomo Party 亦可使用。

- **自动化免维护**：
  - 内置 GitHub Actions 工作流，每天自动拉取上游最新规则并合并构建发布。

---

## 📥 规则订阅地址与二维码

> 支持直接复制 Raw 订阅地址，或使用 **Shadowrocket / 系统相机** 扫描下方二维码一键下载添加：

| 规则类型 | 说明 | 订阅地址 (Raw) | 扫码导入 (二维码) |
| :--- | :--- | :--- | :---: |
| **整合强效版<br>(推荐)** | 防 DNS 泄露 + Johnshall 每日同步去广告 | `https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/sr_ad_antileak.conf` | <img src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=https%3A%2F%2Fraw.githubusercontent.com%2Fshankangk%2FAntiLeak-AdBlock%2Fmain%2Foutput%2Fsr_ad_antileak.conf" width="160" alt="整合强效版二维码" /> |
| **极简防泄露版** | 纯粹防 DNS 泄露与基础分流，不含庞大广告规则 | `https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/Mini-AntiLeak.conf` | <img src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=https%3A%2F%2Fraw.githubusercontent.com%2Fshankangk%2FAntiLeak-AdBlock%2Fmain%2Foutput%2FMini-AntiLeak.conf" width="160" alt="极简防泄露版二维码" /> |

---

## 📲 在 Shadowrocket 中使用

### 方法一：扫描二维码导入（最便捷）
1. 打开 **Shadowrocket** 客户端。
2. 点击左上角的 **扫描图标**。
3. 扫描上方表格中对应规则的二维码，点击 **保存** 即可完成导入。

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

| 规则类型 | 说明 | 配置地址 (Raw) | 扫码导入 (二维码) |
| :--- | :--- | :--- | :---: |
| **Clash Meta 完整版 (推荐)** | 防 DNS 泄露 + 去广告完整 Mihomo 配置，与 iOS 版同源 | `https://raw.githubusercontent.com/shankangk/AntiLeak-AdBlock/main/output/clash/Meta-AntiLeak.yaml` | <img src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=https%3A%2F%2Fraw.githubusercontent.com%2Fshankangk%2FAntiLeak-AdBlock%2Fmain%2Foutput%2Fclash%2FMeta-AntiLeak.yaml" width="160" alt="Clash Meta 版二维码" /> |

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
- **Clash Verge Rev**：新建覆写并绑定到机场订阅：选 **Script** 类型时用上面的 JS 文件（与 FlClash 同一份，全量 Johnshall 去广告规则）；选 **Merge** 类型时用 Merge 版 YAML。注意 Merge 机制对 `rule-providers` 是整段替换、无法安全叠加远程规则集，所以 Merge 版的去广告只有内核内置的 `GEOSITE category-ads-all`，其余防泄露部分（fake-ip DNS、TUN、STUN 拦截）与 JS 版一致。
- 两种覆写都会新增一个 **AntiLeak** 策略组（`include-all` 自动包含你的全部节点），仅作为加密 DNS 的指定出口，不影响你在机场策略组里的任何选择；随时关掉覆写即可完整还原机场配置。

### Android 关键设置

1. **关闭系统「私人 DNS」**：设置 → 网络和互联网 → 私人 DNS，选「关闭」或「自动」，不要指定第三方 DoT 服务器，否则 DNS 会绕过本配置的接管。
2. **关闭浏览器自带安全 DNS**：Chrome → 设置 → 隐私和安全 → 使用安全 DNS，选「使用当前服务提供商」或关闭，避免浏览器 DoH 绕行。
3. **确认 TUN/VPN 模式已开启**（FlClash 默认开启）。WebRTC 的 STUN 探测已由配置内规则拦截，无需像 iOS 版那样再找开关。
4. 断开重连一次使配置全面生效，泄露检测方法见下一节（用 Chrome 访问即可）。

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
