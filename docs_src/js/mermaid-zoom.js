// Interactive zoom/pan for Mermaid diagrams
document.addEventListener('DOMContentLoaded', function() {
    // Wait for mermaid to render
    setTimeout(function() {
        initializeMermaidZoom();
    }, 1000);
    
    // Also initialize on dynamic content changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                setTimeout(initializeMermaidZoom, 500);
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

function initializeMermaidZoom() {
    // Find all mermaid diagrams
    const mermaidDivs = document.querySelectorAll('.mermaid');
    
    mermaidDivs.forEach(function(div, index) {
        const svg = div.querySelector('svg');
        
        if (svg && !svg.hasAttribute('data-zoom-initialized')) {
            // Mark as initialized to avoid duplicate initialization
            svg.setAttribute('data-zoom-initialized', 'true');
            
            // Only add zoom to larger diagrams (skip simple ones)
            const bbox = svg.getBBox ? svg.getBBox() : null;
            if (bbox && (bbox.width > 400 || bbox.height > 300)) {
                
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
                    
                } catch (error) {
                    console.log('SVG Pan Zoom not available for diagram:', svg.id);
                    // Fallback: basic CSS zoom on hover
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
            }
        }
    });
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