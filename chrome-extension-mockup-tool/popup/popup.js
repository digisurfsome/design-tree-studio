document.getElementById('captureBtn').addEventListener('click', async () => {
  const btn = document.getElementById('captureBtn');
  btn.textContent = 'Capturing...';
  btn.disabled = true;

  try {
    // Get the current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Capture the visible tab
    const dataUrl = await chrome.tabs.captureVisibleTab(null, { format: 'png' });

    // Store the screenshot and open editor
    await chrome.storage.local.set({
      screenshot: dataUrl,
      sourceUrl: tab.url,
      sourceTitle: tab.title,
      captureTime: Date.now()
    });

    // Open the editor in a new tab
    chrome.tabs.create({ url: chrome.runtime.getURL('editor/editor.html') });

    // Close the popup
    window.close();
  } catch (error) {
    console.error('Capture failed:', error);
    btn.textContent = 'Error - Try Again';
    btn.disabled = false;
  }
});
