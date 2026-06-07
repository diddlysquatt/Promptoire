// Promptoire Chrome Extension - Options Page Script

class PromptoireManager {
    constructor() {
        this.prompts = {};
        this.settings = {};
        this.currentCategory = null;
        this.currentPromptIndex = null;
        this.unsavedChanges = false;
        this.categoryOrder = [];
        this.focusedCategoryName = null;
        this._drag = { active: false, fromName: null, overName: null, insertBefore: true };
        
        this.init();
    }
    
    async init() {
        this.showLoading(true);
        await this.loadData();
        this.setupEventListeners();
        this.renderUI();
        this.loadStats();
        this.checkSyncStatus();
        this.showLoading(false);
    }
    
    async loadData() {
        try {
            const result = await chrome.storage.sync.get(['prompts', 'settings']);
            
            this.prompts = result.prompts || this.getDefaultPrompts();
            this.settings = result.settings || this.getDefaultSettings();
            this.reconcileCategoryOrder();
            
            // Save defaults if nothing exists
            if (!result.prompts) {
                await this.savePrompts();
            }
            if (!result.settings) {
                await this.saveSettings();
            }
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.showNotification('Error loading data', 'error');
            this.prompts = this.getDefaultPrompts();
            this.settings = this.getDefaultSettings();
            this.reconcileCategoryOrder();
        }
    }
    
    getDefaultPrompts() {
        const categories = {
            "Writing": [
                {
                    title: "Blog Post Outline",
                    prompt: "Write a detailed outline for a blog post about {topic} in a {tone} tone. Include:\n- Hook/introduction\n- 3-5 main points\n- Supporting details\n- Call to action"
                },
                {
                    title: "Creative Story",
                    prompt: "Write a creative short story about {theme} in {genre} style. Make it engaging and around 500 words."
                },
                {
                    title: "Email Draft",
                    prompt: "Draft a professional email about {subject} with a {tone} tone. Include clear action items and next steps."
                }
            ],
            "Coding": [
                {
                    title: "Python Docstring",
                    prompt: "Write a comprehensive Google-style docstring for this Python function:\n\n{code}\n\nInclude:\n- Brief description\n- Args with types\n- Returns with type\n- Raises (if applicable)\n- Example usage"
                },
                {
                    title: "Code Review",
                    prompt: "Review this code for best practices, potential bugs, performance improvements, and maintainability:\n\n{code}\n\nProvide specific suggestions and explain your reasoning."
                }
            ],
            "AI Tools": [
                {
                    title: "System Prompt",
                    prompt: "You are a helpful AI assistant specialized in {domain}. Your responses should be {tone} and focus on {objective}. Always provide practical, actionable advice."
                },
                {
                    title: "Explain Concept",
                    prompt: "Explain {concept} in simple terms for someone who is {background}. Use {format} format and include practical examples."
                }
            ]
        };
        return {
            categories,
            categoryOrder: Object.keys(categories)
        };
    }
    
    getDefaultSettings() {
        return {
            theme: "dark",
            collapsedCategories: [],
            showPreviews: true,
            autoClose: true
        };
    }
    
    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Header actions
        document.getElementById('importBtn').addEventListener('click', () => this.importPrompts());
        document.getElementById('exportBtn').addEventListener('click', () => this.exportPrompts());
        document.getElementById('saveBtn').addEventListener('click', () => this.saveAll());
        
        // Category management
        document.getElementById('addCategoryBtn').addEventListener('click', () => this.showAddCategoryModal());
        
        // Prompt management
        document.getElementById('addPromptBtn').addEventListener('click', () => this.addNewPrompt());
        document.getElementById('savePromptBtn').addEventListener('click', () => this.saveCurrentPrompt());
        document.getElementById('deletePromptBtn').addEventListener('click', () => this.deleteCurrentPrompt());
        
        // Form inputs
        document.getElementById('promptTitle').addEventListener('input', () => this.markUnsaved());
        document.getElementById('promptContent').addEventListener('input', () => {
            this.markUnsaved();
            this.updateVariablesDisplay();
        });
        
        // Settings
        document.getElementById('showPreviews').addEventListener('change', (e) => {
            this.settings.showPreviews = e.target.checked;
            this.saveSettings();
        });
        
        document.getElementById('autoClose').addEventListener('change', (e) => {
            this.settings.autoClose = e.target.checked;
            this.saveSettings();
        });
        
        // Modal handling
        this.setupModalHandlers();
        
        // Sync actions
        document.getElementById('forceSyncBtn').addEventListener('click', () => this.forceSync());
        document.getElementById('clearSyncBtn').addEventListener('click', () => this.clearSyncData());
        document.getElementById('backupBtn').addEventListener('click', () => this.createBackup());
        document.getElementById('restoreFile').addEventListener('change', (e) => this.restoreBackup(e));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // Warn about unsaved changes
        window.addEventListener('beforeunload', (e) => {
            if (this.unsavedChanges) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    }
    
    setupModalHandlers() {
        // Add Category Modal
        const addCategoryModal = document.getElementById('addCategoryModal');
        const cancelCategoryBtn = document.getElementById('cancelCategoryBtn');
        const createCategoryBtn = document.getElementById('createCategoryBtn');
        const newCategoryInput = document.getElementById('newCategoryName');
        
        // Close modal handlers
        addCategoryModal.querySelector('.modal-close').addEventListener('click', () => {
            this.hideModal('addCategoryModal');
        });
        
        cancelCategoryBtn.addEventListener('click', () => {
            this.hideModal('addCategoryModal');
        });
        
        // Create category
        createCategoryBtn.addEventListener('click', () => {
            this.createCategory(newCategoryInput.value.trim());
        });
        
        // Enter key in input
        newCategoryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.createCategory(newCategoryInput.value.trim());
            }
        });
        
        // Click outside to close
        addCategoryModal.addEventListener('click', (e) => {
            if (e.target === addCategoryModal) {
                this.hideModal('addCategoryModal');
            }
        });
        
        // Notification close
        document.querySelector('.notification-close').addEventListener('click', () => {
            this.hideNotification();
        });
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        // Load tab-specific content
        if (tabName === 'settings') {
            this.loadSettingsTab();
        } else if (tabName === 'sync') {
            this.checkSyncStatus();
        }
    }
    
    renderUI() {
        this.renderCategories();
        this.renderPromptsList();
        this.clearEditor();
    }
    
    renderCategories() {
        const categoriesList = document.getElementById('categoriesList');
        categoriesList.innerHTML = '';
        const orderedNames = this.categoryOrder && this.categoryOrder.length > 0
            ? this.categoryOrder
            : Object.keys(this.prompts.categories);
        orderedNames.forEach((categoryName) => {
            const prompts = this.prompts.categories[categoryName];
            if (!prompts) return;
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'category-item';
            categoryDiv.setAttribute('draggable', 'true');
            categoryDiv.setAttribute('tabindex', '0');
            categoryDiv.setAttribute('role', 'option');
            categoryDiv.dataset.category = categoryName;
            categoryDiv.innerHTML = `
                <div class="category-name">
                    <span>📁</span>
                    <span>${categoryName}</span>
                </div>
                <span class="category-count">${prompts.length}</span>
            `;
            
            categoryDiv.addEventListener('click', () => {
                this.selectCategory(categoryName);
            });
            categoryDiv.addEventListener('focus', () => {
                this.focusedCategoryName = categoryName;
            });
            // Drag and drop events
            categoryDiv.addEventListener('dragstart', (e) => this.onCategoryDragStart(e, categoryName));
            categoryDiv.addEventListener('dragenter', (e) => this.onCategoryDragEnter(e, categoryName));
            categoryDiv.addEventListener('dragover', (e) => this.onCategoryDragOver(e, categoryName));
            categoryDiv.addEventListener('dragleave', (e) => this.onCategoryDragLeave(e, categoryName));
            categoryDiv.addEventListener('drop', (e) => this.onCategoryDrop(e, categoryName));
            categoryDiv.addEventListener('dragend', () => this.onCategoryDragEnd());
            
            categoriesList.appendChild(categoryDiv);
        });
    }
    
    selectCategory(categoryName) {
        this.currentCategory = categoryName;
        this.currentPromptIndex = null;
        
        // Update UI
        document.querySelectorAll('.category-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeEl = document.querySelector(`.category-item[data-category="${CSS.escape(categoryName)}"]`);
        if (activeEl) {
            activeEl.classList.add('active');
            this.focusedCategoryName = categoryName;
        }
        
        document.getElementById('promptsPanelTitle').textContent = `💡 ${categoryName}`;
        document.getElementById('addPromptBtn').disabled = false;
        
        this.renderPromptsList();
        this.clearEditor();
    }
    
    renderPromptsList() {
        const promptsList = document.getElementById('promptsList');
        
        if (!this.currentCategory) {
            promptsList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📝</div>
                    <div class="empty-text">Select a category to view prompts</div>
                </div>
            `;
            return;
        }
        
        const prompts = this.prompts.categories[this.currentCategory] || [];
        
        if (prompts.length === 0) {
            promptsList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📝</div>
                    <div class="empty-text">No prompts in this category</div>
                    <div class="empty-subtext">Click "Add Prompt" to create your first prompt</div>
                </div>
            `;
            return;
        }
        
        promptsList.innerHTML = '';
        
        prompts.forEach((prompt, index) => {
            const promptDiv = document.createElement('div');
            promptDiv.className = 'prompt-list-item';
            promptDiv.innerHTML = `
                <div class="prompt-list-title">
                    <span>💡</span>
                    <span>${prompt.title}</span>
                </div>
                <div class="prompt-list-preview">${prompt.prompt.substring(0, 80)}${prompt.prompt.length > 80 ? '...' : ''}</div>
            `;
            
            promptDiv.addEventListener('click', () => {
                this.selectPrompt(index);
            });
            
            promptsList.appendChild(promptDiv);
        });
    }
    
    selectPrompt(index) {
        this.currentPromptIndex = index;
        
        // Update UI
        document.querySelectorAll('.prompt-list-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const promptItems = document.querySelectorAll('.prompt-list-item');
        if (promptItems[index]) {
            promptItems[index].classList.add('active');
        }
        
        this.loadPromptInEditor();
    }
    
    loadPromptInEditor() {
        if (this.currentCategory === null || this.currentPromptIndex === null) {
            this.clearEditor();
            return;
        }
        
        const prompt = this.prompts.categories[this.currentCategory][this.currentPromptIndex];
        
        document.getElementById('editForm').style.display = 'block';
        document.getElementById('editEmpty').style.display = 'none';
        
        document.getElementById('promptTitle').value = prompt.title;
        document.getElementById('promptTitle').disabled = false;
        document.getElementById('promptContent').value = prompt.prompt;
        document.getElementById('promptContent').disabled = false;
        document.getElementById('savePromptBtn').disabled = false;
        document.getElementById('deletePromptBtn').disabled = false;
        
        this.updateVariablesDisplay();
        this.unsavedChanges = false;
    }
    
    clearEditor() {
        document.getElementById('editForm').style.display = 'none';
        document.getElementById('editEmpty').style.display = 'flex';
        
        document.getElementById('promptTitle').value = '';
        document.getElementById('promptTitle').disabled = true;
        document.getElementById('promptContent').value = '';
        document.getElementById('promptContent').disabled = true;
        document.getElementById('savePromptBtn').disabled = true;
        document.getElementById('deletePromptBtn').disabled = true;
        
        this.updateVariablesDisplay();
        this.unsavedChanges = false;
    }
    
    updateVariablesDisplay() {
        const content = document.getElementById('promptContent').value;
        const variablesDisplay = document.getElementById('variablesDisplay');
        
        // Detect placeholders consistent with desktop app:
        // {Identifier} where Identifier matches [A-Za-z_][A-Za-z0-9_]{0,31}
        // Ignore braces inside backtick code and regex quantifiers like {2} or {1,3}
        let masked = content
            .replace(/```[\s\S]*?```/g, m => m.replace(/\{/g, '\uFFF0').replace(/\}/g, '\uFFF1'))
            .replace(/`[^`]*`/g, m => m.replace(/\{/g, '\uFFF0').replace(/\}/g, '\uFFF1'))
            .replace(/\{\d+(?:,\d+)?\}/g, m => m.replace(/\{/g, '\uFFF0').replace(/\}/g, '\uFFF1'));
        const variables = masked.match(/\{([A-Za-z_][A-Za-z0-9_]{0,31})\}/g);
        
        if (variables && variables.length > 0) {
            const uniqueVars = [...new Set(variables)];
            variablesDisplay.innerHTML = uniqueVars.map(variable => 
                `<span class="variable-tag">${variable}</span>`
            ).join('');
        } else {
            variablesDisplay.innerHTML = '<span class="no-variables">No variables detected</span>';
        }
    }
    
    addNewPrompt() {
        if (!this.currentCategory) {
            this.showNotification('Please select a category first', 'warning');
            return;
        }
        
        const newPrompt = {
            title: 'New Prompt',
            prompt: 'Enter your prompt here...'
        };
        
        this.prompts.categories[this.currentCategory].push(newPrompt);
        const newIndex = this.prompts.categories[this.currentCategory].length - 1;
        
        this.renderPromptsList();
        this.selectPrompt(newIndex);
        
        // Focus and auto-highlight title field
        setTimeout(() => {
            const titleField = document.getElementById('promptTitle');
            titleField.focus();
            titleField.select();
        }, 100);
        
        this.markUnsaved();
    }
    
    async saveCurrentPrompt() {
        if (this.currentCategory === null || this.currentPromptIndex === null) {
            return;
        }
        
        const title = document.getElementById('promptTitle').value.trim();
        const content = document.getElementById('promptContent').value.trim();
        
        if (!title || !content) {
            this.showNotification('Title and content cannot be empty', 'error');
            return;
        }
        
        this.prompts.categories[this.currentCategory][this.currentPromptIndex] = {
            title: title,
            prompt: content
        };
        
        this.renderPromptsList();
        this.selectPrompt(this.currentPromptIndex); // Refresh selection
        
        try {
            await this.savePrompts();
            this.unsavedChanges = false;
            const saveBtn = document.getElementById('savePromptBtn');
            if (saveBtn) {
                saveBtn.textContent = '💾 Save';
            }
            this.showNotification('Prompt saved successfully');
        } catch (error) {
            this.showNotification('Error saving prompt', 'error');
        }
    }
    
    async deleteCurrentPrompt() {
        if (this.currentCategory === null || this.currentPromptIndex === null) {
            return;
        }
        
        const prompt = this.prompts.categories[this.currentCategory][this.currentPromptIndex];
        
        if (confirm(`Are you sure you want to delete "${prompt.title}"?`)) {
            this.prompts.categories[this.currentCategory].splice(this.currentPromptIndex, 1);
            
            this.renderCategories();
            this.renderPromptsList();
            this.clearEditor();
            
            await this.savePrompts();
            this.showNotification('Prompt deleted successfully');
        }
    }
    
    showAddCategoryModal() {
        const modal = document.getElementById('addCategoryModal');
        const input = document.getElementById('newCategoryName');
        
        input.value = '';
        modal.classList.add('show');
        
        setTimeout(() => input.focus(), 100);
    }
    
    hideModal(modalId) {
        document.getElementById(modalId).classList.remove('show');
    }
    
    async createCategory(name) {
        if (!name) {
            this.showNotification('Category name cannot be empty', 'error');
            return;
        }
        
        if (this.prompts.categories[name]) {
            this.showNotification('Category already exists', 'error');
            return;
        }
        
        this.prompts.categories[name] = [];
        if (!this.categoryOrder) this.categoryOrder = [];
        this.categoryOrder.push(name);
        this.prompts.categoryOrder = this.categoryOrder.slice();
        
        this.hideModal('addCategoryModal');
        this.renderCategories();
        await this.savePrompts();
        
        // Select the new category and prepare for adding a prompt
        this.selectCategory(name);
        
        // Auto-click add prompt to start editing
        setTimeout(() => {
            this.addNewPrompt();
        }, 200);
        
        this.showNotification(`✅ Category "${name}" created`);
    }
    
    markUnsaved() {
        this.unsavedChanges = true;
        
        // Visual indicator
        const saveBtn = document.getElementById('savePromptBtn');
        if (!saveBtn.disabled) {
            saveBtn.textContent = '💾 Save*';
        }
    }
    
    async saveAll() {
        try {
            if (this.currentPromptIndex !== null) {
                await this.saveCurrentPrompt();
            }
            
            await Promise.all([
                this.savePrompts(),
                this.saveSettings()
            ]);
            
            this.unsavedChanges = false;
            this.showNotification('All changes saved successfully');
        } catch (error) {
            console.error('Save error:', error);
            this.showNotification('Error saving changes', 'error');
        }
    }
    
    async savePrompts() {
        try {
            if (this.categoryOrder && Array.isArray(this.categoryOrder)) {
                this.prompts.categoryOrder = this.categoryOrder.slice();
            }
            await chrome.storage.sync.set({ prompts: this.prompts });
        } catch (error) {
            console.error('Failed to save prompts:', error);
            throw error;
        }
    }
    
    async saveSettings() {
        try {
            await chrome.storage.sync.set({ settings: this.settings });
        } catch (error) {
            console.error('Failed to save settings:', error);
            throw error;
        }
    }
    
    async exportPrompts() {
        try {
            const dataStr = JSON.stringify(this.prompts, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `promptoire-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            URL.revokeObjectURL(url);
            
            this.showNotification('Prompts exported successfully');
        } catch (error) {
            console.error('Export failed:', error);
            this.showNotification('Export failed', 'error');
        }
    }
    
    importPrompts() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            try {
                const text = await file.text();
                const data = JSON.parse(text);
                
                if (data.categories && typeof data.categories === 'object') {
                    if (confirm('This will replace all your current prompts. Are you sure?')) {
                        this.prompts = data;
                        this.reconcileCategoryOrder();
                        await this.savePrompts();
                        this.renderUI();
                        this.showNotification('Prompts imported successfully');
                    }
                } else {
                    this.showNotification('Invalid prompt file format', 'error');
                }
            } catch (error) {
                console.error('Import failed:', error);
                this.showNotification('Import failed', 'error');
            }
        };
        
        input.click();
    }
    
    loadSettingsTab() {
        document.getElementById('showPreviews').checked = this.settings.showPreviews;
        document.getElementById('autoClose').checked = this.settings.autoClose;
    }
    
    async loadStats() {
        const statsGrid = document.getElementById('statsGrid');
        
        // Calculate stats
        const totalCategories = Object.keys(this.prompts.categories).length;
        const totalPrompts = Object.values(this.prompts.categories).reduce((sum, prompts) => sum + prompts.length, 0);
        const avgPromptsPerCategory = totalCategories > 0 ? Math.round(totalPrompts / totalCategories) : 0;
        
        // Get storage usage
        let storageUsed = 0;
        try {
            const result = await chrome.storage.sync.getBytesInUse();
            storageUsed = Math.round((result / 1024) * 100) / 100; // KB
        } catch (error) {
            console.error('Failed to get storage usage:', error);
        }
        
        statsGrid.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${totalCategories}</div>
                <div class="stat-label">Categories</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${totalPrompts}</div>
                <div class="stat-label">Total Prompts</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${avgPromptsPerCategory}</div>
                <div class="stat-label">Avg per Category</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${storageUsed} KB</div>
                <div class="stat-label">Storage Used</div>
            </div>
        `;
    }
    
    async checkSyncStatus() {
        const syncStatus = document.getElementById('syncStatus');
        
        try {
            // Check if Chrome sync is enabled
            const isSignedIn = await new Promise((resolve) => {
                chrome.identity.getProfileUserInfo((userInfo) => {
                    resolve(!!userInfo.email);
                });
            });
            
            if (isSignedIn) {
                syncStatus.innerHTML = `
                    <span class="sync-indicator">✅</span>
                    <span>Chrome sync is enabled - your prompts are being synced</span>
                `;
            } else {
                syncStatus.innerHTML = `
                    <span class="sync-indicator">⚠️</span>
                    <span>Chrome sync is disabled - sign in to Chrome to sync your prompts</span>
                `;
            }
        } catch (error) {
            syncStatus.innerHTML = `
                <span class="sync-indicator">❌</span>
                <span>Unable to check sync status</span>
            `;
        }
    }
    
    async forceSync() {
        this.showLoading(true, 'Syncing...');
        
        try {
            // Force save to trigger sync
            await this.saveAll();
            
            setTimeout(() => {
                this.showLoading(false);
                this.showNotification('Sync completed successfully');
            }, 2000);
        } catch (error) {
            this.showLoading(false);
            this.showNotification('Sync failed', 'error');
        }
    }
    
    async clearSyncData() {
        if (confirm('This will delete all your synced prompts and settings. Are you sure?')) {
            try {
                await chrome.storage.sync.clear();
                this.prompts = this.getDefaultPrompts();
                this.settings = this.getDefaultSettings();
                this.renderUI();
                this.showNotification('Sync data cleared successfully');
            } catch (error) {
                this.showNotification('Failed to clear sync data', 'error');
            }
        }
    }
    
    createBackup() {
        this.exportPrompts(); // Same as export for now
    }
    
    restoreBackup(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        this.importPrompts(); // Same as import for now
        event.target.value = ''; // Reset file input
    }
    
    handleKeyboard(event) {
        // Ctrl/Cmd + S to save
        if ((event.ctrlKey || event.metaKey) && event.key === 's') {
            event.preventDefault();
            this.saveAll();
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            document.querySelectorAll('.modal.show').forEach(modal => {
                modal.classList.remove('show');
            });
        }

        // Alt + ArrowUp/ArrowDown to reorder focused category
        if (event.altKey && (event.key === 'ArrowUp' || event.key === 'ArrowDown')) {
            const categoriesList = document.getElementById('categoriesList');
            const isFocusInCategories = categoriesList.contains(document.activeElement);
            const targetName = isFocusInCategories && document.activeElement && document.activeElement.classList.contains('category-item')
                ? document.activeElement.dataset.category
                : (this.focusedCategoryName || this.currentCategory);
            if (targetName) {
                event.preventDefault();
                const delta = event.key === 'ArrowUp' ? -1 : 1;
                this.moveCategoryByOffset(targetName, delta, { preserveFocus: true });
            }
        }
    }
    
    showNotification(message, type = 'success') {
        const notification = document.getElementById('notification');
        const icon = notification.querySelector('.notification-icon');
        const text = notification.querySelector('.notification-text');
        
        // Set content
        text.textContent = message;
        
        // Set type
        notification.className = `notification ${type}`;
        
        // Set icon
        switch (type) {
            case 'success':
                icon.textContent = '✅';
                break;
            case 'error':
                icon.textContent = '❌';
                break;
            case 'warning':
                icon.textContent = '⚠️';
                break;
            default:
                icon.textContent = '✅';
        }
        
        // Show notification
        notification.classList.add('show');
        
        // Auto-hide after 4 seconds
        setTimeout(() => {
            this.hideNotification();
        }, 4000);
    }
    
    hideNotification() {
        document.getElementById('notification').classList.remove('show');
    }
    
    showLoading(show, text = 'Loading...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingText = overlay.querySelector('.loading-text');
        
        loadingText.textContent = text;
        
        if (show) {
            overlay.classList.add('show');
        } else {
            overlay.classList.remove('show');
        }
    }

    // ----- Category Order Helpers -----
    reconcileCategoryOrder() {
        const names = Object.keys(this.prompts.categories || {});
        let order = Array.isArray(this.prompts.categoryOrder) ? this.prompts.categoryOrder.slice() : [];
        // Remove duplicates and non-existing
        const seen = new Set();
        order = order.filter(name => names.includes(name) && !seen.has(name) && seen.add(name));
        // Append missing in original key order
        names.forEach(name => {
            if (!order.includes(name)) order.push(name);
        });
        this.categoryOrder = order;
        this.prompts.categoryOrder = order.slice();
    }

    moveCategoryByOffset(categoryName, delta, { preserveFocus = false } = {}) {
        const idx = this.categoryOrder.indexOf(categoryName);
        if (idx === -1) return;
        const newIdx = Math.max(0, Math.min(this.categoryOrder.length - 1, idx + delta));
        if (newIdx === idx) return;
        const order = this.categoryOrder.slice();
        order.splice(idx, 1);
        order.splice(newIdx, 0, categoryName);
        this.categoryOrder = order;
        this.prompts.categoryOrder = order.slice();
        this.renderCategories();
        // Restore selection highlight and focus
        if (this.currentCategory) {
            const activeEl = document.querySelector(`.category-item[data-category="${CSS.escape(this.currentCategory)}"]`);
            if (activeEl) activeEl.classList.add('active');
        }
        if (preserveFocus) {
            const focusEl = document.querySelector(`.category-item[data-category="${CSS.escape(categoryName)}"]`);
            if (focusEl) focusEl.focus();
        }
        // Persist immediately
        this.savePrompts();
    }

    onCategoryDragStart(event, fromName) {
        this._drag = { active: true, fromName, overName: null, insertBefore: true };
        event.dataTransfer.effectAllowed = 'move';
        // Needed for Firefox, harmless in Chrome
        event.dataTransfer.setData('text/plain', fromName);
        const list = document.getElementById('categoriesList');
        list.classList.add('dragging');
        const el = event.currentTarget;
        if (el) el.classList.add('dragging');
    }

    onCategoryDragEnter(event, overName) {
        event.preventDefault();
        if (!this._drag.active || overName === this._drag.fromName) return;
        this._drag.overName = overName;
    }

    onCategoryDragOver(event, overName) {
        event.preventDefault();
        if (!this._drag.active) return;
        const item = event.currentTarget;
        if (!item || overName === this._drag.fromName) return;
        const rect = item.getBoundingClientRect();
        const before = (event.clientY - rect.top) < rect.height / 2;
        this._drag.insertBefore = before;
        // Visual cue
        document.querySelectorAll('.category-item').forEach(el => {
            el.classList.remove('drop-before', 'drop-after');
        });
        item.classList.add(before ? 'drop-before' : 'drop-after');
    }

    onCategoryDragLeave(event, overName) {
        const item = event.currentTarget;
        if (item) item.classList.remove('drop-before', 'drop-after');
    }

    onCategoryDrop(event, targetName) {
        event.preventDefault();
        if (!this._drag.active) return;
        document.querySelectorAll('.category-item').forEach(el => {
            el.classList.remove('drop-before', 'drop-after');
        });
        const from = this._drag.fromName;
        const to = targetName;
        if (!from || !to || from === to) return this.onCategoryDragEnd();
        const fromIdx = this.categoryOrder.indexOf(from);
        let toIdx = this.categoryOrder.indexOf(to);
        if (fromIdx === -1 || toIdx === -1) return this.onCategoryDragEnd();
        const order = this.categoryOrder.slice();
        // Remove dragged item first
        order.splice(fromIdx, 1);
        // Adjust target index if it was after the removed index
        if (fromIdx < toIdx) {
            toIdx = toIdx - 1;
        }
        // Compute final insertion index
        let insertIdx = this._drag.insertBefore ? toIdx : toIdx + 1;
        const finalIdx = Math.max(0, Math.min(order.length, insertIdx));
        order.splice(finalIdx, 0, from);
        this.categoryOrder = order;
        this.prompts.categoryOrder = order.slice();
        this.renderCategories();
        // Restore selection and focus
        if (this.currentCategory) {
            const activeEl = document.querySelector(`.category-item[data-category="${CSS.escape(this.currentCategory)}"]`);
            if (activeEl) activeEl.classList.add('active');
        }
        const focusEl = document.querySelector(`.category-item[data-category="${CSS.escape(from)}"]`);
        if (focusEl) focusEl.focus();
        this.savePrompts();
        this.onCategoryDragEnd();
    }

    onCategoryDragEnd() {
        const list = document.getElementById('categoriesList');
        if (list) list.classList.remove('dragging');
        document.querySelectorAll('.category-item').forEach(el => {
            el.classList.remove('dragging', 'drop-before', 'drop-after');
        });
        this._drag = { active: false, fromName: null, overName: null, insertBefore: true };
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PromptoireManager();
}); 