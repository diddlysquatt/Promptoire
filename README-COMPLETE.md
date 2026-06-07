# Promptoire 🧠 - Complete Project

**The Ultimate Prompt Library for AI Enthusiasts**

![Desktop](https://img.shields.io/badge/Windows-Desktop-blue) ![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-brightgreen) ![Cross Platform](https://img.shields.io/badge/Platform-Cross_Platform-orange)

A powerful, always-accessible prompt management system available in **two versions**: a feature-rich Windows desktop app and a cross-platform Chrome Extension. Perfect for managing your LLM prompts, AI workflows, and creative templates!

---

## 🎯 **Choose Your Version**

| 🖥️ **Desktop Version** | 🌐 **Chrome Extension** |
|-------------------------|--------------------------|
| ✅ **Windows 10/11** | ✅ **Any OS with Chrome** |
| ✅ **Native Performance** | ✅ **Chromebook Support** |
| ✅ **Advanced Customization** | ✅ **Auto Chrome Sync** |
| ✅ **Local File Control** | ✅ **One-Click Install** |
| ✅ **System Tray Integration** | ✅ **Browser Integration** |
| ✅ **Python Extensibility** | ✅ **Universal Access** |

---

## 🖥️ **Desktop Version - Windows Promptoire**

### **🚀 Features**
- **🧠 Floating Brain Icon**: Always-on-top 32x32px window
- **📝 Full Prompt Editor**: Professional tree-view management interface
- **🎨 Complete Customization**: Icons, themes, colors, positions
- **🖱️ Scroll Wheel Support**: Smooth scrolling everywhere
- **🚀 Windows Auto-Start**: Boot with Windows (one-click setup)
- **💾 Position Memory**: Remembers where you place it
- **📁 File Management**: Direct JSON editing + GUI interface

### **📦 Installation**
```bash
# Install dependencies
pip install -r requirements.txt

# Run Promptoire
python promptoire.py
```

### **⚡ Quick Start**
1. **Run**: `python promptoire.py`
2. **Right-click** the 🧠 icon for menu
3. **Click "📝 Edit Prompts"** for management interface
4. **Click "⚙️ Settings"** for customization

### **🎨 Key Features**
- **Icon Customization**: Choose emojis or upload custom images
- **Advanced Editor**: Tree view with drag-and-drop (coming soon)
- **Theme Engine**: Full color customization
- **Windows Integration**: Auto-start + system tray
- **Scroll Support**: Mouse wheel everywhere

---

## 🌐 **Chrome Extension - Universal Promptoire**

### **🚀 Features**
- **🎯 Universal Access**: Works on **any device** with Chrome
- **📚 Chromebook Ready**: Perfect for Chrome OS users
- **☁️ Chrome Sync**: Automatic sync across all devices
- **📱 Responsive**: Desktop, laptop, tablet, Chromebook
- **🔍 Smart Search**: Real-time search with highlighting
- **📊 Analytics**: Usage statistics and storage monitoring

### **📦 Installation**
1. **Open Chrome** → Go to `chrome://extensions/`
2. **Enable "Developer mode"** (top-right toggle)
3. **Click "Load unpacked"** → Select `chrome-extension` folder
4. **Pin to toolbar** → Click puzzle icon → Pin Promptoire

### **⚡ Quick Start**
1. **Click** the 🧠 icon in Chrome toolbar
2. **Browse** categories or search prompts
3. **Click any prompt** to copy to clipboard
4. **Manage prompts** via "📝 Manage Prompts" button

### **🎨 Key Features**
- **Chrome Sync**: Syncs across ALL your Chrome browsers
- **Cross-Platform**: Windows, Mac, Linux, Chrome OS, Android
- **Professional UI**: Beautiful management interface
- **Export/Import**: Backup and share prompt libraries
- **Statistics**: Track usage and storage

---

## 📊 **Feature Comparison**

| Feature | Desktop | Chrome Extension |
|---------|---------|------------------|
| **🎯 Platform Support** | Windows Only | Any OS with Chrome |
| **📚 Chromebook Support** | ❌ No | ✅ Yes |
| **☁️ Auto-Sync** | Manual files | ✅ Chrome Sync |
| **🎨 Theme Customization** | ✅ Full control | Basic settings |
| **📝 Advanced Editor** | ✅ Tree view + more | Web-based editor |
| **🚀 Performance** | Native speed | Fast web-based |
| **📱 Mobile Access** | ❌ No | ✅ Chrome mobile |
| **🔧 Installation** | Python required | One-click |
| **💾 Local Control** | ✅ Full file access | Cloud-based |
| **🎮 Keyboard Shortcuts** | ✅ Global hotkeys | In-browser only |

---

## 🎯 **Which Version Should I Choose?**

### **🖥️ Choose Desktop If You:**
- Use **Windows 10/11** exclusively
- Want **maximum customization** and control
- Prefer **native desktop applications**
- Need **advanced prompt management**
- Want **local file storage** and control
- Love **system-level integration**

### **🌐 Choose Chrome Extension If You:**
- Use **Chromebooks** or multiple operating systems
- Want **automatic sync** across devices
- Prefer **browser-based** tools
- Need **universal access** from any Chrome browser
- Want **one-click installation**
- Share computers or work from multiple locations

### **🎉 Why Not Both?**
Many users run **both versions**:
- **Desktop** for primary Windows workstation
- **Chrome Extension** for Chromebooks, travel, other devices
- Export/import to keep them synchronized!

---

## 🚀 **Getting Started**

### **Desktop Version Setup**
```bash
# 1. Clone repository
git clone [repository-url]
cd "Promptoire"

# 2. Install dependencies  
pip install -r requirements.txt

# 3. Run Promptoire
python promptoire.py

# 4. Right-click brain icon → Settings/Edit Prompts
```

### **Chrome Extension Setup**
```bash
# 1. Navigate to chrome-extension folder
cd chrome-extension

# 2. Open Chrome Extensions
# Go to chrome://extensions/

# 3. Enable Developer Mode
# Toggle "Developer mode" in top-right

# 4. Load Extension
# Click "Load unpacked" → Select chrome-extension folder

# 5. Pin to Toolbar
# Click puzzle icon → Pin Promptoire
```

---

## 📁 **Project Structure**

```
Promptoire/
├── promptoire.py              # 🖥️ Desktop app (main)
├── requirements.txt           # 🖥️ Python dependencies
├── prompts.json              # 🖥️ Desktop prompts data
├── settings.json             # 🖥️ Desktop settings
├── run.bat                   # 🖥️ Windows launcher
├── start_promptoire.bat      # 🖥️ Auto-start script
├── README.md                 # 🖥️ Desktop documentation
├── chrome-extension/         # 🌐 Chrome Extension
│   ├── manifest.json         # 🌐 Extension config
│   ├── popup.html/.css/.js   # 🌐 Main popup
│   ├── options.html/.css/.js # 🌐 Management interface
│   ├── background.js         # 🌐 Service worker
│   ├── icons/               # 🌐 Extension icons
│   └── README.md            # 🌐 Extension docs
└── README-COMPLETE.md       # 📚 This file
```

---

## 🎨 **Sample Prompts Included**

Both versions come with **professional prompt templates**:

### **📝 Writing**
- Blog Post Outlines
- Creative Stories  
- Professional Emails
- Social Media Posts

### **💻 Coding**
- Python Docstrings
- Code Reviews
- Debug Assistance
- Algorithm Explanations

### **🤖 AI Tools**
- System Prompts
- Concept Explanations
- Option Comparisons
- Step-by-Step Guides

### **📈 Marketing**
- Product Descriptions
- Ad Copy Creation
- Value Propositions

### **🔍 Research**
- Topic Research
- Competitive Analysis
- Fact Checking

---

## 🔧 **Advanced Usage**

### **Desktop Customization**
```python
# Edit promptoire.py for advanced features
# Customize themes, add new shortcuts
# Integrate with other Python tools
```

### **Chrome Extension Development**
```javascript
// Edit popup.js or options.js
// Add new features, modify UI
// Integrate with web APIs
```

### **Cross-Platform Workflow**
1. **Primary Setup**: Use Desktop version as main library
2. **Mobile/Travel**: Access via Chrome Extension
3. **Sync**: Export from Desktop → Import to Extension
4. **Backup**: Regular exports from both versions

---

## 🎯 **Use Cases**

### **Content Creators**
- Blog post templates
- Social media prompts
- Video script outlines
- SEO content frameworks

### **Software Developers**
- Code documentation templates
- Code review checklists
- Git commit message formats
- Technical writing prompts

### **AI Researchers**
- System prompt templates
- Fine-tuning instructions
- Evaluation frameworks
- Research methodologies

### **Business Professionals**
- Email templates
- Meeting agenda formats
- Proposal structures
- Report outlines

### **Students & Educators**
- Essay structures
- Research frameworks
- Study guides
- Assignment templates

---

## 🛣️ **Roadmap**

### **Desktop Version 2.0**
- [ ] Global hotkeys
- [ ] Drag & drop reordering
- [ ] Plugin system
- [ ] AI integration
- [ ] Multiple themes
- [ ] Advanced search

### **Chrome Extension 2.0**
- [ ] Chrome Web Store listing
- [ ] Context menu integration
- [ ] Website text field injection
- [ ] Advanced template variables
- [ ] Usage analytics
- [ ] Collaboration features

### **Cross-Platform**
- [ ] Mobile app versions
- [ ] Cloud sync service
- [ ] Team collaboration
- [ ] AI-powered suggestions
- [ ] Marketplace for prompts

---

## 🤝 **Contributing**

We welcome contributions to both versions!

### **Desktop (Python)**
1. Fork repository
2. Create feature branch
3. Test on Windows 10/11
4. Submit pull request

### **Chrome Extension (Web)**
1. Fork repository
2. Edit chrome-extension files
3. Test in Chrome/Chromebook
4. Submit pull request

---

## 📄 **License**

MIT License - Use freely for personal and commercial projects!

---

## 🙏 **Acknowledgments**

- **Desktop**: Built with Python + Tkinter for maximum Windows integration
- **Chrome Extension**: Built with modern web standards for universal access
- **Design**: Inspired by modern productivity tools and AI workflows
- **Community**: Thanks to all users and contributors!

---

**🚀 Ready to supercharge your AI workflow?**

**Download both versions and never lose track of your perfect prompts again!**

*Choose Desktop for power, choose Chrome Extension for portability, choose both for the ultimate experience!* 🧠✨ 