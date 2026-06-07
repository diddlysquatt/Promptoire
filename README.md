# Promptoire 🧠

A floating, minimal prompt library for Windows 11. Always-accessible launcher for your best LLM prompts with one-click copy-to-clipboard functionality.

![Promptoire Demo](https://img.shields.io/badge/Status-MVP_Ready-brightgreen)

## ✨ Features

- **🎯 Always on top**: Compact floating bar stays visible
- **🔍 Smart search**: Fuzzy search with optional in‑title highlight
- **📋 One‑click copy**: Click any prompt to copy immediately
- **🖱️ Drag to move**: Drag the bar or its handle to reposition
- **📌 Teleport to cursor**: Global hotkey moves the bar to your mouse
- **⌨️ Hotkeys**: Focus search (Ctrl+F), Editor (Ctrl+E), Settings (Ctrl+,), more
- **↩️ Undo delete**: Restore recently deleted items from the toast
- **🧺 Bulk edit**: Shift‑click/Shift‑Arrow multi‑select; move, delete, or re‑categorize
- **↕️ Sorting**: Move prompts/categories Up/Down to reorder
- **🕒 Backups**: One‑click JSON backups with timestamp
- **🔑 Stable IDs**: Content‑based IDs for reliable referencing
- **🎨 Themes**: Modern dark presets with customizable accents
- **🪟 Tray**: Optional system tray with quick actions

## 🚀 Quick Start

### Prerequisites
- Windows 11 (or Windows 10)
- Python 3.7+ installed

### Installation
Option A — Packaged (no Python required)
1. Download the ZIP from Releases
2. Unzip anywhere (e.g., `C:\Apps\Promptoire`)
3. Run `start_promptoire.bat`
   - If present, the script launches `dist\Promptoire.exe` (one‑file) or `dist\Promptoire\Promptoire.exe` (one‑dir), otherwise falls back to `pythonw promptoire.py`.

Option B — From source (for development)
1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run Promptoire:
   ```bash
   python promptoire.py
   ```

### First Use
1. A small brain emoji (🧠) will appear in the top-left corner
2. **Click** the brain to expand the prompt library
3. **Browse** categories and click any prompt to copy it
4. **Right-click** the brain for context menu (Edit Library, Exit)
5. **Drag** the brain icon to move it anywhere on screen

## 📚 How to Use

### Browsing Prompts
- Click the 🧠 to open the drawer
- Browse nested categories; use the search bar (Ctrl+F) for fuzzy search
- Click any prompt to copy it to the clipboard

### Adding Custom Prompts
1. Right‑click the 🧠 icon → "Edit Library" (full editor)
2. **Or manually edit** `prompts.json`:
   ```json
   {
     "categories": {
       "Your Category": [
         {
           "title": "Your Prompt Title",
           "prompt": "Your prompt text with {placeholders}"
         }
       ]
     }
   }
   ```

### Prompt Templates
Prompts support placeholders like `{topic}`, `{tone}`, `{code}`, etc.:
```
"Write a blog post about {topic} in a {tone} tone"
```
When you copy the prompt, you can manually replace the placeholders.

## 🎛️ Configuration

### Moving the Bar
- Drag the bar or its right‑side handle to reposition
- Use "Teleport to cursor" for instant reposition (set the hotkey in Settings)

### Customizing Prompts
Edit `prompts.json` to:
- Add new categories
- Create new prompts
- Modify existing prompts
- Use placeholder variables like `{topic}`, `{code}`, etc.

## 🏗️ Project Structure

```
Promptoire/
├── promptoire.py      # Main application
├── prompts.json       # Prompt library data
├── requirements.txt   # Python dependencies
├── README.md         # This file
└── run.bat           # Windows launcher (optional)
```

## 🔧 Advanced Usage

### Desktop Shortcut and Startup
- Create a desktop/startup shortcut to `start_promptoire.bat` or the packaged EXE:
  - One‑file: `dist\Promptoire.exe`
  - One‑dir: `dist\Promptoire\Promptoire.exe`
- To auto‑start with Windows: Win+R → `shell:startup` → place the shortcut there
- In‑app: Settings → "Desktop Shortcut" can create a `.lnk` on Windows

### Creating Executable
Preferred: use the provided spec (handles data, hooks, and optional deps)
```bash
pip install pyinstaller
pyinstaller Promptoire.spec
```

## 🎨 Customization Ideas

### Theme Colors
Edit via Settings (Ctrl+,) → "🎨 Color Scheme". Presets can be selected or choose "Custom" to tweak colors:

- background, foreground, accent
- button_bg, button_hover, border
- highlight, highlight_text, slider_trough
- category_bar, category_text, muted_text

Optional drawer background image:
- Toggle "Background Image (Drawer) → Enable"
- Set Image Path (file path or data URI)
- Fit: "cover" or "contain"

### Window Size
Adjust the drawer size:
```python
self.drawer.geometry("300x400")  # Width x Height
```

## 🪟 Run without console window
- Use `start_promptoire.bat` (or `run.bat`) to launch via `pythonw` when running from source
- The app is single‑instance and writes logs to `logs/promptoire.log`

## 📦 Build as EXE (no install required)
```bash
pip install -r requirements.txt
pyinstaller Promptoire.spec
```
- Outputs:
  - One‑file: `dist/Promptoire.exe`
  - One‑dir: `dist/Promptoire/Promptoire.exe`
- Tip: One‑dir often starts faster on some antivirus setups (UPX is disabled in the spec)

### Windows 11 Setup On Another PC
- Download the ZIP you ship (contains EXE, defaults, license, readme)
- Unzip anywhere (e.g., `C:\Apps\Promptoire`)
- Run `start_promptoire.bat` or the EXE (`dist\Promptoire.exe` or `dist\Promptoire\Promptoire.exe`)
- Optional auto‑start: Win+R → `shell:startup` → place a shortcut

## ⌨️ Shortcuts
- **Toggle Drawer**: configurable (shown in Help); click 🧠 to open/close
- **Focus Search**: Ctrl+F
- **Edit Prompts**: Ctrl+E
- **Settings**: Ctrl+,
- **Reload Prompts**: Ctrl+R
- **Help / Guide**: F1
- **Close Panel**: Esc / Ctrl+W
- **Teleport to Cursor (global)**: default Ctrl+Alt+X (Settings → Hotkeys)

## ⚙️ Performance tips
- Prefer the onedir build on systems with strict antivirus; first‑run of one‑file can be slower
- If Settings/UI feel sluggish:
  - Reduce font scale and bar scale
  - Disable search highlight in Settings
  - Avoid large background images
  - Keep your `prompts.json` reasonably sized; use Backups/Import‑Export to curate

## 🐛 Troubleshooting

### "Module not found" error
```bash
pip install pyperclip
```

### Brain emoji not showing
- Ensure your system supports Unicode emojis
- Or replace with a text character in the code: `text="P"`

### Drawer not appearing
- Try clicking directly on the brain emoji
- Ensure no other apps are blocking the window

## 🎯 Roadmap

- [ ] ✅ **MVP Complete**: Basic floating dock with prompts
- [ ] 🎨 **Visual Polish**: Better icons, animations, themes
- [ ] ⚙️ **Prompt Editor**: Built-in GUI for editing prompts
- [ ] 🔧 **Settings Panel**: Position saving, hotkeys, auto-start
- [ ] 📱 **Template Variables**: Auto-fill prompt placeholders
- [ ] 🌐 **Cloud Sync**: Backup/sync prompts across devices
- [ ] 🎪 **Favorites**: Star frequently used prompts
- [ ] 📊 **Usage Stats**: Track most-used prompts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - feel free to use, modify, and distribute!

## 🙏 Credits

- Built with Python + Tkinter for maximum compatibility
- Uses `pyperclip` for cross-platform clipboard support
- Inspired by modern launcher apps and prompt management tools

---

**Enjoy your floating prompt library!** 🚀

*Made with ❤️ for the AI-powered workflow* 