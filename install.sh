#!/bin/bash
#
# AI Agent Workflow - Quick Installation Script
# https://github.com/jmontp/agent-workflow
#
# This script installs the AI Agent Workflow system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ASCII banner
echo -e "${BLUE}"
cat << "EOF"
    ╔═══════════════════════════════════════════════════════════════╗
    ║   AI Agent Workflow Installer - Your AI Team Awaits! 🤖      ║
    ╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Check Python version
print_info "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        print_status "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.8+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check pip
print_info "Checking pip..."
if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    print_status "pip found"
    PIP_CMD=$(command -v pip3 || command -v pip)
else
    print_error "pip not found. Please install pip"
    exit 1
fi

# Check git (optional)
if command -v git &> /dev/null; then
    print_status "git found (optional dependency)"
else
    print_warning "git not found (optional, but recommended)"
fi

# Create temporary directory for installation
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

print_info "Installing AI Agent Workflow..."

# Install from PyPI
if $PIP_CMD install agent-workflow; then
    print_status "AI Agent Workflow installed successfully!"
else
    print_warning "PyPI installation failed, trying from source..."
    
    # Fallback to GitHub installation
    if command -v git &> /dev/null; then
        git clone https://github.com/jmontp/agent-workflow.git
        cd agent-workflow
        $PIP_CMD install -e .
        print_status "AI Agent Workflow installed from source!"
    else
        print_error "Could not install from source (git required)"
        exit 1
    fi
fi

# Verify installation
print_info "Verifying installation..."
if command -v agent-orch &> /dev/null; then
    print_status "Installation verified!"
    echo ""
    agent-orch version
else
    print_error "Installation verification failed"
    exit 1
fi

# Cleanup
cd ~
rm -rf "$TEMP_DIR"

# Success message
echo ""
echo -e "${GREEN}"
cat << "EOF"
    ╔═══════════════════════════════════════════════════════════════╗
    ║   🎉 Installation Complete! 🎉                                ║
    ║                                                               ║
    ║   Get started with:                                           ║
    ║   $ agent-orch init                                           ║
    ║   $ agent-orch start                                          ║
    ║                                                               ║
    ║   Documentation: https://agent-workflow.readthedocs.io        ║
    ╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if we should create an alias
if [ -n "$SHELL" ]; then
    SHELL_RC=""
    case "$SHELL" in
        */bash)
            SHELL_RC="$HOME/.bashrc"
            ;;
        */zsh)
            SHELL_RC="$HOME/.zshrc"
            ;;
    esac
    
    if [ -n "$SHELL_RC" ] && [ -f "$SHELL_RC" ]; then
        if ! grep -q "alias aw=" "$SHELL_RC"; then
            print_info "Adding 'aw' alias to $SHELL_RC..."
            echo "alias aw='agent-orch'" >> "$SHELL_RC"
            print_status "You can now use 'aw' as a shortcut for 'agent-orch'"
            print_info "Run 'source $SHELL_RC' to use the alias in this session"
        fi
    fi
fi

print_info "Run 'agent-orch help' to see available commands"