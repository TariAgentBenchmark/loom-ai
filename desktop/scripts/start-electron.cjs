const { spawn } = require("node:child_process");
const electron = require("electron");
const waitOn = require("wait-on");

const targetUrl =
  process.env.LOOMAI_DESKTOP_URL ||
  process.env.LOOMAI_DEV_URL ||
  "http://localhost:3000";

waitOn({
  resources: [targetUrl],
  timeout: 120000,
  interval: 500,
}).then(
  () => {
    const child = spawn(electron, ["."], {
      stdio: "inherit",
      env: {
        ...process.env,
        LOOMAI_DESKTOP_URL: targetUrl,
      },
    });

    child.on("exit", (code, signal) => {
      if (signal) {
        process.kill(process.pid, signal);
        return;
      }

      process.exit(code || 0);
    });
  },
  (error) => {
    console.error(`Timed out waiting for ${targetUrl}`);
    console.error(error.message || error);
    process.exit(1);
  },
);
