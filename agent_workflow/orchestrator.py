#!/usr/bin/env python3
"""
Orchestrator entry point for agent-workflow package.

This module provides a simple entry point for running the orchestrator
directly as a module or script.
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

from .core.orchestrator import Orchestrator


async def main():
    """Main entry point for orchestrator."""
    # Simple orchestrator runner for testing
    # In production, this would be much more sophisticated
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting agent-workflow orchestrator...")
    
    # Create orchestrator instance
    orchestrator = Orchestrator()
    
    # Mock project for testing
    test_projects = [{
        "name": "test-project",
        "path": str(Path.cwd()),
        "mode": "blocking"
    }]
    
    try:
        await orchestrator.start(test_projects)
    except KeyboardInterrupt:
        logger.info("Shutting down orchestrator...")
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())