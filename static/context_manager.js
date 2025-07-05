// Context Manager UI JavaScript

let contextTypesChart = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeChart();
    loadStats();
    loadRecentContexts();
    loadSuggestions();
    loadPatterns();
    checkProjectStatus();
    
    // Load visualization if project is initialized
    checkAndLoadVisualization();
    
    // Refresh data every 30 seconds
    setInterval(() => {
        loadStats();
        loadRecentContexts();
    }, 30000);
});

// Initialize Chart.js
function initializeChart() {
    const ctx = document.getElementById('context-types-chart').getContext('2d');
    contextTypesChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#0066ff', '#4CAF50', '#f44336', '#ff9800',
                    '#2196F3', '#9C27B0', '#795548'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/context/stats');
        const stats = await response.json();
        
        // Update stat cards
        document.getElementById('total-contexts').textContent = stats.total_contexts;
        document.getElementById('patterns-detected').textContent = stats.patterns_detected;
        document.getElementById('docs-analyzed').textContent = stats.docs_analyzed || 0;
        document.getElementById('current-project').textContent = stats.project_id;
        
        // Update chart
        const types = Object.entries(stats.by_type).filter(([_, count]) => count > 0);
        contextTypesChart.data.labels = types.map(([type, _]) => type);
        contextTypesChart.data.datasets[0].data = types.map(([_, count]) => count);
        contextTypesChart.update();
    } catch (error) {
        showStatus('Failed to load statistics', 'error');
    }
}

// Load recent contexts
async function loadRecentContexts() {
    try {
        const response = await fetch('/api/context/query?limit=10');
        const contexts = await response.json();
        
        const listEl = document.getElementById('contexts-list');
        if (contexts.length === 0) {
            listEl.innerHTML = '<p class="loading">No contexts found</p>';
            return;
        }
        
        listEl.innerHTML = contexts.map(ctx => `
            <div class="context-item">
                <div class="context-header">
                    <span class="context-type ${ctx.type}">${ctx.type}</span>
                    <span class="context-time">${formatTime(ctx.timestamp)}</span>
                </div>
                <div class="context-data">${formatContextData(ctx)}</div>
                ${ctx.tags.length > 0 ? `
                    <div class="context-tags">
                        ${ctx.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');
    } catch (error) {
        showStatus('Failed to load contexts', 'error');
    }
}

// Load suggestions
async function loadSuggestions() {
    try {
        const response = await fetch('/api/context/suggest');
        const data = await response.json();
        const suggestions = data.suggestions;
        
        const listEl = document.getElementById('suggestions-list');
        if (!suggestions || suggestions.length === 0) {
            listEl.innerHTML = '<p class="loading">No suggestions at this time</p>';
            return;
        }
        
        listEl.innerHTML = suggestions.map(s => `
            <div class="suggestion-item">
                <span class="suggestion-confidence">${(s.confidence * 100).toFixed(0)}%</span>
                <div class="suggestion-task">${s.task}</div>
                <div class="suggestion-reason">${s.reason}</div>
            </div>
        `).join('');
    } catch (error) {
        showStatus('Failed to load suggestions', 'error');
    }
}

// Load patterns
async function loadPatterns() {
    try {
        const response = await fetch('/api/context/patterns?min=2');
        const patterns = await response.json();
        
        const listEl = document.getElementById('patterns-list');
        const patternEntries = Object.entries(patterns);
        
        if (patternEntries.length === 0) {
            listEl.innerHTML = '<p class="loading">No patterns detected yet</p>';
            return;
        }
        
        // Sort by count descending
        patternEntries.sort((a, b) => b[1] - a[1]);
        
        listEl.innerHTML = patternEntries.slice(0, 10).map(([pattern, count]) => `
            <div class="pattern-item">
                <span class="pattern-name">${pattern}</span>
                <span class="pattern-count">${count}</span>
            </div>
        `).join('');
    } catch (error) {
        showStatus('Failed to load patterns', 'error');
    }
}

// Log decision
async function logDecision() {
    const decision = document.getElementById('decision-input').value.trim();
    const reasoning = document.getElementById('reasoning-input').value.trim();
    
    if (!decision || !reasoning) {
        showStatus('Please fill in both decision and reasoning', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/context/decision', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ decision, reasoning })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showStatus('Decision logged successfully', 'success');
            
            // Clear inputs
            document.getElementById('decision-input').value = '';
            document.getElementById('reasoning-input').value = '';
            
            // Reload data
            loadStats();
            loadRecentContexts();
            
            // Show suggestions if any
            if (result.suggestions && result.suggestions.length > 0) {
                loadSuggestions();
            }
        } else {
            showStatus('Failed to log decision', 'error');
        }
    } catch (error) {
        showStatus('Error logging decision', 'error');
    }
}

// Log error
async function logError() {
    const error = document.getElementById('error-input').value.trim();
    const context = document.getElementById('error-context').value.trim();
    
    if (!error) {
        showStatus('Please enter an error message', 'error');
        return;
    }
    
    try {
        const contextData = {
            type: 'error',
            source: 'web-ui',
            data: {
                error: error,
                context: context ? { note: context } : {}
            },
            tags: ['error', 'web-ui']
        };
        
        const response = await fetch('/api/context', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(contextData)
        });
        
        if (response.ok) {
            showStatus('Error logged successfully', 'success');
            
            // Clear inputs
            document.getElementById('error-input').value = '';
            document.getElementById('error-context').value = '';
            
            // Reload data
            loadStats();
            loadRecentContexts();
        } else {
            showStatus('Failed to log error', 'error');
        }
    } catch (error) {
        showStatus('Error logging error', 'error');
    }
}

// Query contexts
async function queryContexts() {
    const query = document.getElementById('query-input').value.trim();
    const type = document.getElementById('type-filter').value;
    
    let url = '/api/context/query?limit=20';
    if (query) url += `&q=${encodeURIComponent(query)}`;
    if (type) url += `&type=${type}`;
    
    try {
        const response = await fetch(url);
        const contexts = await response.json();
        
        const listEl = document.getElementById('contexts-list');
        if (contexts.length === 0) {
            listEl.innerHTML = '<p class="loading">No contexts found matching criteria</p>';
            return;
        }
        
        listEl.innerHTML = contexts.map(ctx => `
            <div class="context-item">
                <div class="context-header">
                    <span class="context-type ${ctx.type}">${ctx.type}</span>
                    <span class="context-time">${formatTime(ctx.timestamp)}</span>
                </div>
                <div class="context-data">${formatContextData(ctx)}</div>
                ${ctx.tags.length > 0 ? `
                    <div class="context-tags">
                        ${ctx.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        showStatus(`Found ${contexts.length} contexts`, 'info');
    } catch (error) {
        showStatus('Failed to query contexts', 'error');
    }
}

// Analyze document
async function analyzeDoc() {
    const docPath = document.getElementById('doc-path-input').value.trim();
    
    if (!docPath) {
        showStatus('Please enter a document path', 'error');
        return;
    }
    
    showStatus('Analyzing document...', 'info');
    
    try {
        // Use the cm CLI backend through a custom endpoint
        const response = await fetch('/api/context/analyze-doc', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ doc_path: docPath })
        });
        
        if (!response.ok) {
            throw new Error('Failed to analyze document');
        }
        
        const result = await response.json();
        
        // Display results
        const resultsEl = document.getElementById('doc-results');
        resultsEl.innerHTML = `
            <div class="doc-result">
                <h4>${docPath}</h4>
                <p>Document Type: <strong>${result.doc_type}</strong></p>
                <div class="quality-scores">
                    ${Object.entries(result.quality_scores).map(([metric, score]) => `
                        <div class="quality-score">
                            <span class="quality-score-label">${metric}:</span>
                            <div class="quality-score-bar">
                                <div class="quality-score-fill" style="width: ${score * 100}%"></div>
                            </div>
                            <span class="quality-score-value">${(score * 100).toFixed(0)}%</span>
                        </div>
                    `).join('')}
                </div>
                ${result.staleness_indicators.length > 0 ? `
                    <p class="staleness-warning">⚠️ Staleness indicators: ${result.staleness_indicators.join(', ')}</p>
                ` : ''}
            </div>
        `;
        
        showStatus('Document analyzed successfully', 'success');
    } catch (error) {
        showStatus('Failed to analyze document', 'error');
    }
}

// Learn patterns
async function learnPatterns() {
    showStatus('Learning documentation patterns...', 'info');
    
    try {
        const response = await fetch('/api/context/learn-patterns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error('Failed to learn patterns');
        }
        
        const result = await response.json();
        
        showStatus(
            `Learned patterns from ${result.files_analyzed} files: ` +
            `${result.headers_found} headers, ${result.phrases_found} common phrases`,
            'success'
        );
        
        // Reload patterns
        loadPatterns();
    } catch (error) {
        showStatus('Failed to learn patterns', 'error');
    }
}

// Refresh suggestions
function refreshSuggestions() {
    loadSuggestions();
    showStatus('Suggestions refreshed', 'info');
}

// Helper functions
function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatContextData(ctx) {
    if (ctx.type === 'decision') {
        return `<strong>Decision:</strong> ${ctx.data.decision}<br><strong>Reasoning:</strong> ${ctx.data.reasoning}`;
    } else if (ctx.type === 'error') {
        return `<strong>Error:</strong> ${ctx.data.error}`;
    } else {
        const dataStr = JSON.stringify(ctx.data);
        return dataStr.length > 100 ? dataStr.substring(0, 100) + '...' : dataStr;
    }
}

function showStatus(message, type) {
    const statusEl = document.getElementById('status-message');
    statusEl.textContent = message;
    statusEl.className = `status-message ${type}`;
    statusEl.style.display = 'block';
    
    setTimeout(() => {
        statusEl.style.display = 'none';
    }, 3000);
}

// Check project initialization status
async function checkProjectStatus() {
    try {
        const response = await fetch('/api/context/project-status');
        const status = await response.json();
        
        const statusEl = document.getElementById('project-status');
        const initBtn = document.getElementById('init-btn');
        
        if (status.initialized) {
            statusEl.className = 'project-status initialized';
            statusEl.innerHTML = `
                ✅ Project initialized<br>
                <small>Last indexed: ${new Date(status.index_timestamp).toLocaleString()}</small><br>
                <small>${status.total_concepts} concepts, ${status.total_functions} functions, ${status.total_classes} classes</small>
            `;
            initBtn.textContent = 'Re-initialize Project';
        } else {
            statusEl.className = 'project-status not-initialized';
            statusEl.innerHTML = '⚠️ ' + status.message;
            initBtn.textContent = 'Initialize Project';
        }
    } catch (error) {
        console.error('Failed to check project status:', error);
    }
}

// Initialize project
async function initializeProject() {
    const btn = document.getElementById('init-btn');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Initializing...';
    
    showStatus('Scanning project files...', 'info');
    
    try {
        const response = await fetch('/api/context/init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_root: '.' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus(
                `Project initialized! Scanned ${result.files_scanned} files, found ${result.concepts_mapped} concepts in ${result.duration_seconds.toFixed(1)}s`,
                'success'
            );
            
            // Reload project status
            checkProjectStatus();
            
            // Reload stats
            loadStats();
        } else {
            showStatus('Failed to initialize project: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showStatus('Error initializing project', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

// Find information
async function findInformation() {
    const query = document.getElementById('find-input').value.trim();
    
    if (!query) {
        showStatus('Please enter a search query', 'error');
        return;
    }
    
    const resultsEl = document.getElementById('find-results');
    resultsEl.innerHTML = '<p class="loading">Searching...</p>';
    
    try {
        const response = await fetch('/api/context/find', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        
        if (response.status === 400 && data.not_initialized) {
            resultsEl.innerHTML = '<p class="error">Project not initialized. Click "Initialize Project" first.</p>';
            showStatus('Project not initialized', 'error');
            return;
        }
        
        if (!response.ok) {
            throw new Error(data.error || 'Search failed');
        }
        
        const results = data.results;
        
        if (results.length === 0) {
            resultsEl.innerHTML = '<p class="loading">No results found</p>';
        } else {
            resultsEl.innerHTML = results.map(r => `
                <div class="find-result-item">
                    <span class="find-result-confidence">${(r.confidence * 100).toFixed(0)}%</span>
                    <div class="find-result-file">${r.file}</div>
                    <div class="find-result-type">${r.content}</div>
                    <div class="find-result-context">${r.context}</div>
                </div>
            `).join('');
        }
    } catch (error) {
        resultsEl.innerHTML = `<p class="error">Search failed: ${error.message}</p>`;
        showStatus('Search failed', 'error');
    }
}

// Knowledge Graph Visualization
let graphData = null;
let simulation = null;
let svg = null;
let g = null;
let zoom = null;
let visibleTypes = {
    doc: true,
    code: true,
    concept: true
};

async function checkAndLoadVisualization() {
    try {
        const response = await fetch('/api/context/project-status');
        const status = await response.json();
        
        if (status.initialized) {
            loadKnowledgeGraph();
        }
    } catch (error) {
        console.error('Failed to check visualization status:', error);
    }
}

async function loadKnowledgeGraph() {
    try {
        const response = await fetch('/api/context/visualization/graph');
        if (!response.ok) {
            if (response.status === 400) {
                // Project not initialized
                return;
            }
            throw new Error('Failed to load graph data');
        }
        
        graphData = await response.json();
        
        // Display stats
        const statsEl = document.getElementById('graph-stats');
        statsEl.innerHTML = `
            <strong>Graph Statistics:</strong>
            ${graphData.stats.totalNodes} nodes
            (${graphData.stats.docNodes} docs,
            ${graphData.stats.codeNodes} code,
            ${graphData.stats.conceptNodes} concepts) |
            ${graphData.stats.totalEdges} connections
        `;
        
        renderGraph();
    } catch (error) {
        console.error('Failed to load knowledge graph:', error);
    }
}

function renderGraph() {
    const container = document.getElementById('visualization-container');
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Clear existing graph
    d3.select('#knowledge-graph').selectAll('*').remove();
    
    // Create SVG
    svg = d3.select('#knowledge-graph')
        .attr('width', width)
        .attr('height', height);
    
    // Create zoom behavior
    zoom = d3.zoom()
        .scaleExtent([0.1, 10])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });
    
    svg.call(zoom);
    
    // Create main group
    g = svg.append('g');
    
    // Create arrow markers for directed edges
    svg.append('defs').selectAll('marker')
        .data(['references', 'imports', 'contains'])
        .enter().append('marker')
        .attr('id', d => `arrow-${d}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 15)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', d => {
            if (d === 'references') return '#2196F3';
            if (d === 'imports') return '#4CAF50';
            return '#ff9800';
        });
    
    // Create force simulation
    simulation = d3.forceSimulation(graphData.nodes)
        .force('link', d3.forceLink(graphData.edges)
            .id(d => d.id)
            .distance(d => d.type === 'contains' ? 50 : 100))
        .force('charge', d3.forceManyBody()
            .strength(d => d.type === 'concept' ? -200 : -400))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide()
            .radius(d => d.type === 'concept' ? 15 : 20));
    
    // Create links
    const link = g.append('g')
        .selectAll('line')
        .data(graphData.edges)
        .enter().append('line')
        .attr('class', d => `link ${d.type}`)
        .attr('marker-end', d => `url(#arrow-${d.type})`);
    
    // Create nodes
    const node = g.append('g')
        .selectAll('g')
        .data(graphData.nodes)
        .enter().append('g')
        .attr('class', 'node-group')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add circles for nodes
    node.append('circle')
        .attr('class', d => `node ${d.type}`)
        .attr('r', d => {
            if (d.type === 'concept') return 8;
            if (d.type === 'code') return 10;
            return 12;
        })
        .on('click', showNodeInfo)
        .on('mouseover', highlightConnections)
        .on('mouseout', resetHighlight);
    
    // Add labels
    node.append('text')
        .attr('class', 'node-label')
        .attr('dy', -15)
        .text(d => d.label.length > 20 ? d.label.substring(0, 20) + '...' : d.label);
    
    // Update positions on tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
    
    // Apply initial visibility
    updateVisibility();
}

function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

function highlightConnections(event, d) {
    // Get connected nodes
    const connectedNodes = new Set();
    connectedNodes.add(d.id);
    
    graphData.edges.forEach(edge => {
        if (edge.source.id === d.id || edge.source === d.id) {
            connectedNodes.add(edge.target.id || edge.target);
        }
        if (edge.target.id === d.id || edge.target === d.id) {
            connectedNodes.add(edge.source.id || edge.source);
        }
    });
    
    // Update node styles
    d3.selectAll('.node').classed('dimmed', node => !connectedNodes.has(node.id));
    d3.selectAll('.node').classed('highlighted', node => node.id === d.id);
    
    // Update link styles
    d3.selectAll('.link').classed('dimmed', edge => {
        const sourceId = edge.source.id || edge.source;
        const targetId = edge.target.id || edge.target;
        return !connectedNodes.has(sourceId) || !connectedNodes.has(targetId);
    });
}

function resetHighlight() {
    d3.selectAll('.node').classed('dimmed', false).classed('highlighted', false);
    d3.selectAll('.link').classed('dimmed', false).classed('highlighted', false);
}

function showNodeInfo(event, d) {
    const infoEl = document.getElementById('node-info');
    infoEl.classList.add('active');
    
    let infoHtml = `<h4>${d.label}</h4>`;
    infoHtml += `<div class="info-row"><strong>Type:</strong> ${d.type}</div>`;
    
    if (d.path) {
        infoHtml += `<div class="info-row"><strong>Path:</strong> ${d.path}</div>`;
    }
    
    if (d.metrics) {
        infoHtml += '<div class="info-row"><strong>Metrics:</strong></div>';
        Object.entries(d.metrics).forEach(([key, value]) => {
            infoHtml += `<div class="info-row" style="margin-left: 20px">${key}: ${value}</div>`;
        });
    }
    
    infoEl.innerHTML = infoHtml;
}

function toggleNodeType(type) {
    visibleTypes[type] = !visibleTypes[type];
    updateVisibility();
}

function updateVisibility() {
    d3.selectAll('.node-group').style('display', d => visibleTypes[d.type] ? 'block' : 'none');
    
    d3.selectAll('.link').style('display', edge => {
        const source = graphData.nodes.find(n => n.id === (edge.source.id || edge.source));
        const target = graphData.nodes.find(n => n.id === (edge.target.id || edge.target));
        return visibleTypes[source.type] && visibleTypes[target.type] ? 'block' : 'none';
    });
}

function resetZoom() {
    svg.transition()
        .duration(750)
        .call(zoom.transform, d3.zoomIdentity);
}

// Visualization Switching
let currentVisualization = 'graph';
let visualizations = {
    treemap: null,
    tree: null
};

function switchVisualization(type) {
    // Update button states
    document.querySelectorAll('.viz-type-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Hide all visualizations
    document.querySelectorAll('.viz-content').forEach(viz => {
        viz.style.display = 'none';
    });
    
    // Show selected visualization
    document.getElementById(`viz-${type}`).style.display = 'block';
    currentVisualization = type;
    
    // Load visualization if needed
    switch (type) {
        case 'graph':
            // Already loaded
            break;
            
        case 'treemap':
            if (!visualizations.treemap) {
                visualizations.treemap = new ProjectTreemap('treemap-container');
                visualizations.treemap.load();
            }
            break;
            
        case 'tree':
            if (!visualizations.tree) {
                visualizations.tree = new DirectoryTreeView('tree-container', 'tree-details');
                visualizations.tree.load();
            }
            break;
    }
}