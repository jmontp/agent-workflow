#!/bin/bash
# Quick documentation health check script
# Usage: ./tools/documentation/check_docs.sh [quick|full|ci|html]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

case "${1:-quick}" in
    "quick")
        echo "🔍 Running quick documentation health check..."
        python3 tools/documentation/health_check.py --quick
        ;;
    "full")
        echo "🔍 Running full documentation health check..."
        python3 tools/documentation/health_check.py
        ;;
    "ci")
        echo "🔍 Running CI documentation health check..."
        python3 tools/documentation/ci_health_check.py
        ;;
    "html")
        echo "🔍 Generating HTML health report..."
        python3 tools/documentation/health_check.py --format html --output docs_health_report.html
        echo "✅ HTML report generated: docs_health_report.html"
        ;;
    "json")
        echo "🔍 Generating JSON health report..."
        python3 tools/documentation/health_check.py --format json --output docs_health_report.json
        echo "✅ JSON report generated: docs_health_report.json"
        ;;
    *)
        echo "Usage: $0 [quick|full|ci|html|json]"
        echo ""
        echo "  quick - Fast health check (default)"
        echo "  full  - Complete health check with link validation"
        echo "  ci    - CI/CD optimized check"
        echo "  html  - Generate HTML report"
        echo "  json  - Generate JSON report"
        exit 1
        ;;
esac