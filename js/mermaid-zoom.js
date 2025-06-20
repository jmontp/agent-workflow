// Interactive zoom/pan for Mermaid diagrams
(function() {
    'use strict';
    
    console.log('Mermaid zoom script loaded');
    
    // Try to initialize immediately when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeWithRetry);
    } else {
        initializeWithRetry();
    }
    
    // Function to initialize with retry logic
    function initializeWithRetry() {
        console.log('Attempting to initialize Mermaid zoom...');
        
        // Try multiple times with increasing delays
        const delays = [500, 1000, 2000, 3000, 5000];
        
        delays.forEach(function(delay) {
            setTimeout(function() {
                console.log('Checking for Mermaid diagrams (delay: ' + delay + 'ms)');
                initializeMermaidZoom();
            }, delay);
        });
        
        // Also set up a mutation observer for dynamic content
        setupMutationObserver();
    }
    
    function setupMutationObserver() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    // Check if any added nodes contain Mermaid content
                    for (let i = 0; i < mutation.addedNodes.length; i++) {
                        const node = mutation.addedNodes[i];
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            if (node.classList && node.classList.contains('mermaid') ||
                                node.querySelector && node.querySelector('.mermaid')) {
                                console.log('New Mermaid content detected, initializing zoom...');
                                setTimeout(initializeMermaidZoom, 200);
                                break;
                            }
                        }
                    }
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('Mutation observer set up for Mermaid diagrams');
    }
})();

function initializeMermaidZoom() {
    console.log('initializeMermaidZoom called');
    
    // Find all mermaid diagrams
    const mermaidDivs = document.querySelectorAll('.mermaid');
    console.log('Found', mermaidDivs.length, 'Mermaid divs');
    
    if (mermaidDivs.length === 0) {
        // Check if we have pre elements that haven't been converted yet
        const preElements = document.querySelectorAll('pre.mermaid');
        console.log('Found', preElements.length, 'pre.mermaid elements that may need conversion');
        return; // Exit early if no rendered diagrams found
    }
    
    mermaidDivs.forEach(function(div, index) {
        console.log('Processing Mermaid div', index);
        const svg = div.querySelector('svg');
        
        if (!svg) {
            console.log('No SVG found in Mermaid div', index);
            return;
        }
        
        if (svg.hasAttribute('data-zoom-initialized')) {
            console.log('SVG already initialized for zoom, skipping');
            return;
        }
        
        // Mark as initialized to avoid duplicate initialization
        svg.setAttribute('data-zoom-initialized', 'true');
        console.log('Initializing zoom for SVG', index);
        
        // Only add zoom to larger diagrams (skip simple ones)
        let bbox;
        try {
            bbox = svg.getBBox();
            console.log('SVG bbox:', bbox);
        } catch (e) {
            console.log('Could not get bbox, using fallback size check');
            bbox = { width: 500, height: 400 }; // Default to enable zoom
        }
        
        if (bbox && (bbox.width > 400 || bbox.height > 300)) {
            console.log('SVG is large enough for zoom, proceeding...');
                
                // Add a container div for better control
                const container = document.createElement('div');
                container.className = 'mermaid-zoom-container';
                container.style.cssText = `
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    overflow: hidden;
                    background: white;
                    position: relative;
                    margin: 20px 0;
                `;
                
                // Add zoom controls
                const controls = document.createElement('div');
                controls.className = 'zoom-controls';
                controls.style.cssText = `
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    z-index: 1000;
                    background: rgba(255,255,255,0.9);
                    border-radius: 4px;
                    padding: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                `;
                
                controls.innerHTML = `
                    <button onclick="zoomIn('${svg.id || 'mermaid-' + index}')" style="margin: 2px; padding: 5px 8px; border: none; background: #2196F3; color: white; border-radius: 3px; cursor: pointer;">🔍+</button>
                    <button onclick="zoomOut('${svg.id || 'mermaid-' + index}')" style="margin: 2px; padding: 5px 8px; border: none; background: #2196F3; color: white; border-radius: 3px; cursor: pointer;">🔍-</button>
                    <button onclick="resetZoom('${svg.id || 'mermaid-' + index}')" style="margin: 2px; padding: 5px 8px; border: none; background: #666; color: white; border-radius: 3px; cursor: pointer;">↺</button>
                `;
                
                // Add instructions
                const instructions = document.createElement('div');
                instructions.style.cssText = `
                    position: absolute;
                    bottom: 10px;
                    left: 10px;
                    background: rgba(0,0,0,0.7);
                    color: white;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-size: 12px;
                    z-index: 1000;
                `;
                instructions.textContent = 'Drag to pan • Scroll to zoom';
                
                // Wrap the diagram
                div.parentNode.insertBefore(container, div);
                container.appendChild(div);
                container.appendChild(controls);
                container.appendChild(instructions);
                
                // Set SVG properties for zoom
                svg.style.cssText = `
                    width: 100%;
                    height: 500px;
                    cursor: move;
                `;
                
                // Assign unique ID if doesn't exist
                if (!svg.id) {
                    svg.id = 'mermaid-' + index;
                }
                
                // Initialize svg-pan-zoom
                try {
                    console.log('Checking if svgPanZoom is available...');
                    if (typeof svgPanZoom === 'undefined') {
                        throw new Error('svgPanZoom library not loaded');
                    }
                    
                    console.log('Initializing svgPanZoom for', svg.id);
                    const panZoomInstance = svgPanZoom(svg, {
                        zoomEnabled: true,
                        controlIconsEnabled: false,
                        fit: true,
                        center: true,
                        minZoom: 0.3,
                        maxZoom: 5,
                        zoomScaleSensitivity: 0.3,
                        panEnabled: true,
                        dblClickZoomEnabled: true,
                        mouseWheelZoomEnabled: true
                    });
                    
                    // Store reference for control buttons
                    window['panZoom_' + svg.id] = panZoomInstance;
                    console.log('SVG Pan Zoom initialized successfully for', svg.id);
                    
                } catch (error) {
                    console.error('SVG Pan Zoom failed for diagram:', svg.id, error);
                    // Fallback: basic CSS zoom on hover
                    console.log('Using fallback zoom implementation');
                    svg.style.transition = 'transform 0.3s ease';
                    svg.addEventListener('wheel', function(e) {
                        e.preventDefault();
                        const scale = e.deltaY > 0 ? 0.9 : 1.1;
                        const currentTransform = svg.style.transform || 'scale(1)';
                        const currentScale = parseFloat(currentTransform.match(/scale\(([^)]+)\)/)?.[1] || '1');
                        const newScale = Math.max(0.3, Math.min(3, currentScale * scale));
                        svg.style.transform = `scale(${newScale})`;
                    });
                }
            } else {
                console.log('SVG too small for zoom, skipping');
            }
        } else {
            console.log('No valid bbox found, skipping zoom for this SVG');
        }
    });
    
    console.log('initializeMermaidZoom completed');
}

// Control functions for zoom buttons
function zoomIn(svgId) {
    const instance = window['panZoom_' + svgId];
    if (instance) {
        instance.zoomIn();
    }
}

function zoomOut(svgId) {
    const instance = window['panZoom_' + svgId];
    if (instance) {
        instance.zoomOut();
    }
}

function resetZoom(svgId) {
    const instance = window['panZoom_' + svgId];
    if (instance) {
        instance.resetZoom();
        instance.center();
        instance.fit();
    }
}