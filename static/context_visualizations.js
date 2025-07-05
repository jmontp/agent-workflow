// Additional Context Manager Visualizations

// Directory Tree Visualization
class DirectoryTreeView {
    constructor(containerId, detailsId) {
        this.containerId = containerId;
        this.detailsId = detailsId;
        this.data = null;
        this.selectedNode = null;
    }
    
    async load() {
        try {
            const response = await fetch('/api/context/visualization/directory-tree');
            if (!response.ok) throw new Error('Failed to load directory tree data');
            
            this.data = await response.json();
            this.render();
        } catch (error) {
            console.error('Failed to load directory tree:', error);
        }
    }
    
    render() {
        const container = document.getElementById(this.containerId);
        container.innerHTML = '';
        container.className = 'directory-tree';
        
        // Create tree structure
        const rootUl = document.createElement('ul');
        rootUl.className = 'tree-root';
        
        // Render the tree
        this.renderNode(this.data, rootUl);
        container.appendChild(rootUl);
        
        // Show root details by default
        this.showNodeDetails(this.data);
    }
    
    renderNode(node, parentElement) {
        const li = document.createElement('li');
        li.className = node.type === 'directory' ? 'tree-directory' : 'tree-file';
        
        const nodeElement = document.createElement('div');
        nodeElement.className = 'tree-node';
        
        // Add expand/collapse button for directories
        if (node.type === 'directory' && node.children && node.children.length > 0) {
            const expandBtn = document.createElement('span');
            expandBtn.className = 'tree-expand';
            expandBtn.textContent = '▶';
            expandBtn.onclick = () => this.toggleExpand(expandBtn, li);
            nodeElement.appendChild(expandBtn);
        } else if (node.type === 'directory') {
            // Empty directory
            const spacer = document.createElement('span');
            spacer.className = 'tree-spacer';
            nodeElement.appendChild(spacer);
        }
        
        // Add icon
        const icon = document.createElement('span');
        icon.className = 'tree-icon';
        icon.textContent = this.getIcon(node);
        nodeElement.appendChild(icon);
        
        // Add name
        const name = document.createElement('span');
        name.className = 'tree-name';
        name.textContent = node.name;
        name.onclick = () => this.showNodeDetails(node);
        nodeElement.appendChild(name);
        
        // Add description preview if available
        if (node.description) {
            const desc = document.createElement('span');
            desc.className = 'tree-description';
            desc.textContent = ' - ' + (node.description.length > 50 ? 
                node.description.substring(0, 50) + '...' : node.description);
            nodeElement.appendChild(desc);
        }
        
        li.appendChild(nodeElement);
        
        // Add children
        if (node.children && node.children.length > 0) {
            const childUl = document.createElement('ul');
            childUl.className = 'tree-children';
            childUl.style.display = 'none'; // Start collapsed
            
            node.children.forEach(child => {
                this.renderNode(child, childUl);
            });
            
            li.appendChild(childUl);
        }
        
        parentElement.appendChild(li);
    }
    
    toggleExpand(button, li) {
        const children = li.querySelector('.tree-children');
        if (children) {
            if (children.style.display === 'none') {
                children.style.display = 'block';
                button.textContent = '▼';
                button.classList.add('expanded');
            } else {
                children.style.display = 'none';
                button.textContent = '▶';
                button.classList.remove('expanded');
            }
        }
    }
    
    getIcon(node) {
        if (node.type === 'directory') {
            if (node.name.includes('test')) return '🧪';
            if (node.name.includes('doc')) return '📚';
            if (node.name.includes('src') || node.name.includes('lib')) return '📦';
            return '📁';
        } else {
            const ext = node.name.split('.').pop().toLowerCase();
            const iconMap = {
                'py': '🐍',
                'js': '📜',
                'ts': '📘',
                'jsx': '⚛️',
                'tsx': '⚛️',
                'md': '📝',
                'json': '📋',
                'yaml': '⚙️',
                'yml': '⚙️',
                'html': '🌐',
                'css': '🎨',
                'sh': '🔧',
                'txt': '📄'
            };
            return iconMap[ext] || '📄';
        }
    }
    
    showNodeDetails(node) {
        this.selectedNode = node;
        const detailsEl = document.getElementById(this.detailsId);
        
        let html = `<h3>${node.name}</h3>`;
        html += `<div class="detail-type"><strong>Type:</strong> ${node.type}</div>`;
        
        if (node.path) {
            html += `<div class="detail-path"><strong>Path:</strong> ${node.path}</div>`;
        }
        
        if (node.description) {
            html += `<div class="detail-description"><strong>Description:</strong><br>${node.description}</div>`;
        }
        
        if (node.metrics) {
            html += '<div class="detail-metrics"><strong>Metrics:</strong><ul>';
            Object.entries(node.metrics).forEach(([key, value]) => {
                html += `<li>${key}: ${value}</li>`;
            });
            html += '</ul></div>';
        }
        
        if (node.type === 'directory' && node.children) {
            html += `<div class="detail-stats">Contains ${node.children.length} items</div>`;
        }
        
        detailsEl.innerHTML = html;
        detailsEl.className = 'tree-details active';
    }
}

// Treemap Visualization
class ProjectTreemap {
    constructor(containerId) {
        this.containerId = containerId;
        this.width = 800;
        this.height = 600;
        this.colorScale = d3.scaleOrdinal()
            .domain(['doc', 'code', 'test', 'config'])
            .range(['#2196F3', '#4CAF50', '#ff9800', '#9C27B0']);
    }
    
    async load() {
        try {
            const response = await fetch('/api/context/visualization/treemap');
            if (!response.ok) throw new Error('Failed to load treemap data');
            
            this.data = await response.json();
            this.render();
        } catch (error) {
            console.error('Failed to load treemap:', error);
        }
    }
    
    render() {
        const container = document.getElementById(this.containerId);
        container.innerHTML = '';
        
        const svg = d3.select(`#${this.containerId}`)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height);
        
        const root = d3.hierarchy(this.data)
            .sum(d => d.value || 0)
            .sort((a, b) => b.value - a.value);
        
        d3.treemap()
            .size([this.width, this.height])
            .padding(2)
            .round(true)(root);
        
        const leaf = svg.selectAll('g')
            .data(root.leaves())
            .enter().append('g')
            .attr('transform', d => `translate(${d.x0},${d.y0})`);
        
        // Add rectangles
        leaf.append('rect')
            .attr('class', 'treemap-rect')
            .attr('fill', d => this.colorScale(d.data.fileType))
            .attr('width', d => d.x1 - d.x0)
            .attr('height', d => d.y1 - d.y0)
            .on('click', (event, d) => this.showFileInfo(d.data));
        
        // Add labels for larger rectangles
        leaf.append('text')
            .attr('class', 'treemap-label')
            .attr('x', 4)
            .attr('y', 20)
            .text(d => {
                const width = d.x1 - d.x0;
                const height = d.y1 - d.y0;
                if (width > 50 && height > 20) {
                    return d.data.name.length > 15 ? 
                        d.data.name.substring(0, 15) + '...' : d.data.name;
                }
                return '';
            });
        
        // Add legend
        const legend = svg.append('g')
            .attr('transform', `translate(${this.width - 100}, 10)`);
        
        const legendItems = ['doc', 'code', 'test', 'config'];
        legendItems.forEach((item, i) => {
            const g = legend.append('g')
                .attr('transform', `translate(0, ${i * 20})`);
            
            g.append('rect')
                .attr('width', 15)
                .attr('height', 15)
                .attr('fill', this.colorScale(item));
            
            g.append('text')
                .attr('x', 20)
                .attr('y', 12)
                .text(item);
        });
    }
    
    showFileInfo(file) {
        const infoEl = document.getElementById('treemap-info');
        infoEl.innerHTML = `
            <h4>${file.name}</h4>
            <div>Path: ${file.path}</div>
            <div>Type: ${file.fileType}</div>
            <div>Size: ${file.value} lines</div>
            ${file.metrics ? `
                <div>Functions: ${file.metrics.functions || 0}</div>
                <div>Classes: ${file.metrics.classes || 0}</div>
                <div>Complexity: ${(file.metrics.complexity || 0).toFixed(2)}</div>
            ` : ''}
        `;
        infoEl.classList.add('active');
    }
}

// Export for use in main context_manager.js
window.DirectoryTreeView = DirectoryTreeView;
window.ProjectTreemap = ProjectTreemap;