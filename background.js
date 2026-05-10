const PRIVATE_KEY_PEM = `-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCUHMdMJFSzOnuO
OIRY3UZcWTXfCexZ15UOXjZB8fvgLxyvTN5gTh+Wo6SNb48ojuIw/p3fltMom3ZW
eyeKD5QB/sL+LgWHs10GrCE73TYwsmhdXUCyZhZX7VK8meqsFBBf7SDTPcJ6lfup
XsFstxQWV9nq2FQAQLSzUVU46KGjADKV7cEwamQ+C+0ix74EfDYvaZohfUtHEMie
MB5xYePJnxPS1qqP4Ftsgco5/hZfscsf9lR4+LSDAj+krNRo2j6Kto030Kxrwymi
7KbfVvlXujYsoh+LlhEXEAxHYUTbllKvcKRWvEiMNkW64+lFMclVIkHs0KjRPrOY
0nfy0iVJAgMBAAECggEAQdrP5HOM84nv0OshMW/lbn89/Dcpz0KTJGnQXx7seqAH
9YvMnm5uDikhq79sHED3oog7guRJbBc/lTE6AeFuUjrH0YN98vnVxXc4aakwhJN2
4vhpIUlR6vN7I5+eH7fmFfjV7QbbV20jkgmvIBsBA/Q40Pox01Dx538k0OJiqBnr
h+jdL99lURPYkG3/mfT3R2pG+vIP2PYydW0pi87f6AK4pxFZnAF82MuGcCM+Byr0
ga8/pSV4wmkU+kezK4P6RfbSi4tuUszvaBWcczAgqEN3yltYwN0v/JSk2oHcBSx4
phJV/RGGGg/IRHt4d0zi3PRfTrx2YI7AEgc1TCVSxwKBgQDMTdr6j64IMtWM45TG
QMcwtZLDutdCpvkVBGtpzdj3DWP2ZYAWQoO1ko1T2IOKkNWIXO3PEmX2fnTvyERk
XPQeiLf085TNnfnzKvCG8DrQwHZqdb2Wt1M2FJkYvxd14CALK2l6yHUEAyNveUoD
VcmtOapYvCndo9d7JpmoiCzelwKBgQC5lwKqyhwLEvbKegMMSZKrL5AsdKbp/r/r
Vovgw2wBhtmj7Gr8bnkS9nAmI3mETCFolxmbDHPK2Yt6D/+LtIcOdalI6Ox93nHx
IV2kPQff5czWa78IiiGPeJYrp/ZBZK33egWJWPAsQsZAms0GXAQ9vSomUUBi8rUT
Lkc03c13HwKBgQCsSqv0yd5WA6ib3ADHADH7HeTbM2H9T5qW4tdCrtnd3mkCja5r
F0TDhwewQdMMs/+fs97I1hcuvI4Y+KbUjJ9CcMHRzOkcTbFQJFIbOdQf3279cLWl
uIxv+wbxG5XJTm03fjDB3vLvo0Xq6DpGfb5KW2sQ0f3scBN0Q6Upv003mQKBgFPk
oG8Fx6F15BtpBiGyzFsXuAtwe9dAsg6246opjJQwGgfQohgT9CUPQ2jqFk8oft2h
mBCPk3Q53KPDwZesdnSh2XE84VKQkF8Y3xSUBhA+99ZhhExe7IbHUtLPLTEoSr+Y
6BHLI15OnQGtOErMo5oo/XmutvVDk3jlLYkHTo6vAoGBAKaT2qIDOStdCrwRbvD1
SF/pcEytM0rQhiJYmBXKeayUsICTxnSdixb42BSRDTL14F6Jzv2GcGRh80Jx1DVL
6Dmv27MEXx3OnCiHmTCHi3CxqKXhOvJGQCbtLLjluP6pAvQCZ7s3KB6/zS4v/fIv
zygLJrETnjWa1iAMPLnIB9lB
-----END PRIVATE KEY-----`;

const CONFIG_URLS = [
  'https://gitlab.com/zhifan999/fq/-/raw/main/config.json',
  'https://www.githubip.xyz/config.json'
];

// [v1.5.2] 通知文件地址(明文 JSON,不加密)
const NOTICE_URLS = [
  'https://gitlab.com/zhifan999/fq/-/raw/main/notice.json',
  'https://www.githubip.xyz/notice.json'
];

const CACHE_TTL  = 5 * 60 * 1000;

let isConnected    = false;
let cachedConfig   = null;
let cacheTime      = 0;
let activeNode     = null;

// [v1.5.2] 通知缓存(独立于配置缓存)
let cachedNotice    = null;
let noticeCacheTime = 0;

// [v1.5.2] 拉取通知(明文 JSON,不依赖 RSA 解密)
async function fetchNotice() {
  if (cachedNotice !== null && Date.now() - noticeCacheTime < CACHE_TTL) {
    return cachedNotice;
  }
  for (const url of NOTICE_URLS) {
    try {
      const res = await fetch(url, {
        cache: 'no-store',
        signal: AbortSignal.timeout(5000)
      });
      if (res.ok) {
        cachedNotice = await res.json();
        noticeCacheTime = Date.now();
        return cachedNotice;
      }
    } catch {
      continue;
    }
  }
  // 所有源失败:返回 null,popup 端不显示通知(优雅降级)
  cachedNotice = null;
  noticeCacheTime = Date.now();
  return null;
}

async function fetchAndDecryptConfig() {
  if (cachedConfig && Date.now() - cacheTime < CACHE_TTL) return cachedConfig;

  let envelope = null;
  for (const url of CONFIG_URLS) {
    try {
      const res = await fetch(url, {
        cache: 'no-store',
        signal: AbortSignal.timeout(5000)
      });
      if (res.ok) {
        envelope = await res.json();
        break;
      }
    } catch {
      continue;
    }
  }

  if (!envelope) throw new Error('all config sources failed');

  const privateKey = await crypto.subtle.importKey(
    'pkcs8', pemToBuffer(PRIVATE_KEY_PEM),
    { name: 'RSA-OAEP', hash: 'SHA-1' }, false, ['decrypt']
  );
  const aesKeyBuf = await crypto.subtle.decrypt(
    { name: 'RSA-OAEP' }, privateKey, base64ToBuffer(envelope.key)
  );
  const aesKey = await crypto.subtle.importKey(
    'raw', aesKeyBuf, { name: 'AES-CBC' }, false, ['decrypt']
  );
  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-CBC', iv: base64ToBuffer(envelope.iv) },
    aesKey, base64ToBuffer(envelope.data)
  );
  cachedConfig = JSON.parse(new TextDecoder().decode(decrypted));
  cacheTime = Date.now();
  return cachedConfig;
}

function pemToBuffer(pem) {
  return base64ToBuffer(pem.replace(/-----[^-]+-----/g, '').replace(/\s/g, ''));
}
function base64ToBuffer(b64) {
  const bin = atob(b64);
  const buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return buf.buffer;
}

// 并行 TLS 握手检测单个节点
async function testNode(node) {
  const start = Date.now();
  try {
    await fetch(`https://${node.server}:${node.port}/`, {
      method: 'HEAD',
      mode: 'no-cors',
      cache: 'no-store',
      signal: AbortSignal.timeout(5000)
    });
    const ms = Date.now() - start;
    return { status: ms < 800 ? 'ok' : 'slow', ms };
  } catch {
    return { status: 'fail', ms: 0 };
  }
}

// 并行检测所有节点
async function checkAllNodes() {
  const config = await fetchAndDecryptConfig();
  const results = await Promise.all(
    config.nodes.map(async node => {
      const result = await testNode(node);
      return { ...node, ...result };
    })
  );
  return results;
}

async function setProxy(server, port) {
  const data = await chrome.storage.local.get(['globalMode']);
  const global = data.globalMode === true;
  return new Promise((resolve, reject) => {
    chrome.proxy.settings.set({
      value: { mode: 'pac_script', pacScript: { data: buildPacScript(server, port, global) } },
      scope: 'regular'
    }, () => {
      if (chrome.runtime.lastError) reject(chrome.runtime.lastError);
      else resolve();
    });
  });
}

async function connect(node) {
  try {
    const config = await fetchAndDecryptConfig();

    // 确定要尝试的节点顺序
    let nodesToTry = [];

    if (node) {
      // 用户手动选择了节点，只尝试这个
      nodesToTry = [node];
    } else {
      // 自动连接：优先上次用的节点，其次其他节点
      const saved = await chrome.storage.local.get(['lastNode']);
      const lastNode = saved.lastNode
        ? config.nodes.find(n => n.server === saved.lastNode)
        : null;
      const others = config.nodes.filter(n => n.server !== saved.lastNode);
      nodesToTry = lastNode ? [lastNode, ...others] : config.nodes;
    }

    // 逐个尝试节点
    for (const n of nodesToTry) {
      await setProxy(n.server, n.port);
      const ok = await verifyConnection();
      if (ok) {
        activeNode = n;
        isConnected = true;
        updateIcon(true);
        // [v1.5.1] 同时持久化整个 activeNode 对象,防止 Service Worker 休眠后丢失
        chrome.storage.local.set({
          connected: true,
          lastNode: n.server,
          activeNodeData: n
        });
        return { success: true, node: n };
      }
    }

    // 所有节点都失败
    chrome.proxy.settings.set({ value: { mode: 'system' }, scope: 'regular' });
    return { success: false, error: 'all nodes failed' };

  } catch (e) {
    console.error('connect error:', e);
    return { success: false, error: e.message };
  }
}

async function verifyConnection() {
  try {
    await fetch('https://www.google.com/generate_204', {
      method: 'GET',
      mode: 'no-cors',
      cache: 'no-store',
      signal: AbortSignal.timeout(6000)
    });
    return true;
  } catch {
    return false;
  }
}

function disconnect() {
  chrome.proxy.settings.set({ value: { mode: 'system' }, scope: 'regular' });
  isConnected = false;
  activeNode  = null;
  // [v1.5.1] 同时清除持久化的 activeNode
  chrome.storage.local.set({ connected: false });
  chrome.storage.local.remove('activeNodeData');
  updateIcon(false);
}

function buildPacScript(server, port, global) {
  if (global) {
    return 'function FindProxyForURL(url,host){' +
      'if(isPlainHostName(host)||shExpMatch(host,"*.local")||' +
      'isInNet(host,"127.0.0.0","255.0.0.0")||' +
      'isInNet(host,"192.168.0.0","255.255.0.0")||' +
      'isInNet(host,"10.0.0.0","255.0.0.0"))return "DIRECT";' +
      'return "HTTPS ' + server + ':' + port + '";}';
  }
  return 'function FindProxyForURL(url,host){' +
    'if(isPlainHostName(host)||shExpMatch(host,"*.local")||' +
    'isInNet(host,"127.0.0.0","255.0.0.0")||' +
    'isInNet(host,"192.168.0.0","255.255.0.0")||' +
    'isInNet(host,"10.0.0.0","255.0.0.0"))return "DIRECT";' +
    'var d=[".cn",".baidu.com",".qq.com",".weixin.qq.com",' +
    '".taobao.com",".tmall.com",".jd.com",".alipay.com",' +
    '".aliyun.com",".tencent.com",".163.com",".126.com",' +
    '".sina.com.cn",".weibo.com",".bilibili.com",".iqiyi.com",' +
    '".youku.com",".meituan.com",".dianping.com",".ctrip.com",' +
    '".zhihu.com",".douban.com",".xiaohongshu.com",".toutiao.com",' +
    '".bytedance.com",".douyin.com",".kuaishou.com"];' +
    'for(var i=0;i<d.length;i++){' +
    'if(dnsDomainIs(host,d[i])||host===d[i].replace(/^\\./, ""))return "DIRECT";}' +
    'return "HTTPS ' + server + ':' + port + '";}';
}

function updateIcon(connected) {
  const canvas = new OffscreenCanvas(32, 32);
  const ctx    = canvas.getContext('2d');
  ctx.clearRect(0, 0, 32, 32);
  ctx.strokeStyle = connected ? '#1D9E75' : '#aaaaaa';
  ctx.lineWidth = 2; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.arc(16, 16, 10, 0, Math.PI * 2); ctx.stroke();
  ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.ellipse(16, 16, 5, 10, 0, 0, Math.PI * 2); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(6, 16); ctx.lineTo(26, 16); ctx.stroke();
  chrome.action.setIcon({ imageData: ctx.getImageData(0, 0, 32, 32) });
}

function restoreState() {
  // [v1.5.1] Service Worker 启动时,从 storage 和 proxy settings 恢复状态
  chrome.proxy.settings.get({ incognito: false }, (cfg) => {
    const proxyActive = cfg.value.mode === 'pac_script';
    if (proxyActive) {
      // 代理仍激活,尝试从 storage 恢复 activeNode
      chrome.storage.local.get(['activeNodeData'], (data) => {
        if (data.activeNodeData) {
          activeNode = data.activeNodeData;
          isConnected = true;
          updateIcon(true);
        } else {
          isConnected = true;
          updateIcon(true);
        }
      });
    } else {
      isConnected = false;
      activeNode  = null;
      updateIcon(false);
    }
  });
}

// 浏览器启动时清除代理和状态
chrome.runtime.onStartup.addListener(() => {
  chrome.proxy.settings.set({ value: { mode: 'system' }, scope: 'regular' });
  chrome.storage.local.set({ connected: false });
  // [v1.5.1] 同时清除持久化的 activeNode(浏览器启动 = 断开连接)
  chrome.storage.local.remove('activeNodeData');
  isConnected = false;
  activeNode  = null;
  updateIcon(false);
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'getStatus') {
    chrome.proxy.settings.get({ incognito: false }, (cfg) => {
      const proxyActive = cfg.value.mode === 'pac_script';
      if (proxyActive !== isConnected) { isConnected = proxyActive; updateIcon(proxyActive); }
      // [v1.5.1] 如果内存中 activeNode 已丢失但代理仍激活,从 storage 恢复
      if (proxyActive && !activeNode) {
        chrome.storage.local.get(['activeNodeData'], (data) => {
          if (data.activeNodeData) {
            activeNode = data.activeNodeData;
          }
          sendResponse({ connected: isConnected, activeNode });
        });
        return; // 异步返回,等 storage 读取完成
      }
      sendResponse({ connected: isConnected, activeNode });
    });
    return true;
  } else if (msg.action === 'getNodes') {
    fetchAndDecryptConfig().then(cfg => sendResponse({ nodes: cfg.nodes }));
    return true;
  } else if (msg.action === 'getNotice') {
    // [v1.5.2] 拉取通知,失败返回 null
    fetchNotice().then(notice => sendResponse({ notice })).catch(() => sendResponse({ notice: null }));
    return true;
  } else if (msg.action === 'checkNodes') {
    checkAllNodes().then(results => sendResponse({ results }));
    return true;
  } else if (msg.action === 'connect') {
    connect(msg.node || null).then(sendResponse);
    return true;
  } else if (msg.action === 'setMode') {
    // 切换模式后如果已连接，重新应用代理
    if (isConnected && activeNode) {
      setProxy(activeNode.server, activeNode.port);
    }
    sendResponse({ success: true });
  } else if (msg.action === 'disconnect') {
    disconnect();
    sendResponse({ success: true });
  }
});

restoreState();
