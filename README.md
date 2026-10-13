# Shadowrocket-AntiLeak-AdBlock 🛡️

提供针对 iOS **Shadowrocket (小火箭)** 的**防 DNS 泄露**与**全能广告拦截**整合规则配置，支持 GitHub Actions 每日北京时间 09:15 自动定时构建更新。

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
- **自动化免维护**：
  - 内置 GitHub Actions 工作流，每天自动拉取上游最新规则并合并构建发布。

---

## 📥 规则订阅地址与二维码

> 支持直接复制 Raw 订阅地址，或使用 **Shadowrocket / 系统相机** 扫描下方二维码一键下载添加：

| 规则类型 | 说明 | 订阅地址 (Raw) | 扫码导入 (二维码) |
| :--- | :--- | :--- | :---: |
| **整合强效版<br>(推荐)** | 防 DNS 泄露 + Johnshall 每日同步去广告 | `https://raw.githubusercontent.com/shankangk/Shadowrocket-AntiLeak-AdBlock/main/output/sr_ad_antileak.conf` | <img src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=https%3A%2F%2Fraw.githubusercontent.com%2Fshankangk%2FShadowrocket-AntiLeak-AdBlock%2Fmain%2Foutput%2Fsr_ad_antileak.conf" width="160" alt="整合强效版二维码" /> |
| **极简防泄露版** | 纯粹防 DNS 泄露与基础分流，不含庞大广告规则 | `https://raw.githubusercontent.com/shankangk/Shadowrocket-AntiLeak-AdBlock/main/output/Mini-AntiLeak.conf` | <img src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=https%3A%2F%2Fraw.githubusercontent.com%2Fshankangk%2FShadowrocket-AntiLeak-AdBlock%2Fmain%2Foutput%2FMini-AntiLeak.conf" width="160" alt="极简防泄露版二维码" /> |

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
2. 仓库名称填写：`Shadowrocket-AntiLeak-AdBlock`。
3. 设置为 **Public**（公开仓库）。
4. **不要勾选** "Add a README file"（保持空仓库）。

### 第二步：推送代码至 GitHub
在本地终端中进入该项目目录，执行：

```bash
git init
git add .
git commit -m "feat: initial commit with AntiLeak and AdBlock automation"
git branch -M main
git remote add origin [https://github.com/shankangk/Shadowrocket-AntiLeak-AdBlock.git](https://github.com/shankangk/Shadowrocket-AntiLeak-AdBlock.git)
git push -u origin main
