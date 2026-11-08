# 综合花型 GPT 备用通道

适用于 `extract_pattern` 的 `combined` 和 `combined_t2` 模式中的 GPT 分支。

- 首选 Tuzi `gpt-image-2-vip`；请求失败、返回空图/无法解析或超时后，再尝试 `gpt-image-2`。
- 使用相同图片和提示词，但按通道分别适配协议：VIP 暂保留 `/v1/chat/completions` 非流式 JSON；标准 `gpt-image-2` 必须用 `/v1/images/edits` 的 `multipart/form-data` 文件上传，不能沿用 Chat 请求。VIP 成功时不调用备用。
- 标准备援将输入规范化为 PNG，发送 `model`、`prompt`、`n=1`、`response_format=b64_json`，可选传入调用方指定的 `quality`。不额外固定输出尺寸；返回的 Base64 由原有图片保存逻辑持久化，URL 响应也兼容。
- 标准图片编辑 POST 不自动重发，以避免连接超时或 5xx 时上游已开始生图却被重复提交、重复计费。错误保留服务端响应及不含密钥/原始图片的请求摘要。
- 两路共享现有 `extract_pattern_combined_branch_timeout_seconds` 预算：VIP 最多用一半，备用使用剩余时间，不增加整个分支的最长等待时间。
- 外部取消任务时立即向上传播取消，不再启动备用请求。超时取消本地等待不保证上游取消生成或停止计费。
- 备用结果仍计为原有 GPT 分支的一张结果，不额外增加综合模型张数、不更改用户积分定价，也不改变其他模型分支。
- 失败诊断记录每次尝试的模型、attempt、fallback、超时预算及下游错误；全部失败时保留在现有 branchErrors 中。成功使用的模型写入后端日志。
- 无需新增环境变量或修改生产 `.env`，已有 Tuzi API key 必须有两个模型的权限。
- 实际生图是付费操作；测试除响应模拟外，使用 HTTP MockTransport 检查完整 Multipart 编码、上传文件、模型路由、错误和取消。部署检查仅检查容器/健康接口及运行代码，不自动生图。协议测试通过不等于真实生图验收通过。

## 标准图像接口依据

- [服务商 GPT-Image-2 指南](https://wiki.tu-zi.com/s/8c61a536-7a59-4410-a5e2-8dab3d041958/zh-cn/doc/1-3ZP5NmGPe2.md)
- [图片编辑接口](https://wiki.tu-zi.com/s/8c61a536-7a59-4410-a5e2-8dab3d041958/zh-cn/api-reference/tuziapi/model/images/gpt-image/openai-compatible/bian-ji-tu-pian-tu-sheng-tu--op_a2ebbd2d61.md)
- 生产错误已明确指出标准 `gpt-image-2` 不支持 `/v1/chat/completions`。VIP 的 400 根因尚未确定，见 [VIP 排查记录](tuzi-vip-investigation.md)。

排查“后端有图、前端没图”时需要具体任务 ID 或发生时间。上游生图完成不等于应用已取得可下载结果；需逐步核对上游响应、结果下载/持久化、任务状态和浏览器图片请求，不能仅凭上游控制台显示成功就判定为前端问题。
