const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");
const { exec } = require("child_process");
const path = require("path");

const app = express();
const PORT = 3000;
const FLASK_BACKEND = process.env.FLASK_BACKEND || "http://localhost:5000";

// Serve static files
app.use(express.static(path.join(__dirname, "public")));

// Proxy API requests to Flask backend
app.use(
  "/api",
  createProxyMiddleware({
    target: FLASK_BACKEND,
    changeOrigin: true,
  })
);

// Fallback to index.html
app.get("*", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

app.listen(PORT, () => {
  const url = `http://localhost:${PORT}`;
  console.log(`Frontend running at ${url}`);
  console.log(`Proxying API requests to ${FLASK_BACKEND}`);

  // Auto-open browser
  const start = process.platform === "win32" ? "start" : process.platform === "darwin" ? "open" : "xdg-open";
  exec(`${start} ${url}`);
});
