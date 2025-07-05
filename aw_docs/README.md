# Agent Workflow Documentation (aw_docs)

This directory contains the Context Manager data for this project.

## What's Tracked

- **context_store/contexts/**: All development decisions, errors, and patterns
- **context_store/indices/**: Project metadata and search indices  
- **context_store/doc_metadata/**: Documentation quality tracking

## Git Workflow

All files in aw_docs are tracked in git to enable:
- Team collaboration on context
- Historical analysis of project evolution
- Consistent development patterns

## Usage

- `cm init`: Initialize project indices (scan all docs and code)
- `cm find <query>`: Search project knowledge
- `cm log-decision`: Track important decisions
- `cm stats`: View project statistics
- `cm status`: Check initialization status

## Directory Structure

```
aw_docs/
├── context_store/
│   ├── contexts/          # Historical context entries
│   │   ├── active/        # Current contexts by date
│   │   └── archive/       # Archived contexts
│   ├── indices/           # Project search indices
│   │   ├── project_index.json
│   │   ├── concept_map.json
│   │   └── quick_lookups.json
│   └── doc_metadata/      # Documentation metadata
│       ├── metadata/      # Per-file metadata
│       └── patterns/      # Learned patterns
└── README.md             # This file
```

## Context Manager

The Context Manager is the "nervous system" of the agent-workflow system. It:
- Tracks all decisions, errors, and patterns
- Learns from project evolution
- Provides fast information retrieval
- Suggests next actions based on patterns

## Integration

This directory is designed to be:
- **Git-tracked**: Share context with your team
- **Portable**: Copy to new projects to maintain patterns
- **Extensible**: Add new tools and indices as needed