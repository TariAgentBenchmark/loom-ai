# Seedream 接入（综合模型普通香蕉替换 / 用嘴改图模型pro）

## 已确认需求

- 只替换综合模型 `combined` 中原 `combined_detail` 的普通香蕉分支。Gemini Pro、GPT、RunningHub 三路不换供应商；综合T2、牛仔和其他调用 Gemini 2.5 的功能不变。
- 新分支使用邮件指定的完整提花提示词 `SEEDREAM_PATTERN_PROMPT`，不把固定提花指令用于用户的“用嘴改图”。
- “用嘴改图”分成“模型1”和“模型pro”。模型1保留原 2K / 4K；模型pro映射 `model=seedream_pro`，支持原有单张、双参考图、批量入口。
- 默认仍为模型1。模型pro输出按实测 2K 展示，不因提示词写了4K就承诺4K。
- 模型pro直接沿用普通 `prompt_edit` 价格及会员折扣；没有新增收费档位。原 `prompt_edit_pro_4k` 和综合模型价格不变。

## 实测基础

2026-11-16 从正式服务器按附件协议提交了一次测试，任务号 `7b75943d1b674bb49eb9d8525d16d4c6`。
接口受理后剩余499次；查询同一任务完成后下载HTTP 200，PNG为2048×2048、2156187字节，已校验图片有效。
测试输入是自行绘制的花朵，不使用客户图片。API 的进度说明包含排队、浏览器和豆包生成状态，因此需按异步慢任务处理，不能假设是即时的官方直连接口。
开发后的协议及恢复测试均使用模拟接口，不另外提交付费任务。

## 协议与结果

- HTTPS服务地址：`https://a6.zifeiyuai.top:2345`。
- 鉴权：`X-API-Key`。不得在前端、日志或Git中暴露密钥。
- `POST /add_task`：Multipart，字段 `prompt`、`ratio`，参考图用重复的 `file` 字段上传，规范化为PNG。
- 比例为 `auto` 时按首张图（含EXIF方向）匹配附件支持的比例。
- `GET /try_get?taskid=...`：code=1等候、code=0完成、code=-1失败。
- 只接受同源下载，不跟随重定向；限制100MB并验证图片，保存到应用现有结果存储后交付，而不是把需鉴权的上游URL直接返回前端。
- 每个应用任务/综合分支取首张结果，保持原出图数量。

## 密钥与配置

新增配置：`seedream_base_url`、`seedream_api_key`、`seedream_api_key_file`、`seedream_poll_interval_seconds`、`seedream_poll_timeout_seconds`。
API并发限流新增seedream（默认2），不调高其他供应商限制。

生产使用既有 `./backend/data:/app/data` 挂载，放置 **单行密钥文件**：

- 服务器：`~/loom-ai/backend/data/.env.seedream`
- 容器：`/app/data/.env.seedream`（默认相对路径 `./data/.env.seedream`）
- 只含密钥原文一行，不是 `KEY=value` 格式；权限0600。
- 此新文件受现有 `.env.*` Git忽略规则保护，整个data目录也被Docker构建上下文排除。
- 非空的 `SEEDREAM_API_KEY` 优先于文件，方便应用直跑/测试。当前compose不自动转发这些新环境变量，生产默认采用文件方式，不需要改compose或覆盖任何既有 `.env`。

## 恢复与扣费保护

- 上游任务号、完成结果和综合其他分支的结果存入 `Task.extra_metadata.seedreamState`，写入前校验processing_token，旧worker不能覆盖新worker。
- 一轮轮询默认600秒，不套用其他综合分支360秒超时；等候未完成则保留processing和预占积分，由已有watchdog恢复。
- 综合等待Seedream恢复时，已成功的其他分支先持久化，失败分支也记录为已尝试。没有可查询任务号的Gemini/GPT调用还会在开始前打标；如果worker意外退出且结果没来得及保存，不盲目重发，可能按原规则交付部分结果并退差额。正常恢复不会因等待新接口而再次调用其他付费分支。
- POST超时/连接中断或worker在提交中退出且未拿到任务号时，标记提交状态不确定。**不能自动重新POST**，需核对上游；避免一次任务消耗多次次数。
- GET和下载可重试，同一完成任务的下载失败不再次生图。恢复仍受现有watchdog最大次数限制，最终失败按原规则退积分，不无限等待。
- 没有改变既有业务数据库结构，也不自动修补已经失败退款的历史任务。

## 上线检查

- 后端117项相关回归通过，前端38项相关测试及生产构建通过，新Python模块lint通过。
- 前端全量测试仍有原管理端/测试工具的4个失败套件、25项失败；已在未改动的2abc279隔离工作树复现相同失败数，不混入本次修复。
- 密钥文件正确挂载且未跟踪进Git；只打印“配置存在/匹配”，不输出内容。
- 队列空闲时仅更新backend/frontend。基础设施及既有 `.env` 不改。
- 验证线上模型选择、版本、首页和健康接口。可复用前述已经完成的测试任务做查询/下载/保存验证，并拦截POST，避免新增生图次数。
