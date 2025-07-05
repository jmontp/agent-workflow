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
    
    // Setup "All" checkbox handler for Context Collection Tester
    const allCheckbox = document.getElementById('include-all');
    if (allCheckbox) {
        allCheckbox.addEventListener('change', toggleAllIncludes);
    }
    
    // Initialize preset examples for Context Collection Tester
    const presetSelect = document.getElementById('preset-examples-select');
    if (presetSelect && presetSelect.options.length === 1) {
        presetExamples.forEach(example => {
            const option = document.createElement('option');
            option.value = example.value;
            option.textContent = example.text;
            presetSelect.appendChild(option);
        });
    }
    
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

// Context Collection Tester Functions
function toggleAdvancedOptions() {
    const advancedOptions = document.getElementById('advanced-options');
    const toggleIndicator = document.getElementById('advanced-toggle');
    
    if (advancedOptions.style.display === 'none') {
        advancedOptions.style.display = 'block';
        toggleIndicator.classList.add('expanded');
        toggleIndicator.textContent = '▼';
    } else {
        advancedOptions.style.display = 'none';
        toggleIndicator.classList.remove('expanded');
        toggleIndicator.textContent = '▶';
    }
}

function loadPresetExample() {
    const select = document.getElementById('preset-examples-select');
    const textarea = document.getElementById('task-description');
    
    if (select.value) {
        textarea.value = select.value;
    }
}

function loadExample() {
    // Load a random example
    const examples = [
        "Fix the authentication bug in the login system",
        "Add dark mode support to the UI",
        "Write unit tests for the Context Manager",
        "Document the API endpoints"
    ];
    
    const randomExample = examples[Math.floor(Math.random() * examples.length)];
    document.getElementById('task-description').value = randomExample;
    document.getElementById('preset-examples-select').value = randomExample;
}

function clearContextCollection() {
    clearContext();
}

async function collectContext() {
    const taskDescription = document.getElementById('task-description').value.trim();
    
    if (!taskDescription) {
        showStatus('Please enter a task description', 'error');
        return;
    }
    
    // Gather all parameters
    const params = {
        task_description: taskDescription,
        agent_type: document.getElementById('agent-type').value,
        max_tokens: parseInt(document.getElementById('max-tokens').value),
        min_relevance: parseFloat(document.getElementById('min-relevance').value),
        explain_selection: document.getElementById('explain-selection').checked
    };
    
    // Determine include types
    const includeTypes = [];
    if (document.getElementById('include-all').checked) {
        includeTypes.push('all');
    } else {
        if (document.getElementById('include-code').checked) includeTypes.push('code');
        if (document.getElementById('include-docs').checked) includeTypes.push('docs');
        if (document.getElementById('include-contexts').checked) includeTypes.push('contexts');
        if (document.getElementById('include-folders').checked) includeTypes.push('folders');
    }
    params.include_types = includeTypes;
    
    // Get exclude patterns
    const excludePatterns = document.getElementById('exclude-patterns').value.trim();
    if (excludePatterns) {
        params.exclude_patterns = excludePatterns.split(',').map(p => p.trim());
    }
    
    // Show loading state
    showStatus('Collecting context...', 'info');
    document.getElementById('context-results').style.display = 'none';
    
    try {
        const response = await fetch('/api/context/collect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Context collection failed');
        }
        
        // Display results
        displayContextResults(data);
        showStatus('Context collected successfully', 'success');
        
    } catch (error) {
        showStatus(`Failed to collect context: ${error.message}`, 'error');
    }
}

// Store the last context collection data globally for the agent view
let lastContextCollectionData = null;

function displayContextResults(data) {
    const resultsDiv = document.getElementById('context-results');
    resultsDiv.style.display = 'block';
    
    // Store the data for agent view
    lastContextCollectionData = data;
    window.currentContextData = data;
    
    // Display task analysis using the new render function
    const analysisDiv = document.getElementById('task-analysis');
    analysisDiv.innerHTML = renderTaskAnalysis(data.task_analysis);
    
    // Display token usage visualization
    const tokenVizDiv = document.getElementById('token-usage-viz');
    const totalTokens = data.metadata?.token_usage?.total || 0;
    const maxTokens = data.metadata?.max_tokens || 8000;
    tokenVizDiv.innerHTML = renderTokenUsage(data, totalTokens, maxTokens);
    
    // Display collected items
    const itemsDiv = document.getElementById('collected-items');
    itemsDiv.innerHTML = renderCollectedItems(data);
    
    // Add agent view button if we have the formatted data
    if (data.agent_formatted || data.agent_view) {
        const buttonDiv = document.createElement('div');
        buttonDiv.style.marginTop = '20px';
        buttonDiv.innerHTML = `
            <button class="btn btn-primary" onclick="showAgentView()">Show Agent View</button>
        `;
        resultsDiv.appendChild(buttonDiv);
    }
}

// Export functions
async function exportToJSON() {
    const taskDescription = document.getElementById('task-description').value;
    
    if (!taskDescription) {
        showStatus('No context collection to export', 'error');
        return;
    }
    
    // Re-collect the context to get fresh data
    try {
        const response = await fetch('/api/context/collect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                task_description: taskDescription,
                agent_type: document.getElementById('agent-type').value,
                max_tokens: parseInt(document.getElementById('max-tokens').value)
            })
        });
        
        const data = await response.json();
        
        // Create and download JSON file
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `context-collection-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        showStatus('Exported to JSON', 'success');
    } catch (error) {
        showStatus('Export failed', 'error');
    }
}

async function exportToMarkdown() {
    const taskDescription = document.getElementById('task-description').value;
    
    if (!taskDescription) {
        showStatus('No context collection to export', 'error');
        return;
    }
    
    // Re-collect the context to get fresh data
    try {
        const response = await fetch('/api/context/collect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                task_description: taskDescription,
                agent_type: document.getElementById('agent-type').value,
                max_tokens: parseInt(document.getElementById('max-tokens').value)
            })
        });
        
        const data = await response.json();
        
        // Create markdown content
        let markdown = `# Context Collection Report\n\n`;
        markdown += `**Task:** ${taskDescription}\n\n`;
        markdown += `**Generated:** ${new Date().toISOString()}\n\n`;
        
        if (data.metadata) {
            markdown += `## Metadata\n\n`;
            markdown += `- Agent Type: ${data.metadata.agent_type}\n`;
            markdown += `- Total Tokens: ${data.metadata.token_usage.total}\n`;
            markdown += `- Max Tokens: ${data.metadata.max_tokens}\n\n`;
        }
        
        if (data.contexts && data.contexts.length > 0) {
            markdown += `## Contexts\n\n`;
            data.contexts.forEach(ctx => {
                markdown += `### ${ctx.type}\n\n`;
                markdown += `\`\`\`json\n${JSON.stringify(ctx.data, null, 2)}\n\`\`\`\n\n`;
            });
        }
        
        if (data.code && data.code.length > 0) {
            markdown += `## Code Files\n\n`;
            data.code.forEach(item => {
                markdown += `### ${item.path}\n\n`;
                markdown += `\`\`\`python\n${item.content}\n\`\`\`\n\n`;
            });
        }
        
        if (data.docs && data.docs.length > 0) {
            markdown += `## Documentation\n\n`;
            data.docs.forEach(item => {
                markdown += `### ${item.path}\n\n`;
                markdown += `${item.content}\n\n`;
            });
        }
        
        // Create and download markdown file
        const blob = new Blob([markdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `context-collection-${Date.now()}.md`;
        a.click();
        URL.revokeObjectURL(url);
        
        showStatus('Exported to Markdown', 'success');
    } catch (error) {
        showStatus('Export failed', 'error');
    }
}

async function copyToClipboard() {
    const taskDescription = document.getElementById('task-description').value;
    
    if (!taskDescription) {
        showStatus('No context collection to copy', 'error');
        return;
    }
    
    // Get the visible content from the results
    const resultsDiv = document.getElementById('context-results');
    const textContent = resultsDiv.innerText;
    
    try {
        await navigator.clipboard.writeText(textContent);
        showStatus('Copied to clipboard', 'success');
    } catch (error) {
        showStatus('Failed to copy to clipboard', 'error');
    }
}

// Context Collection Tester Functions

// Preset examples array
const presetExamples = [
    { value: "Fix the authentication bug in the login system", text: "Fix authentication bug" },
    { value: "Add dark mode support to the UI", text: "Add dark mode support" },
    { value: "Write unit tests for the Context Manager", text: "Write unit tests" },
    { value: "Document the API endpoints", text: "Document API endpoints" },
    { value: "Implement the Swiss Army Knife agent with TaskRequest/TaskResult schema", text: "Implement Swiss Army Knife agent" },
    { value: "Refactor the state machine to use async/await", text: "Refactor state machine" },
    { value: "Add WebSocket error handling and reconnection logic", text: "Add WebSocket error handling" },
    { value: "Create a new visualization for project dependencies", text: "Create dependency visualization" },
    { value: "Optimize the context collection algorithm for better performance", text: "Optimize context collection" },
    { value: "Debug why the project initialization is failing", text: "Debug project initialization" }
];


// Toggle advanced options visibility
function toggleAdvancedOptions() {
    const advancedSection = document.getElementById('advanced-options');
    const toggleBtn = document.querySelector('.advanced-toggle');
    
    if (advancedSection.style.display === 'none' || !advancedSection.style.display) {
        advancedSection.style.display = 'block';
        toggleBtn.textContent = '▼ Advanced Options';
    } else {
        advancedSection.style.display = 'none';
        toggleBtn.textContent = '▶ Advanced Options';
    }
}

// Load preset example into textarea
function loadExample() {
    const select = document.getElementById('preset-examples-select');
    const textarea = document.getElementById('task-description');
    
    if (select.value) {
        textarea.value = select.value;
    }
}

// Clear context collection form and results
function clearContext() {
    // Clear form inputs
    document.getElementById('task-description').value = '';
    document.getElementById('preset-examples-select').value = '';
    document.getElementById('agent-type').value = 'swiss_army_knife';
    document.getElementById('max-tokens').value = '8000';
    document.getElementById('min-relevance').value = '0.3';
    document.getElementById('exclude-patterns').value = '';
    document.getElementById('explain-selection').checked = false;
    
    // Reset checkboxes
    document.getElementById('include-all').checked = true;
    toggleAllIncludes(); // This will check all sub-checkboxes
    
    // Hide results
    document.getElementById('context-results').style.display = 'none';
    
    showStatus('Context collection cleared', 'info');
}

// Render task analysis section
function renderTaskAnalysis(analysis) {
    if (!analysis) return '<p>No task analysis available</p>';
    
    let html = '<div class="task-analysis-content">';
    
    if (analysis.keywords && analysis.keywords.length > 0) {
        html += '<div class="analysis-item">';
        html += '<strong>Keywords:</strong> ';
        html += analysis.keywords.map(k => `<span class="keyword-tag">${k}</span>`).join(' ');
        html += '</div>';
    }
    
    if (analysis.actions && analysis.actions.length > 0) {
        html += '<div class="analysis-item">';
        html += '<strong>Actions:</strong> ';
        html += analysis.actions.map(a => `<span class="action-tag">${a}</span>`).join(' ');
        html += '</div>';
    }
    
    if (analysis.concepts && analysis.concepts.length > 0) {
        html += '<div class="analysis-item">';
        html += '<strong>Concepts:</strong> ';
        html += analysis.concepts.map(c => `<span class="concept-tag">${c}</span>`).join(' ');
        html += '</div>';
    }
    
    if (analysis.complexity) {
        html += '<div class="analysis-item">';
        html += `<strong>Complexity:</strong> <span class="complexity-${analysis.complexity}">${analysis.complexity}</span>`;
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

// Render token usage visualization
function renderTokenUsage(items, totalTokens, maxTokens) {
    // Calculate token counts by type
    const tokensByType = {
        contexts: 0,
        code: 0,
        docs: 0,
        folders: 0
    };
    
    // Count tokens from items
    if (items.contexts) tokensByType.contexts = items.contexts.reduce((sum, c) => sum + (c.token_count || 0), 0);
    if (items.code) tokensByType.code = items.code.reduce((sum, c) => sum + (c.token_count || 0), 0);
    if (items.docs) tokensByType.docs = items.docs.reduce((sum, d) => sum + (d.token_count || 0), 0);
    if (items.folders) tokensByType.folders = items.folders.reduce((sum, f) => sum + (f.token_count || 0), 0);
    
    let html = '<div class="token-usage-chart">';
    
    // Create bars for each type
    const types = [
        { name: 'Contexts', key: 'contexts', color: '#0066ff' },
        { name: 'Code', key: 'code', color: '#4CAF50' },
        { name: 'Docs', key: 'docs', color: '#2196F3' },
        { name: 'Folders', key: 'folders', color: '#ff9800' }
    ];
    
    types.forEach(type => {
        const tokens = tokensByType[type.key];
        const percentage = totalTokens > 0 ? (tokens / totalTokens * 100) : 0;
        
        html += `
            <div class="token-usage-row">
                <span class="token-type-label">${type.name}:</span>
                <div class="token-bar-wrapper">
                    <div class="token-bar" style="width: ${percentage}%; background-color: ${type.color};"></div>
                </div>
                <span class="token-count">${tokens.toLocaleString()} (${percentage.toFixed(1)}%)</span>
            </div>
        `;
    });
    
    // Total usage bar
    const usagePercentage = maxTokens > 0 ? (totalTokens / maxTokens * 100) : 0;
    html += `
        <div class="token-usage-total">
            <strong>Total Usage:</strong>
            <div class="token-bar-wrapper">
                <div class="token-bar ${usagePercentage > 90 ? 'warning' : ''}" 
                     style="width: ${usagePercentage}%; background-color: ${usagePercentage > 90 ? '#f44336' : '#0066ff'};"></div>
            </div>
            <span>${totalTokens.toLocaleString()} / ${maxTokens.toLocaleString()} (${usagePercentage.toFixed(1)}%)</span>
        </div>
    `;
    
    html += '</div>';
    return html;
}

// Render collected items in organized sections
function renderCollectedItems(items) {
    let html = '<div class="collected-items-container">';
    
    // Add "Show Agent View" button at the top
    html += '<div class="agent-view-controls">';
    html += '<button class="btn btn-primary" onclick="showAgentView()">Show Agent View</button>';
    html += '</div>';
    
    // Render contexts
    if (items.contexts && items.contexts.length > 0) {
        html += '<div class="item-section">';
        html += `<h4>Contexts (${items.contexts.length})</h4>`;
        items.contexts.forEach(ctx => {
            html += renderItemCard('context', ctx);
        });
        html += '</div>';
    }
    
    // Render code
    if (items.code && items.code.length > 0) {
        html += '<div class="item-section">';
        html += `<h4>Code Files (${items.code.length})</h4>`;
        items.code.forEach(item => {
            html += renderItemCard('code', item);
        });
        html += '</div>';
    }
    
    // Render docs
    if (items.docs && items.docs.length > 0) {
        html += '<div class="item-section">';
        html += `<h4>Documentation (${items.docs.length})</h4>`;
        items.docs.forEach(item => {
            html += renderItemCard('doc', item);
        });
        html += '</div>';
    }
    
    // Render folders
    if (items.folders && items.folders.length > 0) {
        html += '<div class="item-section">';
        html += `<h4>Folder Descriptions (${items.folders.length})</h4>`;
        items.folders.forEach(item => {
            html += renderItemCard('folder', item);
        });
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

// Render individual item card
function renderItemCard(type, item) {
    let title, content, relevance, tokens, explanation;
    
    if (type === 'context') {
        title = `${item.type} Context`;
        content = JSON.stringify(item.data, null, 2);
        relevance = item.relevance_score;
        tokens = item.token_count;
    } else {
        title = item.path || 'Unknown';
        content = item.content || item.description || '';
        relevance = item.relevance_score;
        tokens = item.token_count;
        explanation = item.selection_reason;
    }
    
    return `
        <div class="collected-item-card ${type}">
            <div class="item-header">
                <span class="item-type-badge ${type}">${type}</span>
                <span class="item-title">${title}</span>
                ${relevance ? `<span class="item-relevance">${(relevance * 100).toFixed(0)}%</span>` : ''}
                ${tokens ? `<span class="item-tokens">${tokens} tokens</span>` : ''}
            </div>
            ${explanation ? `<div class="item-explanation">${explanation}</div>` : ''}
            <div class="item-content">
                <pre>${escapeHtml(content.substring(0, 500))}${content.length > 500 ? '...' : ''}</pre>
            </div>
        </div>
    `;
}

// Escape HTML for safe display
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show Agent View modal
function showAgentView() {
    if (!lastContextCollectionData || !lastContextCollectionData.agent_formatted) {
        showStatus('No agent view available', 'error');
        return;
    }
    
    // Create modal if it doesn't exist
    let modal = document.getElementById('agent-view-modal');
    if (!modal) {
        modal = createAgentViewModal();
        document.body.appendChild(modal);
    }
    
    // Get the agent-formatted content
    const agentContent = lastContextCollectionData.agent_formatted;
    const totalTokens = lastContextCollectionData.total_tokens || 0;
    
    // Update modal content
    const contentEl = document.getElementById('agent-view-content');
    const tokenCountEl = document.getElementById('agent-view-token-count');
    
    // Add line numbers to the content
    const lines = agentContent.split('\n');
    const numberedContent = lines.map((line, i) => {
        const lineNum = (i + 1).toString().padStart(4, ' ');
        return `<span class="line-number">${lineNum}</span>${escapeHtml(line)}`;
    }).join('\n');
    
    contentEl.innerHTML = numberedContent;
    tokenCountEl.textContent = `Total Tokens: ${totalTokens.toLocaleString()}`;
    
    // Show modal
    modal.style.display = 'block';
}

// Create the Agent View modal
function createAgentViewModal() {
    const modal = document.createElement('div');
    modal.id = 'agent-view-modal';
    modal.className = 'agent-view-modal';
    modal.innerHTML = `
        <div class="agent-view-modal-content">
            <div class="agent-view-header">
                <h3>Agent View</h3>
                <div class="agent-view-actions">
                    <span id="agent-view-token-count" class="token-count"></span>
                    <button class="btn btn-secondary" onclick="copyAgentView()">Copy to Clipboard</button>
                    <button class="btn btn-close" onclick="closeAgentView()">×</button>
                </div>
            </div>
            <div class="agent-view-body">
                <pre id="agent-view-content" class="agent-view-pre"></pre>
            </div>
        </div>
    `;
    
    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeAgentView();
        }
    });
    
    return modal;
}

// Close Agent View modal
function closeAgentView() {
    const modal = document.getElementById('agent-view-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Copy agent view to clipboard
async function copyAgentView() {
    if (!lastContextCollectionData || !lastContextCollectionData.agent_formatted) {
        showStatus('No content to copy', 'error');
        return;
    }
    
    try {
        await navigator.clipboard.writeText(lastContextCollectionData.agent_formatted);
        showStatus('Copied to clipboard', 'success');
    } catch (error) {
        showStatus('Failed to copy to clipboard', 'error');
    }
}

// Export results in different formats
// Show Agent View function
function showAgentView() {
    const data = window.currentContextData;
    if (!data || (!data.agent_formatted && !data.agent_view)) {
        showStatus('No agent view available', 'error');
        return;
    }
    
    const agentContent = data.agent_formatted || data.agent_view;
    
    // Create modal overlay
    const modalOverlay = document.createElement('div');
    modalOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: #1a1a1a;
        border-radius: 8px;
        width: 90%;
        max-width: 1200px;
        height: 80vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    `;
    
    // Create header
    const header = document.createElement('div');
    header.style.cssText = `
        padding: 20px;
        border-bottom: 1px solid #333;
        display: flex;
        justify-content: space-between;
        align-items: center;
    `;
    header.innerHTML = `
        <h3 style="margin: 0; color: #fff;">Agent View - Complete Context</h3>
        <div>
            <button class="btn btn-secondary" onclick="copyAgentView()" style="margin-right: 10px;">Copy to Clipboard</button>
            <button class="btn btn-secondary" onclick="closeAgentView()">Close</button>
        </div>
    `;
    
    // Create content area
    const contentArea = document.createElement('div');
    contentArea.style.cssText = `
        flex: 1;
        overflow: auto;
        padding: 20px;
    `;
    
    // Create pre element for the content
    const pre = document.createElement('pre');
    pre.style.cssText = `
        margin: 0;
        font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.5;
        color: #e0e0e0;
        white-space: pre-wrap;
        word-wrap: break-word;
    `;
    pre.textContent = agentContent;
    
    // Store agent content globally for copy function
    window.currentAgentView = agentContent;
    
    // Assemble modal
    contentArea.appendChild(pre);
    modalContent.appendChild(header);
    modalContent.appendChild(contentArea);
    modalOverlay.appendChild(modalContent);
    document.body.appendChild(modalOverlay);
    
    // Store reference for closing
    window.agentViewModal = modalOverlay;
    
    // Close on overlay click
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) {
            closeAgentView();
        }
    });
    
    // Close on escape key
    document.addEventListener('keydown', function escapeHandler(e) {
        if (e.key === 'Escape') {
            closeAgentView();
            document.removeEventListener('keydown', escapeHandler);
        }
    });
}

function closeAgentView() {
    if (window.agentViewModal) {
        window.agentViewModal.remove();
        window.agentViewModal = null;
    }
}

function copyAgentView() {
    if (window.currentAgentView) {
        navigator.clipboard.writeText(window.currentAgentView).then(() => {
            showStatus('Agent view copied to clipboard!', 'success');
        }).catch(err => {
            showStatus('Failed to copy to clipboard', 'error');
            console.error('Copy failed:', err);
        });
    }
}

function exportResults(format) {
    const resultsDiv = document.getElementById('context-results');
    if (resultsDiv.style.display === 'none') {
        showStatus('No results to export', 'error');
        return;
    }
    
    // Get the last collected context data
    const taskDescription = document.getElementById('task-description').value;
    
    switch(format) {
        case 'json':
            exportToJSON();
            break;
        case 'markdown':
            exportToMarkdown();
            break;
        case 'clipboard':
            copyToClipboard();
            break;
    }
}

// Toggle all include checkboxes
function toggleAllIncludes() {
    const allCheckbox = document.getElementById('include-all');
    const checkboxes = ['include-code', 'include-docs', 'include-contexts', 'include-folders'];
    
    checkboxes.forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox) {
            checkbox.checked = allCheckbox.checked;
            checkbox.disabled = allCheckbox.checked;
        }
    });
}

// Add CSS for token usage visualization
const style = document.createElement('style');
style.textContent = `
.token-usage-bars {
    padding: 10px;
}

.token-bar-row {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
}

.token-bar-label {
    width: 80px;
    font-weight: 500;
}

.token-bar-container {
    flex: 1;
    height: 20px;
    background: #e0e0e0;
    border-radius: 10px;
    margin: 0 10px;
    overflow: hidden;
}

.token-bar {
    height: 100%;
    transition: width 0.3s ease;
}

.token-bar-value {
    width: 120px;
    text-align: right;
    font-size: 0.9em;
    color: #666;
}

.token-total {
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid #ddd;
    text-align: center;
}

/* Context Collection Tester Styles */
.task-analysis-content {
    padding: 10px;
}

.analysis-item {
    margin-bottom: 10px;
}

.keyword-tag, .action-tag, .concept-tag {
    display: inline-block;
    padding: 2px 8px;
    margin: 2px;
    border-radius: 12px;
    font-size: 0.85em;
    background: #e3f2fd;
    color: #1976d2;
}

.action-tag {
    background: #e8f5e9;
    color: #388e3c;
}

.concept-tag {
    background: #fff3e0;
    color: #f57c00;
}

.complexity-low { color: #4caf50; }
.complexity-medium { color: #ff9800; }
.complexity-high { color: #f44336; }

.token-usage-chart {
    padding: 15px;
}

.token-usage-row {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
}

.token-type-label {
    width: 80px;
    font-weight: 500;
}

.token-bar-wrapper {
    flex: 1;
    height: 20px;
    background: #f0f0f0;
    border-radius: 10px;
    margin: 0 10px;
    position: relative;
    overflow: hidden;
}

.token-bar {
    height: 100%;
    transition: width 0.3s ease;
}

.token-bar.warning {
    background: #f44336 !important;
}

.token-count {
    width: 150px;
    text-align: right;
    font-size: 0.9em;
}

.token-usage-total {
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid #ddd;
}

.collected-items-container {
    padding: 10px;
}

.item-section {
    margin-bottom: 20px;
}

.item-section h4 {
    margin-bottom: 10px;
    color: #333;
}

.collected-item-card {
    background: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 8px;
    margin-bottom: 10px;
    padding: 12px;
}

.collected-item-card.context { border-left: 4px solid #0066ff; }
.collected-item-card.code { border-left: 4px solid #4caf50; }
.collected-item-card.doc { border-left: 4px solid #2196f3; }
.collected-item-card.folder { border-left: 4px solid #ff9800; }

.item-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}

.item-type-badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: 500;
    text-transform: uppercase;
}

.item-type-badge.context { background: #e3f2fd; color: #0066ff; }
.item-type-badge.code { background: #e8f5e9; color: #4caf50; }
.item-type-badge.doc { background: #e3f2fd; color: #2196f3; }
.item-type-badge.folder { background: #fff3e0; color: #ff9800; }

.item-title {
    flex: 1;
    font-weight: 500;
}

.item-relevance {
    background: #4caf50;
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.85em;
}

.item-tokens {
    color: #666;
    font-size: 0.85em;
}

.item-explanation {
    margin-bottom: 8px;
    padding: 8px;
    background: #f0f0f0;
    border-radius: 4px;
    font-size: 0.9em;
    font-style: italic;
    color: #555;
}

.item-content {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 8px;
    overflow-x: auto;
}

.item-content pre {
    margin: 0;
    font-size: 0.85em;
    white-space: pre-wrap;
    word-wrap: break-word;
}

/* Agent View Modal Styles */
.agent-view-modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    overflow: auto;
    background-color: rgba(0, 0, 0, 0.4);
}

.agent-view-modal-content {
    background-color: #1e1e1e;
    margin: 2% auto;
    padding: 0;
    border: 1px solid #888;
    border-radius: 8px;
    width: 90%;
    max-width: 1200px;
    height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.agent-view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    background-color: #2d2d2d;
    border-bottom: 1px solid #444;
    border-radius: 8px 8px 0 0;
}

.agent-view-header h3 {
    margin: 0;
    color: #fff;
}

.agent-view-actions {
    display: flex;
    align-items: center;
    gap: 15px;
}

.agent-view-actions .token-count {
    color: #aaa;
    font-size: 14px;
}

.agent-view-actions .btn {
    padding: 6px 12px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

.agent-view-actions .btn-secondary {
    background-color: #4a4a4a;
    color: #fff;
}

.agent-view-actions .btn-secondary:hover {
    background-color: #5a5a5a;
}

.agent-view-actions .btn-close {
    background-color: transparent;
    color: #aaa;
    font-size: 24px;
    padding: 0;
    width: 30px;
    height: 30px;
}

.agent-view-actions .btn-close:hover {
    color: #fff;
}

.agent-view-body {
    flex: 1;
    overflow: auto;
    padding: 20px;
    background-color: #1e1e1e;
}

.agent-view-pre {
    margin: 0;
    padding: 0;
    background-color: transparent;
    color: #d4d4d4;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.5;
    white-space: pre;
    overflow-x: auto;
}

.line-number {
    display: inline-block;
    width: 50px;
    padding-right: 15px;
    color: #858585;
    text-align: right;
    user-select: none;
    border-right: 1px solid #404040;
    margin-right: 15px;
}

.agent-view-controls {
    margin-bottom: 15px;
    text-align: center;
}

.agent-view-controls .btn {
    background-color: #0066ff;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

.agent-view-controls .btn:hover {
    background-color: #0052cc;
}
`;
document.head.appendChild(style);