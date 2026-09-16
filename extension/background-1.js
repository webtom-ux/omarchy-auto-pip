const NATIVE_HOST = "com.webtom.auto_pip"
const YOUTUBE_URLS = ["*://*.youtube.com/*", "*://youtube.com/*"]

let port = null
let reconnectTimer = null

function youtubeTabs() {
  return chrome.tabs.query({ url: YOUTUBE_URLS })
}

function debug(payload) {
  if (port) {
    try {
      port.postMessage({ debug: payload })
    } catch (_error) {}
  }
}

async function sendCommand(cmd) {
  const tabs = await youtubeTabs()
  debug({ cmd, tabCount: (tabs || []).length, urls: (tabs || []).map((tab) => tab.url) })
  await Promise.all(
    (tabs || []).map(async (tab) => {
      if (tab.id === undefined) return
      try {
        const result = await chrome.tabs.sendMessage(tab.id, { cmd })
        debug({ tabId: tab.id, result })
      } catch (error) {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ["content.js"],
        }).catch(() => {})
        try {
          const result = await chrome.tabs.sendMessage(tab.id, { cmd })
          debug({ tabId: tab.id, retried: true, result })
        } catch (retryError) {
          debug({ tabId: tab.id, error: String(retryError) })
        }
      }
    })
  )
}

function connectNative() {
  if (port) return
  try {
    port = chrome.runtime.connectNative(NATIVE_HOST)
  } catch (_error) {
    port = null
    reconnectTimer = setTimeout(connectNative, 2000)
    return
  }

  port.onMessage.addListener((message) => {
    const cmd = message && message.cmd
    if (cmd === "enter" || cmd === "exit") sendCommand(cmd)
  })
  port.onDisconnect.addListener(() => {
    port = null
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(connectNative, 1000)
  })
}

setTimeout(connectNative, 0)
