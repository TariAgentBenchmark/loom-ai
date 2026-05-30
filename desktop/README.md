# LoomAI Desktop

这是 LoomAI 的 Electron 桌面壳。它独立于 `frontend/`，不会改变现有 Web 端的 Next.js 构建、路由或部署方式。

## 开发

```bash
cd desktop
npm install
npm run dev
```

如果 Electron 二进制下载较慢，可以先配置镜像：

```bash
ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/ npm install
```

`npm run dev` 会同时启动：

- `../frontend` 的 `npm run dev`
- Electron 窗口，默认加载 `http://localhost:3000`

如果你已经单独启动了 Web 前端，可以只运行：

```bash
cd desktop
npm run start
```

## 地址配置

默认地址：

- 开发环境：`http://localhost:3000`
- 打包后：`https://tuyunai.cn`

可以通过环境变量覆盖：

```bash
LOOMAI_DESKTOP_URL=http://localhost:3000 npm run start
LOOMAI_WEB_URL=https://your-web-domain.example npm run dist
```

`LOOMAI_DESKTOP_URL` 优先级最高，适合开发和临时测试。`LOOMAI_WEB_URL` 适合打包生产桌面应用时指定 Web 入口。

桌面端默认会在入口 URL 上附加 `desktop=1&desktopLogin=1`，前端会据此在启动时打开登录弹窗。普通 Web 访问不带这些参数，因此仍保持原来的首页行为。如果需要临时关闭桌面启动登录：

```bash
LOOMAI_DESKTOP_LOGIN_ON_START=0 npm run start
```

## 打包

```bash
cd desktop
npm run dist:mac
npm run dist:win
npm run dist:linux
```

构建产物输出到 `desktop/dist/`，该目录已被根 `.gitignore` 忽略。

## GitHub Release

仓库提供了 `.github/workflows/desktop-release.yml`，用于构建 macOS 和 Windows 桌面 Release。

触发方式：

- 推送 tag：`v*` 或 `desktop-v*`
- GitHub Actions 页面手动运行 `Build Desktop Release`

示例：

```bash
git tag desktop-v0.1.0
git push origin desktop-v0.1.0
```

手动运行 workflow 时可以填写 `web_url`，它会作为打包后桌面端加载的 Web 入口。

当前 CI 构建默认关闭代码签名，产物可以用于内部测试。面向真实用户分发前，需要补 Apple Developer ID / Windows 代码签名证书和 macOS notarization。

## 当前边界

第一版是桌面壳方案：桌面端复用现有 Web 站点，不内置 Next.js 服务，也不改动 Web 端代码。后续如果需要离线运行、系统托盘、自动更新、原生文件选择器或 deep link 支付回跳，可以在这个 `desktop/` 包里继续扩展。
