// Promptoire Chrome Extension - Background Service Worker

// Initialize extension on install
chrome.runtime.onInstalled.addListener((details) => {
    console.log('Promptoire installed:', details.reason);
    
    // Set default badge text
    chrome.action.setBadgeText({
        text: ''
    });
    
    // Set default badge color
    chrome.action.setBadgeBackgroundColor({
        color: '#2196F3'
    });
});

// Handle extension startup
chrome.runtime.onStartup.addListener(() => {
    console.log('Promptoire started');
});

// Handle storage changes (optional: for sync debugging)
chrome.storage.onChanged.addListener((changes, namespace) => {
    console.log('Storage changed:', changes, 'in', namespace);
});

// Handle keyboard shortcuts (if we add any in the future)
chrome.commands.onCommand.addListener((command) => {
    console.log('Command triggered:', command);
    
    switch (command) {
        case 'open_promptoire':
            // Open the popup programmatically
            chrome.action.openPopup();
            break;
    }
});

// Optional: Track usage statistics
chrome.action.onClicked.addListener((tab) => {
    // This won't fire when popup is set, but keeping for future use
    console.log('Extension icon clicked');
});

// Handle context menu actions (future feature)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Message received:', request);
    
    switch (request.action) {
        case 'copyToClipboard':
            // Handle clipboard operations if needed
            sendResponse({ success: true });
            break;
        
        case 'openOptions':
            chrome.runtime.openOptionsPage();
            sendResponse({ success: true });
            break;
            
        default:
            sendResponse({ success: false, error: 'Unknown action' });
    }
    
    return true; // Keep message channel open for async response
});

// Handle tab updates (future feature for context-aware prompts)
chrome.tabs.onActivated.addListener((activeInfo) => {
    // Future: Could adapt prompts based on current website
    console.log('Tab activated:', activeInfo.tabId);
});

// Error handling
chrome.runtime.onSuspend.addListener(() => {
    console.log('Promptoire background script suspending');
});

// Keep service worker alive if needed (Chrome extensions can go dormant)
const keepAlive = () => {
    chrome.runtime.getPlatformInfo(() => {
        // This helps prevent the service worker from going dormant
    });
};

// Run keepAlive every 25 seconds (service workers go dormant after 30 seconds of inactivity)
setInterval(keepAlive, 25000); 