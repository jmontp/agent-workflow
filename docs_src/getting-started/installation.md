# Installation Guide

<div class="hero-banner">
  <h2>⚡ The Fastest Path to AI Development</h2>
  <p>Get your AI agent team running in under 60 seconds</p>
</div>

<!-- Platform Switcher (Stripe-style tabs) -->
<div class="platform-switcher">
  <div class="switcher-tabs">
    <button class="tab-button active" data-platform="quick">🚀 Quick Start</button>
    <button class="tab-button" data-platform="macos">🍎 macOS</button>  
    <button class="tab-button" data-platform="windows">🪟 Windows</button>
    <button class="tab-button" data-platform="linux">🐧 Linux</button>
    <button class="tab-button" data-platform="docker">🐳 Docker</button>
  </div>

  <!-- Quick Start Tab -->
  <div class="tab-content active" id="quick">
    <div class="one-line-wonder">
      <h3>One-Line Installation</h3>
      <div class="install-command">
        <code>pip install agent-workflow</code>
        <button class="copy-btn" onclick="copyToClipboard('pip install agent-workflow')">📋 Copy</button>
      </div>
      <p class="install-note">✨ That's it! No complex setup, no configuration hell.</p>
    </div>

    <div class="quick-verify">
      <h4>Verify Installation</h4>
      <div class="code-block">
        <pre><code># Test your installation
agent-orch version

# Initialize your first project  
agent-orch init --interactive</code></pre>
      </div>
    </div>

    <div class="alternative-methods">
      <h4>Alternative Quick Methods</h4>
      <div class="method-grid">
        <div class="method-card">
          <h5>🔧 Install Script</h5>
          <code>curl -sSL https://raw.githubusercontent.com/jmontp/agent-workflow/main/scripts/install.sh | bash</code>
        </div>
        <div class="method-card">
          <h5>📦 From Source</h5>
          <code>git clone https://github.com/jmontp/agent-workflow.git && cd agent-workflow && pip install -e .</code>
        </div>
      </div>
    </div>
  </div>

  <!-- macOS Tab -->
  <div class="tab-content" id="macos">
    <div class="platform-steps">
      <div class="step">
        <span class="step-number">1</span>
        <div class="step-content">
          <h4>Install Dependencies</h4>
          <div class="code-block">
            <pre><code># Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Git
brew install python@3.11 git</code></pre>
          </div>
        </div>
      </div>

      <div class="step">
        <span class="step-number">2</span>
        <div class="step-content">
          <h4>Install Agent Workflow</h4>
          <div class="code-block">
            <pre><code># Direct installation
pip3 install agent-workflow

# Or with development tools
pip3 install agent-workflow[dev,docs,web]</code></pre>
          </div>
        </div>
      </div>

      <div class="step">
        <span class="step-number">3</span>
        <div class="step-content">
          <h4>Verify Installation</h4>
          <div class="code-block">
            <pre><code># Test installation
agent-orch version

# Initialize configuration
agent-orch init</code></pre>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Windows Tab -->
  <div class="tab-content" id="windows">
    <div class="windows-methods">
      <div class="method-toggle">
        <button class="toggle-btn active" data-method="wsl">WSL2 (Recommended)</button>
        <button class="toggle-btn" data-method="native">Native Windows</button>
      </div>

      <div class="method-content active" id="wsl-method">
        <div class="platform-steps">
          <div class="step">
            <span class="step-number">1</span>
            <div class="step-content">
              <h4>Enable WSL2</h4>
              <div class="code-block">
                <pre><code># In PowerShell (as Administrator)
wsl --install -d Ubuntu
wsl --set-default-version 2

# Restart computer after installation</code></pre>
              </div>
            </div>
          </div>

          <div class="step">
            <span class="step-number">2</span>
            <div class="step-content">
              <h4>Install in WSL2</h4>
              <div class="code-block">
                <pre><code># In WSL2 terminal
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

# Install agent workflow
pip3 install agent-workflow</code></pre>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="method-content" id="native-method">
        <div class="platform-steps">
          <div class="step">
            <span class="step-number">1</span>
            <div class="step-content">
              <h4>Install Prerequisites</h4>
              <ul>
                <li>Download Python 3.8+ from <a href="https://python.org">python.org</a></li>
                <li>Download Git from <a href="https://git-scm.com">git-scm.com</a></li>
                <li>Ensure "Add to PATH" is checked during installation</li>
              </ul>
            </div>
          </div>

          <div class="step">
            <span class="step-number">2</span>
            <div class="step-content">
              <h4>Install Agent Workflow</h4>
              <div class="code-block">
                <pre><code># In Command Prompt or PowerShell
pip install agent-workflow

# Create virtual environment (recommended)
python -m venv agent-env
agent-env\Scripts\activate
pip install agent-workflow</code></pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Linux Tab -->
  <div class="tab-content" id="linux">
    <div class="linux-distros">
      <div class="distro-toggle">
        <button class="toggle-btn active" data-distro="ubuntu">Ubuntu/Debian</button>
        <button class="toggle-btn" data-distro="fedora">Fedora/RHEL</button>
        <button class="toggle-btn" data-distro="arch">Arch Linux</button>
      </div>

      <div class="distro-content active" id="ubuntu-distro">
        <div class="platform-steps">
          <div class="step">
            <span class="step-number">1</span>
            <div class="step-content">
              <h4>Install Dependencies</h4>
              <div class="code-block">
                <pre><code># Update system
sudo apt update && sudo apt upgrade -y

# Install Python and build tools
sudo apt install -y python3 python3-pip python3-venv git curl build-essential</code></pre>
              </div>
            </div>
          </div>

          <div class="step">
            <span class="step-number">2</span>
            <div class="step-content">
              <h4>Install Agent Workflow</h4>
              <div class="code-block">
                <pre><code># Direct installation
pip3 install agent-workflow

# Or with all extras
pip3 install agent-workflow[dev,docs,web,ai]</code></pre>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="distro-content" id="fedora-distro">
        <div class="platform-steps">
          <div class="step">
            <span class="step-number">1</span>
            <div class="step-content">
              <h4>Install Dependencies</h4>
              <div class="code-block">
                <pre><code># Update system
sudo dnf update -y

# Install Python and build tools
sudo dnf install -y python3 python3-pip python3-venv git curl gcc</code></pre>
              </div>
            </div>
          </div>

          <div class="step">
            <span class="step-number">2</span>
            <div class="step-content">
              <h4>Install Agent Workflow</h4>
              <div class="code-block">
                <pre><code>pip3 install agent-workflow</code></pre>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="distro-content" id="arch-distro">
        <div class="platform-steps">
          <div class="step">
            <span class="step-number">1</span>
            <div class="step-content">
              <h4>Install Dependencies</h4>
              <div class="code-block">
                <pre><code># Update system
sudo pacman -Syu

# Install Python and build tools
sudo pacman -S python python-pip git curl base-devel</code></pre>
              </div>
            </div>
          </div>

          <div class="step">
            <span class="step-number">2</span>
            <div class="step-content">
              <h4>Install Agent Workflow</h4>
              <div class="code-block">
                <pre><code>pip install agent-workflow</code></pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Docker Tab -->
  <div class="tab-content" id="docker">
    <div class="docker-note">
      <div class="note-box">
        <h4>🚧 Docker Support Coming Soon</h4>
        <p>We're working on official Docker images. For now, you can create your own:</p>
      </div>
    </div>

    <div class="platform-steps">
      <div class="step">
        <span class="step-number">1</span>
        <div class="step-content">
          <h4>Create Dockerfile</h4>
          <div class="code-block">
            <pre><code>FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install agent-workflow
RUN pip install agent-workflow[web]

# Expose ports
EXPOSE 8080

# Start command
CMD ["agent-orch", "start", "--web", "--port", "8080"]</code></pre>
          </div>
        </div>
      </div>

      <div class="step">
        <span class="step-number">2</span>
        <div class="step-content">
          <h4>Build and Run</h4>
          <div class="code-block">
            <pre><code># Build image
docker build -t agent-workflow .

# Run container
docker run -d \
  --name agent-workflow \
  -p 8080:8080 \
  -v ~/.agent-workflow:/root/.agent-workflow \
  -e DISCORD_BOT_TOKEN=your_token \
  agent-workflow</code></pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Verification Dashboard -->
<div class="verification-dashboard">
  <h2>🎯 Installation Verification Dashboard</h2>
  <div class="checklist-grid">
    <div class="check-item">
      <input type="checkbox" id="check-python" class="check-box">
      <label for="check-python">
        <span class="check-title">Python 3.8+</span>
        <code>python3 --version</code>
      </label>
    </div>
    
    <div class="check-item">
      <input type="checkbox" id="check-install" class="check-box">
      <label for="check-install">
        <span class="check-title">Agent Workflow Installed</span>
        <code>agent-orch version</code>
      </label>
    </div>
    
    <div class="check-item">
      <input type="checkbox" id="check-config" class="check-box">
      <label for="check-config">
        <span class="check-title">Configuration Initialized</span>
        <code>agent-orch init</code>
      </label>
    </div>
    
    <div class="check-item">
      <input type="checkbox" id="check-health" class="check-box">
      <label for="check-health">
        <span class="check-title">Health Check Passed</span>
        <code>agent-orch health</code>
      </label>
    </div>
  </div>
  
  <div class="verification-status">
    <div class="status-indicator" id="verification-status">
      <span id="status-text">Complete the checklist above</span>
    </div>
  </div>
</div>

## System Requirements

<div class="requirements-grid">
  <div class="req-card">
    <h4>🐍 Python</h4>
    <p><strong>3.8+</strong> (3.11 recommended)</p>
    <small>All platforms supported</small>
  </div>
  
  <div class="req-card">
    <h4>💾 Memory</h4>
    <p><strong>4GB+</strong> (8GB recommended)</p>
    <small>For multi-project setups</small>
  </div>
  
  <div class="req-card">
    <h4>💿 Storage</h4>
    <p><strong>2GB+</strong> free space</p>
    <small>Dependencies + workspace</small>
  </div>
  
  <div class="req-card">
    <h4>🌐 Network</h4>
    <p><strong>Internet</strong> connection</p>
    <small>For AI API calls</small>
  </div>
</div>

## Initial Configuration

After installation, set up your environment:

```bash
# Interactive setup wizard
agent-orch init --interactive

# Manual configuration
agent-orch configure --ai-provider claude --discord-enabled
```

The setup wizard will guide you through:

- **AI Provider Setup** (Claude, OpenAI, or Mock mode)
- **Discord Bot Configuration** (optional but recommended)  
- **Project Registration** (add your existing projects)
- **Security Settings** (API keys, permissions)

## Prerequisites & Accounts

### Required for Full Features

1. **Discord Bot Token** ([Get one here](https://discord.com/developers/applications))
   - Enables the collaborative HITL interface
   - Creates project-specific channels automatically

2. **AI Provider API Key**
   - **Claude**: [claude.ai](https://claude.ai) (recommended)
   - **OpenAI**: [platform.openai.com](https://platform.openai.com)
   - **Mock Mode**: No API key needed (for testing)

### Optional Enhancements

3. **GitHub Token** ([Create here](https://github.com/settings/tokens))
   - Enhanced git operations and PR management
   - Repository analysis and documentation generation

4. **Claude Code CLI** ([Install guide](https://docs.anthropic.com/en/docs/claude-code))
   - Advanced AI coding capabilities
   - Seamless integration with development workflow

## Troubleshooting Installation

<details class="troubleshoot-section">
<summary><strong>🚨 Common Installation Issues</strong></summary>

### Permission Errors
```bash
# Use user installation if system install fails
pip install --user agent-workflow

# Or create a virtual environment
python3 -m venv ~/.agent-workflow-venv
source ~/.agent-workflow-venv/bin/activate
pip install agent-workflow
```

### Python Version Issues
```bash
# Check your Python version
python3 --version

# If you have multiple Python versions, use specific version
python3.11 -m pip install agent-workflow
```

### Package Conflicts
```bash
# Create clean environment
python3 -m venv clean-env
source clean-env/bin/activate
pip install --upgrade pip
pip install agent-workflow
```

</details>

<details class="troubleshoot-section">
<summary><strong>🔧 Platform-Specific Issues</strong></summary>

### macOS Issues
```bash
# If Homebrew installation fails
brew update && brew doctor

# XCode command line tools
xcode-select --install

# M1 Mac architecture issues
arch -arm64 pip install agent-workflow
```

### Windows Issues
```bash
# PowerShell execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Long path support
git config --system core.longpaths true

# Visual C++ build tools (if needed)
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### Linux Issues
```bash
# Ubuntu/Debian: Missing build tools
sudo apt install build-essential python3-dev

# CentOS/RHEL: Development tools
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel

# Alpine Linux: Build dependencies
apk add gcc musl-dev python3-dev
```

</details>

<details class="troubleshoot-section">
<summary><strong>🌐 Network & API Issues</strong></summary>

### Corporate Firewall
```bash
# Use corporate proxy
pip install --proxy http://proxy.company.com:8080 agent-workflow

# Trust corporate certificates
pip install --trusted-host pypi.org --trusted-host pypi.python.org agent-workflow
```

### Slow Download Speeds
```bash
# Use different PyPI mirror
pip install -i https://pypi.python.org/simple/ agent-workflow

# Or use conda-forge
conda install -c conda-forge agent-workflow
```

</details>

<details class="troubleshoot-section">
<summary><strong>⚙️ Configuration Issues</strong></summary>

### Missing Configuration Directory
```bash
# Manually create config directory
mkdir -p ~/.agent-workflow
agent-orch init --force
```

### API Key Issues
```bash
# Test API connectivity
agent-orch health --verbose

# Reset configuration
agent-orch configure --reset
```

### Discord Bot Issues
```bash
# Verify bot token
agent-orch setup-discord --test-token

# Check bot permissions
agent-orch setup-discord --check-permissions
```

</details>

## Advanced Installation Options

### Development Installation

For contributors and advanced users:

```bash
# Clone the repository
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest tests/unit/ -v
```

### Custom Installation Locations

```bash
# Install to custom directory
pip install --target /custom/path agent-workflow

# Add to Python path
export PYTHONPATH="/custom/path:$PYTHONPATH"
```

### Offline Installation

```bash
# Download packages for offline installation
pip download agent-workflow -d /path/to/offline/packages

# Install offline
pip install --find-links /path/to/offline/packages --no-index agent-workflow
```

## Verification Tests

Run these commands to verify your installation:

```bash
# 1. Basic installation check
agent-orch version

# 2. System health check
agent-orch health

# 3. Configuration test
agent-orch init --dry-run

# 4. API connectivity test (if configured)
agent-orch test-api

# 5. Discord integration test (if configured)  
agent-orch test-discord
```

Expected output for a successful installation:
```
✅ Agent Workflow v1.0.0 installed
✅ Python 3.8+ detected
✅ All dependencies satisfied
✅ Configuration directory created
✅ System ready for initialization
```

## Next Steps

<div class="next-steps-grid">
  <div class="next-step-card">
    <h4>🚀 Quick Start</h4>
    <p>Get your first project running in minutes</p>
    <a href="quick-start.md" class="step-link">Continue →</a>
  </div>
  
  <div class="next-step-card">
    <h4>⚙️ Configuration</h4>
    <p>Set up Discord bot and AI providers</p>
    <a href="configuration.md" class="step-link">Configure →</a>
  </div>
  
  <div class="next-step-card">
    <h4>🤖 Discord Setup</h4>
    <p>Enable collaborative AI workflow</p>
    <a href="../deployment/discord-setup.md" class="step-link">Setup →</a>
  </div>
  
  <div class="next-step-card">
    <h4>📚 User Guide</h4>
    <p>Learn all commands and workflows</p>
    <a href="../user-guide/hitl-commands.md" class="step-link">Learn →</a>
  </div>
</div>

---

<div class="installation-complete">
  <h3>🎉 Installation Complete!</h3>
  <p>Your AI Agent Workflow system is ready. Choose your next step above to get started.</p>
</div>

<!-- Interactive Elements Script -->
<script>
// Platform switcher functionality
document.addEventListener('DOMContentLoaded', function() {
    // Platform tabs
    const platformTabs = document.querySelectorAll('.tab-button');
    const platformContents = document.querySelectorAll('.tab-content');
    
    platformTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const platform = this.dataset.platform;
            
            // Update active tab
            platformTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Update active content
            platformContents.forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(platform).classList.add('active');
        });
    });
    
    // Windows method toggle
    const methodToggles = document.querySelectorAll('.toggle-btn[data-method]');
    const methodContents = document.querySelectorAll('.method-content');
    
    methodToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const method = this.dataset.method;
            
            methodToggles.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            methodContents.forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(method + '-method').classList.add('active');
        });
    });
    
    // Linux distro toggle
    const distroToggles = document.querySelectorAll('.toggle-btn[data-distro]');
    const distroContents = document.querySelectorAll('.distro-content');
    
    distroToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const distro = this.dataset.distro;
            
            distroToggles.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            distroContents.forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(distro + '-distro').classList.add('active');
        });
    });
    
    // Verification checklist
    const checkboxes = document.querySelectorAll('.check-box');
    const statusText = document.getElementById('status-text');
    const statusIndicator = document.getElementById('verification-status');
    
    function updateVerificationStatus() {
        const checked = document.querySelectorAll('.check-box:checked').length;
        const total = checkboxes.length;
        const percentage = Math.round((checked / total) * 100);
        
        if (percentage === 100) {
            statusText.textContent = '🎉 Installation verified! Ready to start.';
            statusIndicator.className = 'status-indicator complete';
        } else if (percentage >= 50) {
            statusText.textContent = `${percentage}% complete - Keep going!`;
            statusIndicator.className = 'status-indicator progress';
        } else {
            statusText.textContent = `${percentage}% complete - Follow the steps above`;
            statusIndicator.className = 'status-indicator incomplete';
        }
    }
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateVerificationStatus);
    });
});

// Copy to clipboard function
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Show feedback
        const copyBtn = event.target;
        const originalText = copyBtn.textContent;
        copyBtn.textContent = '✅ Copied!';
        setTimeout(() => {
            copyBtn.textContent = originalText;
        }, 2000);
    });
}
</script>

<!-- Styles -->
<style>
.hero-banner {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 2rem;
}

.platform-switcher {
    border: 1px solid #e1e5e9;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 2rem;
}

.switcher-tabs {
    display: flex;
    background: #f8f9fa;
    border-bottom: 1px solid #e1e5e9;
}

.tab-button {
    flex: 1;
    padding: 1rem;
    border: none;
    background: transparent;
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 500;
}

.tab-button:hover {
    background: #e9ecef;
}

.tab-button.active {
    background: white;
    border-bottom: 2px solid #667eea;
    color: #667eea;
}

.tab-content {
    display: none;
    padding: 2rem;
}

.tab-content.active {
    display: block;
}

.one-line-wonder {
    text-align: center;
    background: #f8f9fa;
    padding: 2rem;
    border-radius: 8px;
    margin-bottom: 2rem;
}

.install-command {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    margin: 1rem 0;
}

.install-command code {
    font-size: 1.2rem;
    padding: 0.5rem 1rem;
    background: white;
    border: 2px solid #667eea;
    border-radius: 6px;
}

.copy-btn {
    padding: 0.5rem 1rem;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
}

.copy-btn:hover {
    background: #5a67d8;
}

.method-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-top: 1rem;
}

.method-card {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #667eea;
}

.platform-steps {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.step {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
}

.step-number {
    background: #667eea;
    color: white;
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    flex-shrink: 0;
}

.step-content {
    flex: 1;
}

.toggle-btn {
    padding: 0.5rem 1rem;
    border: 1px solid #dee2e6;
    background: #f8f9fa;
    cursor: pointer;
    transition: all 0.2s;
}

.toggle-btn.active {
    background: #667eea;
    color: white;
    border-color: #667eea;
}

.method-content, .distro-content {
    display: none;
    margin-top: 1rem;
}

.method-content.active, .distro-content.active {
    display: block;
}

.verification-dashboard {
    background: #f8f9fa;
    padding: 2rem;
    border-radius: 12px;
    margin: 2rem 0;
}

.checklist-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

.check-item {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #e1e5e9;
}

.check-item label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
}

.check-title {
    font-weight: 500;
    flex: 1;
}

.status-indicator {
    text-align: center;
    padding: 1rem;
    border-radius: 8px;
    margin-top: 1rem;
    font-weight: 500;
}

.status-indicator.incomplete {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
}

.status-indicator.progress {
    background: #d1ecf1;
    border: 1px solid #bee5eb;
    color: #0c5460;
}

.status-indicator.complete {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}

.requirements-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

.req-card {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid #e1e5e9;
    text-align: center;
}

.next-steps-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    margin: 2rem 0;
}

.next-step-card {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid #e1e5e9;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}

.next-step-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.step-link {
    display: inline-block;
    padding: 0.5rem 1rem;
    background: #667eea;
    color: white;
    text-decoration: none;
    border-radius: 6px;
    margin-top: 1rem;
    transition: background 0.2s;
}

.step-link:hover {
    background: #5a67d8;
}

.installation-complete {
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 12px;
    margin: 2rem 0;
}

.troubleshoot-section {
    margin: 1rem 0;
    border: 1px solid #e1e5e9;
    border-radius: 8px;
}

.troubleshoot-section summary {
    padding: 1rem;
    background: #f8f9fa;
    cursor: pointer;
}

.troubleshoot-section[open] summary {
    border-bottom: 1px solid #e1e5e9;
}

.docker-note {
    text-align: center;
    margin-bottom: 2rem;
}

.note-box {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    padding: 1rem;
    border-radius: 8px;
    color: #856404;
}

@media (max-width: 768px) {
    .switcher-tabs {
        flex-direction: column;
    }
    
    .method-grid {
        grid-template-columns: 1fr;
    }
    
    .install-command {
        flex-direction: column;
    }
}
</style>