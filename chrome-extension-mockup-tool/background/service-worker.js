// Handle keyboard shortcut
chrome.commands.onCommand.addListener(async (command) => {
  if (command === 'capture-page') {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

      const dataUrl = await chrome.tabs.captureVisibleTab(null, { format: 'png' });

      await chrome.storage.local.set({
        screenshot: dataUrl,
        sourceUrl: tab.url,
        sourceTitle: tab.title,
        captureTime: Date.now()
      });

      chrome.tabs.create({ url: chrome.runtime.getURL('editor/editor.html') });
    } catch (error) {
      console.error('Capture failed:', error);
    }
  }
});

// Handle messages from editor for downloads
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'download') {
    chrome.downloads.download({
      url: message.dataUrl,
      filename: message.filename,
      saveAs: true
    });
    sendResponse({ success: true });
  }
  return true;
});
