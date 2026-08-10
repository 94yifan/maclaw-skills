// CDP screenshot helper: node shot.js <targetId> <outfile>
const http = require('http');
const WebSocket = require('ws');

const targetId = process.argv[2];
const outfile = process.argv[3];

http.get('http://127.0.0.1:18800/json', (res) => {
  let data = '';
  res.on('data', (c) => data += c);
  res.on('end', () => {
    const targets = JSON.parse(data);
    const t = targets.find(x => x.id === targetId);
    if (!t) { console.error('target not found'); process.exit(1); }
    const ws = new WebSocket(t.webSocketDebuggerUrl);
    ws.on('open', () => {
      ws.send(JSON.stringify({id: 1, method: 'Page.captureScreenshot', params: {format: 'jpeg', quality: 70, captureBeyondViewport: false}}));
    });
    ws.on('message', (msg) => {
      const m = JSON.parse(msg.toString());
      if (m.id === 1) {
        const fs = require('fs');
        fs.writeFileSync(outfile, Buffer.from(m.result.data, 'base64'));
        console.log('saved', outfile);
        ws.close();
        process.exit(0);
      }
    });
  });
});
