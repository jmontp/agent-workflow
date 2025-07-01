/**
 * FINAL LAYOUT ENFORCER - Nuclear option to force correct state machine layout
 * This script ensures the state diagrams are always visible and interface panels are hidden
 */

(function() {
    'use strict';
    
    console.log('🚀 Final Layout Enforcer: Activating...');
    
    // Immediate execution - don't wait for DOM
    function enforceLayout() {
        // 1. FORCE SHOW state machine content
        const showElements = [
            '.visualization-grid',
            '.diagram-container', 
            '#workflow-diagram',
            '#tdd-diagram',
            'main[role="main"]'
        ];
        
        showElements.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (el) {
                    el.style.display = 'block';
                    el.style.visibility = 'visible';
                    el.style.opacity = '1';
                    el.style.position = 'static';
                    console.log(`✅ Forced visible: ${selector}`);
                }
            });
        });
        
        // 2. FORCE HIDE interface management panels
        const hideElements = [
            '.interface-panel',
            '.agent-testing-panel',
            '.interface-management',
            '.testing-controls',
            '.agent-interface-management',
            '.activity-panel'
        ];
        
        hideElements.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (el) {
                    el.remove(); // Completely remove from DOM
                    console.log(`🗑️ Removed: ${selector}`);
                }
            });
        });
        
        // 3. ENSURE proper app layout
        const appLayout = document.querySelector('.app-layout');
        if (appLayout) {
            appLayout.style.display = 'flex';
            appLayout.style.height = '100vh';
            console.log('✅ App layout enforced');
        }
        
        // 4. ENSURE main content layout
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.style.flex = '1';
            mainContent.style.display = 'flex';
            mainContent.style.flexDirection = 'column';
            console.log('✅ Main content layout enforced');
        }
        
        // 5. ADD visual confirmation
        const visualGrid = document.querySelector('.visualization-grid');
        if (visualGrid && !visualGrid.querySelector('.layout-enforcer-badge')) {
            const badge = document.createElement('div');
            badge.className = 'layout-enforcer-badge';
            badge.innerHTML = '🎯 State Machine Visualizer (Layout Enforced)';
            badge.style.cssText = `
                background: #4CAF50;
                color: white;
                padding: 10px;
                text-align: center;
                border-radius: 4px;
                margin-bottom: 20px;
                font-weight: bold;
            `;
            visualGrid.insertBefore(badge, visualGrid.firstChild);
            console.log('✅ Visual confirmation added');
        }
        
        console.log('✅ Final Layout Enforcer: Layout enforcement complete!');
    }
    
    // Apply immediately
    enforceLayout();
    
    // Apply on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', enforceLayout);
    } else {
        enforceLayout();
    }
    
    // Apply after all scripts load
    window.addEventListener('load', enforceLayout);
    
    // Continuous monitoring to prevent regression
    const observer = new MutationObserver(function(mutations) {
        let needsEnforcement = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                // Check if any interface panels were added
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.classList && (
                            node.classList.contains('interface-panel') ||
                            node.classList.contains('agent-testing-panel') ||
                            node.classList.contains('interface-management')
                        )) {
                            needsEnforcement = true;
                        }
                    }
                });
            }
        });
        
        if (needsEnforcement) {
            console.log('🔄 Interface panels detected, re-enforcing layout...');
            setTimeout(enforceLayout, 100);
        }
    });
    
    // Start monitoring after DOM is ready
    if (document.body) {
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    } else {
        document.addEventListener('DOMContentLoaded', function() {
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        });
    }
    
    // Emergency functions
    window.emergencyEnforceLayout = enforceLayout;
    window.forceShowStateDiagrams = function() {
        const grid = document.querySelector('.visualization-grid');
        if (grid) {
            grid.style.display = 'block';
            grid.style.visibility = 'visible';
            grid.scrollIntoView({ behavior: 'smooth' });
        }
    };
    
    console.log('🎯 Final Layout Enforcer: Fully loaded and monitoring');
    
})();