#!/usr/bin/env python3
"""
Simple test script to validate documentation CI checks will work
This replicates the key checks from the GitHub Actions workflow
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {description}")
            return True
        else:
            print(f"❌ {description}")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out")
        return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def main():
    """Test documentation CI workflow locally"""
    print("Testing Documentation CI Workflow")
    print("=" * 40)
    
    root_path = Path(__file__).parent.parent
    os.chdir(root_path)
    
    all_passed = True
    
    # Test 1: YAML validation
    all_passed &= run_command("""
python3 -c "
import yaml
files = ['mkdocs.yml', 'orch-config.yaml', 'config.example.yml']
for f in files:
    try:
        with open(f, 'r') as file:
            if f == 'mkdocs.yml':
                # Skip MkDocs-specific tags for this simple test
                continue
            yaml.safe_load(file)
        print(f'✅ {f}')
    except FileNotFoundError:
        print(f'⚠️ {f} not found')
    except Exception as e:
        print(f'❌ {f}: {e}')
        exit(1)
"
    """, "YAML validation")
    
    # Test 2: Documentation structure
    all_passed &= run_command("""
python3 -c "
from pathlib import Path
docs_dir = Path('docs_src')
required = ['index.md', 'getting-started/index.md', 'user-guide/index.md']
missing = [f for f in required if not (docs_dir / f).exists()]
if missing:
    print('❌ Missing files:', missing)
    exit(1)
else:
    print('✅ All required files exist')
"
    """, "Documentation structure check")
    
    # Test 3: Basic link check (simplified)
    all_passed &= run_command("""
python3 -c "
import re
from pathlib import Path
broken = 0
for md in Path('docs_src').rglob('*.md'):
    content = md.read_text(encoding='utf-8', errors='ignore')
    broken += len(re.findall(r'\\]\\(\\s*\\)', content))
if broken > 0:
    print(f'❌ Found {broken} empty links')
    exit(1)
else:
    print('✅ No obvious broken links found')
"
    """, "Basic link validation")
    
    # Test 4: Documentation quality check
    if Path("tools/check_docs_quality.py").exists():
        all_passed &= run_command("python3 tools/check_docs_quality.py", "Documentation quality check")
    else:
        print("⚠️  Documentation quality checker not found, skipping")
    
    # Summary
    print("\n" + "=" * 40)
    if all_passed:
        print("✅ All documentation CI checks would pass!")
        print("   Your documentation is ready for CI/CD.")
    else:
        print("❌ Some checks failed.")
        print("   Please fix the issues before pushing to CI.")
    
    return all_passed

if __name__ == "__main__":
    import os
    success = main()
    sys.exit(0 if success else 1)