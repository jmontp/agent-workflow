#!/usr/bin/env python3
"""
Documentation Health Check Tool

Provides comprehensive health monitoring for documentation including:
- Navigation coverage analysis
- Broken links detection
- Content quality assessment
- Consistency validation
- Actionable recommendations

Usage:
    python tools/documentation/health_check.py [--format json|html|console]
    python tools/documentation/health_check.py --quick
    python tools/documentation/health_check.py --output health_report.html
"""

import argparse
import json
import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from datetime import datetime
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass
class HealthIssue:
    """Represents a documentation health issue."""
    type: str
    severity: str  # 'high', 'medium', 'low'
    file_path: str
    line_number: Optional[int]
    message: str
    recommendation: str
    context: Optional[str] = None


@dataclass
class HealthMetrics:
    """Overall health metrics for documentation."""
    total_files: int = 0
    files_in_navigation: int = 0
    files_with_content: int = 0
    broken_links: int = 0
    missing_images: int = 0
    inconsistencies: int = 0
    quality_score: float = 0.0
    health_grade: str = "F"


class DocumentationHealthChecker:
    """Comprehensive documentation health analysis tool."""
    
    def __init__(self, root_path: str = None):
        self.root_path = Path(root_path) if root_path else Path(__file__).parent.parent.parent
        self.docs_path = self.root_path / "docs_src"
        self.mkdocs_config = self.root_path / "mkdocs.yml"
        
        # Health tracking
        self.issues: List[HealthIssue] = []
        self.metrics = HealthMetrics()
        self.navigation_files: Set[str] = set()
        self.existing_files: Set[str] = set()
        
        # Content patterns
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
        self.code_block_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)
        self.incomplete_pattern = re.compile(r'(TODO|FIXME|XXX|PLACEHOLDER|TBD|Coming soon)', re.IGNORECASE)
        
    def run_health_check(self, quick: bool = False) -> Dict[str, Any]:
        """Run comprehensive health check."""
        print("🔍 Starting documentation health check...")
        
        # Step 1: Analyze navigation coverage
        self._analyze_navigation_coverage()
        
        # Step 2: Check file structure and content
        self._analyze_file_structure()
        
        # Step 3: Validate links and references
        if not quick:
            self._validate_links_and_references()
        
        # Step 4: Assess content quality
        self._assess_content_quality()
        
        # Step 5: Check consistency
        self._check_consistency()
        
        # Step 6: Calculate metrics and grade
        self._calculate_health_metrics()
        
        return self._generate_report()
    
    def _analyze_navigation_coverage(self):
        """Analyze which files are included in navigation."""
        print("📊 Analyzing navigation coverage...")
        
        if not self.mkdocs_config.exists():
            self.issues.append(HealthIssue(
                type="configuration",
                severity="high",
                file_path="mkdocs.yml",
                line_number=None,
                message="MkDocs configuration file not found",
                recommendation="Create mkdocs.yml configuration file"
            ))
            return
        
        try:
            # Use more robust YAML parsing for MkDocs config
            with open(self.mkdocs_config, 'r') as f:
                lines = f.readlines()
            
            # Extract just the nav section manually since the full YAML is complex
            nav_section = []
            in_nav = False
            nav_indent = 0
            
            for line in lines:
                if line.strip().startswith('nav:'):
                    in_nav = True
                    nav_indent = len(line) - len(line.lstrip())
                    continue
                
                if in_nav:
                    # Check if we're still in the nav section
                    if line.strip() == '':
                        continue
                    
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= nav_indent and line.strip() and not line.startswith(' '):
                        # We've left the nav section
                        break
                    
                    if current_indent > nav_indent:
                        nav_section.append(line)
            
            # Parse the nav section to extract file references
            self._parse_nav_section(nav_section)
            
        except Exception as e:
            self.issues.append(HealthIssue(
                type="configuration",
                severity="high",
                file_path="mkdocs.yml",
                line_number=None,
                message=f"Failed to parse MkDocs configuration: {str(e)}",
                recommendation="Fix YAML syntax in mkdocs.yml"
            ))
    
    def _parse_nav_section(self, nav_lines: List[str]):
        """Parse navigation section to extract file references."""
        for line in nav_lines:
            # Look for file references in the format: "- file.md" or "Title: file.md"
            if '.md' in line:
                # Extract the markdown file reference
                match = re.search(r'([a-zA-Z0-9/_-]+\.md)', line)
                if match:
                    self.navigation_files.add(match.group(1))
    
    def _extract_nav_files(self, nav_items: List, prefix: str = ""):
        """Recursively extract files from navigation structure."""
        for item in nav_items:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, str):
                        # File reference
                        self.navigation_files.add(value)
                    elif isinstance(value, list):
                        # Nested navigation
                        self._extract_nav_files(value, prefix + key + "/")
            elif isinstance(item, str):
                # Direct file reference
                self.navigation_files.add(item)
    
    def _analyze_file_structure(self):
        """Analyze documentation file structure."""
        print("📁 Analyzing file structure...")
        
        if not self.docs_path.exists():
            self.issues.append(HealthIssue(
                type="structure",
                severity="high",
                file_path="docs_src/",
                line_number=None,
                message="Documentation source directory not found",
                recommendation="Create docs_src directory and add documentation files"
            ))
            return
        
        # Find all markdown files
        md_files = list(self.docs_path.rglob("*.md"))
        self.metrics.total_files = len(md_files)
        
        for md_file in md_files:
            relative_path = str(md_file.relative_to(self.docs_path))
            self.existing_files.add(relative_path)
            
            # Check if file is in navigation
            if relative_path in self.navigation_files:
                self.metrics.files_in_navigation += 1
            else:
                # Check if it's a special file that doesn't need navigation
                if not self._is_special_file(relative_path):
                    self.issues.append(HealthIssue(
                        type="navigation",
                        severity="medium",
                        file_path=relative_path,
                        line_number=None,
                        message="File not included in navigation",
                        recommendation=f"Add {relative_path} to mkdocs.yml navigation"
                    ))
            
            # Check file content
            self._analyze_file_content(md_file)
    
    def _is_special_file(self, file_path: str) -> bool:
        """Check if file is a special file that doesn't need navigation."""
        special_files = {
            'CLAUDE.md', 'README.md', 'STYLE_GUIDE.md', 
            'IMPLEMENTATION_SUMMARY.md', 'NEEDED_SCREENSHOTS.md'
        }
        
        # Check if it's an archive file
        if 'archive/' in file_path or 'compliance/' in file_path:
            return True
            
        # Check if it's a special filename
        filename = Path(file_path).name
        return filename in special_files
    
    def _analyze_file_content(self, file_path: Path):
        """Analyze content quality of a single file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.issues.append(HealthIssue(
                type="content",
                severity="medium",
                file_path=str(file_path.relative_to(self.docs_path)),
                line_number=None,
                message=f"Failed to read file: {str(e)}",
                recommendation="Fix file encoding or permissions"
            ))
            return
        
        relative_path = str(file_path.relative_to(self.docs_path))
        
        # Check for empty files
        if not content.strip():
            self.issues.append(HealthIssue(
                type="content",
                severity="high",
                file_path=relative_path,
                line_number=None,
                message="File is empty",
                recommendation="Add content to the file or remove it"
            ))
            return
        
        # Check for meaningful content
        if len(content.strip()) < 50:
            self.issues.append(HealthIssue(
                type="content",
                severity="medium",
                file_path=relative_path,
                line_number=None,
                message="File has very little content",
                recommendation="Expand content or consider merging with another file"
            ))
        else:
            self.metrics.files_with_content += 1
        
        # Check for incomplete content markers
        for match in self.incomplete_pattern.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            self.issues.append(HealthIssue(
                type="content",
                severity="low",
                file_path=relative_path,
                line_number=line_num,
                message=f"Incomplete content marker found: {match.group(1)}",
                recommendation="Complete the content or remove the placeholder"
            ))
        
        # Check for proper heading structure
        self._check_heading_structure(relative_path, content)
    
    def _check_heading_structure(self, file_path: str, content: str):
        """Check if file has proper heading structure."""
        headings = self.heading_pattern.findall(content)
        
        if not headings:
            self.issues.append(HealthIssue(
                type="structure",
                severity="medium",
                file_path=file_path,
                line_number=None,
                message="No headings found in file",
                recommendation="Add at least one heading to structure the content"
            ))
            return
        
        # Check for proper heading hierarchy
        prev_level = 0
        for heading_match in self.heading_pattern.finditer(content):
            level = len(heading_match.group(1))
            title = heading_match.group(2)
            line_num = content[:heading_match.start()].count('\n') + 1
            
            # Check for skipped heading levels
            if level > prev_level + 1:
                self.issues.append(HealthIssue(
                    type="structure",
                    severity="low",
                    file_path=file_path,
                    line_number=line_num,
                    message=f"Heading level jumps from {prev_level} to {level}",
                    recommendation="Use proper heading hierarchy (don't skip levels)",
                    context=f"Heading: {title}"
                ))
            
            prev_level = level
    
    def _validate_links_and_references(self):
        """Validate all links and references in documentation."""
        print("🔗 Validating links and references...")
        
        for md_file in self.docs_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
            except:
                continue
            
            relative_path = str(md_file.relative_to(self.docs_path))
            
            # Check markdown links
            for match in self.link_pattern.finditer(content):
                link_text = match.group(1)
                link_url = match.group(2)
                line_num = content[:match.start()].count('\n') + 1
                
                self._validate_link(relative_path, line_num, link_text, link_url)
            
            # Check image references
            for match in self.image_pattern.finditer(content):
                alt_text = match.group(1)
                img_path = match.group(2)
                line_num = content[:match.start()].count('\n') + 1
                
                self._validate_image(relative_path, line_num, alt_text, img_path)
    
    def _validate_link(self, file_path: str, line_num: int, text: str, url: str):
        """Validate a single link."""
        # Skip empty or placeholder links
        if not url or url == "#" or url.startswith("mailto:"):
            return
        
        # External links - just check format
        if url.startswith(('http://', 'https://')):
            # Check for suspicious external links
            if 'localhost' in url or '127.0.0.1' in url:
                self.issues.append(HealthIssue(
                    type="links",
                    severity="medium",
                    file_path=file_path,
                    line_number=line_num,
                    message="Link points to localhost",
                    recommendation="Use production URL or remove link",
                    context=f"Link: {text} -> {url}"
                ))
            return
        
        # Internal links
        if not url.startswith('#'):
            # Remove anchor if present
            if '#' in url:
                url_path, anchor = url.split('#', 1)
            else:
                url_path = url
            
            if url_path:
                # Check if target file exists
                target_path = self.docs_path / Path(file_path).parent / url_path
                if not target_path.exists():
                    self.metrics.broken_links += 1
                    self.issues.append(HealthIssue(
                        type="links",
                        severity="high",
                        file_path=file_path,
                        line_number=line_num,
                        message="Broken internal link",
                        recommendation="Fix the link path or create the target file",
                        context=f"Link: {text} -> {url}"
                    ))
    
    def _validate_image(self, file_path: str, line_num: int, alt_text: str, img_path: str):
        """Validate a single image reference."""
        # Skip external images
        if img_path.startswith(('http://', 'https://')):
            return
        
        # Check if image exists
        target_path = self.docs_path / Path(file_path).parent / img_path
        if not target_path.exists():
            self.metrics.missing_images += 1
            self.issues.append(HealthIssue(
                type="images",
                severity="medium",
                file_path=file_path,
                line_number=line_num,
                message="Missing image file",
                recommendation="Add the image file or update the path",
                context=f"Image: {alt_text} -> {img_path}"
            ))
        
        # Check for missing alt text
        if not alt_text.strip():
            self.issues.append(HealthIssue(
                type="accessibility",
                severity="low",
                file_path=file_path,
                line_number=line_num,
                message="Image missing alt text",
                recommendation="Add descriptive alt text for accessibility",
                context=f"Image: {img_path}"
            ))
    
    def _assess_content_quality(self):
        """Assess overall content quality."""
        print("📝 Assessing content quality...")
        
        # Check for code examples
        files_with_code = 0
        for md_file in self.docs_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                if self.code_block_pattern.search(content):
                    files_with_code += 1
            except:
                continue
        
        # Report if documentation lacks examples
        if files_with_code < self.metrics.total_files * 0.3:
            self.issues.append(HealthIssue(
                type="quality",
                severity="medium",
                file_path="overall",
                line_number=None,
                message="Documentation lacks code examples",
                recommendation="Add more code examples to improve usability"
            ))
    
    def _check_consistency(self):
        """Check for consistency issues across documentation."""
        print("🔍 Checking consistency...")
        
        # Check for consistent file naming
        file_names = [f.name for f in self.docs_path.rglob("*.md")]
        naming_styles = defaultdict(int)
        
        for name in file_names:
            stem = name.replace('.md', '')
            if '-' in stem:
                naming_styles['kebab-case'] += 1
            elif '_' in stem:
                naming_styles['snake_case'] += 1
            elif any(c.isupper() for c in stem):
                naming_styles['PascalCase'] += 1
            else:
                naming_styles['lowercase'] += 1
        
        # Report inconsistent naming if there's a clear minority
        if len(naming_styles) > 1:
            most_common = max(naming_styles.items(), key=lambda x: x[1])
            if most_common[1] > sum(naming_styles.values()) * 0.7:
                for style, count in naming_styles.items():
                    if style != most_common[0] and count > 0:
                        self.issues.append(HealthIssue(
                            type="consistency",
                            severity="low",
                            file_path="overall",
                            line_number=None,
                            message=f"Inconsistent file naming: {count} files use {style} style",
                            recommendation=f"Consider renaming to match {most_common[0]} style"
                        ))
                        self.metrics.inconsistencies += 1
    
    def _calculate_health_metrics(self):
        """Calculate overall health metrics and grade."""
        print("📊 Calculating health metrics...")
        
        # Calculate coverage percentages
        nav_coverage = (self.metrics.files_in_navigation / max(self.metrics.total_files, 1)) * 100
        content_coverage = (self.metrics.files_with_content / max(self.metrics.total_files, 1)) * 100
        
        # Count issues by severity
        high_issues = len([i for i in self.issues if i.severity == 'high'])
        medium_issues = len([i for i in self.issues if i.severity == 'medium'])
        low_issues = len([i for i in self.issues if i.severity == 'low'])
        
        # Calculate quality score (0-100)
        base_score = 100.0
        
        # Penalties
        base_score -= high_issues * 15  # -15 for each high severity issue
        base_score -= medium_issues * 5  # -5 for each medium severity issue
        base_score -= low_issues * 2    # -2 for each low severity issue
        
        # Bonuses
        if nav_coverage > 90:
            base_score += 10
        if content_coverage > 90:
            base_score += 10
        if self.metrics.broken_links == 0:
            base_score += 5
        
        self.metrics.quality_score = max(0, min(100, base_score))
        
        # Assign grade
        if self.metrics.quality_score >= 90:
            self.metrics.health_grade = "A"
        elif self.metrics.quality_score >= 80:
            self.metrics.health_grade = "B"
        elif self.metrics.quality_score >= 70:
            self.metrics.health_grade = "C"
        elif self.metrics.quality_score >= 60:
            self.metrics.health_grade = "D"
        else:
            self.metrics.health_grade = "F"
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report."""
        # Group issues by type and severity
        issues_by_type = defaultdict(list)
        issues_by_severity = defaultdict(list)
        
        for issue in self.issues:
            issues_by_type[issue.type].append(issue)
            issues_by_severity[issue.severity].append(issue)
        
        # Generate actionable recommendations
        recommendations = self._generate_recommendations()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "health_grade": self.metrics.health_grade,
                "quality_score": round(self.metrics.quality_score, 1),
                "total_files": self.metrics.total_files,
                "files_in_navigation": self.metrics.files_in_navigation,
                "files_with_content": self.metrics.files_with_content,
                "navigation_coverage": round((self.metrics.files_in_navigation / max(self.metrics.total_files, 1)) * 100, 1),
                "content_coverage": round((self.metrics.files_with_content / max(self.metrics.total_files, 1)) * 100, 1),
                "total_issues": len(self.issues),
                "high_severity_issues": len(issues_by_severity['high']),
                "medium_severity_issues": len(issues_by_severity['medium']),
                "low_severity_issues": len(issues_by_severity['low']),
                "broken_links": self.metrics.broken_links,
                "missing_images": self.metrics.missing_images,
                "consistency_issues": self.metrics.inconsistencies
            },
            "issues_by_type": {
                issue_type: [self._issue_to_dict(issue) for issue in issues]
                for issue_type, issues in issues_by_type.items()
            },
            "issues_by_severity": {
                severity: [self._issue_to_dict(issue) for issue in issues]
                for severity, issues in issues_by_severity.items()
            },
            "recommendations": recommendations,
            "navigation_analysis": {
                "files_in_nav": sorted(list(self.navigation_files)),
                "files_missing_from_nav": sorted(list(
                    self.existing_files - self.navigation_files - 
                    {f for f in self.existing_files if self._is_special_file(f)}
                ))
            }
        }
    
    def _issue_to_dict(self, issue: HealthIssue) -> Dict[str, Any]:
        """Convert HealthIssue to dictionary."""
        return {
            "type": issue.type,
            "severity": issue.severity,
            "file_path": issue.file_path,
            "line_number": issue.line_number,
            "message": issue.message,
            "recommendation": issue.recommendation,
            "context": issue.context
        }
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations."""
        recommendations = []
        
        # High priority recommendations
        high_issues = [i for i in self.issues if i.severity == 'high']
        if high_issues:
            recommendations.append({
                "priority": "high",
                "title": "Fix Critical Issues",
                "description": f"Address {len(high_issues)} high-severity issues immediately",
                "actions": [
                    "Fix broken links and missing files",
                    "Add content to empty files",
                    "Resolve configuration errors"
                ]
            })
        
        # Navigation improvements
        nav_coverage = (self.metrics.files_in_navigation / max(self.metrics.total_files, 1)) * 100
        if nav_coverage < 80:
            recommendations.append({
                "priority": "medium",
                "title": "Improve Navigation Coverage",
                "description": f"Only {nav_coverage:.1f}% of files are in navigation",
                "actions": [
                    "Review files not in navigation",
                    "Add important files to mkdocs.yml",
                    "Consider organizing content better"
                ]
            })
        
        # Content quality improvements
        content_coverage = (self.metrics.files_with_content / max(self.metrics.total_files, 1)) * 100
        if content_coverage < 80:
            recommendations.append({
                "priority": "medium",
                "title": "Improve Content Quality",
                "description": f"Only {content_coverage:.1f}% of files have substantial content",
                "actions": [
                    "Add content to stub files",
                    "Remove or merge minimal files",
                    "Add more examples and details"
                ]
            })
        
        # Consistency improvements
        if self.metrics.inconsistencies > 0:
            recommendations.append({
                "priority": "low",
                "title": "Improve Consistency",
                "description": f"{self.metrics.inconsistencies} consistency issues found",
                "actions": [
                    "Standardize file naming conventions",
                    "Use consistent heading styles",
                    "Apply consistent formatting"
                ]
            })
        
        return recommendations


def format_console_output(report: Dict[str, Any]) -> str:
    """Format report for console output."""
    lines = []
    
    # Header
    lines.append("=" * 60)
    lines.append("📋 DOCUMENTATION HEALTH REPORT")
    lines.append("=" * 60)
    
    # Summary
    summary = report['summary']
    lines.append(f"\n🎯 OVERALL HEALTH GRADE: {summary['health_grade']}")
    lines.append(f"📊 Quality Score: {summary['quality_score']}/100")
    lines.append(f"📁 Total Files: {summary['total_files']}")
    lines.append(f"🧭 Navigation Coverage: {summary['navigation_coverage']}%")
    lines.append(f"📝 Content Coverage: {summary['content_coverage']}%")
    
    # Issues summary
    lines.append(f"\n🚨 ISSUES SUMMARY:")
    lines.append(f"  • High Severity: {summary['high_severity_issues']}")
    lines.append(f"  • Medium Severity: {summary['medium_severity_issues']}")
    lines.append(f"  • Low Severity: {summary['low_severity_issues']}")
    lines.append(f"  • Broken Links: {summary['broken_links']}")
    lines.append(f"  • Missing Images: {summary['missing_images']}")
    
    # Top recommendations
    if report['recommendations']:
        lines.append(f"\n💡 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'][:3], 1):
            lines.append(f"\n{i}. {rec['title']} ({rec['priority']} priority)")
            lines.append(f"   {rec['description']}")
            for action in rec['actions'][:2]:
                lines.append(f"   • {action}")
    
    # Quick fixes
    high_issues = report['issues_by_severity'].get('high', [])
    if high_issues:
        lines.append(f"\n🔧 IMMEDIATE ACTIONS NEEDED:")
        for issue in high_issues[:5]:
            lines.append(f"  • {issue['file_path']}: {issue['message']}")
            lines.append(f"    → {issue['recommendation']}")
    
    lines.append("\n" + "=" * 60)
    lines.append("Run with --format json for detailed report")
    lines.append("Run with --format html for visual report")
    
    return "\n".join(lines)


def format_html_output(report: Dict[str, Any]) -> str:
    """Format report as HTML."""
    summary = report['summary']
    
    # Determine grade color
    grade_colors = {
        'A': '#4CAF50', 'B': '#8BC34A', 'C': '#FFC107', 
        'D': '#FF9800', 'F': '#F44336'
    }
    grade_color = grade_colors.get(summary['health_grade'], '#F44336')
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Documentation Health Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .grade {{ font-size: 4em; font-weight: bold; color: {grade_color}; margin: 20px 0; }}
        .score {{ font-size: 1.5em; color: #666; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #333; }}
        .metric-label {{ color: #666; font-size: 0.9em; }}
        .section {{ margin: 30px 0; }}
        .section-title {{ font-size: 1.5em; font-weight: bold; margin-bottom: 15px; color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        .issue {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #ddd; }}
        .issue.high {{ border-left-color: #F44336; }}
        .issue.medium {{ border-left-color: #FF9800; }}
        .issue.low {{ border-left-color: #FFC107; }}
        .issue-title {{ font-weight: bold; color: #333; }}
        .issue-path {{ color: #666; font-size: 0.9em; }}
        .issue-message {{ margin: 10px 0; }}
        .issue-recommendation {{ color: #4CAF50; font-style: italic; }}
        .recommendation {{ background: #e3f2fd; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #2196F3; }}
        .recommendation-title {{ font-weight: bold; color: #1976D2; }}
        .recommendation-priority {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; color: white; }}
        .priority-high {{ background: #F44336; }}
        .priority-medium {{ background: #FF9800; }}
        .priority-low {{ background: #FFC107; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(45deg, #4CAF50, #8BC34A); transition: width 0.3s ease; }}
        .timestamp {{ text-align: center; color: #999; font-size: 0.9em; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Documentation Health Report</h1>
            <div class="grade">{summary['health_grade']}</div>
            <div class="score">Quality Score: {summary['quality_score']}/100</div>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{summary['total_files']}</div>
                <div class="metric-label">Total Files</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary['navigation_coverage']}%</div>
                <div class="metric-label">Navigation Coverage</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary['content_coverage']}%</div>
                <div class="metric-label">Content Coverage</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary['total_issues']}</div>
                <div class="metric-label">Total Issues</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📊 Progress Overview</div>
            <div style="margin: 20px 0;">
                <div style="margin-bottom: 10px;">Navigation Coverage: {summary['navigation_coverage']}%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {summary['navigation_coverage']}%;"></div>
                </div>
            </div>
            <div style="margin: 20px 0;">
                <div style="margin-bottom: 10px;">Content Coverage: {summary['content_coverage']}%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {summary['content_coverage']}%;"></div>
                </div>
            </div>
        </div>
    """
    
    # Add recommendations section
    if report['recommendations']:
        html += '<div class="section"><div class="section-title">💡 Recommendations</div>'
        for rec in report['recommendations']:
            priority_class = f"priority-{rec['priority']}"
            html += f"""
            <div class="recommendation">
                <div class="recommendation-title">
                    {rec['title']} 
                    <span class="recommendation-priority {priority_class}">{rec['priority']}</span>
                </div>
                <div style="margin: 10px 0;">{rec['description']}</div>
                <ul>
            """
            for action in rec['actions']:
                html += f"<li>{action}</li>"
            html += "</ul></div>"
        html += "</div>"
    
    # Add high priority issues
    if 'high' in report['issues_by_severity'] and report['issues_by_severity']['high']:
        html += '<div class="section"><div class="section-title">🚨 High Priority Issues</div>'
        for issue in report['issues_by_severity']['high'][:10]:
            html += f"""
            <div class="issue high">
                <div class="issue-title">{issue['message']}</div>
                <div class="issue-path">📁 {issue['file_path']}</div>
                <div class="issue-message">{issue.get('context', '')}</div>
                <div class="issue-recommendation">💡 {issue['recommendation']}</div>
            </div>
            """
        html += "</div>"
    
    html += f"""
        <div class="timestamp">
            Generated on {datetime.fromisoformat(report['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
    """
    
    return html


def main():
    """Main entry point for the health checker."""
    parser = argparse.ArgumentParser(description='Check documentation health')
    parser.add_argument(
        '--format',
        choices=['console', 'json', 'html'],
        default='console',
        help='Output format (default: console)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: stdout)'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick check (skips link validation)'
    )
    parser.add_argument(
        '--root',
        type=str,
        help='Root directory path (default: auto-detect)'
    )
    
    args = parser.parse_args()
    
    # Initialize and run health check
    checker = DocumentationHealthChecker(args.root)
    report = checker.run_health_check(quick=args.quick)
    
    # Format output
    if args.format == 'json':
        output = json.dumps(report, indent=2)
    elif args.format == 'html':
        output = format_html_output(report)
    else:  # console
        output = format_console_output(report)
    
    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"✅ Health report saved to: {args.output}")
    else:
        print(output)
    
    # Exit with appropriate code
    high_issues = len(report['issues_by_severity'].get('high', []))
    if high_issues > 0:
        return 1  # Exit with error code if high-severity issues found
    return 0


if __name__ == '__main__':
    exit(main())