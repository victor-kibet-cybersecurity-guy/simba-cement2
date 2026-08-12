import express from 'express';
import compression from 'compression';
import path from 'path';
import fs from 'fs';

const app = express();
const PORT = 3000;

// Enable gzip/deflate response compression for high Lighthouse performance scores
app.use(compression());

// Serve static files with custom Cache-Control headers
app.use(express.static(process.cwd(), {
  setHeaders: (res, filePath) => {
    if (filePath.endsWith('sw.js')) {
      // Service worker must revalidate instantly
      res.setHeader('Cache-Control', 'public, max-age=0, must-revalidate');
    } else if (filePath.endsWith('.css') || filePath.endsWith('.js') || filePath.match(/\.(jpg|jpeg|png|webp|svg|ico|woff2?)$/i)) {
      // Static assets cached for 1 year
      res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
    } else if (filePath.endsWith('.html')) {
      // HTML files cached briefly
      res.setHeader('Cache-Control', 'public, max-age=3600, must-revalidate');
    }
  }
}));

// Handle extensionless HTML routes if needed (e.g., /about -> /about.html)
app.use((req, res, next) => {
  if (req.method !== 'GET' && req.method !== 'HEAD') return next();

  const filePath = req.path.endsWith('/') ? req.path + 'index.html' : req.path;
  const possibleHtml = path.join(process.cwd(), filePath + '.html');
  if (fs.existsSync(possibleHtml) && fs.statSync(possibleHtml).isFile()) {
    return res.sendFile(possibleHtml);
  }
  next();
});

// Fallback to index.html for navigation if file not found
app.use((req, res) => {
  const indexPath = path.join(process.cwd(), 'index.html');
  if (fs.existsSync(indexPath)) {
    res.sendFile(indexPath);
  } else {
    res.status(404).send('Not Found');
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on http://0.0.0.0:${PORT}`);
});
