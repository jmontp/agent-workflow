/**
 * Project Manager - Handle project tab bar UI and project switching
 * 
 * This module provides the visual project switching interface for the Discord web visualizer.
 * It manages project tabs, mobile dropdown, and coordinates with Agent B's backend APIs.
 */

class ProjectManager {
    constructor() {
        this.projects = new Map();
        this.activeProject = 'default';
        this.contextMenu = null;
        this.isInitialized = false;
        
        // Initialize the project manager
        this.initialize();
    }
    
    /**
     * Initialize the project manager
     */
    async initialize() {
        console.log('🚀 Initializing ProjectManager...');
        
        try {
            await this.loadProjects();
            this.setupEventHandlers();
            this.setupKeyboardShortcuts();
            this.updateProjectDisplay();
            this.isInitialized = true;
            
            console.log('✅ ProjectManager initialized successfully');
        } catch (error) {
            if (window.ErrorManager) {
                window.ErrorManager.handleError(error, {
                    component: 'ProjectManager',
                    operation: 'initialization'
                });
            } else {
                console.error('❌ Failed to initialize ProjectManager:', error);
            }
        }
    }
    
    /**
     * Load projects from backend API
     */
    async loadProjects() {
        try {
            // Try to load from API first
            const response = await fetch('/api/projects');
            
            if (response.ok) {
                const data = await response.json();
                this.projects.clear();
                
                // Add projects from API
                if (data.projects && Array.isArray(data.projects)) {
                    data.projects.forEach(project => {
                        this.projects.set(project.id, {
                            id: project.id,
                            name: project.name,
                            icon: project.icon || '📁',
                            status: project.status || 'idle',
                            path: project.path,
                            lastActivity: project.lastActivity
                        });
                    });
                }
                
                // Set active project
                if (data.activeProject) {
                    this.activeProject = data.activeProject;
                }
            } else {
                throw new Error(`API response: ${response.status}`);
            }
        } catch (error) {
            console.warn('⚠️ Could not load projects from API, using defaults:', error.message);
            
            // Fallback to default project
            this.projects.clear();
            this.projects.set('default', {
                id: 'default',
                name: 'Default Project',
                icon: '📁',
                status: 'idle',
                path: '/default',
                lastActivity: new Date().toISOString()
            });
            this.activeProject = 'default';
        }
    }
    
    /**
     * Setup event handlers for project tab interactions
     */
    setupEventHandlers() {
        const tabList = document.getElementById('project-tab-list');
        const mobileSelect = document.getElementById('mobile-project-select');
        
        // Tab click handlers
        if (tabList) {
            tabList.addEventListener('click', (e) => {
                const tab = e.target.closest('.project-tab');
                if (tab && !tab.classList.contains('active')) {
                    const projectId = tab.getAttribute('data-project');
                    this.switchProject(projectId);
                }
            });
            
            // Right-click context menu
            tabList.addEventListener('contextmenu', (e) => {
                const tab = e.target.closest('.project-tab');
                if (tab) {
                    e.preventDefault();
                    const projectId = tab.getAttribute('data-project');
                    this.showContextMenu(e.clientX, e.clientY, projectId);
                }
            });
        }
        
        // Mobile select handler
        if (mobileSelect) {
            mobileSelect.addEventListener('change', (e) => {
                const projectId = e.target.value;
                if (projectId && projectId !== this.activeProject) {
                    this.switchProject(projectId);
                }
            });
        }
        
        // Control button handlers
        this.setupControlHandlers();
        
        // Scroll indicators for tab list
        this.setupScrollIndicators();
        
        // Close context menu on outside click
        document.addEventListener('click', () => {
            this.hideContextMenu();
        });
        
        // Handle window resize for responsive behavior
        window.addEventListener('resize', () => {
            this.updateScrollIndicators();
        });
    }
    
    /**
     * Setup control button handlers
     */
    setupControlHandlers() {
        const addProjectBtn = document.getElementById('add-project-btn');
        const projectSettingsBtn = document.getElementById('project-settings-btn');
        const globalViewBtn = document.getElementById('global-view-btn');
        const mobileAddBtn = document.getElementById('mobile-add-project');
        const mobileSettingsBtn = document.getElementById('mobile-project-settings');
        
        if (addProjectBtn) {
            addProjectBtn.addEventListener('click', () => {
                this.showAddProjectDialog();
            });
        }
        
        if (projectSettingsBtn) {
            projectSettingsBtn.addEventListener('click', () => {
                this.showProjectSettings(this.activeProject);
            });
        }
        
        if (globalViewBtn) {
            globalViewBtn.addEventListener('click', () => {
                this.toggleGlobalView();
            });
        }
        
        if (mobileAddBtn) {
            mobileAddBtn.addEventListener('click', () => {
                this.showAddProjectDialog();
            });
        }
        
        if (mobileSettingsBtn) {
            mobileSettingsBtn.addEventListener('click', () => {
                this.showProjectSettings(this.activeProject);
            });
        }
    }
    
    /**
     * Setup scroll indicators for tab overflow
     */
    setupScrollIndicators() {
        const tabList = document.getElementById('project-tab-list');
        if (!tabList) return;
        
        tabList.addEventListener('scroll', () => {
            this.updateScrollIndicators();
        });
        
        // Initial update
        setTimeout(() => {
            this.updateScrollIndicators();
        }, 100);
    }
    
    /**
     * Update scroll indicators based on scroll position
     */
    updateScrollIndicators() {
        const tabList = document.getElementById('project-tab-list');
        if (!tabList) return;
        
        const { scrollLeft, scrollWidth, clientWidth } = tabList;
        
        // Check if scrollable
        const isScrollable = scrollWidth > clientWidth;
        const canScrollLeft = scrollLeft > 0;
        const canScrollRight = scrollLeft < (scrollWidth - clientWidth - 1);
        
        if (isScrollable && canScrollLeft) {
            tabList.classList.add('scrollable-left');
        } else {
            tabList.classList.remove('scrollable-left');
        }
        
        if (isScrollable && canScrollRight) {
            tabList.classList.add('scrollable-right');
        } else {
            tabList.classList.remove('scrollable-right');
        }
    }
    
    /**
     * Setup keyboard shortcuts for project management
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Only handle shortcuts when not typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 't': // Ctrl+T - New project
                        e.preventDefault();
                        this.showAddProjectDialog();
                        break;
                        
                    case ',': // Ctrl+, - Project settings
                        e.preventDefault();
                        this.showProjectSettings(this.activeProject);
                        break;
                        
                    case 'g': // Ctrl+G - Global view
                        e.preventDefault();
                        this.toggleGlobalView();
                        break;
                }
            }
            
            // Alt + number for project switching
            if (e.altKey && e.key >= '1' && e.key <= '9') {
                e.preventDefault();
                const projectIndex = parseInt(e.key) - 1;
                const projectIds = Array.from(this.projects.keys());
                if (projectIds[projectIndex]) {
                    this.switchProject(projectIds[projectIndex]);
                }
            }
        });
    }
    
    /**
     * Switch to a different project
     */
    async switchProject(projectId) {
        if (!this.projects.has(projectId) || projectId === this.activeProject) {
            return;
        }
        
        console.log(`🔄 Switching to project: ${projectId}`);
        
        try {
            // Notify backend of project switch
            const response = await fetch('/api/projects/switch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ projectId })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.activeProject = projectId;
                    this.updateProjectDisplay();
                    this.updatePageTitle();
                    this.notifyProjectSwitch(projectId);
                    
                    console.log(`✅ Successfully switched to project: ${projectId}`);
                } else {
                    throw new Error(result.error || 'Switch failed');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('❌ Failed to switch project:', error);
            
            // Still update UI optimistically for better UX
            this.activeProject = projectId;
            this.updateProjectDisplay();
            this.updatePageTitle();
            this.notifyProjectSwitch(projectId);
            
            // Show error message
            this.showErrorMessage(`Failed to switch project: ${error.message}`);
        }
    }
    
    /**
     * Add a new project
     */
    async addProject(projectData) {
        console.log('➕ Adding new project:', projectData);
        
        try {
            const response = await fetch('/api/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(projectData)
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // Add to local projects
                    this.projects.set(result.project.id, result.project);
                    this.updateProjectDisplay();
                    
                    // Switch to new project
                    await this.switchProject(result.project.id);
                    
                    console.log(`✅ Successfully added project: ${result.project.id}`);
                    this.showSuccessMessage(`Project "${result.project.name}" added successfully`);
                } else {
                    throw new Error(result.error || 'Add failed');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('❌ Failed to add project:', error);
            this.showErrorMessage(`Failed to add project: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Remove a project
     */
    async removeProject(projectId) {
        if (projectId === 'default') {
            this.showErrorMessage('Cannot remove the default project');
            return;
        }
        
        console.log(`🗑️ Removing project: ${projectId}`);
        
        try {
            const response = await fetch(`/api/projects/${projectId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // Remove from local projects
                    this.projects.delete(projectId);
                    
                    // Switch to default if removing active project
                    if (projectId === this.activeProject) {
                        await this.switchProject('default');
                    }
                    
                    this.updateProjectDisplay();
                    
                    console.log(`✅ Successfully removed project: ${projectId}`);
                    this.showSuccessMessage(`Project removed successfully`);
                } else {
                    throw new Error(result.error || 'Remove failed');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('❌ Failed to remove project:', error);
            this.showErrorMessage(`Failed to remove project: ${error.message}`);
        }
    }
    
    /**
     * Update project status
     */
    updateProjectStatus(projectId, status) {
        if (this.projects.has(projectId)) {
            const project = this.projects.get(projectId);
            project.status = status;
            project.lastActivity = new Date().toISOString();
            
            // Update UI
            this.updateProjectDisplay();
            
            console.log(`📊 Updated project ${projectId} status to: ${status}`);
        }
    }
    
    /**
     * Update project display in UI
     */
    updateProjectDisplay() {
        this.renderProjectTabs();
        this.renderMobileSelector();
        this.updateActiveTabIndicator();
    }
    
    /**
     * Render project tabs
     */
    renderProjectTabs() {
        const tabList = document.getElementById('project-tab-list');
        if (!tabList) return;
        
        // Clear existing tabs
        tabList.innerHTML = '';
        
        // Create tabs for each project
        this.projects.forEach((project) => {
            const tab = this.createProjectTab(project);
            tabList.appendChild(tab);
        });
        
        // Update scroll indicators
        setTimeout(() => {
            this.updateScrollIndicators();
        }, 50);
    }
    
    /**
     * Create a project tab element using DOM utilities
     */
    createProjectTab(project) {
        const tab = DOMUtils.createElement('div', {
            class: `project-tab ${project.id === this.activeProject ? 'active' : ''}`,
            'data-project': project.id,
            title: `${project.name} (${project.status})`
        }, `
            <span class="project-icon">${project.icon}</span>
            <span class="project-name">${project.name}</span>
            <span class="project-status-dot" data-status="${project.status}"></span>
        `);
        
        // Add entrance animation
        DOMUtils.addClass(tab, 'tab-enter');
        setTimeout(() => {
            DOMUtils.removeClass(tab, 'tab-enter');
        }, 300);
        
        return tab;
    }
    
    /**
     * Render mobile project selector
     */
    renderMobileSelector() {
        const mobileSelect = document.getElementById('mobile-project-select');
        if (!mobileSelect) return;
        
        // Clear existing options
        mobileSelect.innerHTML = '';
        
        // Add options for each project
        this.projects.forEach((project) => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = `${project.icon} ${project.name}`;
            option.selected = project.id === this.activeProject;
            mobileSelect.appendChild(option);
        });
    }
    
    /**
     * Update active tab indicator
     */
    updateActiveTabIndicator() {
        const tabs = document.querySelectorAll('.project-tab');
        tabs.forEach(tab => {
            const projectId = tab.getAttribute('data-project');
            if (projectId === this.activeProject) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
    }
    
    /**
     * Update page title based on active project
     */
    updatePageTitle() {
        const project = this.projects.get(this.activeProject);
        if (project) {
            document.title = `${project.name} - TDD State Visualizer`;
        }
    }
    
    /**
     * Show context menu for project tab
     */
    showContextMenu(x, y, projectId) {
        this.hideContextMenu();
        
        const project = this.projects.get(projectId);
        if (!project) return;
        
        const menu = document.createElement('div');
        menu.className = 'project-tab-context-menu';
        menu.style.left = `${x}px`;
        menu.style.top = `${y}px`;
        
        const isDefault = projectId === 'default';
        const isActive = projectId === this.activeProject;
        
        menu.innerHTML = `
            <div class="context-menu-item" data-action="switch" ${isActive ? 'style="display:none"' : ''}>
                <span>🔄</span>
                <span>Switch to Project</span>
            </div>
            <div class="context-menu-item" data-action="settings">
                <span>⚙️</span>
                <span>Project Settings</span>
            </div>
            <div class="context-menu-item" data-action="refresh">
                <span>🔄</span>
                <span>Refresh Status</span>
            </div>
            <div class="context-menu-divider"></div>
            <div class="context-menu-item" data-action="duplicate">
                <span>📋</span>
                <span>Duplicate Project</span>
            </div>
            <div class="context-menu-item destructive" data-action="remove" ${isDefault ? 'style="display:none"' : ''}>
                <span>🗑️</span>
                <span>Remove Project</span>
            </div>
        `;
        
        // Add event handlers
        menu.addEventListener('click', (e) => {
            e.stopPropagation();
            const item = e.target.closest('.context-menu-item');
            if (item) {
                const action = item.getAttribute('data-action');
                this.handleContextMenuAction(action, projectId);
            }
        });
        
        document.body.appendChild(menu);
        this.contextMenu = menu;
        
        // Position menu to stay within viewport
        const menuRect = menu.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        if (menuRect.right > viewportWidth) {
            menu.style.left = `${x - menuRect.width}px`;
        }
        
        if (menuRect.bottom > viewportHeight) {
            menu.style.top = `${y - menuRect.height}px`;
        }
        
        menu.style.display = 'block';
    }
    
    /**
     * Hide context menu
     */
    hideContextMenu() {
        if (this.contextMenu) {
            this.contextMenu.remove();
            this.contextMenu = null;
        }
    }
    
    /**
     * Handle context menu actions
     */
    async handleContextMenuAction(action, projectId) {
        this.hideContextMenu();
        
        switch (action) {
            case 'switch':
                await this.switchProject(projectId);
                break;
                
            case 'settings':
                this.showProjectSettings(projectId);
                break;
                
            case 'refresh':
                await this.refreshProjectStatus(projectId);
                break;
                
            case 'duplicate':
                await this.duplicateProject(projectId);
                break;
                
            case 'remove':
                if (confirm(`Are you sure you want to remove the project "${this.projects.get(projectId)?.name}"?`)) {
                    await this.removeProject(projectId);
                }
                break;
        }
    }
    
    /**
     * Show add project dialog
     */
    showAddProjectDialog() {
        const dialog = this.createAddProjectDialog();
        document.body.appendChild(dialog);
    }
    
    /**
     * Create add project dialog
     */
    createAddProjectDialog() {
        const dialog = document.createElement('div');
        dialog.className = 'modal';
        dialog.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>➕ Add New Project</h3>
                    <button class="btn btn-small close-btn">×</button>
                </div>
                <div class="modal-body">
                    <form id="add-project-form">
                        <div class="form-group">
                            <label for="project-name">Project Name:</label>
                            <input type="text" id="project-name" required maxlength="50" placeholder="My Project">
                        </div>
                        <div class="form-group">
                            <label for="project-path">Project Path:</label>
                            <input type="text" id="project-path" required placeholder="/path/to/project">
                        </div>
                        <div class="form-group">
                            <label for="project-icon">Icon:</label>
                            <select id="project-icon">
                                <option value="📁">📁 Folder</option>
                                <option value="🚀">🚀 Rocket</option>
                                <option value="⚙️">⚙️ Gear</option>
                                <option value="🎯">🎯 Target</option>
                                <option value="💡">💡 Bulb</option>
                                <option value="🔧">🔧 Wrench</option>
                                <option value="📊">📊 Chart</option>
                                <option value="🌟">🌟 Star</option>
                            </select>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="submit" form="add-project-form" class="btn btn-primary">Add Project</button>
                    <button type="button" class="btn btn-secondary cancel-btn">Cancel</button>
                </div>
            </div>
        `;
        
        // Event handlers
        const closeBtn = dialog.querySelector('.close-btn');
        const cancelBtn = dialog.querySelector('.cancel-btn');
        const form = dialog.querySelector('#add-project-form');
        
        const closeDialog = () => {
            dialog.remove();
        };
        
        closeBtn.addEventListener('click', closeDialog);
        cancelBtn.addEventListener('click', closeDialog);
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) closeDialog();
        });
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const projectData = {
                name: formData.get('project-name') || document.getElementById('project-name').value,
                path: formData.get('project-path') || document.getElementById('project-path').value,
                icon: document.getElementById('project-icon').value
            };
            
            try {
                await this.addProject(projectData);
                closeDialog();
            } catch (error) {
                // Error already handled in addProject
            }
        });
        
        // Focus first input
        setTimeout(() => {
            const nameInput = dialog.querySelector('#project-name');
            if (nameInput) nameInput.focus();
        }, 100);
        
        return dialog;
    }
    
    /**
     * Show project settings
     */
    showProjectSettings(projectId) {
        console.log(`⚙️ Showing settings for project: ${projectId}`);
        const project = this.projects.get(projectId);
        if (!project) {
            this.showErrorMessage('Project not found');
            return;
        }
        
        const dialog = this.createProjectSettingsDialog(project);
        document.body.appendChild(dialog);
    }
    
    /**
     * Create project settings dialog
     */
    createProjectSettingsDialog(project) {
        const dialog = document.createElement('div');
        dialog.className = 'modal project-settings-modal';
        dialog.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h3>⚙️ Project Settings - ${project.name}</h3>
                    <button class="btn btn-small close-btn">×</button>
                </div>
                <div class="modal-body">
                    <div class="settings-tabs">
                        <button class="settings-tab active" data-tab="general">General</button>
                        <button class="settings-tab" data-tab="workflow">Workflow</button>
                        <button class="settings-tab" data-tab="agents">Agents</button>
                        <button class="settings-tab" data-tab="notifications">Notifications</button>
                        <button class="settings-tab" data-tab="advanced">Advanced</button>
                    </div>
                    
                    <div class="settings-content">
                        <!-- General Settings -->
                        <div class="settings-panel active" data-panel="general">
                            <form id="project-settings-form">
                                <div class="form-row">
                                    <div class="form-group">
                                        <label for="settings-project-name">Project Name:</label>
                                        <input type="text" id="settings-project-name" value="${project.name}" required maxlength="50">
                                    </div>
                                    <div class="form-group">
                                        <label for="settings-project-icon">Icon:</label>
                                        <div class="icon-selector">
                                            <select id="settings-project-icon">
                                                <option value="📁" ${project.icon === '📁' ? 'selected' : ''}>📁 Folder</option>
                                                <option value="🚀" ${project.icon === '🚀' ? 'selected' : ''}>🚀 Rocket</option>
                                                <option value="⚙️" ${project.icon === '⚙️' ? 'selected' : ''}>⚙️ Gear</option>
                                                <option value="🎯" ${project.icon === '🎯' ? 'selected' : ''}>🎯 Target</option>
                                                <option value="💡" ${project.icon === '💡' ? 'selected' : ''}>💡 Bulb</option>
                                                <option value="🔧" ${project.icon === '🔧' ? 'selected' : ''}>🔧 Wrench</option>
                                                <option value="📊" ${project.icon === '📊' ? 'selected' : ''}>📊 Chart</option>
                                                <option value="🌟" ${project.icon === '🌟' ? 'selected' : ''}>🌟 Star</option>
                                                <option value="🎨" ${project.icon === '🎨' ? 'selected' : ''}>🎨 Art</option>
                                                <option value="🏗️" ${project.icon === '🏗️' ? 'selected' : ''}>🏗️ Construction</option>
                                            </select>
                                            <div class="icon-preview">${project.icon}</div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="form-group">
                                    <label for="settings-project-path">Project Path:</label>
                                    <div class="path-input-group">
                                        <input type="text" id="settings-project-path" value="${project.path}" required>
                                        <button type="button" class="btn btn-small browse-btn" title="Browse for folder">📁</button>
                                    </div>
                                </div>
                                
                                <div class="form-row">
                                    <div class="form-group">
                                        <label for="settings-project-status">Status:</label>
                                        <select id="settings-project-status">
                                            <option value="idle" ${project.status === 'idle' ? 'selected' : ''}>Idle</option>
                                            <option value="active" ${project.status === 'active' ? 'selected' : ''}>Active</option>
                                            <option value="paused" ${project.status === 'paused' ? 'selected' : ''}>Paused</option>
                                            <option value="error" ${project.status === 'error' ? 'selected' : ''}>Error</option>
                                            <option value="complete" ${project.status === 'complete' ? 'selected' : ''}>Complete</option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <label for="settings-project-priority">Priority:</label>
                                        <select id="settings-project-priority">
                                            <option value="low" ${project.priority === 'low' ? 'selected' : ''}>Low</option>
                                            <option value="normal" ${project.priority === 'normal' ? 'selected' : ''}>Normal</option>
                                            <option value="high" ${project.priority === 'high' ? 'selected' : ''}>High</option>
                                            <option value="urgent" ${project.priority === 'urgent' ? 'selected' : ''}>Urgent</option>
                                        </select>
                                    </div>
                                </div>
                                
                                <div class="form-group">
                                    <label for="settings-project-description">Description:</label>
                                    <textarea id="settings-project-description" rows="3" placeholder="Project description...">${project.description || ''}</textarea>
                                </div>
                                
                                <div class="form-group">
                                    <label for="settings-project-tags">Tags:</label>
                                    <div class="tags-input-container">
                                        <input type="text" id="settings-project-tags" placeholder="Enter tags separated by commas" value="${(project.tags || []).join(', ')}">
                                        <div class="tags-preview"></div>
                                    </div>
                                </div>
                            </form>
                        </div>
                        
                        <!-- Workflow Settings -->
                        <div class="settings-panel" data-panel="workflow">
                            <div class="form-group">
                                <label>Workflow Mode:</label>
                                <div class="radio-group">
                                    <label class="radio-option">
                                        <input type="radio" name="workflow-mode" value="blocking" ${project.workflowMode === 'blocking' ? 'checked' : ''}>
                                        <span class="radio-label">🛑 Blocking (Requires approval)</span>
                                    </label>
                                    <label class="radio-option">
                                        <input type="radio" name="workflow-mode" value="partial" ${project.workflowMode === 'partial' ? 'checked' : ''}>
                                        <span class="radio-label">⚡ Partial (Quarantined execution)</span>
                                    </label>
                                    <label class="radio-option">
                                        <input type="radio" name="workflow-mode" value="autonomous" ${project.workflowMode === 'autonomous' ? 'checked' : ''}>
                                        <span class="radio-label">🤖 Autonomous (Full automation)</span>
                                    </label>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label>TDD Settings:</label>
                                <div class="checkbox-group">
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.tddEnabled ? 'checked' : ''}>
                                        <span class="checkbox-label">Enable TDD workflows</span>
                                    </label>
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.autoTestRun ? 'checked' : ''}>
                                        <span class="checkbox-label">Auto-run tests on code changes</span>
                                    </label>
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.requireTestCoverage ? 'checked' : ''}>
                                        <span class="checkbox-label">Require minimum test coverage</span>
                                    </label>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="settings-test-coverage">Min Test Coverage (%):</label>
                                    <input type="number" id="settings-test-coverage" min="0" max="100" value="${project.minTestCoverage || 80}">
                                </div>
                                <div class="form-group">
                                    <label for="settings-max-cycles">Max TDD Cycles:</label>
                                    <input type="number" id="settings-max-cycles" min="1" max="10" value="${project.maxTddCycles || 3}">
                                </div>
                            </div>
                        </div>
                        
                        <!-- Agent Settings -->
                        <div class="settings-panel" data-panel="agents">
                            <div class="agent-config-grid">
                                <div class="agent-config-card">
                                    <h4>🎨 Design Agent</h4>
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.agents?.design?.enabled !== false ? 'checked' : ''}>
                                        <span class="checkbox-label">Enabled</span>
                                    </label>
                                    <div class="form-group">
                                        <label>Creativity Level:</label>
                                        <input type="range" min="1" max="10" value="${project.agents?.design?.creativity || 5}" class="slider">
                                    </div>
                                </div>
                                
                                <div class="agent-config-card">
                                    <h4>💻 Code Agent</h4>
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.agents?.code?.enabled !== false ? 'checked' : ''}>
                                        <span class="checkbox-label">Enabled</span>
                                    </label>
                                    <div class="form-group">
                                        <label>Code Style:</label>
                                        <select>
                                            <option value="minimal">Minimal</option>
                                            <option value="standard" selected>Standard</option>
                                            <option value="verbose">Verbose</option>
                                        </select>
                                    </div>
                                </div>
                                
                                <div class="agent-config-card">
                                    <h4>🧪 QA Agent</h4>
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.agents?.qa?.enabled !== false ? 'checked' : ''}>
                                        <span class="checkbox-label">Enabled</span>
                                    </label>
                                    <div class="form-group">
                                        <label>Test Rigor:</label>
                                        <select>
                                            <option value="basic">Basic</option>
                                            <option value="thorough" selected>Thorough</option>
                                            <option value="exhaustive">Exhaustive</option>
                                        </select>
                                    </div>
                                </div>
                                
                                <div class="agent-config-card">
                                    <h4>📊 Data Agent</h4>
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.agents?.data?.enabled !== false ? 'checked' : ''}>
                                        <span class="checkbox-label">Enabled</span>
                                    </label>
                                    <div class="form-group">
                                        <label>Analysis Depth:</label>
                                        <select>
                                            <option value="summary">Summary</option>
                                            <option value="detailed" selected>Detailed</option>
                                            <option value="comprehensive">Comprehensive</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Notifications Settings -->
                        <div class="settings-panel" data-panel="notifications">
                            <div class="form-group">
                                <label>Notification Preferences:</label>
                                <div class="checkbox-group">
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.notifications?.stateChanges !== false ? 'checked' : ''}>
                                        <span class="checkbox-label">State changes</span>
                                    </label>
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.notifications?.errors !== false ? 'checked' : ''}>
                                        <span class="checkbox-label">Errors and failures</span>
                                    </label>
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.notifications?.completions !== false ? 'checked' : ''}>
                                        <span class="checkbox-label">Task completions</span>
                                    </label>
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.notifications?.approvals ? 'checked' : ''}>
                                        <span class="checkbox-label">Approval requests</span>
                                    </label>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="settings-notification-interval">Notification Interval:</label>
                                    <select id="settings-notification-interval">
                                        <option value="immediate" ${project.notificationInterval === 'immediate' ? 'selected' : ''}>Immediate</option>
                                        <option value="5min" ${project.notificationInterval === '5min' ? 'selected' : ''}>Every 5 minutes</option>
                                        <option value="15min" ${project.notificationInterval === '15min' ? 'selected' : ''}>Every 15 minutes</option>
                                        <option value="hourly" ${project.notificationInterval === 'hourly' ? 'selected' : ''}>Hourly</option>
                                        <option value="daily" ${project.notificationInterval === 'daily' ? 'selected' : ''}>Daily</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label for="settings-quiet-hours">Quiet Hours:</label>
                                    <input type="text" id="settings-quiet-hours" placeholder="22:00-08:00" value="${project.quietHours || ''}">
                                </div>
                            </div>
                        </div>
                        
                        <!-- Advanced Settings -->
                        <div class="settings-panel" data-panel="advanced">
                            <div class="form-group">
                                <label>Resource Limits:</label>
                                <div class="resource-limits">
                                    <div class="form-row">
                                        <div class="form-group">
                                            <label for="settings-cpu-limit">CPU Limit (%):</label>
                                            <input type="number" id="settings-cpu-limit" min="10" max="100" value="${project.resourceLimits?.cpu || 50}">
                                        </div>
                                        <div class="form-group">
                                            <label for="settings-memory-limit">Memory Limit (MB):</label>
                                            <input type="number" id="settings-memory-limit" min="100" max="8192" value="${project.resourceLimits?.memory || 1024}">
                                        </div>
                                    </div>
                                    <div class="form-row">
                                        <div class="form-group">
                                            <label for="settings-timeout">Timeout (seconds):</label>
                                            <input type="number" id="settings-timeout" min="30" max="3600" value="${project.timeout || 300}">
                                        </div>
                                        <div class="form-group">
                                            <label for="settings-max-concurrent">Max Concurrent Tasks:</label>
                                            <input type="number" id="settings-max-concurrent" min="1" max="10" value="${project.maxConcurrentTasks || 2}">
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label>Git Integration:</label>
                                <div class="checkbox-group">
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.gitIntegration?.enabled !== false ? 'checked' : ''}>
                                        <span class="checkbox-label">Enable git integration</span>
                                    </label>
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.gitIntegration?.autoCommit ? 'checked' : ''}>
                                        <span class="checkbox-label">Auto-commit changes</span>
                                    </label>
                                    <label class="checkbox-option">
                                        <input type="checkbox" ${project.gitIntegration?.createPRs ? 'checked' : ''}>
                                        <span class="checkbox-label">Create pull requests</span>
                                    </label>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label for="settings-git-branch">Default Branch:</label>
                                <input type="text" id="settings-git-branch" value="${project.gitIntegration?.defaultBranch || 'main'}" placeholder="main">
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <div class="footer-actions">
                        <button type="button" class="btn btn-danger remove-project-btn">🗑️ Remove Project</button>
                        <div class="main-actions">
                            <button type="submit" form="project-settings-form" class="btn btn-primary">💾 Save Changes</button>
                            <button type="button" class="btn btn-secondary cancel-btn">Cancel</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.setupProjectSettingsHandlers(dialog, project);
        return dialog;
    }
    
    /**
     * Setup event handlers for project settings dialog
     */
    setupProjectSettingsHandlers(dialog, project) {
        const closeBtn = dialog.querySelector('.close-btn');
        const cancelBtn = dialog.querySelector('.cancel-btn');
        const removeBtn = dialog.querySelector('.remove-project-btn');
        const form = dialog.querySelector('#project-settings-form');
        const iconSelect = dialog.querySelector('#settings-project-icon');
        const iconPreview = dialog.querySelector('.icon-preview');
        const tagsInput = dialog.querySelector('#settings-project-tags');
        const tagsPreview = dialog.querySelector('.tags-preview');
        
        // Modal close handlers
        const closeDialog = () => dialog.remove();
        closeBtn.addEventListener('click', closeDialog);
        cancelBtn.addEventListener('click', closeDialog);
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) closeDialog();
        });
        
        // Tab switching
        const tabs = dialog.querySelectorAll('.settings-tab');
        const panels = dialog.querySelectorAll('.settings-panel');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetPanel = tab.getAttribute('data-tab');
                
                // Update active tab
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                // Update active panel
                panels.forEach(p => p.classList.remove('active'));
                dialog.querySelector(`[data-panel="${targetPanel}"]`).classList.add('active');
            });
        });
        
        // Icon preview update
        iconSelect.addEventListener('change', (e) => {
            iconPreview.textContent = e.target.value;
        });
        
        // Tags preview update
        const updateTagsPreview = () => {
            const tags = tagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag);
            tagsPreview.innerHTML = tags.map(tag => `<span class="tag">${tag}</span>`).join('');
        };
        
        tagsInput.addEventListener('input', updateTagsPreview);
        updateTagsPreview(); // Initial update
        
        // Remove project handler
        if (removeBtn) {
            removeBtn.addEventListener('click', async () => {
                if (project.id === 'default') {
                    this.showErrorMessage('Cannot remove the default project');
                    return;
                }
                
                const confirmed = await this.showConfirmDialog(
                    'Remove Project',
                    `Are you sure you want to remove "${project.name}"?`,
                    'This action cannot be undone.'
                );
                
                if (confirmed) {
                    closeDialog();
                    await this.removeProject(project.id);
                }
            });
        }
        
        // Form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.saveProjectSettings(project.id, form, closeDialog);
        });
        
        // Focus first input
        setTimeout(() => {
            const nameInput = dialog.querySelector('#settings-project-name');
            if (nameInput) nameInput.focus();
        }, 100);
    }
    
    /**
     * Save project settings
     */
    async saveProjectSettings(projectId, form, closeCallback) {
        const formData = new FormData(form);
        const settings = {
            name: document.getElementById('settings-project-name').value,
            icon: document.getElementById('settings-project-icon').value,
            path: document.getElementById('settings-project-path').value,
            status: document.getElementById('settings-project-status').value,
            priority: document.getElementById('settings-project-priority').value,
            description: document.getElementById('settings-project-description').value,
            tags: document.getElementById('settings-project-tags').value.split(',').map(tag => tag.trim()).filter(tag => tag),
            workflowMode: document.querySelector('input[name="workflow-mode"]:checked')?.value,
            // Add other settings as needed
        };
        
        try {
            const response = await fetch(`/api/projects/${projectId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // Update local project data
                    const project = this.projects.get(projectId);
                    Object.assign(project, settings);
                    
                    this.updateProjectDisplay();
                    this.showSuccessMessage('Project settings saved successfully');
                    closeCallback();
                } else {
                    throw new Error(result.error || 'Save failed');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Failed to save project settings:', error);
            this.showErrorMessage(`Failed to save settings: ${error.message}`);
        }
    }
    
    /**
     * Toggle global view
     */
    toggleGlobalView() {
        console.log('🌐 Toggling global view');
        const globalDialog = this.createGlobalViewDialog();
        document.body.appendChild(globalDialog);
    }
    
    /**
     * Create global view dialog with project search and management
     */
    createGlobalViewDialog() {
        const dialog = document.createElement('div');
        dialog.className = 'modal global-view-modal';
        dialog.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h3>🌐 Global Project View</h3>
                    <div class="header-controls">
                        <button class="btn btn-small refresh-btn" title="Refresh all projects">🔄</button>
                        <button class="btn btn-small close-btn">×</button>
                    </div>
                </div>
                <div class="modal-body">
                    <div class="global-view-toolbar">
                        <div class="search-container">
                            <input type="text" id="project-search" placeholder="Search projects..." class="search-input">
                            <button class="search-btn" title="Search">🔍</button>
                        </div>
                        <div class="filter-container">
                            <select id="status-filter" class="filter-select">
                                <option value="">All Statuses</option>
                                <option value="idle">Idle</option>
                                <option value="active">Active</option>
                                <option value="paused">Paused</option>
                                <option value="error">Error</option>
                                <option value="complete">Complete</option>
                            </select>
                            <select id="priority-filter" class="filter-select">
                                <option value="">All Priorities</option>
                                <option value="low">Low</option>
                                <option value="normal">Normal</option>
                                <option value="high">High</option>
                                <option value="urgent">Urgent</option>
                            </select>
                        </div>
                        <div class="view-controls">
                            <button class="view-toggle active" data-view="grid" title="Grid View">⊞</button>
                            <button class="view-toggle" data-view="list" title="List View">☰</button>
                        </div>
                    </div>
                    
                    <div class="projects-container">
                        <div id="projects-grid" class="projects-grid">
                            <!-- Projects will be populated here -->
                        </div>
                    </div>
                    
                    <div class="bulk-actions">
                        <div class="bulk-actions-controls">
                            <label class="checkbox-option">
                                <input type="checkbox" id="select-all-projects">
                                <span class="checkbox-label">Select All</span>
                            </label>
                            <div class="selected-count">0 selected</div>
                        </div>
                        <div class="bulk-actions-buttons">
                            <button class="btn btn-secondary" id="bulk-start-btn" disabled>▶️ Start Selected</button>
                            <button class="btn btn-secondary" id="bulk-pause-btn" disabled>⏸️ Pause Selected</button>
                            <button class="btn btn-secondary" id="bulk-stop-btn" disabled>⏹️ Stop Selected</button>
                            <button class="btn btn-danger" id="bulk-remove-btn" disabled>🗑️ Remove Selected</button>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <div class="footer-stats">
                        <span class="stat">Total: <span id="total-projects">0</span></span>
                        <span class="stat">Active: <span id="active-projects">0</span></span>
                        <span class="stat">Idle: <span id="idle-projects">0</span></span>
                    </div>
                    <div class="footer-actions">
                        <button class="btn btn-primary" id="add-project-global-btn">➕ Add Project</button>
                        <button class="btn btn-secondary" id="close-global-btn">Close</button>
                    </div>
                </div>
            </div>
        `;
        
        this.setupGlobalViewHandlers(dialog);
        this.populateGlobalView(dialog);
        return dialog;
    }
    
    /**
     * Setup global view dialog handlers
     */
    setupGlobalViewHandlers(dialog) {
        const closeBtn = dialog.querySelector('.close-btn');
        const closeGlobalBtn = dialog.querySelector('#close-global-btn');
        const refreshBtn = dialog.querySelector('.refresh-btn');
        const searchInput = dialog.querySelector('#project-search');
        const statusFilter = dialog.querySelector('#status-filter');
        const priorityFilter = dialog.querySelector('#priority-filter');
        const viewToggles = dialog.querySelectorAll('.view-toggle');
        const selectAllCheckbox = dialog.querySelector('#select-all-projects');
        const addProjectBtn = dialog.querySelector('#add-project-global-btn');
        
        // Close handlers
        const closeDialog = () => dialog.remove();
        closeBtn.addEventListener('click', closeDialog);
        closeGlobalBtn.addEventListener('click', closeDialog);
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) closeDialog();
        });
        
        // Refresh handler
        refreshBtn.addEventListener('click', async () => {
            await this.loadProjects();
            this.populateGlobalView(dialog);
            this.showSuccessMessage('Projects refreshed');
        });
        
        // Search and filter handlers
        const applyFilters = () => {
            this.filterProjects(dialog, {
                search: searchInput.value,
                status: statusFilter.value,
                priority: priorityFilter.value
            });
        };
        
        searchInput.addEventListener('input', applyFilters);
        statusFilter.addEventListener('change', applyFilters);
        priorityFilter.addEventListener('change', applyFilters);
        
        // View toggle handlers
        viewToggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                const view = toggle.getAttribute('data-view');
                viewToggles.forEach(t => t.classList.remove('active'));
                toggle.classList.add('active');
                this.switchProjectView(dialog, view);
            });
        });
        
        // Select all handler
        selectAllCheckbox.addEventListener('change', (e) => {
            const checkboxes = dialog.querySelectorAll('.project-checkbox');
            checkboxes.forEach(cb => {
                cb.checked = e.target.checked;
            });
            this.updateBulkActions(dialog);
        });
        
        // Add project handler
        addProjectBtn.addEventListener('click', () => {
            closeDialog();
            this.showAddProjectDialog();
        });
        
        // Bulk action handlers
        this.setupBulkActionHandlers(dialog);
    }
    
    /**
     * Populate global view with projects
     */
    populateGlobalView(dialog) {
        const projectsGrid = dialog.querySelector('#projects-grid');
        const totalProjectsSpan = dialog.querySelector('#total-projects');
        const activeProjectsSpan = dialog.querySelector('#active-projects');
        const idleProjectsSpan = dialog.querySelector('#idle-projects');
        
        // Clear existing projects
        projectsGrid.innerHTML = '';
        
        // Count projects by status
        let totalProjects = 0;
        let activeProjects = 0;
        let idleProjects = 0;
        
        // Create project cards
        this.projects.forEach((project) => {
            const projectCard = this.createProjectCard(project);
            projectsGrid.appendChild(projectCard);
            
            totalProjects++;
            if (project.status === 'active') activeProjects++;
            if (project.status === 'idle') idleProjects++;
        });
        
        // Update stats
        totalProjectsSpan.textContent = totalProjects;
        activeProjectsSpan.textContent = activeProjects;
        idleProjectsSpan.textContent = idleProjects;
        
        // Setup project card handlers
        this.setupProjectCardHandlers(dialog);
    }
    
    /**
     * Create a project card for global view
     */
    createProjectCard(project) {
        const card = document.createElement('div');
        card.className = `project-card ${project.status}`;
        card.setAttribute('data-project-id', project.id);
        card.setAttribute('data-status', project.status);
        card.setAttribute('data-priority', project.priority || 'normal');
        
        const lastActivity = project.lastActivity ? new Date(project.lastActivity).toLocaleString() : 'Never';
        const description = project.description || 'No description';
        const tags = project.tags || [];
        
        card.innerHTML = `
            <div class="project-card-header">
                <label class="checkbox-option">
                    <input type="checkbox" class="project-checkbox" data-project-id="${project.id}">
                    <span class="checkbox-label"></span>
                </label>
                <div class="project-icon-large">${project.icon}</div>
                <div class="project-status-indicator" data-status="${project.status}" title="Status: ${project.status}"></div>
            </div>
            <div class="project-card-body">
                <h4 class="project-title">${project.name}</h4>
                <p class="project-description">${description}</p>
                <div class="project-path" title="${project.path}">📁 ${project.path}</div>
                <div class="project-tags">
                    ${tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
            </div>
            <div class="project-card-footer">
                <div class="project-meta">
                    <span class="last-activity">🕐 ${lastActivity}</span>
                    <span class="priority-badge ${project.priority || 'normal'}">${project.priority || 'normal'}</span>
                </div>
                <div class="project-actions">
                    <button class="btn btn-small switch-btn" title="Switch to project" data-project-id="${project.id}">🔄</button>
                    <button class="btn btn-small settings-btn" title="Project settings" data-project-id="${project.id}">⚙️</button>
                    <button class="btn btn-small status-btn" title="Change status" data-project-id="${project.id}">⚡</button>
                </div>
            </div>
        `;
        
        return card;
    }
    
    /**
     * Setup project card event handlers
     */
    setupProjectCardHandlers(dialog) {
        const projectCards = dialog.querySelectorAll('.project-card');
        
        projectCards.forEach(card => {
            const projectId = card.getAttribute('data-project-id');
            const switchBtn = card.querySelector('.switch-btn');
            const settingsBtn = card.querySelector('.settings-btn');
            const statusBtn = card.querySelector('.status-btn');
            const checkbox = card.querySelector('.project-checkbox');
            
            // Switch project
            switchBtn.addEventListener('click', async () => {
                dialog.remove();
                await this.switchProject(projectId);
            });
            
            // Open settings
            settingsBtn.addEventListener('click', () => {
                dialog.remove();
                this.showProjectSettings(projectId);
            });
            
            // Change status
            statusBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showStatusMenu(e.target, projectId);
            });
            
            // Checkbox change
            checkbox.addEventListener('change', () => {
                this.updateBulkActions(dialog);
            });
            
            // Card click (select/deselect)
            card.addEventListener('click', (e) => {
                if (e.target.closest('.project-actions') || e.target.closest('.checkbox-option')) {
                    return;
                }
                
                checkbox.checked = !checkbox.checked;
                this.updateBulkActions(dialog);
            });
        });
    }
    
    /**
     * Filter projects based on search and filter criteria
     */
    filterProjects(dialog, filters) {
        const projectCards = dialog.querySelectorAll('.project-card');
        let visibleCount = 0;
        
        projectCards.forEach(card => {
            const projectId = card.getAttribute('data-project-id');
            const project = this.projects.get(projectId);
            
            if (!project) return;
            
            let visible = true;
            
            // Search filter
            if (filters.search) {
                const searchTerm = filters.search.toLowerCase();
                const searchableText = `${project.name} ${project.description || ''} ${project.path} ${(project.tags || []).join(' ')}`.toLowerCase();
                visible = visible && searchableText.includes(searchTerm);
            }
            
            // Status filter
            if (filters.status) {
                visible = visible && project.status === filters.status;
            }
            
            // Priority filter
            if (filters.priority) {
                visible = visible && (project.priority || 'normal') === filters.priority;
            }
            
            // Show/hide card
            card.style.display = visible ? 'block' : 'none';
            if (visible) visibleCount++;
        });
        
        // Update visible count
        const selectedCountSpan = dialog.querySelector('.selected-count');
        selectedCountSpan.textContent = `${visibleCount} visible`;
    }
    
    /**
     * Switch project view (grid/list)
     */
    switchProjectView(dialog, view) {
        const projectsGrid = dialog.querySelector('#projects-grid');
        projectsGrid.className = `projects-${view}`;
    }
    
    /**
     * Update bulk actions based on selected projects
     */
    updateBulkActions(dialog) {
        const checkboxes = dialog.querySelectorAll('.project-checkbox:checked');
        const selectedCount = checkboxes.length;
        const selectedCountSpan = dialog.querySelector('.selected-count');
        const bulkActionButtons = dialog.querySelectorAll('.bulk-actions-buttons .btn');
        
        selectedCountSpan.textContent = `${selectedCount} selected`;
        
        // Enable/disable bulk action buttons
        bulkActionButtons.forEach(btn => {
            btn.disabled = selectedCount === 0;
        });
    }
    
    /**
     * Setup bulk action handlers
     */
    setupBulkActionHandlers(dialog) {
        const bulkStartBtn = dialog.querySelector('#bulk-start-btn');
        const bulkPauseBtn = dialog.querySelector('#bulk-pause-btn');
        const bulkStopBtn = dialog.querySelector('#bulk-stop-btn');
        const bulkRemoveBtn = dialog.querySelector('#bulk-remove-btn');
        
        const getSelectedProjects = () => {
            const checkboxes = dialog.querySelectorAll('.project-checkbox:checked');
            return Array.from(checkboxes).map(cb => cb.getAttribute('data-project-id'));
        };
        
        bulkStartBtn.addEventListener('click', async () => {
            const selectedProjects = getSelectedProjects();
            await this.bulkUpdateProjectStatus(selectedProjects, 'active');
            this.populateGlobalView(dialog);
        });
        
        bulkPauseBtn.addEventListener('click', async () => {
            const selectedProjects = getSelectedProjects();
            await this.bulkUpdateProjectStatus(selectedProjects, 'paused');
            this.populateGlobalView(dialog);
        });
        
        bulkStopBtn.addEventListener('click', async () => {
            const selectedProjects = getSelectedProjects();
            await this.bulkUpdateProjectStatus(selectedProjects, 'idle');
            this.populateGlobalView(dialog);
        });
        
        bulkRemoveBtn.addEventListener('click', async () => {
            const selectedProjects = getSelectedProjects();
            const confirmed = await this.showConfirmDialog(
                'Remove Projects',
                `Are you sure you want to remove ${selectedProjects.length} project(s)?`,
                'This action cannot be undone.'
            );
            
            if (confirmed) {
                await this.bulkRemoveProjects(selectedProjects);
                this.populateGlobalView(dialog);
            }
        });
    }
    
    /**
     * Show status change menu
     */
    showStatusMenu(button, projectId) {
        const menu = document.createElement('div');
        menu.className = 'status-menu';
        menu.innerHTML = `
            <div class="status-menu-item" data-status="idle">
                <span class="status-dot idle"></span>
                <span>Idle</span>
            </div>
            <div class="status-menu-item" data-status="active">
                <span class="status-dot active"></span>
                <span>Active</span>
            </div>
            <div class="status-menu-item" data-status="paused">
                <span class="status-dot paused"></span>
                <span>Paused</span>
            </div>
            <div class="status-menu-item" data-status="error">
                <span class="status-dot error"></span>
                <span>Error</span>
            </div>
            <div class="status-menu-item" data-status="complete">
                <span class="status-dot complete"></span>
                <span>Complete</span>
            </div>
        `;
        
        // Position menu
        const rect = button.getBoundingClientRect();
        menu.style.position = 'fixed';
        menu.style.top = `${rect.bottom + 5}px`;
        menu.style.left = `${rect.left}px`;
        menu.style.zIndex = '10001';
        
        // Add click handlers
        menu.addEventListener('click', async (e) => {
            const item = e.target.closest('.status-menu-item');
            if (item) {
                const status = item.getAttribute('data-status');
                await this.updateProjectStatus(projectId, status);
                this.showSuccessMessage(`Project status updated to ${status}`);
            }
            menu.remove();
        });
        
        // Close menu on outside click
        const closeMenu = (e) => {
            if (!menu.contains(e.target) && e.target !== button) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        };
        
        document.addEventListener('click', closeMenu);
        document.body.appendChild(menu);
    }
    
    /**
     * Bulk update project status
     */
    async bulkUpdateProjectStatus(projectIds, status) {
        const promises = projectIds.map(projectId => this.updateProjectStatus(projectId, status));
        await Promise.all(promises);
        this.showSuccessMessage(`Updated ${projectIds.length} project(s) to ${status}`);
    }
    
    /**
     * Bulk remove projects
     */
    async bulkRemoveProjects(projectIds) {
        const promises = projectIds.map(projectId => {
            if (projectId !== 'default') {
                return this.removeProject(projectId);
            }
        });
        await Promise.all(promises.filter(Boolean));
        this.showSuccessMessage(`Removed ${projectIds.length} project(s)`);
    }
    
    /**
     * Show confirmation dialog
     */
    async showConfirmDialog(title, message, details = '') {
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.className = 'modal confirm-dialog';
            dialog.innerHTML = `
                <div class="modal-content small">
                    <div class="modal-header">
                        <h3>⚠️ ${title}</h3>
                    </div>
                    <div class="modal-body">
                        <p class="confirm-message">${message}</p>
                        ${details ? `<p class="confirm-details">${details}</p>` : ''}
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-danger confirm-btn">Confirm</button>
                        <button class="btn btn-secondary cancel-btn">Cancel</button>
                    </div>
                </div>
            `;
            
            const confirmBtn = dialog.querySelector('.confirm-btn');
            const cancelBtn = dialog.querySelector('.cancel-btn');
            
            const cleanup = () => {
                dialog.remove();
            };
            
            confirmBtn.addEventListener('click', () => {
                cleanup();
                resolve(true);
            });
            
            cancelBtn.addEventListener('click', () => {
                cleanup();
                resolve(false);
            });
            
            dialog.addEventListener('click', (e) => {
                if (e.target === dialog) {
                    cleanup();
                    resolve(false);
                }
            });
            
            document.body.appendChild(dialog);
        });
    }
    
    /**
     * Refresh project status
     */
    async refreshProjectStatus(projectId) {
        console.log(`🔄 Refreshing status for project: ${projectId}`);
        
        try {
            const response = await fetch(`/api/projects/${projectId}/status`);
            if (response.ok) {
                const data = await response.json();
                this.updateProjectStatus(projectId, data.status);
                this.showSuccessMessage('Project status refreshed');
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Failed to refresh project status:', error);
            this.showErrorMessage('Failed to refresh project status');
        }
    }
    
    /**
     * Duplicate project
     */
    async duplicateProject(projectId) {
        console.log(`📋 Duplicating project: ${projectId}`);
        // TODO: Implement project duplication
        this.showInfoMessage('Project duplication coming soon!');
    }
    
    /**
     * Notify other components of project switch
     */
    notifyProjectSwitch(projectId) {
        // Update discord chat project context
        if (window.discordChat) {
            window.discordChat.projectName = projectId;
        }
        
        // Emit custom event for other components
        window.dispatchEvent(new CustomEvent('projectSwitch', {
            detail: { projectId, project: this.projects.get(projectId) }
        }));
        
        // Update visualizer context if available
        if (window.visualizer) {
            window.visualizer.currentProject = projectId;
        }
    }
    
    /**
     * Show success message
     */
    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }
    
    /**
     * Show error message
     */
    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }
    
    /**
     * Show info message
     */
    showInfoMessage(message) {
        this.showMessage(message, 'info');
    }
    
    /**
     * Show message to user using unified system
     */
    showMessage(message, type = 'info') {
        // Use global DOM utilities message system
        if (window.domUtils) {
            window.domUtils.showMessage(message, type);
        } else {
            // Fallback for compatibility
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
        
        // Also log to activity log if available
        if (window.visualizer && window.visualizer.addActivityLog) {
            window.visualizer.addActivityLog('Project Manager', message, type);
        }
    }
    
    /**
     * Get current active project
     */
    getActiveProject() {
        return this.projects.get(this.activeProject);
    }
    
    /**
     * Get all projects
     */
    getAllProjects() {
        return Array.from(this.projects.values());
    }
    
    /**
     * Check if project manager is initialized
     */
    isReady() {
        return this.isInitialized;
    }
}

// Add CSS for message toasts
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    .modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .modal-content {
        background: var(--chat-bg);
        border-radius: var(--chat-border-radius);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        max-width: 500px;
        width: 90%;
        max-height: 90vh;
        overflow-y: auto;
    }
    
    .modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px;
        border-bottom: 1px solid var(--chat-border);
    }
    
    .modal-header h3 {
        margin: 0;
        color: var(--chat-text);
    }
    
    .modal-body {
        padding: 20px;
    }
    
    .modal-footer {
        display: flex;
        gap: 10px;
        justify-content: flex-end;
        padding: 20px;
        border-top: 1px solid var(--chat-border);
    }
    
    .form-group {
        margin-bottom: 16px;
    }
    
    .form-group label {
        display: block;
        margin-bottom: 4px;
        font-weight: 500;
        color: var(--chat-text);
    }
    
    .form-group input,
    .form-group select {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid var(--chat-border);
        border-radius: var(--chat-border-radius);
        background: var(--chat-input-bg);
        color: var(--chat-text);
        font-size: 14px;
    }
    
    .form-group input:focus,
    .form-group select:focus {
        outline: none;
        border-color: var(--chat-accent);
    }
    
    .btn {
        padding: 8px 16px;
        border: none;
        border-radius: var(--chat-border-radius);
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all var(--chat-animation-duration) var(--chat-animation-easing);
    }
    
    .btn-primary {
        background: var(--chat-accent);
        color: white;
    }
    
    .btn-primary:hover {
        background: color-mix(in srgb, var(--chat-accent) 80%, black);
    }
    
    .btn-secondary {
        background: var(--chat-message-bg);
        color: var(--chat-text);
        border: 1px solid var(--chat-border);
    }
    
    .btn-secondary:hover {
        background: color-mix(in srgb, var(--chat-message-bg) 80%, black);
    }
    
    .close-btn {
        background: none;
        border: none;
        font-size: 18px;
        color: var(--chat-text-muted);
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
    }
    
    .close-btn:hover {
        background: var(--chat-message-bg);
        color: var(--chat-text);
    }
`;
document.head.appendChild(style);

// Global instance
let projectManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing ProjectManager...');
    projectManager = new ProjectManager();
    
    // Expose to global scope
    window.projectManager = projectManager;
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProjectManager;
}

// Also expose to window for browser usage
if (typeof window !== 'undefined') {
    window.ProjectManager = ProjectManager;
}