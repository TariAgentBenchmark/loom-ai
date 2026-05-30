const path = require("node:path");
const {
  app,
  BrowserWindow,
  Menu,
  dialog,
  shell,
} = require("electron");

const APP_ID = "cn.tuyunai.loomai";
const DEFAULT_DEVELOPMENT_URL = "http://localhost:3000";
const DEFAULT_PRODUCTION_URL = "https://tuyunai.cn";
const ALLOWED_EXTERNAL_PROTOCOLS = new Set(["http:", "https:", "mailto:", "tel:"]);
const DESKTOP_QUERY_PARAM = "desktop";
const DESKTOP_LOGIN_QUERY_PARAM = "desktopLogin";
const APP_ICON_PATH = path.join(__dirname, "resources", "icon.png");

let mainWindow = null;
let targetUrl = null;
let downloadHandlerInstalled = false;

const gotSingleInstanceLock = app.requestSingleInstanceLock();

if (!gotSingleInstanceLock) {
  app.quit();
}

function normalizeUrl(rawUrl, fallbackUrl) {
  const value = (rawUrl || "").trim();
  const candidate = value || fallbackUrl;
  const withScheme = /^[a-z][a-z\d+\-.]*:\/\//i.test(candidate)
    ? candidate
    : `https://${candidate}`;

  try {
    const parsedUrl = new URL(withScheme);
    if (parsedUrl.protocol !== "http:" && parsedUrl.protocol !== "https:") {
      return fallbackUrl;
    }
    return parsedUrl.toString();
  } catch {
    return fallbackUrl;
  }
}

function resolveTargetUrl() {
  const fallbackUrl = app.isPackaged
    ? DEFAULT_PRODUCTION_URL
    : DEFAULT_DEVELOPMENT_URL;

  const configuredUrl =
    process.env.LOOMAI_DESKTOP_URL ||
    (app.isPackaged ? process.env.LOOMAI_WEB_URL : process.env.LOOMAI_DEV_URL);

  return applyDesktopLaunchParams(normalizeUrl(configuredUrl, fallbackUrl));
}

function applyDesktopLaunchParams(urlString) {
  if (process.env.LOOMAI_DESKTOP_LOGIN_ON_START === "0") {
    return urlString;
  }

  try {
    const parsedUrl = new URL(urlString);

    if (!parsedUrl.searchParams.has(DESKTOP_QUERY_PARAM)) {
      parsedUrl.searchParams.set(DESKTOP_QUERY_PARAM, "1");
    }

    if (!parsedUrl.searchParams.has(DESKTOP_LOGIN_QUERY_PARAM)) {
      parsedUrl.searchParams.set(DESKTOP_LOGIN_QUERY_PARAM, "1");
    }

    return parsedUrl.toString();
  } catch {
    return urlString;
  }
}

function isInternalNavigation(urlString) {
  if (!targetUrl) {
    return false;
  }

  try {
    const nextUrl = new URL(urlString);
    if (nextUrl.protocol === "file:") {
      return true;
    }

    const appUrl = new URL(targetUrl);
    return nextUrl.origin === appUrl.origin;
  } catch {
    return false;
  }
}

function openExternalUrl(urlString) {
  try {
    const parsedUrl = new URL(urlString);
    if (ALLOWED_EXTERNAL_PROTOCOLS.has(parsedUrl.protocol)) {
      shell.openExternal(parsedUrl.toString());
    }
  } catch {
    // Ignore malformed URLs from the renderer.
  }
}

function installAppMenu() {
  const template = [
    ...(process.platform === "darwin"
      ? [
          {
            label: app.name,
            submenu: [
              { role: "about" },
              { type: "separator" },
              { role: "services" },
              { type: "separator" },
              { role: "hide" },
              { role: "hideOthers" },
              { role: "unhide" },
              { type: "separator" },
              { role: "quit" },
            ],
          },
        ]
      : []),
    {
      label: "Edit",
      submenu: [
        { role: "undo" },
        { role: "redo" },
        { type: "separator" },
        { role: "cut" },
        { role: "copy" },
        { role: "paste" },
        { role: "selectAll" },
      ],
    },
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "forceReload" },
        ...(app.isPackaged ? [] : [{ role: "toggleDevTools" }]),
        { type: "separator" },
        { role: "resetZoom" },
        { role: "zoomIn" },
        { role: "zoomOut" },
        { type: "separator" },
        { role: "togglefullscreen" },
      ],
    },
    {
      label: "Window",
      submenu: [{ role: "minimize" }, { role: "close" }],
    },
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function installDownloadHandler(window) {
  if (downloadHandlerInstalled) {
    return;
  }

  downloadHandlerInstalled = true;
  window.webContents.session.on("will-download", (event, item) => {
    const savePath = dialog.showSaveDialogSync({
      defaultPath: item.getFilename(),
      buttonLabel: "Save",
      properties: ["createDirectory"],
    });

    if (!savePath) {
      item.cancel();
      return;
    }

    item.setSavePath(savePath);
  });
}

function loadOfflinePage(window, failedUrl, description) {
  window.loadFile(path.join(__dirname, "offline.html"), {
    query: {
      target: targetUrl || DEFAULT_PRODUCTION_URL,
      failed: failedUrl || "",
      message: description || "Unable to load LoomAI.",
    },
  });
}

function createMainWindow() {
  const window = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 1024,
    minHeight: 700,
    title: "LoomAI",
    backgroundColor: "#f8fafc",
    icon: APP_ICON_PATH,
    show: false,
    autoHideMenuBar: process.platform !== "darwin",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true,
      devTools: !app.isPackaged || process.env.LOOMAI_ENABLE_DEVTOOLS === "1",
    },
  });

  installDownloadHandler(window);

  window.once("ready-to-show", () => {
    window.show();
  });

  window.webContents.setWindowOpenHandler(({ url }) => {
    if (isInternalNavigation(url)) {
      return { action: "allow" };
    }

    openExternalUrl(url);
    return { action: "deny" };
  });

  window.webContents.on("will-navigate", (event, url) => {
    if (isInternalNavigation(url)) {
      return;
    }

    event.preventDefault();
    openExternalUrl(url);
  });

  window.webContents.on(
    "did-fail-load",
    (_event, _errorCode, errorDescription, validatedUrl, isMainFrame) => {
      const failedUrl = String(validatedUrl || "");
      if (isMainFrame === false || failedUrl.startsWith("file://")) {
        return;
      }

      loadOfflinePage(window, failedUrl, errorDescription);
    },
  );

  window.loadURL(targetUrl);
  return window;
}

app.on("second-instance", () => {
  if (!mainWindow) {
    return;
  }

  if (mainWindow.isMinimized()) {
    mainWindow.restore();
  }

  mainWindow.focus();
});

app.whenReady().then(() => {
  app.setAppUserModelId(APP_ID);
  targetUrl = resolveTargetUrl();
  installAppMenu();
  mainWindow = createMainWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createMainWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
