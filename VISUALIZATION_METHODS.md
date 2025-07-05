# Context Manager Visualization Methods

## Overview
The Context Manager now supports multiple visualization methods to provide different perspectives on your project structure and quality.

## Available Visualizations

### 1. Knowledge Graph (Default)
- **Purpose**: Shows relationships between documentation, code files, and concepts
- **Features**:
  - Interactive force-directed graph
  - Three node types: docs (blue), code (green), concepts (orange)
  - Edge types: references, imports, contains
  - Drag nodes to rearrange
  - Click nodes for details
  - Toggle visibility by node type

### 2. Project Treemap
- **Purpose**: Visualize project structure and file sizes
- **Features**:
  - Hierarchical view of project directories
  - Rectangle size represents lines of code or complexity
  - Color coding: docs (blue), code (green), tests (orange), config (purple)
  - Click rectangles for file details
  - Shows metrics like functions, classes, complexity

### 3. 3D Explorer
- **Purpose**: Navigate project relationships in 3D space
- **Features**:
  - Three.js powered 3D visualization
  - Different node shapes for different file types
  - Drag to rotate, scroll to zoom
  - Click nodes to focus camera
  - Real-time physics simulation

### 4. Quality Heatmap
- **Purpose**: Identify documentation and code quality at a glance
- **Features**:
  - Matrix view of files vs quality metrics
  - Color scale from red (poor) to green (excellent)
  - Metrics: completeness, clarity, structure, up-to-date, examples
  - Hover for specific scores
  - Summary statistics

## Usage

1. Initialize your project first:
   ```bash
   cm init
   ```

2. Open the Context Manager web UI:
   ```
   http://localhost:5000/context-manager
   ```

3. Click on the visualization type buttons to switch between views

## API Endpoints

- `/api/context/visualization/graph` - Knowledge graph data
- `/api/context/visualization/treemap` - Treemap hierarchical data
- `/api/context/visualization/quality` - Quality heatmap data

## Implementation Details

- Visualizations are loaded on-demand for performance
- Data is cached client-side until project re-initialization
- All visualizations use the same underlying project index
- 3D visualization requires WebGL support

## Future Enhancements

- Timeline visualization for project evolution
- Dependency graph focusing on imports/exports
- Code coverage overlay
- Real-time updates as files change