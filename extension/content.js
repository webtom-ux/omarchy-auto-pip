function mainVideo() {
  return (
    document.querySelector("video.html5-main-video") ||
    document.querySelector("video")
  )
}

async function enterPip() {
  const video = mainVideo()
  if (!video) return { ok: false, error: "no-video" }

  if (document.pictureInPictureElement && document.pictureInPictureElement !== video) {
    try {
      await document.exitPictureInPicture()
    } catch (_error) {}
  }
  if (document.pictureInPictureElement === video) {
    return { ok: true, already: true }
  }

  if (video.paused) {
    try {
      await video.play()
    } catch (_error) {}
  }

  try {
    await video.requestPictureInPicture()
    return { ok: true }
  } catch (error) {
    const button =
      document.querySelector(".ytp-pip-button") ||
      document.querySelector('button[aria-label*="icture-in-icture" i]') ||
      document.querySelector('button[title*="icture-in-icture" i]')
    if (button) {
      button.click()
      return { ok: true, via: "button" }
    }
    return { ok: false, error: String(error) }
  }
}

async function exitPip() {
  if (!document.pictureInPictureElement) return { ok: true, already: true }
  try {
    await document.exitPictureInPicture()
    return { ok: true }
  } catch (error) {
    return { ok: false, error: String(error) }
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  const cmd = message && message.cmd
  if (cmd === "enter") {
    enterPip().then(sendResponse)
    return true
  }
  if (cmd === "exit") {
    exitPip().then(sendResponse)
    return true
  }
  return false
})
