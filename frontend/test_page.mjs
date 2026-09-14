import { chromium } from 'playwright';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const logs = [];
page.on('console', msg => logs.push(`CONSOLE ${msg.type()}: ${msg.text()}`));
page.on('pageerror', err => logs.push(`PAGEERROR: ${err.message}\n${err.stack}`));
page.on('requestfailed', req => logs.push(`REQUESTFAILED ${req.url()} ${req.failure().errorText}`));
console.log('goto http://localhost:5173');
try {
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle', timeout: 15000 });
} catch(e) { logs.push(`GOTO ERROR ${e.message}`); }
await page.waitForTimeout(2000);
console.log('---LOGS---');
logs.forEach(l => console.log(l));
try {
  const content = await page.content();
  console.log('---CONTENT SNIPPET---');
  console.log(content.slice(0, 3000));
  const url = page.url();
  console.log('URL', url);
  const title = await page.title();
  console.log('TITLE', title);
} catch(e) { console.log('content error', e.message); }
await browser.close();
console.log('done');