const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");
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
  console.log(`Frontend running at http://localhost:${PORT}`);
  console.log(`Proxying API requests to ${FLASK_BACKEND}`);
});
