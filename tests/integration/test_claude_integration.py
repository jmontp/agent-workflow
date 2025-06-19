#!/usr/bin/env python3
"""
Test Claude Code integration specifically.
"""

import sys
import asyncio
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))

async def test_claude_integration():
    """Test actual Claude Code integration"""
    print("Testing Claude Code Integration")
    print("=" * 40)
    
    from claude_client import ClaudeCodeClient
    
    client = ClaudeCodeClient()
    print(f"Claude Code available: {client.available}")
    
    if not client.available:
        print("Claude Code not available - tests will use fallbacks")
        return True
    
    try:
        # Test simple code generation
        print("\nTesting code generation...")
        code = await client.generate_code("Create a simple Python function that adds two numbers")
        print("Generated code:")
        print("-" * 20)
        print(code[:200] + "..." if len(code) > 200 else code)
        print("-" * 20)
        
        # Test code analysis
        print("\nTesting code analysis...")
        sample_code = """
def add_numbers(a, b):
    return a + b
        """
        analysis = await client.analyze_code(sample_code, "review")
        print("Analysis result:")
        print("-" * 20)
        print(analysis[:200] + "..." if len(analysis) > 200 else analysis)
        print("-" * 20)
        
        print("\n✅ Claude Code integration working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Claude Code integration failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_claude_integration())
    sys.exit(0 if success else 1)