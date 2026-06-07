// Promptoire Chrome Extension - Main Popup Script

class Promptoire {
    constructor() {
        this.prompts = {};
        this.settings = {};
        this.filteredPrompts = {};
        
        this.init();
    }
    
    async init() {
        await this.loadData();
        this.setupEventListeners();
        this.renderPrompts();
        this.hideLoading();
    }
    
    async loadData() {
        try {
            // Load prompts and settings from Chrome storage
            const result = await chrome.storage.sync.get(['prompts', 'settings']);
            
            this.prompts = result.prompts || this.getDefaultPrompts();
            this.settings = result.settings || this.getDefaultSettings();
            
            // Save defaults if nothing exists
            if (!result.prompts) {
                await this.savePrompts();
            }
            if (!result.settings) {
                await this.saveSettings();
            }
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.prompts = this.getDefaultPrompts();
            this.settings = this.getDefaultSettings();
        }
    }
    
    getDefaultPrompts() {
        return {
            categories: {
                "Writing": {
                    prompts: [
                        {
                            title: "Email Draft",
                            prompt: "Draft a professional email about {subject} with a {tone} tone. Include clear action items and next steps."
                        }
                    ],
                    subcategories: {
                        "Content Creation": {
                            prompts: [
                                {
                                    title: "Blog Post Outline",
                                    prompt: "Write a detailed outline for a blog post about {topic} in a {tone} tone. Include:\n- Hook/introduction\n- 3-5 main points\n- Supporting details\n- Call to action"
                                },
                                {
                                    title: "Social Media Post",
                                    prompt: "Create an engaging social media post about {topic} for {platform}. Include relevant hashtags and keep it under {character_limit} characters."
                                }
                            ]
                        },
                        "Creative Writing": {
                            prompts: [
                                {
                                    title: "Creative Story",
                                    prompt: "Write a creative short story about {theme} in {genre} style. Make it engaging and around 500 words."
                                }
                            ]
                        }
                    }
                },
                "Coding": {
                    prompts: [
                        {
                            title: "Algorithm Explanation",
                            prompt: "Explain the {algorithm_name} algorithm in simple terms, including:\n- How it works\n- Time/space complexity\n- Use cases\n- Simple example with code"
                        }
                    ],
                    subcategories: {
                        "Python": {
                            prompts: [
                                {
                                    title: "Python Docstring",
                                    prompt: "Write a comprehensive Google-style docstring for this Python function:\n\n{code}\n\nInclude:\n- Brief description\n- Args with types\n- Returns with type\n- Raises (if applicable)\n- Example usage"
                                }
                            ]
                        },
                        "General": {
                            prompts: [
                                {
                                    title: "Code Review",
                                    prompt: "Review this code for best practices, potential bugs, performance improvements, and maintainability:\n\n{code}\n\nProvide specific suggestions and explain your reasoning."
                                },
                                {
                                    title: "Debug Help",
                                    prompt: "Help me debug this code that's producing {error_type}:\n\n{code}\n\nError message: {error_message}\n\nExplain what's wrong and how to fix it."
                                }
                            ]
                        }
                    }
                },
                "AI Tools": {
                    prompts: [
                        {
                            title: "System Prompt",
                            prompt: "You are a helpful AI assistant specialized in {domain}. Your responses should be {tone} and focus on {objective}. Always provide practical, actionable advice."
                        },
                        {
                            title: "Explain Concept",
                            prompt: "Explain {concept} in simple terms for someone who is {background}. Use {format} format and include practical examples."
                        }
                    ],
                    subcategories: {
                        "Prompt Engineering": {
                            prompts: [
                                {
                                    title: "Compare Options",
                                    prompt: "Compare {option1} vs {option2} for {use_case}. Consider:\n- Pros and cons\n- Performance\n- Cost\n- Ease of use\n- Best fit scenarios"
                                },
                                {
                                    title: "Step-by-Step Guide",
                                    prompt: "Create a detailed step-by-step guide for {task}. Assume the reader is {skill_level} and include:\n- Prerequisites\n- Clear numbered steps\n- Common pitfalls to avoid\n- Success criteria"
                                }
                            ]
                        }
                    }
                },
                "Research": {
                    prompts: [
                        {
                            title: "Topic Research",
                            prompt: "Research {topic} and provide:\n- Key concepts and definitions\n- Current trends and developments\n- Main challenges or controversies\n- Credible sources for further reading"
                        },
                        {
                            title: "Competitive Analysis",
                            prompt: "Analyze the competitive landscape for {industry/product}:\n- Main competitors\n- Their strengths/weaknesses\n- Market positioning\n- Opportunities for differentiation"
                        },
                        {
                            title: "Fact Check",
                            prompt: "Fact-check this claim: {statement}\n\nProvide:\n- Verification status (true/false/partially true)\n- Supporting evidence\n- Credible sources\n- Any important context or nuances"
                        }
                    ]
                }
            }
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
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const clearSearch = document.getElementById('clearSearch');
        
        searchInput.addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });
        
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchInput.value = '';
                this.handleSearch('');
            }
        });
        
        clearSearch.addEventListener('click', () => {
            searchInput.value = '';
            this.handleSearch('');
        });
        
        // Header buttons
        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.openSettings();
        });
        
        document.getElementById('addBtn').addEventListener('click', () => {
            this.openManager('add');
        });
        
        // Footer buttons
        document.getElementById('manageBtn').addEventListener('click', () => {
            this.openManager();
        });
        
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportPrompts();
        });
    }
    
    handleSearch(query) {
        const clearBtn = document.getElementById('clearSearch');
        
        if (query.trim()) {
            clearBtn.style.display = 'block';
            this.filteredPrompts = this.filterPrompts(query);
            // Expand all categories when searching to show results
            this.settings.collapsedCategories = [];
        } else {
            clearBtn.style.display = 'none';
            this.filteredPrompts = this.prompts;
        }
        
        this.renderPrompts();
    }
    
    filterPrompts(query) {
        const filtered = { categories: {} };
        const searchTerm = query.toLowerCase();
        
        Object.entries(this.prompts.categories).forEach(([categoryName, categoryData]) => {
            const filteredCategory = this._filterCategoryRecursive(categoryName, categoryData, searchTerm);
            if (filteredCategory) {
                filtered.categories[categoryName] = filteredCategory;
            }
        });
        
        return filtered;
    }
    
    _filterCategoryRecursive(categoryName, categoryData, searchTerm) {
        const categoryMatches = categoryName.toLowerCase().includes(searchTerm);
        let result = null;
        
        // Filter direct prompts
        const matchingPrompts = (categoryData.prompts || []).filter(prompt => 
            prompt.title.toLowerCase().includes(searchTerm) ||
            prompt.prompt.toLowerCase().includes(searchTerm)
        );
        
        // Filter subcategories recursively
        const matchingSubcategories = {};
        if (categoryData.subcategories) {
            Object.entries(categoryData.subcategories).forEach(([subName, subData]) => {
                const filteredSub = this._filterCategoryRecursive(subName, subData, searchTerm);
                if (filteredSub) {
                    matchingSubcategories[subName] = filteredSub;
                }
            });
        }
        
        // Include category if it matches, has matching prompts, or matching subcategories
        if (categoryMatches || matchingPrompts.length > 0 || Object.keys(matchingSubcategories).length > 0) {
            result = {};
            
            if (categoryMatches) {
                // If category name matches, include everything
                result.prompts = categoryData.prompts || [];
                result.subcategories = categoryData.subcategories || {};
            } else {
                // Otherwise include only matching parts
                if (matchingPrompts.length > 0) {
                    result.prompts = matchingPrompts;
                }
                if (Object.keys(matchingSubcategories).length > 0) {
                    result.subcategories = matchingSubcategories;
                }
            }
        }
        
        return result;
    }
    
    renderPrompts() {
        const promptsList = document.getElementById('promptsList');
        const emptyState = document.getElementById('emptyState');
        const searchInput = document.getElementById('searchInput');
        
        const currentPrompts = Object.keys(this.filteredPrompts).length > 0 ? this.filteredPrompts : this.prompts;
        
        // Clear existing content
        promptsList.innerHTML = '';
        
        // Check if we have any prompts to show
        const hasPrompts = Object.keys(currentPrompts.categories).some(category => 
            this._categoryHasContent(currentPrompts.categories[category])
        );
        
        if (!hasPrompts) {
            emptyState.style.display = 'block';
            promptsList.style.display = 'none';
            return;
        }
        
        emptyState.style.display = 'none';
        promptsList.style.display = 'block';
        
        // Initialize collapsed state for all categories on first load
        if (!this._initializedCollapse) {
            this.settings.collapsedCategories = Object.keys(currentPrompts.categories);
            this._initializedCollapse = true;
        }
        
        // Render categories and prompts
        Object.entries(currentPrompts.categories).forEach(([categoryName, categoryData]) => {
            if (!this._categoryHasContent(categoryData)) return;
            
            this._renderCategory(categoryName, categoryData, searchInput.value, 0, promptsList);
        });
    }
    
    _categoryHasContent(categoryData) {
        if (!categoryData) return false;
        if (categoryData.prompts && categoryData.prompts.length > 0) return true;
        if (categoryData.subcategories) {
            return Object.values(categoryData.subcategories).some(sub => this._categoryHasContent(sub));
        }
        return false;
    }
    
    _renderCategory(categoryName, categoryData, searchQuery, level, parentElement) {
        const categoryPath = `${categoryName}_level_${level}`;
        const isCollapsed = this.settings.collapsedCategories.includes(categoryPath);
        const indent = '  '.repeat(level);
        
        // Create category element
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category';
        if (isCollapsed) {
            categoryDiv.classList.add('collapsed');
        }
        
        // Category header
        const headerDiv = document.createElement('div');
        headerDiv.className = 'category-header';
        
        const expandIcon = isCollapsed ? '▶' : '▼';
        const promptCount = this._countPromptsInCategory(categoryData);
        
        headerDiv.innerHTML = `
            <span class="category-icon">${expandIcon}</span>
            <span>${indent}📁 ${categoryName}</span>
            <span class="category-count">(${promptCount})</span>
        `;
        
        headerDiv.addEventListener('click', () => {
            this._toggleCategory(categoryPath, categoryDiv);
        });
        
        categoryDiv.appendChild(headerDiv);
        
        // Category content (only show if not collapsed)
        if (!isCollapsed) {
            const contentDiv = document.createElement('div');
            contentDiv.className = 'category-content';
            
            // Render direct prompts
            if (categoryData.prompts) {
                categoryData.prompts.forEach((prompt, index) => {
                    const promptDiv = this._createPromptElement(prompt, categoryName, index, searchQuery, level + 1);
                    contentDiv.appendChild(promptDiv);
                });
            }
            
            // Render subcategories
            if (categoryData.subcategories) {
                Object.entries(categoryData.subcategories).forEach(([subName, subData]) => {
                    if (this._categoryHasContent(subData)) {
                        this._renderCategory(subName, subData, searchQuery, level + 1, contentDiv);
                    }
                });
            }
            
            categoryDiv.appendChild(contentDiv);
        }
        
        parentElement.appendChild(categoryDiv);
    }
    
    _countPromptsInCategory(categoryData) {
        let count = (categoryData.prompts || []).length;
        if (categoryData.subcategories) {
            Object.values(categoryData.subcategories).forEach(sub => {
                count += this._countPromptsInCategory(sub);
            });
        }
        return count;
    }
    
    _toggleCategory(categoryPath, categoryElement) {
        const isCollapsed = categoryElement.classList.contains('collapsed');
        
        if (isCollapsed) {
            categoryElement.classList.remove('collapsed');
            this.settings.collapsedCategories = this.settings.collapsedCategories.filter(cat => cat !== categoryPath);
        } else {
            categoryElement.classList.add('collapsed');
            this.settings.collapsedCategories.push(categoryPath);
        }
        
        this.saveSettings();
        this.renderPrompts(); // Re-render to update expand/collapse icons
    }
    
    _createPromptElement(prompt, categoryName, index, searchQuery, level) {
        const indent = '  '.repeat(level);
        
        const promptDiv = document.createElement('div');
        promptDiv.className = 'prompt-item';
        
        // Highlight search matches
        let title = prompt.title;
        let preview = prompt.prompt.substring(0, 100) + (prompt.prompt.length > 100 ? '...' : '');
        
        if (searchQuery) {
            const regex = new RegExp(`(${searchQuery})`, 'gi');
            title = title.replace(regex, '<span class="highlight">$1</span>');
            preview = preview.replace(regex, '<span class="highlight">$1</span>');
        }
        
        promptDiv.innerHTML = `
            <div class="prompt-title">
                <span class="prompt-icon">💡</span>
                <span>${indent}${title}</span>
            </div>
            ${this.settings.showPreviews ? `<div class="prompt-preview">${preview}</div>` : ''}
            <div class="prompt-actions">
                <button class="action-btn" title="Edit">✏️</button>
                <button class="action-btn" title="Copy">📋</button>
            </div>
        `;
        
        // Add click handler for copying
        promptDiv.addEventListener('click', (e) => {
            if (!e.target.classList.contains('action-btn')) {
                this.copyPrompt(prompt);
            }
        });
        
        // Add action button handlers
        const actionButtons = promptDiv.querySelectorAll('.action-btn');
        actionButtons[0].addEventListener('click', (e) => {
            e.stopPropagation();
            this.editPrompt(categoryName, index);
        });
        
        actionButtons[1].addEventListener('click', (e) => {
            e.stopPropagation();
            this.copyPrompt(prompt);
        });
        
        return promptDiv;
    }
    

    
    async copyPrompt(prompt) {
        try {
            // Use the modern Clipboard API
            await navigator.clipboard.writeText(prompt.prompt);
            this.showCopyNotification(prompt.title);
            
            // Auto-close popup if setting is enabled
            if (this.settings.autoClose) {
                setTimeout(() => window.close(), 1000);
            }
        } catch (error) {
            console.error('Failed to copy:', error);
            // Fallback for older browsers
            this.fallbackCopy(prompt.prompt);
            this.showCopyNotification(prompt.title);
        }
    }
    
    fallbackCopy(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }
    
    showCopyNotification(title) {
        const notification = document.getElementById('copyNotification');
        const textSpan = notification.querySelector('.copy-text');
        
        textSpan.textContent = `Copied: ${title}`;
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 2000);
    }
    
    hideLoading() {
        const loadingState = document.getElementById('loadingState');
        loadingState.style.display = 'none';
    }
    
    openSettings() {
        chrome.runtime.openOptionsPage();
    }
    
    openManager(mode = 'manage') {
        // Open the options page with a specific mode
        chrome.runtime.openOptionsPage();
    }
    
    editPrompt(categoryName, index) {
        // Store edit context and open options page
        chrome.storage.local.set({
            editContext: {
                category: categoryName,
                index: index,
                mode: 'edit'
            }
        });
        chrome.runtime.openOptionsPage();
    }
    
    async exportPrompts() {
        try {
            const dataStr = JSON.stringify(this.prompts, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            // Create download link
            const a = document.createElement('a');
            a.href = url;
            a.download = `promptoire-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            URL.revokeObjectURL(url);
            
            this.showCopyNotification('Exported prompts');
        } catch (error) {
            console.error('Export failed:', error);
        }
    }
    
    async savePrompts() {
        try {
            await chrome.storage.sync.set({ prompts: this.prompts });
        } catch (error) {
            console.error('Failed to save prompts:', error);
        }
    }
    
    async saveSettings() {
        try {
            await chrome.storage.sync.set({ settings: this.settings });
        } catch (error) {
            console.error('Failed to save settings:', error);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Promptoire();
});

// Handle keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Escape to close
    if (e.key === 'Escape') {
        window.close();
    }
    
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('searchInput').focus();
    }
}); 