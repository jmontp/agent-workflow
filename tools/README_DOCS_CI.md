# Documentation CI/CD Quality Checks

This directory contains automated tools for ensuring documentation quality in CI/CD pipelines.

## 🚀 Quick Start

### Test Documentation Quality Locally
```bash
# Run all quality checks
python3 tools/check_docs_quality.py

# Run with auto-fixes for minor issues
python3 tools/check_docs_quality.py --fix-minor --verbose

# Test CI workflow locally
python3 tools/test_docs_ci.py
```

### Set Up Pre-commit Hooks
```bash
# Install simple pre-commit hook
python3 tools/setup_pre_commit_hook.py --install

# Check hook status
python3 tools/setup_pre_commit_hook.py --status

# Create advanced pre-commit config (requires pre-commit framework)
python3 tools/setup_pre_commit_hook.py --create-config
```

## 📋 CI/CD Integration

### GitHub Actions Workflow

The automated workflow (`.github/workflows/docs-check.yml`) runs on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches  
- Changes to documentation files (`docs_src/**`, `mkdocs.yml`)

**Workflow Steps:**
1. ✅ **YAML Validation** - Validates configuration files
2. ✅ **MkDocs Build Test** - Ensures documentation can build
3. ✅ **Internal Link Check** - Finds broken internal links
4. ✅ **Structure Validation** - Checks required files exist
5. ✅ **Content Quality** - Basic content quality checks
6. ✅ **TODO Audit** - Prevents too many unresolved TODOs

**Execution Time:** ~90 seconds (optimized for speed)

### Integration with Other CI Systems

The tools are designed to be portable and can be integrated with other CI systems:

```bash
# Jenkins, GitLab CI, Azure DevOps, etc.
python3 tools/check_docs_quality.py
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Documentation quality checks failed"
    exit 1
fi
```

## 🛠️ Tools Overview

### 1. Documentation Quality Checker (`check_docs_quality.py`)

**Purpose:** Comprehensive documentation quality validation
**Runtime:** ~5-10 seconds

**Checks Performed:**
- ✅ YAML configuration file validation
- ✅ MkDocs configuration structure
- ✅ Markdown file structure and content
- ✅ Required documentation files
- ✅ Content quality (empty links, merge conflicts)
- ✅ TODO/FIXME marker limits

**Options:**
- `--verbose` - Detailed output
- `--fix-minor` - Auto-fix spacing and formatting issues

### 2. Pre-commit Hook Setup (`setup_pre_commit_hook.py`)

**Purpose:** Install git pre-commit hooks for documentation quality

**Features:**
- Automatic installation of git hooks
- Backup of existing hooks
- Integration with documentation quality checker
- Support for pre-commit framework configuration

**Usage:**
```bash
python3 tools/setup_pre_commit_hook.py --install    # Install hook
python3 tools/setup_pre_commit_hook.py --uninstall  # Remove hook
python3 tools/setup_pre_commit_hook.py --status     # Check status
```

### 3. CI Workflow Tester (`test_docs_ci.py`)

**Purpose:** Local simulation of CI/CD documentation checks
**Runtime:** ~15-20 seconds

**Simulates:**
- YAML validation checks
- Documentation structure validation
- Basic link checking
- Quality checks

### 4. Link Auditor (`audit_links.py`)

**Purpose:** Comprehensive link checking (existing tool)
**Runtime:** ~30-60 seconds

**Features:**
- Internal link validation
- Image reference checking
- File reference validation
- Detailed reporting

## ⚙️ Configuration

### GitHub Actions Environment

The workflow automatically installs required dependencies:
- MkDocs and Material theme
- PyMdown Extensions
- YAML processing libraries

### Environment Variables

No special environment variables required for basic functionality.

**Optional:**
- `GOOGLE_ANALYTICS_KEY` - For MkDocs analytics (handled gracefully if missing)

### Customization

**Modify Check Thresholds:**
Edit `tools/check_docs_quality.py`:
```python
# Line ~280: Adjust TODO/FIXME threshold
if todo_count > 15:  # Change this number
```

**Add Custom Checks:**
Extend the `DocumentationChecker` class with additional validation methods.

## 🔄 Workflow Integration Patterns

### Option 1: Fail Fast (Recommended)
```yaml
# In .github/workflows/docs-check.yml
- name: Quick documentation check
  run: python3 tools/check_docs_quality.py
```

### Option 2: Comprehensive Check
```yaml
- name: Full documentation audit
  run: |
    python3 tools/check_docs_quality.py --fix-minor
    python3 tools/audit_links.py
    mkdocs build --strict
```

### Option 3: Pre-commit Only
```bash
# Install pre-commit hook
python3 tools/setup_pre_commit_hook.py --install
# No CI checks needed - all validation at commit time
```

## 📊 Performance Characteristics

| Tool | Runtime | CPU Usage | Memory Usage |
|------|---------|-----------|--------------|
| `check_docs_quality.py` | 5-10s | Low | <50MB |
| `test_docs_ci.py` | 15-20s | Low | <100MB |
| `audit_links.py` | 30-60s | Medium | <100MB |
| Full CI Workflow | 90s | Medium | <200MB |

## 🐛 Troubleshooting

### Common Issues

**1. YAML Parsing Errors**
```
❌ mkdocs.yml: could not determine a constructor for the tag '!ENV'
```
**Solution:** The quality checker handles this automatically now. If you see this error, update the tool.

**2. Missing Dependencies**
```
ModuleNotFoundError: No module named 'yaml'
```
**Solution:** Install dependencies:
```bash
pip install PyYAML
```

**3. Permission Errors (Pre-commit hooks)**
```
Permission denied: .git/hooks/pre-commit
```
**Solution:** Ensure you're in a git repository and have write permissions.

**4. False Positives**
If legitimate files are flagged as issues, you can:
1. Add file patterns to the skip list in the checker
2. Use specific comment markers to bypass checks
3. Customize the validation logic

### Debug Mode

Run with maximum verbosity:
```bash
python3 tools/check_docs_quality.py --verbose --fix-minor
```

## 🎯 Best Practices

### For Documentation Authors
1. **Run checks locally** before committing
2. **Use pre-commit hooks** for automatic validation
3. **Keep TODO markers minimal** (<15 total)
4. **Test MkDocs builds** locally when making structural changes

### For Project Maintainers
1. **Enable CI checks** on all documentation changes
2. **Require passing checks** for PR approval
3. **Monitor check performance** and adjust timeouts if needed
4. **Review and update** quality thresholds periodically

### For CI/CD Engineers
1. **Cache dependencies** between runs for speed
2. **Run checks in parallel** when possible
3. **Use fail-fast strategies** for quick feedback
4. **Archive check reports** for compliance tracking

## 📈 Future Enhancements

Planned improvements:
- [ ] External link checking (with rate limiting)
- [ ] Image optimization validation
- [ ] Accessibility checks (alt text, heading structure)
- [ ] SEO optimization validation
- [ ] Multi-language documentation support
- [ ] Integration with documentation analytics

## 📞 Support

For issues or feature requests:
1. Check existing documentation in `docs_src/`
2. Review tool source code for customization options
3. Create issues in the project repository
4. Contribute improvements via pull requests

---

**Generated:** $(date)  
**Version:** 1.0.0  
**Compatibility:** Python 3.8+, All major CI/CD platforms