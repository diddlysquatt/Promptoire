# Promptoire Chrome Extension 🧠

A powerful Chrome Extension for managing and accessing your LLM prompts. Works on **any device** with Chrome, including Chromebooks!

![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-brightgreen)
![Cross Platform](https://img.shields.io/badge/Platform-Cross_Platform-blue)
![Chrome Sync](https://img.shields.io/badge/Chrome-Sync_Enabled-orange)

## ✨ Features

- **🎯 Always Accessible**: Click the extension icon in Chrome toolbar
- **📁 Organized Categories**: Writing, Coding, AI Tools, Marketing, Research
- **🔍 Smart Search**: Real-time search with highlighting
- **📋 One-Click Copy**: Instant clipboard access
- **☁️ Chrome Sync**: Automatically syncs across all your devices
- **🎨 Professional UI**: Clean, dark theme with smooth animations
- **⚙️ Full Management**: Add, edit, delete prompts and categories
- **📱 Responsive**: Works on desktop, laptop, and Chromebook
- **🚀 Fast**: Lightweight and optimized for performance

## 🚀 Installation

### Method 1: Load as Developer Extension (Recommended)

1. **Download the Extension**:
   - Download or clone this repository
   - Navigate to the `chrome-extension` folder

2. **Open Chrome Extensions**:
   - Go to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right)

3. **Load the Extension**:
   - Click "Load unpacked"
   - Select the `chrome-extension` folder
   - Promptoire should appear in your extensions

4. **Pin to Toolbar**:
   - Click the puzzle piece icon in Chrome toolbar
   - Find Promptoire and click the pin icon

### Method 2: Chrome Web Store (Coming Soon)
*We're working on publishing to the Chrome Web Store for easier installation.*

## 🎮 How to Use

### 📋 **Quick Access**
1. Click the 🧠 icon in your Chrome toolbar
2. Browse categories or search for prompts
3. Click any prompt to copy it to clipboard
4. Paste wherever you need it!

### 📝 **Managing Prompts**
1. Click the 🧠 icon → Click "📝 Manage Prompts" 
2. **Add Categories**: Click "➕ Add" next to Categories
3. **Add Prompts**: Select a category → Click "➕ Add Prompt"
4. **Edit Prompts**: Click any prompt → Edit in the right panel
5. **Save Changes**: Click "💾 Save All" when done

### ⚙️ **Settings & Sync**
1. Open management page → Click "⚙️ Settings" tab
2. **Appearance**: Toggle previews and auto-close
3. **Sync**: Your prompts sync automatically across Chrome browsers
4. **Export/Import**: Backup or share your prompt library

## 🎯 **Keyboard Shortcuts**

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Focus search bar |
| `Escape` | Close popup |
| `Ctrl/Cmd + S` | Save all changes (in management) |

## 📁 Project Structure

```
chrome-extension/
├── manifest.json          # Extension configuration
├── popup.html             # Main popup interface
├── popup.css              # Popup styling
├── popup.js               # Popup functionality
├── options.html           # Management interface
├── options.css            # Management styling
├── options.js             # Management functionality
├── background.js          # Service worker
├── icons/                 # Extension icons
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── README.md             # This file
```

## 🔧 Development

### Prerequisites
- Chrome Browser
- Basic knowledge of HTML/CSS/JavaScript

### Local Development
1. Make changes to the files
2. Go to `chrome://extensions/`
3. Click the refresh icon on Promptoire
4. Test your changes

### Adding New Features
1. **Popup Features**: Edit `popup.html`, `popup.css`, `popup.js`
2. **Management Features**: Edit `options.html`, `options.css`, `options.js`
3. **Background Tasks**: Edit `background.js`
4. **Permissions**: Update `manifest.json`

## 🎨 Customization

### Adding Default Prompts
Edit the `getDefaultPrompts()` function in both `popup.js` and `options.js`:

```javascript
getDefaultPrompts() {
    return {
        categories: {
            "Your Category": [
                {
                    title: "Your Prompt Title",
                    prompt: "Your prompt text with {variables}"
                }
            ]
        }
    };
}
```

### Styling Changes
- **Popup**: Edit `popup.css`
- **Management**: Edit `options.css`
- **Colors**: Update CSS variables in `:root` sections

### Template Variables
Use `{variable}` format in prompts:
- `{topic}`, `{tone}`, `{code}`, `{theme}`, etc.
- Variables are automatically detected and highlighted

## ☁️ Chrome Sync

Your prompts automatically sync across:
- 💻 Desktop Chrome
- 💻 Laptop Chrome  
- 📱 Chrome on Android
- 📚 Chromebooks
- 🌐 Any device where you're signed into Chrome

**No account needed** - uses your Google Chrome sync!

## 📊 Storage Limits

- **Chrome Sync Storage**: 100KB total
- **Typical Usage**: ~20-50KB for 100+ prompts
- **Local Storage**: Unlimited (fallback)

## 🐛 Troubleshooting

### Extension Not Loading
- Check Chrome version (requires Chrome 88+)
- Ensure "Developer mode" is enabled
- Try reloading the extension

### Prompts Not Syncing
- Check if you're signed into Chrome
- Verify sync is enabled in Chrome settings
- Try "Force Sync" in the Sync tab

### Popup Not Opening
- Check if extension is pinned to toolbar
- Try disabling and re-enabling the extension
- Check Chrome extensions page for errors

### Storage Issues
- Extension uses Chrome's sync storage (limited to 100KB)
- Large prompt libraries may need local storage
- Export prompts as backup regularly

## 🔮 Roadmap

- [ ] **Chrome Web Store**: Official store listing
- [ ] **Context Menus**: Right-click to access prompts
- [ ] **Website Integration**: Inject prompts into text fields
- [ ] **Prompt Templates**: Advanced variable handling
- [ ] **Categories**: Drag & drop reordering
- [ ] **Themes**: Light/dark/custom themes
- [ ] **Statistics**: Usage tracking and analytics
- [ ] **AI Integration**: Built-in prompt testing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - feel free to use, modify, and distribute!

## 🙏 Credits

- Built with Chrome Extension Manifest V3
- Uses Chrome Storage API for sync
- Inspired by modern productivity tools
- Icons from system emoji fonts

---

**Enjoy your cross-platform prompt library!** 🚀

*Perfect for Chromebooks, laptops, desktops, and any device with Chrome*

## 🆚 Comparison: Desktop vs Chrome Extension

| Feature | Desktop Version | Chrome Extension |
|---------|----------------|------------------|
| **Platform** | Windows only | Any OS with Chrome |
| **Chromebook Support** | ❌ No | ✅ Yes |
| **Auto-Sync** | Manual files | ✅ Chrome Sync |
| **Installation** | Python required | One-click install |
| **Always On** | System tray | ✅ Browser toolbar |
| **Customization** | Full Python control | UI-based editing |
| **Performance** | Native speed | Web-based (fast) |

**Choose Chrome Extension if you:**
- Use Chromebooks
- Want automatic sync across devices
- Prefer browser-based tools
- Don't want to install Python

**Choose Desktop if you:**
- Need maximum customization
- Prefer native applications
- Want local file control
- Use Windows exclusively 