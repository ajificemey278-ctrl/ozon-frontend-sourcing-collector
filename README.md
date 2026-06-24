# Ozon Frontend Sourcing Collector

一个面向 Ozon 选品和国内货源分析的公开前端信息采集工具骨架。

它的目标不是绕过平台风控，也不是批量爬取；它只帮助把用户能正常看到的公开前端信息整理成稳定的结构化数据，服务后续的选品、定价和初步运营建议。

## 能采什么

- Ozon 前端商品/搜索结果的公开信息：标题、价格、币种、评价数、评分、到货时效、卖点文本、图片线索。
- 1688 前端货源公开信息：标题、价格、起批、销量、店铺、运费/包邮、规格和属性线索。
- 淘宝/天猫前端货源公开信息：标题、价格、销量/评价、店铺、规格和属性线索。
- 义乌购前端货源公开信息：标题、价格、店铺、起订量、供货信息和属性线索。

## 安全原则

1. 只采公开前端可见信息。
2. 不模拟登录，不保存账号密码，不保存 Cookie。
3. 不绕过验证码、滑块、风控页或登录墙。
4. 不做 IP 代理、IP 轮换、并发轰炸或高频重试。
5. 默认单链接、低频、人工可审核。
6. 遇到验证、403、429、登录页、风控页，立即停止并输出 `verification_required`。

## 推荐流程

1. 用 `build-url` 生成搜索链接。
2. 人工在浏览器打开链接，确认地区、币种、登录状态和验证码情况。
3. 若页面正常，保存可见 HTML 或复制可见文本。
4. 用 `parse-html` 或 `parse-text` 转成 JSON。
5. 后续选品会话基于 JSON 做竞品、货源和运营分析。

## 安装

```bash
python -m pip install -e .[dev]
```

## 命令示例

生成 Ozon 搜索 URL：

```bash
ozon-source-collector build-url --platform ozon --keyword "свечи светодиодные с пультом 3 шт"
```

生成 1688 搜索 URL（自动使用 GB18030 编码，避免中文乱码）：

```bash
ozon-source-collector build-url --platform 1688 --keyword "LED仿真蜡烛 遥控 3件套"
```

解析保存下来的前端 HTML：

```bash
ozon-source-collector parse-html --platform ozon --url "https://www.ozon.ru/search/?text=..." --input page.html
```

解析复制出来的可见文本：

```bash
ozon-source-collector parse-text --platform 1688 --url "https://s.1688.com/..." --input visible.txt
```

明确允许低频单链接网络请求时：

```bash
ozon-source-collector fetch-url --platform yiwugo --url "https://www.yiwugo.com/..." --allow-network
```

`fetch-url` 是低频辅助，不用于批量采集。如果返回验证码、登录、403 或 429，工具会停止并输出阻塞原因。

## 输出格式

所有命令输出 JSON，核心字段：

- `platform`
- `source_url`
- `status`
- `items`
- `blocked_reasons`
- `evidence`
- `warnings`

## 仓库定位

这个仓库只做公开前端数据采集和解析。它不负责自动上架、不保存 Ozon API、不保存店铺密钥、不直接生成最终运营建议。