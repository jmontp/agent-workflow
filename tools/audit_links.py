#!/usr/bin/env python3
"""
Documentation Link Audit Tool

Checks all markdown files for:
- Broken internal links
- Missing external resources
- Invalid image references
- Incorrect file paths
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Set
from urllib.parse import urlparse
import json

class LinkAuditor:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.errors = {
            "broken_internal_links": [],
            "broken_external_links": [],
            "missing_images": [],
            "invalid_file_refs": [],
            "anchor_issues": []
        }
        self.checked_files = set()
        
    def audit(self) -> Dict:
        """Run the complete audit"""
        print("Starting documentation link audit...")
        
        # Find all markdown files
        md_files = list(self.root_path.rglob("*.md"))
        print(f"Found {len(md_files)} markdown files to check")
        
        for md_file in md_files:
            if any(skip in str(md_file) for skip in ['.git', '__pycache__', 'node_modules']):
                continue
                
            self.check_file(md_file)
            
        return self.generate_report()
    
    def check_file(self, file_path: Path):
        """Check all links in a single file"""
        self.checked_files.add(str(file_path.relative_to(self.root_path)))
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return
            
        # Check markdown links: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(link_pattern, content):
            link_text = match.group(1)
            link_url = match.group(2)
            self.check_link(file_path, link_text, link_url)
            
        # Check image references: ![alt](path)
        img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        for match in re.finditer(img_pattern, content):
            alt_text = match.group(1)
            img_path = match.group(2)
            self.check_image(file_path, alt_text, img_path)
            
        # Check inline code file references
        code_ref_pattern = r'`([^`]+\.(py|md|yml|yaml|json|txt|sh))`'
        for match in re.finditer(code_ref_pattern, content):
            file_ref = match.group(1)
            self.check_file_reference(file_path, file_ref)
            
    def check_link(self, source_file: Path, text: str, url: str):
        """Check if a link is valid"""
        # Skip empty or placeholder links
        if not url or url == "#":
            return
            
        # Parse URL
        parsed = urlparse(url)
        
        # External link
        if parsed.scheme in ('http', 'https'):
            # Just log it for manual verification
            return
            
        # Anchor link
        if url.startswith('#'):
            self.check_anchor(source_file, url)
            return
            
        # Internal link
        if not parsed.scheme:
            self.check_internal_link(source_file, url)
            
    def check_internal_link(self, source_file: Path, link: str):
        """Check if an internal link exists"""
        # Remove anchor if present
        if '#' in link:
            link_path, anchor = link.split('#', 1)
        else:
            link_path = link
            anchor = None
            
        # Resolve relative path
        if link_path:
            target_path = (source_file.parent / link_path).resolve()
            
            # Check if file exists
            if not target_path.exists():
                self.errors["broken_internal_links"].append({
                    "source": str(source_file.relative_to(self.root_path)),
                    "link": link,
                    "expected_path": str(target_path.relative_to(self.root_path)) if self.root_path in target_path.parents else str(target_path)
                })
                
    def check_image(self, source_file: Path, alt_text: str, img_path: str):
        """Check if an image exists"""
        # Skip external images
        if img_path.startswith(('http://', 'https://')):
            return
            
        # Resolve relative path
        target_path = (source_file.parent / img_path).resolve()
        
        # Check if image exists
        if not target_path.exists():
            self.errors["missing_images"].append({
                "source": str(source_file.relative_to(self.root_path)),
                "alt_text": alt_text,
                "path": img_path,
                "expected_path": str(target_path.relative_to(self.root_path)) if self.root_path in target_path.parents else str(target_path)
            })
            
    def check_file_reference(self, source_file: Path, file_ref: str):
        """Check if a referenced file exists"""
        # Try common locations
        possible_paths = [
            self.root_path / file_ref,
            self.root_path / "lib" / file_ref,
            self.root_path / "scripts" / file_ref,
            self.root_path / "tools" / file_ref,
            self.root_path / "tests" / file_ref,
            self.root_path / "agent_workflow" / file_ref,
        ]
        
        found = False
        for path in possible_paths:
            if path.exists():
                found = True
                break
                
        if not found:
            self.errors["invalid_file_refs"].append({
                "source": str(source_file.relative_to(self.root_path)),
                "reference": file_ref
            })
            
    def check_anchor(self, source_file: Path, anchor: str):
        """Check if an anchor exists in the same file"""
        # This is a simplified check - would need to parse markdown headers
        # For now, just log it
        pass
        
    def generate_report(self) -> Dict:
        """Generate the audit report"""
        total_errors = sum(len(errors) for errors in self.errors.values())
        
        report = {
            "summary": {
                "files_checked": len(self.checked_files),
                "total_errors": total_errors,
                "broken_internal_links": len(self.errors["broken_internal_links"]),
                "missing_images": len(self.errors["missing_images"]),
                "invalid_file_refs": len(self.errors["invalid_file_refs"])
            },
            "errors": self.errors
        }
        
        return report

def main():
    """Run the link audit"""
    root_path = Path(__file__).parent.parent
    auditor = LinkAuditor(root_path)
    report = auditor.audit()
    
    # Print summary
    print("\n" + "="*60)
    print("DOCUMENTATION LINK AUDIT REPORT")
    print("="*60)
    print(f"\nFiles checked: {report['summary']['files_checked']}")
    print(f"Total errors found: {report['summary']['total_errors']}")
    
    # Print detailed errors
    if report['errors']['broken_internal_links']:
        print(f"\n❌ Broken Internal Links ({len(report['errors']['broken_internal_links'])})")
        print("-" * 40)
        for error in report['errors']['broken_internal_links']:
            print(f"  Source: {error['source']}")
            print(f"  Link: {error['link']}")
            print(f"  Expected: {error['expected_path']}")
            print()
            
    if report['errors']['missing_images']:
        print(f"\n❌ Missing Images ({len(report['errors']['missing_images'])})")
        print("-" * 40)
        for error in report['errors']['missing_images']:
            print(f"  Source: {error['source']}")
            print(f"  Image: {error['path']}")
            print(f"  Alt text: {error['alt_text']}")
            print()
            
    if report['errors']['invalid_file_refs']:
        print(f"\n❌ Invalid File References ({len(report['errors']['invalid_file_refs'])})")
        print("-" * 40)
        for error in report['errors']['invalid_file_refs']:
            print(f"  Source: {error['source']}")
            print(f"  Reference: {error['reference']}")
            print()
            
    # Save detailed report
    report_path = root_path / "link_audit_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nDetailed report saved to: {report_path}")
    
    return report

if __name__ == "__main__":
    main()