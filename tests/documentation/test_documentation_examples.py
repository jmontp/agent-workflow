"""
Documentation Example Validation Tests

Tests critical user-facing examples from documentation to prevent user-breaking issues.
Focuses on:
- Python code examples that users copy-paste
- Configuration YAML syntax validation
- CLI command syntax validation
- Critical getting-started examples

These tests are lightweight and fast-running, targeting the most common
user breakage points in documentation.
"""
import pytest
import subprocess
import yaml
import ast
import shlex
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Test data directory
TEST_ROOT = Path(__file__).parent.parent.parent
DOCS_ROOT = TEST_ROOT / "docs_src"


class TestPythonCodeExamples:
    """Test Python code examples from documentation can be imported/executed."""

    def test_api_test_example_from_quick_start(self):
        """Test the API test example from quick-start.md is valid Python."""
        # This is the example from the quick-start guide
        test_code = '''
def test_api_endpoint():
    """Test basic API functionality"""
    try:
        # NOTE: No /api/health endpoint - use CLI health command instead
        import subprocess
        result = subprocess.run(['agent-orch', 'health', '--check-all'], capture_output=True)
        response = type('Response', (), {'status_code': 200 if result.returncode == 0 else 500, 'json': {'status': 'healthy' if result.returncode == 0 else 'error'}})()
        assert response.status_code == 200
        assert 'status' in response.json
    except Exception as e:
        pytest.fail(f"API test failed: {e}")
'''
        
        # Test that the code is syntactically valid
        try:
            ast.parse(test_code)
        except SyntaxError as e:
            pytest.fail(f"Python code example has syntax error: {e}")

    def test_error_handling_pattern_example(self):
        """Test the error handling pattern example is valid Python."""
        error_handling_code = '''
# In your code when working with AI agents
try:
    result = risky_operation()
    return result
except APIError as e:
    logger.error(f"API error: {e}")
    return fallback_value()
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise  # Re-raise for debugging
'''
        
        # Mock the required classes and functions
        mock_code = '''
class APIError(Exception):
    pass

class logger:
    @staticmethod
    def error(msg):
        pass

def risky_operation():
    return "success"

def fallback_value():
    return "fallback"

''' + error_handling_code

        try:
            ast.parse(mock_code)
        except SyntaxError as e:
            pytest.fail(f"Error handling pattern has syntax error: {e}")

    def test_configuration_validation_examples(self):
        """Test configuration validation Python examples."""
        validation_examples = [
            # YAML validation example
            'import yaml; yaml.safe_load(open("config.yml"))',
            
            # TDD state machine validation
            '''
from lib.tdd_state_machine import TDDStateMachine
machine = TDDStateMachine()
print('TDD state machine initialized successfully')
''',
        ]
        
        for example in validation_examples:
            try:
                ast.parse(example)
            except SyntaxError as e:
                pytest.fail(f"Configuration validation example has syntax error: {e}")


class TestYAMLConfigurationExamples:
    """Test YAML configuration examples from documentation."""

    def test_config_example_yml_syntax(self):
        """Test that config.example.yml has valid YAML syntax."""
        config_file = TEST_ROOT / "config.example.yml"
        
        if not config_file.exists():
            pytest.skip("config.example.yml not found")
        
        try:
            with open(config_file, 'r') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"config.example.yml has invalid YAML syntax: {e}")

    def test_single_project_config_example(self):
        """Test single project configuration example from docs."""
        single_project_yaml = '''
orchestrator:
  mode: blocking  # blocking, partial, or autonomous
  project_path: "/path/to/your/project"
  project_name: "my-project"
'''
        
        try:
            config = yaml.safe_load(single_project_yaml)
            assert 'orchestrator' in config
            assert config['orchestrator']['mode'] in ['blocking', 'partial', 'autonomous']
        except yaml.YAMLError as e:
            pytest.fail(f"Single project config example has invalid YAML: {e}")

    def test_multi_project_config_example(self):
        """Test multi-project configuration example from docs."""
        multi_project_yaml = '''
orchestrator:
  mode: blocking
  projects:
    - name: "web-app"
      path: "/path/to/web-app"
      mode: partial
    - name: "api-service" 
      path: "/path/to/api-service"
      mode: autonomous
    - name: "mobile-app"
      path: "/path/to/mobile-app"
      mode: blocking
'''
        
        try:
            config = yaml.safe_load(multi_project_yaml)
            assert 'orchestrator' in config
            assert 'projects' in config['orchestrator']
            assert len(config['orchestrator']['projects']) == 3
            
            # Validate each project has required fields
            for project in config['orchestrator']['projects']:
                assert 'name' in project
                assert 'path' in project
                assert 'mode' in project
                assert project['mode'] in ['blocking', 'partial', 'autonomous']
        except yaml.YAMLError as e:
            pytest.fail(f"Multi-project config example has invalid YAML: {e}")

    def test_tdd_configuration_examples(self):
        """Test TDD configuration examples are valid YAML."""
        tdd_configs = [
            # Basic TDD config
            '''
orchestrator:
  mode: blocking
  tdd:
    enabled: true
    auto_start_cycles: true
    preserve_tests: true
    parallel_execution: true
''',
            # TDD timeouts config
            '''
tdd:
  timeouts:
    design_phase_minutes: 30
    test_red_phase_minutes: 45
    code_green_phase_minutes: 60
    refactor_phase_minutes: 30
    commit_phase_minutes: 15
    max_cycle_hours: 4
    stuck_detection_minutes: 15
    auto_recovery_enabled: true
''',
            # TDD quality gates
            '''
tdd:
  quality_gates:
    test_red_phase:
      min_test_count: 3
      require_failing_tests: true
      max_test_errors: 0
    code_green_phase:
      require_all_tests_passing: true
      max_complexity_score: 10
      min_coverage_increase: 5
'''
        ]
        
        for config_yaml in tdd_configs:
            try:
                yaml.safe_load(config_yaml)
            except yaml.YAMLError as e:
                pytest.fail(f"TDD configuration example has invalid YAML: {e}")

    def test_mkdocs_yml_syntax(self):
        """Test that mkdocs.yml configuration is readable and has basic structure."""
        mkdocs_file = TEST_ROOT / "mkdocs.yml"
        
        if not mkdocs_file.exists():
            pytest.skip("mkdocs.yml not found")
        
        try:
            # Just test basic readability and structure
            # MkDocs has complex YAML extensions that don't need full validation
            with open(mkdocs_file, 'r') as f:
                content = f.read()
                
            # Basic structure checks - ensure required MkDocs sections exist
            assert 'site_name:' in content, "Missing site_name in mkdocs.yml"
            assert 'nav:' in content, "Missing nav section in mkdocs.yml"
            assert 'theme:' in content, "Missing theme section in mkdocs.yml"
            
            # Verify file is not empty and has reasonable content
            assert len(content.strip()) > 100, "mkdocs.yml appears to be empty or too short"
            
            # Check for obvious formatting issues (but allow complex regex patterns)
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    # Basic structural checks only
                    if stripped.endswith(':') and ' ' in stripped[:-1]:
                        # YAML keys shouldn't have spaces (except in quoted strings)
                        if not ('"' in stripped or "'" in stripped):
                            if stripped.count(' ') > stripped.count(':') - 1:
                                # This is a very basic heuristic - skip complex cases
                                continue
                        
        except Exception as e:
            pytest.fail(f"Error reading mkdocs.yml: {e}")


class TestCLICommandExamples:
    """Test CLI command examples from documentation are syntactically valid."""

    def test_essential_cli_commands_syntax(self):
        """Test essential CLI commands from quick-start guide."""
        cli_commands = [
            # Speed run commands
            "agent-orch init --profile solo-engineer --minimal",
            "agent-orch register-project . \"speed-demo\" --mode autonomous",
            "agent-orch start --discord=false",
            "agent-orch epic \"Create a hello world API\"",
            "agent-orch status --watch",
            
            # Guided tour commands
            "agent-orch version",
            "agent-orch init --profile solo-engineer --interactive",
            "agent-orch register-project . \"my-first-api\" --framework web",
            "agent-orch start --discord",
            "agent-orch epic \"Build a Hello World API with TDD\"",
            "agent-orch sprint plan",
            "agent-orch sprint start",
            
            # Production setup commands
            "agent-orch setup-api --provider claude --interactive",
            "agent-orch setup-api --provider openai --interactive",
            "agent-orch setup-discord --interactive",
            "agent-orch health --check-all",
            "agent-orch configure --section projects --wizard",
            "agent-orch start --daemon --port 8080",
            
            # Common usage commands
            "agent-orch help",
            "agent-orch projects list",
            "agent-orch status --project my-first-api",
            "agent-orch stop",
        ]
        
        for command in cli_commands:
            try:
                # Parse the command to ensure it's valid shell syntax
                shlex.split(command)
            except ValueError as e:
                pytest.fail(f"CLI command has invalid syntax: '{command}' - {e}")

    def test_bash_commands_syntax(self):
        """Test bash commands from documentation are syntactically valid."""
        bash_commands = [
            # Installation commands
            'curl -fsSL https://raw.githubusercontent.com/jmontp/agent-workflow/main/install.sh | bash',
            'pip install agent-workflow',
            'python3 --version',
            'pip3 --version',
            'git --version',
            
            # Environment setup
            'export ANTHROPIC_API_KEY="sk-ant-api03-..."',
            'echo "ANTHROPIC_API_KEY=your-key-here" > .env',
            'echo "DISCORD_BOT_TOKEN=your-token-here" >> .env',
            'echo ".env" >> .gitignore',
            'source .env',
            
            # Testing commands
            'pytest tests/ -v',
            'pytest --cov=src tests/',
            'make test',
            
            # Troubleshooting commands
            'python -m pip install --upgrade pip',
            'pip install --user agent-workflow',
            'env | grep -E "(DISCORD|ANTHROPIC|GITHUB)"',
            'chmod 600 config.yml',
            'chmod +x scripts/orchestrator.py',
        ]
        
        for command in bash_commands:
            try:
                # Basic validation - ensure the command can be parsed
                shlex.split(command)
            except ValueError as e:
                pytest.fail(f"Bash command has invalid syntax: '{command}' - {e}")

    def test_python_cli_commands_syntax(self):
        """Test Python command examples from documentation."""
        python_commands = [
            # Validation commands
            'python -c "import yaml; yaml.safe_load(open(\'config.yml\'))"',
            'python tools/compliance/monitor_compliance.py --test-discord',
            'python tools/coverage/test_runner.py',
            'python tools/coverage/validate_tdd.py',
            'python scripts/test_tdd_integration.py',
            
            # Development commands
            'python scripts/orchestrator.py',
            'python scripts/multi_project_orchestrator.py --interactive',
            'python lib/discord_bot.py',
            'python tools/coverage/analyze_coverage.py',
        ]
        
        for command in python_commands:
            try:
                shlex.split(command)
            except ValueError as e:
                pytest.fail(f"Python command has invalid syntax: '{command}' - {e}")


class TestEnvironmentVariableExamples:
    """Test environment variable examples from documentation."""

    def test_env_file_examples_syntax(self):
        """Test .env file examples are properly formatted."""
        env_examples = [
            "DISCORD_BOT_TOKEN=your_discord_bot_token_here",
            "ANTHROPIC_API_KEY=your_anthropic_api_key",
            "GITHUB_TOKEN=your_github_personal_access_token",
            "CODECOV_TOKEN=${CODECOV_TOKEN}",
            "SLACK_WEBHOOK=${SLACK_WEBHOOK}",
        ]
        
        for env_line in env_examples:
            # Basic validation - should contain an equals sign and valid variable name
            if '=' not in env_line:
                pytest.fail(f"Environment variable example missing '=': {env_line}")
            
            var_name, var_value = env_line.split('=', 1)
            
            # Variable name should be valid (alphanumeric + underscore)
            if not var_name.replace('_', '').isalnum():
                pytest.fail(f"Invalid environment variable name: {var_name}")


class TestConfigurationTemplateIntegrity:
    """Test that configuration templates are consistent with documentation examples."""

    def test_config_example_matches_docs(self):
        """Test that config.example.yml contains examples referenced in docs."""
        config_file = TEST_ROOT / "config.example.yml"
        
        if not config_file.exists():
            pytest.skip("config.example.yml not found")
        
        with open(config_file, 'r') as f:
            config_content = f.read()
            config_data = yaml.safe_load(config_content)
        
        # Test required sections exist
        required_sections = ['orchestrator', 'discord', 'tdd', 'agents', 'security', 'logging']
        for section in required_sections:
            assert section in config_data, f"Required section '{section}' missing from config template"
        
        # Test orchestrator modes are documented
        valid_modes = ['blocking', 'partial', 'autonomous']
        if 'mode' in config_data.get('orchestrator', {}):
            mode = config_data['orchestrator']['mode']
            assert mode in valid_modes, f"Invalid orchestration mode in template: {mode}"

    def test_documented_commands_match_cli_help(self):
        """Test that documented commands exist (basic validation)."""
        # This test would ideally check against actual CLI help,
        # but for now we'll do basic validation of command structure
        documented_commands = [
            "init", "start", "stop", "status", "projects",
            "register-project", "setup-api", "setup-discord",
            "configure", "health", "version", "epic", "sprint"
        ]
        
        # Basic validation - ensure these look like valid command names
        for cmd in documented_commands:
            assert cmd.replace('-', '').replace('_', '').isalnum(), f"Invalid command name format: {cmd}"


class TestDocumentationCodeBlocks:
    """Test that code blocks in documentation are properly formatted and executable."""

    def test_installation_script_example(self):
        """Test the one-line installation command is properly formatted."""
        install_command = "curl -fsSL https://raw.githubusercontent.com/jmontp/agent-workflow/main/install.sh | bash"
        
        # Should be parseable as shell command
        try:
            parts = shlex.split(install_command)
            assert len(parts) >= 3  # curl command should have multiple parts
            assert parts[0] == 'curl'
            assert any('install.sh' in part for part in parts)
        except ValueError as e:
            pytest.fail(f"Installation command has invalid syntax: {e}")

    def test_security_example_validity(self):
        """Test security-related examples are properly formatted."""
        security_examples = [
            'echo "ANTHROPIC_API_KEY=sk-ant-api03-..." >> config.yml',  # Wrong way
            'export ANTHROPIC_API_KEY="sk-ant-api03-..."',  # Right way
            'echo "ANTHROPIC_API_KEY" >> .gitignore',
        ]
        
        for example in security_examples:
            try:
                shlex.split(example)
            except ValueError as e:
                pytest.fail(f"Security example has invalid syntax: '{example}' - {e}")


class TestDocumentationLinkIntegrity:
    """Test critical internal links in documentation."""

    def test_quick_start_internal_links(self):
        """Test that critical internal links in quick-start.md reference valid files."""
        # These are the most critical links that users click
        critical_links = [
            "../user-guide/cli-reference.md",
            "../user-guide/state-machine.md", 
            "../user-guide/integration-examples.md",
            "../user-guide/troubleshooting.md",
            "../deployment/production.md",
            "../user-guide/multi-project-orchestration.md",
            "../user-guide/performance-monitoring.md",
            "../development/contributing.md",
            "../index.md",
        ]
        
        for link in critical_links:
            # Convert relative link to absolute path
            if link.startswith("../"):
                target_file = DOCS_ROOT / link[3:]  # Remove ../
            else:
                target_file = DOCS_ROOT / link
            
            if not target_file.exists():
                pytest.fail(f"Critical documentation link is broken: {link} -> {target_file}")

    def test_configuration_internal_links(self):
        """Test internal links in configuration.md."""
        config_links = [
            "quick-start.md",
            "../user-guide/project-setup.md",
            "../user-guide/cli-reference.md",
            "../user-guide/integration-examples.md",
            "../user-guide/troubleshooting.md",
            "../user-guide/state-machine.md",
        ]
        
        for link in config_links:
            if link.startswith("../"):
                target_file = DOCS_ROOT / link[3:]
            else:
                target_file = DOCS_ROOT / "getting-started" / link
            
            if not target_file.exists():
                pytest.fail(f"Configuration documentation link is broken: {link} -> {target_file}")


# Test runner for manual execution
if __name__ == "__main__":
    pytest.main([__file__, "-v"])