# Tuzi GPT Image 2 VIP 排查记录

## 确认范围（2026-11-08）

正式环境实际运行 revision `22bf7c9`，备用切换已执行，并非部署遗漏。
本文仅记录只读排查；没有向 Chat/Images 生图端点发送新的请求，没有创建付费任务。

### 标准通道：确定是接口协议不匹配

`gpt-image-2` 的生产响应明确表示它是图片模型，不能调用 `/v1/chat/completions`，必须使用 `/v1/images/generations` 或 `/v1/images/edits`。
本次只修标准备用为 Multipart Images Edits，VIP 的请求协议保持不变。

### VIP：暂未定责

- `GET /v1/models` 使用生产 key 返回 200，VIP 模型仍在列表中；公开元数据标注支持 `openai`、`image-generation`。这不等于已经验证该令牌在所选 VIP 渠道上的实际生图能力。
- VIP 生产响应 HTTP 400，仅有 `Invalid request. Please check the request parameters.`，没有具体字段或内层供应商错误。
- 现有请求为 `model=gpt-image-2-vip`、`stream=false`、`messages`，用户内容包含 text 和 `image_url.url=data:image/png;base64,...`。
- 服务商公开通用 Chat 文档允许图片 URL/Base64，stream 默认 false。因此不能仅凭“图片模型”就断定 VIP 也必须改 Images Edits；列表中通用的 openai 标签也不能证明其所有图片输入组合均可用。
- 没找到针对该 VIP 型号的完整独立参数契约，旧的 GPT-4o-image-vip 教程不能直接作为 GPT Image 2 VIP 的协议依据。

## 离线请求检查

从正式服务器读取两条已失败任务的原图，临时替换该实例的 HTTP 发送方法，只构造请求、解码和验证图片，不向生图接口发请求，也不修改数据库。

| 样本任务 | PNG 尺寸 | 规范化 PNG 字节数 | JSON 请求体约字节数 |
| --- | --- | --- | --- |
| 69393 | 277×518 | 205170 | 273951 |
| 69679 | 352×218 | 108535 | 145107 |

两个样本均为有效 RGB PNG，Base64 可严格解码，提示词 68 字符，结构符合当前客户端和通用 Chat 文档。未发现明显的图片损坏、大请求体或漏传 model/messages/stream。
错误日志中的图片长字段已经截断，不能将日志里约 520 字符的保存长度误当作实际请求图片大小。

## 可供服务商追踪的请求

以下为既有失败请求，不是新建测试请求（时间为 UTC）：

- 2026-11-08 07:29，任务 69679：`202611080729014303822348268d9d6IlhgeUK6`
- 2026-11-08 07:28，任务 69678：`202611080728162904380458268d9d6ouIOmbnI`

建议请服务商按 request ID 核对：
1. 当时命中的 VIP 上游渠道及未被网关概括前的错误。
2. 此型号是否支持 Chat 图片编辑、Base64 data URL 及 `stream=false`。
3. 是否存在未公开的图片尺寸、输入方式、令牌分组或参数要求。
4. 若需要其他端点/请求格式，提供该 VIP 型号的可用最小示例。

没有服务商进一步信息或经用户确认的最小真实生图测试，尚不能断言是我们具体哪个 VIP 参数错误，或认定 VIP 上游故障。不得将标准备用协议修复等同于 VIP 已修好。

## 文档

- [通用 Chat 契约](https://wiki.tu-zi.com/s/8c61a536-7a59-4410-a5e2-8dab3d041958/zh-cn/api-reference/tuziapi/model/chat/openai/chuang-jian-mo-xing-xiang-ying-chat--op_ee9e4c136d.md)
- [GPT-Image-2 指南](https://wiki.tu-zi.com/s/8c61a536-7a59-4410-a5e2-8dab3d041958/zh-cn/doc/1-3ZP5NmGPe2.md)
