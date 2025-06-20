/**
 * Universal Search Component (⌘K Style)
 * Enhanced search functionality for MkDocs with autocomplete and category filtering
 */

(function() {
    'use strict';
    
    // Configuration
    const SEARCH_CONFIG = {
        maxResults: 10,
        debounceDelay: 150,
        categories: {
            'getting-started': { icon: '⚡', label: 'Getting Started', color: '#4CAF50' },
            'user-guide': { icon: '📊', label: 'User Guide', color: '#2196F3' },
            'concepts': { icon: '🎯', label: 'Core Concepts', color: '#FF9800' },
            'architecture': { icon: '🔥', label: 'Architecture', color: '#9C27B0' },
            'advanced': { icon: '⚡', label: 'Advanced Topics', color: '#F44336' },
            'development': { icon: '📊', label: 'Development', color: '#607D8B' },
            'deployment': { icon: '🔥', label: 'Deployment', color: '#795548' }
        }
    };
    
    let searchIndex = [];
    let isSearchVisible = false;
    let debounceTimer = null;
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    function init() {
        createSearchInterface();
        setupKeyboardShortcuts();
        loadSearchIndex();
        setupEventListeners();
    }
    
    function createSearchInterface() {
        // Create search overlay
        const overlay = document.createElement('div');
        overlay.id = 'universal-search-overlay';
        overlay.className = 'universal-search-overlay';
        overlay.innerHTML = `
            <div class="universal-search-modal">
                <div class="universal-search-header">
                    <div class="search-input-container">
                        <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <path d="M21 21l-4.35-4.35"></path>
                        </svg>
                        <input type="text" id="universal-search-input" placeholder="Search documentation... (⌘K)" autocomplete="off" />
                        <button class="search-close" aria-label="Close search">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                    <div class="search-filters">
                        <button class="filter-btn active" data-category="all">All</button>
                        <button class="filter-btn" data-category="getting-started">⚡ Getting Started</button>
                        <button class="filter-btn" data-category="user-guide">📊 User Guide</button>
                        <button class="filter-btn" data-category="architecture">🔥 Architecture</button>
                        <button class="filter-btn" data-category="development">📊 Development</button>
                    </div>
                </div>
                <div class="universal-search-body">
                    <div id="search-results" class="search-results">
                        <div class="search-empty-state">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <circle cx="11" cy="11" r="8"></circle>
                                <path d="M21 21l-4.35-4.35"></path>
                            </svg>
                            <h3>Search documentation</h3>
                            <p>Start typing to find pages, commands, and concepts</p>
                            <div class="search-shortcuts">
                                <div class="shortcut-group">
                                    <span class="shortcut-label">Quick actions:</span>
                                    <kbd>/epic</kbd> <span>Epic commands</span>
                                    <kbd>/sprint</kbd> <span>Sprint management</span>
                                    <kbd>/state</kbd> <span>State machine</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="search-footer">
                        <div class="search-navigation-hints">
                            <span><kbd>↑</kbd><kbd>↓</kbd> Navigate</span>
                            <span><kbd>↵</kbd> Select</span>
                            <span><kbd>Esc</kbd> Close</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
    }
    
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // CMD+K or CTRL+K to open search
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                toggleSearch();
                return;
            }
            
            // Forward slash to open search (like GitHub)
            if (e.key === '/' && !isInputFocused()) {
                e.preventDefault();
                toggleSearch();
                return;
            }
            
            // Escape to close search
            if (e.key === 'Escape' && isSearchVisible) {
                closeSearch();
                return;
            }
            
            // Navigation within search results
            if (isSearchVisible) {
                handleSearchNavigation(e);
            }
        });
    }
    
    function setupEventListeners() {
        const overlay = document.getElementById('universal-search-overlay');
        const input = document.getElementById('universal-search-input');
        const closeBtn = overlay.querySelector('.search-close');
        const filterBtns = overlay.querySelectorAll('.filter-btn');
        
        // Close search when clicking overlay
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                closeSearch();
            }
        });
        
        // Close button
        closeBtn.addEventListener('click', closeSearch);
        
        // Search input
        input.addEventListener('input', handleSearchInput);
        input.addEventListener('focus', function() {
            if (!input.value.trim()) {
                showRecentSearches();
            }
        });
        
        // Filter buttons
        filterBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const category = btn.dataset.category;
                filterResults(category);
            });
        });
    }
    
    function toggleSearch() {
        if (isSearchVisible) {
            closeSearch();
        } else {
            openSearch();
        }
    }
    
    function openSearch() {
        const overlay = document.getElementById('universal-search-overlay');
        const input = document.getElementById('universal-search-input');
        
        overlay.classList.add('visible');
        document.body.style.overflow = 'hidden';
        isSearchVisible = true;
        
        // Focus input after animation
        setTimeout(() => {
            input.focus();
        }, 100);
        
        // Track analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'search_open', {
                event_category: 'engagement',
                event_label: 'universal_search'
            });
        }
    }
    
    function closeSearch() {
        const overlay = document.getElementById('universal-search-overlay');
        const input = document.getElementById('universal-search-input');
        
        overlay.classList.remove('visible');
        document.body.style.overflow = '';
        isSearchVisible = false;
        
        // Clear search
        input.value = '';
        clearResults();
    }
    
    function handleSearchInput(e) {
        const query = e.target.value.trim();
        
        if (debounceTimer) {
            clearTimeout(debounceTimer);
        }
        
        debounceTimer = setTimeout(() => {
            if (query.length === 0) {
                showRecentSearches();
            } else if (query.length >= 2) {
                performSearch(query);
            } else {
                clearResults();
            }
        }, SEARCH_CONFIG.debounceDelay);
    }
    
    function loadSearchIndex() {
        // Try to load the existing search index from MkDocs
        fetch('/search/search_index.json')
            .then(response => response.json())
            .then(data => {
                searchIndex = processSearchIndex(data);
                console.log('Search index loaded:', searchIndex.length, 'items');
            })
            .catch(error => {
                console.warn('Could not load search index:', error);
                // Fallback: create basic index from navigation
                createFallbackIndex();
            });
    }
    
    function processSearchIndex(data) {
        const processed = [];
        
        if (data.docs) {
            data.docs.forEach((doc, index) => {
                const url = doc.location || '';
                const category = extractCategory(url);
                
                processed.push({
                    id: index,
                    title: doc.title || 'Untitled',
                    content: doc.text || '',
                    url: url,
                    category: category,
                    keywords: extractKeywords(doc.title, doc.text),
                    section: extractSection(url)
                });
            });
        }
        
        return processed;
    }
    
    function createFallbackIndex() {
        // Create index from navigation links
        const navLinks = document.querySelectorAll('.md-nav__link');
        const processed = [];
        
        navLinks.forEach((link, index) => {
            const url = link.getAttribute('href') || '';
            const title = link.textContent.trim();
            const category = extractCategory(url);
            
            if (url && title && !url.startsWith('#')) {
                processed.push({
                    id: index,
                    title: title,
                    content: '',
                    url: url,
                    category: category,
                    keywords: extractKeywords(title, ''),
                    section: extractSection(url)
                });
            }
        });
        
        searchIndex = processed;
        console.log('Fallback search index created:', searchIndex.length, 'items');
    }
    
    function extractCategory(url) {
        const parts = url.split('/');
        const category = parts[1] || parts[0] || '';
        return category.replace(/\.html?$/, '');
    }
    
    function extractSection(url) {
        const parts = url.split('/');
        return parts[parts.length - 1]?.replace(/\.html?$/, '') || '';
    }
    
    function extractKeywords(title, content) {
        const text = (title + ' ' + content).toLowerCase();
        const keywords = [];
        
        // Extract command patterns
        const commands = text.match(/\/\w+/g) || [];
        keywords.push(...commands);
        
        // Extract important terms
        const terms = text.match(/\b(epic|sprint|agent|tdd|discord|github|state|workflow|orchestrat\w+)\b/g) || [];
        keywords.push(...terms);
        
        return [...new Set(keywords)];
    }
    
    function performSearch(query) {
        const results = searchIndex
            .map(item => {
                const score = calculateRelevanceScore(item, query);
                return { ...item, score };
            })
            .filter(item => item.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, SEARCH_CONFIG.maxResults);
        
        displayResults(results, query);
        
        // Track search analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'search', {
                search_term: query,
                event_category: 'engagement'
            });
        }
    }
    
    function calculateRelevanceScore(item, query) {
        const q = query.toLowerCase();
        let score = 0;
        
        // Title exact match (highest priority)
        if (item.title.toLowerCase().includes(q)) {
            score += 100;
        }
        
        // Keywords match
        const keywordMatches = item.keywords.filter(keyword => 
            keyword.toLowerCase().includes(q)
        );
        score += keywordMatches.length * 50;
        
        // Content match (lower priority)
        if (item.content.toLowerCase().includes(q)) {
            score += 10;
        }
        
        // Category match
        if (item.category.toLowerCase().includes(q)) {
            score += 25;
        }
        
        // Boost for command searches
        if (q.startsWith('/') && item.keywords.includes(q)) {
            score += 200;
        }
        
        return score;
    }
    
    function displayResults(results, query) {
        const container = document.getElementById('search-results');
        
        if (results.length === 0) {
            container.innerHTML = `
                <div class="search-no-results">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="11" cy="11" r="8"></circle>
                        <path d="M21 21l-4.35-4.35"></path>
                    </svg>
                    <h3>No results found</h3>
                    <p>Try adjusting your search or browse by category</p>
                </div>
            `;
            return;
        }
        
        const html = results.map((result, index) => {
            const category = SEARCH_CONFIG.categories[result.category] || 
                { icon: '📄', label: result.category, color: '#666' };
            
            const highlightedTitle = highlightMatch(result.title, query);
            const snippet = createSnippet(result.content, query);
            
            return `
                <div class="search-result" data-index="${index}" data-url="${result.url}">
                    <div class="result-category" style="color: ${category.color}">
                        <span class="category-icon">${category.icon}</span>
                        <span class="category-label">${category.label}</span>
                    </div>
                    <div class="result-content">
                        <h4 class="result-title">${highlightedTitle}</h4>
                        ${snippet ? `<p class="result-snippet">${snippet}</p>` : ''}
                    </div>
                    <div class="result-meta">
                        <span class="result-url">${result.url}</span>
                        <svg class="result-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M7 17L17 7M17 7H7M17 7V17"></path>
                        </svg>
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = html;
        
        // Add click handlers
        container.querySelectorAll('.search-result').forEach(result => {
            result.addEventListener('click', function() {
                const url = this.dataset.url;
                if (url) {
                    navigateToResult(url);
                }
            });
        });
        
        // Highlight first result
        const firstResult = container.querySelector('.search-result');
        if (firstResult) {
            firstResult.classList.add('highlighted');
        }
    }
    
    function highlightMatch(text, query) {
        if (!query) return text;
        
        const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }
    
    function createSnippet(content, query, maxLength = 120) {
        if (!content || !query) return '';
        
        const lowerContent = content.toLowerCase();
        const lowerQuery = query.toLowerCase();
        const index = lowerContent.indexOf(lowerQuery);
        
        if (index === -1) return '';
        
        const start = Math.max(0, index - 50);
        const end = Math.min(content.length, start + maxLength);
        let snippet = content.slice(start, end);
        
        if (start > 0) snippet = '...' + snippet;
        if (end < content.length) snippet = snippet + '...';
        
        return highlightMatch(snippet, query);
    }
    
    function escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    function showRecentSearches() {
        const container = document.getElementById('search-results');
        const recentSearches = getRecentSearches();
        
        if (recentSearches.length === 0) {
            container.innerHTML = `
                <div class="search-empty-state">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="11" cy="11" r="8"></circle>
                        <path d="M21 21l-4.35-4.35"></path>
                    </svg>
                    <h3>Search documentation</h3>
                    <p>Start typing to find pages, commands, and concepts</p>
                    <div class="search-shortcuts">
                        <div class="shortcut-group">
                            <span class="shortcut-label">Quick actions:</span>
                            <kbd>/epic</kbd> <span>Epic commands</span>
                            <kbd>/sprint</kbd> <span>Sprint management</span>
                            <kbd>/state</kbd> <span>State machine</span>
                        </div>
                    </div>
                </div>
            `;
            return;
        }
        
        const html = `
            <div class="recent-searches">
                <h3 class="recent-title">Recent searches</h3>
                ${recentSearches.map(search => `
                    <div class="recent-search-item" data-query="${search.query}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2L12 22"></path>
                            <path d="M17 5H9.5A3.5 3.5 0 0 0 6 8.5V8.5A3.5 3.5 0 0 0 9.5 12H10.5A3.5 3.5 0 0 1 14 15.5V15.5A3.5 3.5 0 0 1 10.5 19H6"></path>
                        </svg>
                        <span>${search.query}</span>
                    </div>
                `).join('')}
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    function getRecentSearches() {
        try {
            return JSON.parse(localStorage.getItem('mkdocs-recent-searches') || '[]');
        } catch {
            return [];
        }
    }
    
    function saveRecentSearch(query) {
        try {
            const recent = getRecentSearches();
            const newSearch = { query, timestamp: Date.now() };
            const filtered = recent.filter(s => s.query !== query);
            filtered.unshift(newSearch);
            const limited = filtered.slice(0, 5);
            localStorage.setItem('mkdocs-recent-searches', JSON.stringify(limited));
        } catch (error) {
            console.warn('Could not save recent search:', error);
        }
    }
    
    function clearResults() {
        const container = document.getElementById('search-results');
        container.innerHTML = '';
    }
    
    function filterResults(category) {
        const input = document.getElementById('universal-search-input');
        const query = input.value.trim();
        
        if (query.length >= 2) {
            performSearch(query, category);
        }
    }
    
    function handleSearchNavigation(e) {
        const results = document.querySelectorAll('.search-result');
        const highlighted = document.querySelector('.search-result.highlighted');
        
        if (results.length === 0) return;
        
        let currentIndex = -1;
        if (highlighted) {
            currentIndex = Array.from(results).indexOf(highlighted);
        }
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const nextIndex = Math.min(currentIndex + 1, results.length - 1);
            highlightResult(results, nextIndex);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const prevIndex = Math.max(currentIndex - 1, 0);
            highlightResult(results, prevIndex);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (highlighted) {
                const url = highlighted.dataset.url;
                if (url) {
                    navigateToResult(url);
                }
            }
        }
    }
    
    function highlightResult(results, index) {
        results.forEach(r => r.classList.remove('highlighted'));
        if (results[index]) {
            results[index].classList.add('highlighted');
        }
    }
    
    function navigateToResult(url) {
        const input = document.getElementById('universal-search-input');
        const query = input.value.trim();
        
        if (query) {
            saveRecentSearch(query);
        }
        
        closeSearch();
        
        // Navigate to result
        if (url.startsWith('http')) {
            window.open(url, '_blank');
        } else {
            window.location.href = url;
        }
        
        // Track analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'search_result_click', {
                event_category: 'engagement',
                event_label: url,
                search_term: query
            });
        }
    }
    
    function isInputFocused() {
        const active = document.activeElement;
        return active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.contentEditable === 'true');
    }
    
    // Public API
    window.UniversalSearch = {
        open: openSearch,
        close: closeSearch,
        toggle: toggleSearch
    };
    
})();