// Minimal static file server for the local DT&AI clone.
const http = require('http');
const fs = require('fs');
const path = require('path');

const root = __dirname;
const port = Number(process.argv[2]) || 8080;

const types = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.woff2': 'font/woff2',
  '.webp': 'image/webp',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.webmanifest': 'application/manifest+json',
  '.xml': 'application/xml',
};

http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(root, url);
  if (!file.startsWith(root)) return res.writeHead(403).end('Forbidden');

  const hasExtension = path.extname(url) !== '';
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    const indexed = path.join(file, 'index.html');
    if (fs.existsSync(indexed)) {
      file = indexed;
    } else if (hasExtension) {
      // A real asset is missing -- 404 rather than silently serving HTML,
      // which would surface as a JS "Unexpected token '<'" error.
      console.log(`404 ${url}`);
      return res.writeHead(404).end('Not found');
    } else {
      file = path.join(root, 'index.html'); // client-side route
    }
  }

  fs.readFile(file, (err, body) => {
    if (err) return res.writeHead(404).end('Not found');
    res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
    res.end(body);
  });
}).listen(port, () => console.log(`DT&AI clone running at http://localhost:${port}`));
