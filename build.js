import fs from 'fs';
import path from 'path';
import { buildSync } from 'esbuild';

console.log('⚡ Starting Simba Cement Kenya build and asset minification process...');

// 1. Minify CSS
try {
  const cssResult = buildSync({
    entryPoints: ['styles.css'],
    outfile: 'styles.min.css',
    minify: true,
    bundle: true,
    loader: { '.css': 'css' }
  });
  
  const rawCssSize = fs.statSync('styles.css').size;
  const minCssSize = fs.statSync('styles.min.css').size;
  console.log(`✅ CSS Minified: ${(rawCssSize / 1024).toFixed(2)} KB → ${(minCssSize / 1024).toFixed(2)} KB (${Math.round((1 - minCssSize / rawCssSize) * 100)}% reduction)`);
} catch (err) {
  console.error('❌ CSS minification error:', err);
}

// 2. Minify JavaScript
try {
  const jsResult = buildSync({
    entryPoints: ['app.js'],
    outfile: 'app.min.js',
    minify: true,
    bundle: true,
    target: ['es2020']
  });

  const rawJsSize = fs.statSync('app.js').size;
  const minJsSize = fs.statSync('app.min.js').size;
  console.log(`✅ JS Minified: ${(rawJsSize / 1024).toFixed(2)} KB → ${(minJsSize / 1024).toFixed(2)} KB (${Math.round((1 - minJsSize / rawJsSize) * 100)}% reduction)`);
} catch (err) {
  console.error('❌ JS minification error:', err);
}

// 3. Update HTML files to reference minified & deferred assets
const files = fs.readdirSync(process.cwd());
const htmlFiles = files.filter(f => f.endsWith('.html'));

let updatedCount = 0;
htmlFiles.forEach(file => {
  let content = fs.readFileSync(file, 'utf-8');
  let original = content;

  // Replace styles.css with styles.min.css
  content = content.replace(/href="styles\.css"/g, 'href="styles.min.css"');

  // Replace app.js with app.min.js and ensure defer attribute is present
  content = content.replace(/<script src="app\.js"><\/script>/g, '<script src="app.min.js" defer></script>');
  content = content.replace(/<script src="app\.js" defer><\/script>/g, '<script src="app.min.js" defer></script>');

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf-8');
    updatedCount++;
  }
});

console.log(`✅ Updated ${updatedCount} HTML pages with minified asset references & deferred JS loading.`);
console.log('🚀 Build completed successfully!');
