/**
 * AI Agent TDD-Scrum Workflow - Interactive Theme Selector
 * Professional color scheme management for MkDocs Material
 */

class ThemeSelector {
  constructor() {
    this.themes = [
      {
        id: 'github',
        name: 'GitHub',
        description: 'Clean, professional, developer-focused',
        colors: ['#0969da', '#f6f8fa', '#1f2328', '#656d76']
      },
      {
        id: 'gitlab',
        name: 'GitLab',
        description: 'Warm, energetic, collaboration-focused',
        colors: ['#fc6d26', '#fafafa', '#303030', '#fca326']
      },
      {
        id: 'vercel',
        name: 'Vercel',
        description: 'Ultra-clean, modern, high-contrast',
        colors: ['#000000', '#ffffff', '#666666', '#0070f3']
      },
      {
        id: 'linear',
        name: 'Linear',
        description: 'Modern, sophisticated, productivity-focused',
        colors: ['#5e6ad2', '#f8fafc', '#0f0f23', '#a855f7']
      },
      {
        id: 'stripe',
        name: 'Stripe',
        description: 'Professional, trustworthy, financial-grade',
        colors: ['#635bff', '#f7f9fc', '#0a2540', '#00d4aa']
      },
      {
        id: 'nord',
        name: 'Nord',
        description: 'Cool, calm, developer-friendly',
        colors: ['#5e81ac', '#eceff4', '#2e3440', '#88c0d0']
      },
      {
        id: 'dracula',
        name: 'Dracula',
        description: 'Vibrant, dark, code-focused',
        colors: ['#bd93f9', '#282a36', '#f8f8f2', '#ff79c6']
      },
      {
        id: 'solarized',
        name: 'Solarized',
        description: 'Balanced, easy on eyes, academic',
        colors: ['#268bd2', '#fdf6e3', '#657b83', '#859900']
      },
      {
        id: 'material',
        name: 'Material',
        description: 'Google\'s Material Design, consistent, familiar',
        colors: ['#3f51b5', '#ffffff', '#212121', '#ff4081']
      },
      {
        id: 'sunset',
        name: 'Sunset',
        description: 'Vibrant, modern, eye-catching gradient',
        colors: ['#ff6b6b', '#ffffff', '#2c3e50', '#4ecdc4']
      }
    ];
    
    this.currentTheme = this.loadTheme();
    this.isOpen = false;
    
    this.init();
  }
  
  init() {
    console.log('Theme selector initializing...');
    this.createHTML();
    this.bindEvents();
    this.applyTheme(this.currentTheme);
    this.updateActiveOption();
    
    // Add keyboard navigation support
    this.addKeyboardSupport();
    
    // Handle system theme preference changes
    this.handleSystemThemeChanges();
    
    console.log('Theme selector initialized successfully');
  }
  
  createHTML() {
    const selectorHTML = `
      <div class="theme-selector" id="theme-selector" role="navigation" aria-label="Theme selector">
        <button class="theme-selector-toggle" id="theme-toggle" aria-expanded="false" aria-haspopup="true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6zm0-10c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4z"/>
          </svg>
          Themes
        </button>
        <div class="theme-selector-dropdown" id="theme-dropdown" role="menu">
          ${this.themes.map(theme => `
            <div class="theme-option" 
                 data-theme="${theme.id}" 
                 role="menuitem" 
                 tabindex="0"
                 aria-label="${theme.name} theme: ${theme.description}">
              <div class="theme-preview" aria-hidden="true">
                ${theme.colors.map(color => `
                  <div class="theme-preview-color" style="background-color: ${color}"></div>
                `).join('')}
              </div>
              <div class="theme-info">
                <div class="theme-name">${theme.name}</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
    
    // Insert the theme selector into the page
    document.body.insertAdjacentHTML('beforeend', selectorHTML);
    
    // Cache DOM elements
    this.selectorEl = document.getElementById('theme-selector');
    this.toggleEl = document.getElementById('theme-toggle');
    this.dropdownEl = document.getElementById('theme-dropdown');
    this.optionEls = document.querySelectorAll('.theme-option');
  }
  
  bindEvents() {
    // Toggle dropdown
    this.toggleEl.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggleDropdown();
    });
    
    // Theme selection
    this.optionEls.forEach(option => {
      option.addEventListener('click', (e) => {
        const themeId = e.currentTarget.dataset.theme;
        this.selectTheme(themeId);
      });
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (!this.selectorEl.contains(e.target)) {
        this.closeDropdown();
      }
    });
    
    // Close dropdown on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.closeDropdown();
        this.toggleEl.focus();
      }
    });
  }
  
  addKeyboardSupport() {
    // Arrow key navigation in dropdown
    this.dropdownEl.addEventListener('keydown', (e) => {
      if (!this.isOpen) return;
      
      const options = Array.from(this.optionEls);
      const currentIndex = options.findIndex(option => option === document.activeElement);
      
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          const nextIndex = (currentIndex + 1) % options.length;
          options[nextIndex].focus();
          break;
          
        case 'ArrowUp':
          e.preventDefault();
          const prevIndex = currentIndex <= 0 ? options.length - 1 : currentIndex - 1;
          options[prevIndex].focus();
          break;
          
        case 'Enter':
        case ' ':
          e.preventDefault();
          if (document.activeElement && document.activeElement.dataset.theme) {
            this.selectTheme(document.activeElement.dataset.theme);
          }
          break;
          
        case 'Home':
          e.preventDefault();
          options[0].focus();
          break;
          
        case 'End':
          e.preventDefault();
          options[options.length - 1].focus();
          break;
      }
    });
    
    // Enter/Space to activate theme options
    this.optionEls.forEach(option => {
      option.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.selectTheme(option.dataset.theme);
        }
      });
    });
  }
  
  handleSystemThemeChanges() {
    // Listen for system dark/light mode changes
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      mediaQuery.addEventListener('change', () => {
        // Only auto-switch if user hasn't manually selected a theme
        if (!localStorage.getItem('selected-theme-manual')) {
          const systemTheme = mediaQuery.matches ? 'dracula' : 'github';
          this.applyTheme(systemTheme);
          this.updateActiveOption();
        }
      });
    }
  }
  
  toggleDropdown() {
    this.isOpen = !this.isOpen;
    this.dropdownEl.classList.toggle('active', this.isOpen);
    this.toggleEl.setAttribute('aria-expanded', this.isOpen.toString());
    
    if (this.isOpen) {
      // Focus first option when opening
      this.optionEls[0].focus();
      
      // Add smooth entrance animation
      requestAnimationFrame(() => {
        this.dropdownEl.style.transform = 'translateY(0)';
      });
    }
  }
  
  closeDropdown() {
    this.isOpen = false;
    this.dropdownEl.classList.remove('active');
    this.toggleEl.setAttribute('aria-expanded', 'false');
  }
  
  selectTheme(themeId) {
    this.currentTheme = themeId;
    this.applyTheme(themeId);
    this.saveTheme(themeId);
    this.updateActiveOption();
    this.closeDropdown();
    
    // Mark as manually selected theme
    localStorage.setItem('selected-theme-manual', 'true');
    
    // Announce theme change for screen readers
    this.announceThemeChange(themeId);
    
    // Trigger custom event for other components
    document.dispatchEvent(new CustomEvent('themeChanged', { 
      detail: { themeId, theme: this.themes.find(t => t.id === themeId) }
    }));
  }
  
  applyTheme(themeId) {
    console.log(`Applying theme: ${themeId}`);
    document.documentElement.setAttribute('data-theme', themeId);
    console.log(`Theme attribute set to: ${document.documentElement.getAttribute('data-theme')}`);
    
    // Also apply to body for better compatibility
    document.body.setAttribute('data-theme', themeId);
    
    // Force CSS recalculation by triggering reflow
    const theme = this.themes.find(t => t.id === themeId);
    if (theme) {
      // Apply theme colors directly to CSS custom properties for immediate effect
      const root = document.documentElement;
      root.style.setProperty('--md-primary-fg-color', theme.colors[0]);
      root.style.setProperty('--md-default-bg-color', themeId === 'dracula' ? theme.colors[1] : '#ffffff');
      root.style.setProperty('--md-default-fg-color', theme.colors[2]);
      root.style.setProperty('--md-accent-fg-color', theme.colors[3]);
      
      console.log(`Applied colors: primary=${theme.colors[0]}, bg=${theme.colors[1]}, fg=${theme.colors[2]}, accent=${theme.colors[3]}`);
    }
    
    // Update meta theme-color for mobile browsers
    this.updateMetaThemeColor(themeId);
    
    // Smooth transition effect
    document.body.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
    setTimeout(() => {
      document.body.style.transition = '';
    }, 300);
  }
  
  updateMetaThemeColor(themeId) {
    const theme = this.themes.find(t => t.id === themeId);
    if (theme) {
      let metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (!metaThemeColor) {
        metaThemeColor = document.createElement('meta');
        metaThemeColor.name = 'theme-color';
        document.head.appendChild(metaThemeColor);
      }
      metaThemeColor.content = theme.colors[0]; // Use primary color
    }
  }
  
  updateActiveOption() {
    this.optionEls.forEach(option => {
      const isActive = option.dataset.theme === this.currentTheme;
      option.classList.toggle('active', isActive);
      option.setAttribute('aria-selected', isActive.toString());
    });
  }
  
  announceThemeChange(themeId) {
    const theme = this.themes.find(t => t.id === themeId);
    if (theme) {
      const announcement = document.createElement('div');
      announcement.setAttribute('aria-live', 'polite');
      announcement.setAttribute('aria-atomic', 'true');
      announcement.style.position = 'absolute';
      announcement.style.left = '-10000px';
      announcement.style.width = '1px';
      announcement.style.height = '1px';
      announcement.style.overflow = 'hidden';
      announcement.textContent = `Theme changed to ${theme.name}: ${theme.description}`;
      
      document.body.appendChild(announcement);
      setTimeout(() => document.body.removeChild(announcement), 1000);
    }
  }
  
  saveTheme(themeId) {
    try {
      localStorage.setItem('selected-theme', themeId);
    } catch (error) {
      console.warn('Unable to save theme preference:', error);
    }
  }
  
  loadTheme() {
    try {
      const saved = localStorage.getItem('selected-theme');
      if (saved && this.themes.find(t => t.id === saved)) {
        return saved;
      }
    } catch (error) {
      console.warn('Unable to load theme preference:', error);
    }
    
    // Default to system preference or GitHub theme
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dracula';
    }
    return 'github';
  }
  
  // Public API methods
  getThemes() {
    return [...this.themes];
  }
  
  getCurrentTheme() {
    return this.currentTheme;
  }
  
  setTheme(themeId) {
    if (this.themes.find(t => t.id === themeId)) {
      this.selectTheme(themeId);
    }
  }
}

// Initialize theme selector when DOM is ready
function initThemeSelector() {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      window.themeSelector = new ThemeSelector();
    });
  } else {
    window.themeSelector = new ThemeSelector();
  }
}

// Auto-initialize unless explicitly disabled
if (!window.disableAutoThemeSelector) {
  initThemeSelector();
}

// Export for manual initialization
window.ThemeSelector = ThemeSelector;
window.initThemeSelector = initThemeSelector;