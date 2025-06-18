"""
Comprehensive test suite for TokenCalculator budget allocation and management.

Tests the dynamic token budget allocation system optimized for agent types and TDD phases,
including token usage tracking and optimization with Claude Code integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any

# Import the modules under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from token_calculator import TokenCalculator, AgentBudgetProfile
from context.models import TokenBudget, TokenUsage, FileType, CompressionLevel
from context.exceptions import ContextError
from tdd_models import TDDState


class TestTokenCalculatorInit:
    """Test TokenCalculator initialization"""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        tc = TokenCalculator()
        
        assert tc.max_tokens == 200000
        assert len(tc.usage_history) == 0
        assert len(tc.agent_profiles) > 0
        assert "DesignAgent" in tc.agent_profiles
        assert "CodeAgent" in tc.agent_profiles
        assert "QAAgent" in tc.agent_profiles
        assert "DataAgent" in tc.agent_profiles
        assert "default" in tc.agent_profiles
    
    def test_init_with_custom_max_tokens(self):
        """Test initialization with custom max_tokens"""
        tc = TokenCalculator(max_tokens=100000)
        
        assert tc.max_tokens == 100000
    
    def test_agent_profiles_structure(self):
        """Test that agent profiles have correct structure"""
        tc = TokenCalculator()
        
        for agent_type, profile in tc.agent_profiles.items():
            assert isinstance(profile, AgentBudgetProfile)
            assert profile.agent_type == agent_type
            assert isinstance(profile.base_allocation, dict)
            assert isinstance(profile.tdd_phase_modifiers, dict)
            assert isinstance(profile.minimum_allocations, dict)
            assert isinstance(profile.priority_factors, dict)
            
            # Check base allocation sums to approximately 1.0
            total_allocation = sum(profile.base_allocation.values())
            assert 0.95 <= total_allocation <= 1.05  # Allow small rounding errors
            
            # Check required allocation keys
            required_keys = {"core_task", "historical", "dependencies", "agent_memory", "buffer"}
            assert set(profile.base_allocation.keys()) == required_keys
            assert set(profile.minimum_allocations.keys()) == required_keys


class TestBudgetCalculation:
    """Test budget calculation functionality"""
    
    @pytest.fixture
    def token_calculator(self):
        """Create a test token calculator"""
        return TokenCalculator(max_tokens=100000)
    
    @pytest.mark.asyncio
    async def test_calculate_budget_design_agent(self, token_calculator):
        """Test budget calculation for DesignAgent"""
        budget = await token_calculator.calculate_budget(
            total_tokens=100000,
            agent_type="DesignAgent",
            tdd_phase=TDDState.DESIGN
        )
        
        assert isinstance(budget, TokenBudget)
        assert budget.total_budget == 100000
        assert budget.core_task > 0
        assert budget.historical > 0
        assert budget.dependencies > 0
        assert budget.agent_memory > 0
        assert budget.buffer > 0
        
        # Total allocation should not exceed budget
        total_allocated = (budget.core_task + budget.historical + 
                          budget.dependencies + budget.agent_memory + budget.buffer)
        assert total_allocated <= budget.total_budget
        
        # DesignAgent should have higher historical allocation
        assert budget.historical >= budget.core_task * 0.5  # At least 50% of core task
    
    @pytest.mark.asyncio
    async def test_calculate_budget_code_agent(self, token_calculator):
        """Test budget calculation for CodeAgent"""
        budget = await token_calculator.calculate_budget(
            total_tokens=100000,
            agent_type="CodeAgent",
            tdd_phase=TDDState.CODE_GREEN
        )
        
        assert isinstance(budget, TokenBudget)
        # CodeAgent should have higher core_task allocation
        assert budget.core_task > budget.historical
        assert budget.core_task > budget.dependencies
    
    @pytest.mark.asyncio
    async def test_calculate_budget_qa_agent(self, token_calculator):
        """Test budget calculation for QAAgent"""
        budget = await token_calculator.calculate_budget(
            total_tokens=100000,
            agent_type="QAAgent",
            tdd_phase=TDDState.TEST_RED
        )
        
        assert isinstance(budget, TokenBudget)
        # QAAgent should have high dependencies allocation for test context
        assert budget.dependencies > budget.historical
    
    @pytest.mark.asyncio
    async def test_calculate_budget_unknown_agent(self, token_calculator):
        """Test budget calculation for unknown agent type"""
        budget = await token_calculator.calculate_budget(
            total_tokens=100000,
            agent_type="UnknownAgent"
        )
        
        assert isinstance(budget, TokenBudget)
        # Should use default profile
        assert budget.total_budget == 100000
    
    @pytest.mark.asyncio
    async def test_calculate_budget_with_tdd_phase_modifiers(self, token_calculator):
        """Test that TDD phase modifiers are applied correctly"""
        # Test DesignAgent in DESIGN phase (should get modifiers)
        design_budget = await token_calculator.calculate_budget(
            total_tokens=100000,
            agent_type="DesignAgent",
            tdd_phase=TDDState.DESIGN
        )
        
        # Test DesignAgent without phase (no modifiers)
        no_phase_budget = await token_calculator.calculate_budget(
            total_tokens=100000,
            agent_type="DesignAgent"
        )
        
        # With DESIGN phase, should have higher allocations due to modifiers
        assert design_budget.core_task >= no_phase_budget.core_task
        assert design_budget.historical >= no_phase_budget.historical
    
    @pytest.mark.asyncio
    async def test_calculate_budget_with_metadata(self, token_calculator):
        """Test budget calculation with metadata adjustments"""
        metadata = {
            "focus_areas": ["historical", "dependencies"],
            "complexity": "high"
        }
        
        budget = await token_calculator.calculate_budget(
            total_tokens=100000,
            agent_type="DesignAgent",
            metadata=metadata
        )
        
        assert isinstance(budget, TokenBudget)
        # Should have applied metadata adjustments
    
    @pytest.mark.asyncio
    async def test_calculate_budget_minimum_allocations_enforced(self, token_calculator):
        """Test that minimum allocations are enforced"""
        # Use very small budget to test minimum enforcement
        budget = await token_calculator.calculate_budget(
            total_tokens=10000,  # Small budget
            agent_type="DesignAgent"
        )
        
        profile = token_calculator.agent_profiles["DesignAgent"]
        
        # Check that minimums are respected (or redistributed appropriately)
        assert budget.core_task > 0
        assert budget.historical > 0
        assert budget.dependencies > 0
        assert budget.agent_memory > 0
        assert budget.buffer >= 0
    
    @pytest.mark.asyncio
    async def test_calculate_budget_zero_tokens_error(self, token_calculator):
        """Test error handling for zero tokens"""
        with pytest.raises(ValueError, match="Total tokens must be positive"):
            await token_calculator.calculate_budget(
                total_tokens=0,
                agent_type="DesignAgent"
            )
    
    @pytest.mark.asyncio
    async def test_calculate_budget_exceeds_max_tokens(self, token_calculator):
        """Test that budget is capped at max_tokens"""
        budget = await token_calculator.calculate_budget(
            total_tokens=300000,  # Exceeds max_tokens (100000)
            agent_type="DesignAgent"
        )
        
        assert budget.total_budget == token_calculator.max_tokens


class TestTokenEstimation:
    """Test token estimation functionality"""
    
    @pytest.fixture
    def token_calculator(self):
        """Create a test token calculator"""
        return TokenCalculator()
    
    @pytest.mark.asyncio
    async def test_estimate_tokens_empty_content(self, token_calculator):
        """Test token estimation for empty content"""
        tokens = await token_calculator.estimate_tokens("")
        assert tokens == 0
    
    @pytest.mark.asyncio
    async def test_estimate_tokens_simple_text(self, token_calculator):
        """Test token estimation for simple text"""
        content = "Hello world! This is a test."
        tokens = await token_calculator.estimate_tokens(content)
        
        # Should be approximately len(content) / 4
        expected = len(content) // 4
        assert tokens >= expected * 0.8  # Allow some variance
        assert tokens <= expected * 1.5
    
    @pytest.mark.asyncio
    async def test_estimate_tokens_with_file_types(self, token_calculator):
        """Test token estimation with different file types"""
        python_code = """
def hello_world():
    print("Hello, world!")
    return True
"""
        markdown_text = """
# Header
This is a markdown document with [links](http://example.com).
"""
        json_data = '{"key": "value", "number": 42, "array": [1, 2, 3]}'
        
        python_tokens = await token_calculator.estimate_tokens(python_code, FileType.PYTHON)
        markdown_tokens = await token_calculator.estimate_tokens(markdown_text, FileType.MARKDOWN)
        json_tokens = await token_calculator.estimate_tokens(json_data, FileType.JSON)
        
        # Python code should have higher token density
        python_ratio = python_tokens / len(python_code)
        markdown_ratio = markdown_tokens / len(markdown_text)
        json_ratio = json_tokens / len(json_data)
        
        assert python_ratio >= markdown_ratio  # Python is more token-dense
        assert json_ratio <= markdown_ratio    # JSON is more compact
    
    @pytest.mark.asyncio
    async def test_estimate_tokens_content_complexity(self, token_calculator):
        """Test that content complexity affects token estimation"""
        simple_content = "This is simple text with basic words."
        complex_content = """
class ComplexClass:
    def __init__(self, parameter_with_long_name):
        self.nested_dict = {'key': {'nested': {'deeply': 'value'}}}
        self.complex_expression = (x for x in range(100) if x % 2 == 0)
"""
        
        simple_tokens = await token_calculator.estimate_tokens(simple_content)
        complex_tokens = await token_calculator.estimate_tokens(complex_content, FileType.PYTHON)
        
        # Complex content should have higher tokens per character ratio
        simple_ratio = simple_tokens / len(simple_content)
        complex_ratio = complex_tokens / len(complex_content)
        
        assert complex_ratio >= simple_ratio


class TestBudgetOptimization:
    """Test budget optimization functionality"""
    
    @pytest.fixture
    def token_calculator(self):
        """Create a test token calculator"""
        return TokenCalculator()
    
    @pytest.fixture
    def sample_budget(self):
        """Create a sample token budget"""
        return TokenBudget(
            total_budget=10000,
            core_task=4000,
            historical=2500,
            dependencies=2000,
            agent_memory=1000,
            buffer=500
        )
    
    @pytest.fixture
    def underused_usage(self):
        """Create underused token usage"""
        return TokenUsage(
            context_id="test",
            total_used=5000,  # Only 50% of budget used
            core_task_used=2000,
            historical_used=1000,
            dependencies_used=1000,
            agent_memory_used=500,
            buffer_used=500
        )
    
    @pytest.fixture
    def overused_usage(self):
        """Create overused token usage"""
        return TokenUsage(
            context_id="test",
            total_used=9800,  # Nearly all budget used
            core_task_used=5000,  # Over budget
            historical_used=2500,
            dependencies_used=1800,
            agent_memory_used=500,
            buffer_used=0
        )
    
    @pytest.mark.asyncio
    async def test_optimize_allocation_underuse(self, token_calculator, sample_budget, underused_usage):
        """Test optimization for under-utilized budget"""
        optimized = await token_calculator.optimize_allocation(
            current_budget=sample_budget,
            actual_usage=underused_usage,
            context_quality=0.8
        )
        
        assert isinstance(optimized, TokenBudget)
        assert optimized.total_budget == sample_budget.total_budget
        
        # Should reduce allocations for under-used components
        assert optimized.core_task <= sample_budget.core_task
        assert optimized.historical <= sample_budget.historical
    
    @pytest.mark.asyncio
    async def test_optimize_allocation_overuse(self, token_calculator, sample_budget, overused_usage):
        """Test optimization for over-utilized budget"""
        optimized = await token_calculator.optimize_allocation(
            current_budget=sample_budget,
            actual_usage=overused_usage,
            context_quality=0.8
        )
        
        assert isinstance(optimized, TokenBudget)
        assert optimized.total_budget == sample_budget.total_budget
        
        # Should increase allocations for over-used components
        assert optimized.core_task >= sample_budget.core_task
    
    @pytest.mark.asyncio
    async def test_optimize_allocation_quality_impact(self, token_calculator, sample_budget):
        """Test that context quality affects optimization"""
        usage = TokenUsage(
            context_id="test",
            total_used=8000,
            core_task_used=4000,
            historical_used=2000,
            dependencies_used=1500,
            agent_memory_used=500
        )
        
        high_quality = await token_calculator.optimize_allocation(
            current_budget=sample_budget,
            actual_usage=usage,
            context_quality=0.9
        )
        
        low_quality = await token_calculator.optimize_allocation(
            current_budget=sample_budget,
            actual_usage=usage,
            context_quality=0.5
        )
        
        # Different quality scores should produce different optimizations
        assert (high_quality.core_task != low_quality.core_task or 
                high_quality.historical != low_quality.historical)
    
    @pytest.mark.asyncio
    async def test_optimize_allocation_builds_history(self, token_calculator, sample_budget, underused_usage):
        """Test that optimization builds usage history"""
        initial_history_length = len(token_calculator.usage_history)
        
        await token_calculator.optimize_allocation(
            current_budget=sample_budget,
            actual_usage=underused_usage,
            context_quality=0.8
        )
        
        assert len(token_calculator.usage_history) == initial_history_length + 1
        assert token_calculator.usage_history[-1] == underused_usage
    
    @pytest.mark.asyncio
    async def test_optimize_allocation_history_limit(self, token_calculator, sample_budget):
        """Test that usage history is limited to 100 entries"""
        # Add 105 entries to history
        for i in range(105):
            usage = TokenUsage(
                context_id=f"test_{i}",
                total_used=5000,
                core_task_used=2000,
                historical_used=1000,
                dependencies_used=1000,
                agent_memory_used=500,
                buffer_used=500
            )
            await token_calculator.optimize_allocation(
                current_budget=sample_budget,
                actual_usage=usage,
                context_quality=0.8
            )
        
        # Should be limited to 100 entries
        assert len(token_calculator.usage_history) == 100


class TestHistoricalOptimization:
    """Test historical optimization functionality"""
    
    @pytest.fixture
    def token_calculator_with_history(self):
        """Create a token calculator with some usage history"""
        tc = TokenCalculator()
        
        # Add some historical data
        for i in range(10):
            usage = TokenUsage(
                context_id=f"designagent_test_{i}",
                total_used=8000,
                core_task_used=3000,
                historical_used=3000,
                dependencies_used=1500,
                agent_memory_used=500
            )
            tc.usage_history.append(usage)
        
        return tc
    
    @pytest.mark.asyncio
    async def test_historical_optimization_design_agent(self, token_calculator_with_history):
        """Test that historical data influences budget for DesignAgent"""
        budget = await token_calculator_with_history.calculate_budget(
            total_tokens=10000,
            agent_type="DesignAgent",
            tdd_phase=TDDState.DESIGN
        )
        
        # Should be influenced by historical usage patterns
        assert isinstance(budget, TokenBudget)
        assert budget.total_budget == 10000
    
    @pytest.mark.asyncio
    async def test_historical_optimization_no_relevant_history(self, token_calculator_with_history):
        """Test optimization when no relevant history exists"""
        budget = await token_calculator_with_history.calculate_budget(
            total_tokens=10000,
            agent_type="UnknownAgent"  # No history for this agent
        )
        
        # Should fall back to default profile
        assert isinstance(budget, TokenBudget)
        assert budget.total_budget == 10000


class TestPerformanceMetrics:
    """Test performance metrics functionality"""
    
    @pytest.fixture
    def token_calculator(self):
        """Create a test token calculator"""
        return TokenCalculator()
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics_initial(self, token_calculator):
        """Test initial performance metrics"""
        metrics = token_calculator.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        assert metrics["budget_calculations"] == 0
        assert metrics["optimization_calls"] == 0
        assert metrics["token_estimations"] == 0
        assert metrics["total_tokens_processed"] == 0
        assert metrics["average_efficiency"] == 0.0
        assert metrics["history_entries"] == 0
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics_after_operations(self, token_calculator):
        """Test performance metrics after performing operations"""
        # Perform some operations
        await token_calculator.calculate_budget(
            total_tokens=10000,
            agent_type="DesignAgent"
        )
        
        await token_calculator.estimate_tokens("Hello world!")
        
        budget = TokenBudget(
            total_budget=10000,
            core_task=4000,
            historical=2500,
            dependencies=2000,
            agent_memory=1000,
            buffer=500
        )
        usage = TokenUsage(
            context_id="test",
            total_used=8000,
            core_task_used=4000,
            historical_used=2000,
            dependencies_used=1500,
            agent_memory_used=500
        )
        
        await token_calculator.optimize_allocation(budget, usage, 0.8)
        
        # Check updated metrics
        metrics = token_calculator.get_performance_metrics()
        
        assert metrics["budget_calculations"] == 1
        assert metrics["optimization_calls"] == 1
        assert metrics["token_estimations"] == 1
        assert metrics["total_tokens_processed"] > 0
        assert metrics["history_entries"] == 1


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.fixture
    def token_calculator(self):
        """Create a test token calculator"""
        return TokenCalculator()
    
    @pytest.mark.asyncio
    async def test_calculate_budget_negative_tokens(self, token_calculator):
        """Test error handling for negative tokens"""
        with pytest.raises(ValueError):
            await token_calculator.calculate_budget(
                total_tokens=-1000,
                agent_type="DesignAgent"
            )
    
    @pytest.mark.asyncio
    async def test_calculate_budget_error_fallback(self, token_calculator):
        """Test that errors fall back to safe default budget"""
        # Mock an error in budget calculation
        with patch.object(token_calculator, '_apply_metadata_adjustments', side_effect=Exception("Test error")):
            budget = await token_calculator.calculate_budget(
                total_tokens=10000,
                agent_type="DesignAgent",
                metadata={"test": "data"}
            )
        
        # Should return safe default budget
        assert isinstance(budget, TokenBudget)
        assert budget.total_budget == 10000


class TestContentTypeDetection:
    """Test content type detection functionality"""
    
    @pytest.fixture
    def token_calculator(self):
        """Create a test token calculator"""
        return TokenCalculator()
    
    def test_detect_python_content(self, token_calculator):
        """Test detection of Python content"""
        python_content = """
def hello():
    import sys
    class MyClass:
        pass
"""
        detected_type = token_calculator._detect_content_type(python_content)
        assert detected_type == FileType.PYTHON
    
    def test_detect_test_content(self, token_calculator):
        """Test detection of test content"""
        test_content = """
def test_function():
    assert True
    
import pytest
import unittest
"""
        detected_type = token_calculator._detect_content_type(test_content)
        assert detected_type == FileType.TEST
    
    def test_detect_markdown_content(self, token_calculator):
        """Test detection of markdown content"""
        markdown_content = """
# Header
This is a [link](http://example.com).
```python
code block
```
"""
        detected_type = token_calculator._detect_content_type(markdown_content)
        assert detected_type == FileType.MARKDOWN
    
    def test_detect_json_content(self, token_calculator):
        """Test detection of JSON content"""
        json_content = '{"key": "value", "number": 42}'
        detected_type = token_calculator._detect_content_type(json_content)
        assert detected_type == FileType.JSON
    
    def test_detect_yaml_content(self, token_calculator):
        """Test detection of YAML content"""
        yaml_content = """
key: value
list:
  - item1
  - item2
"""
        detected_type = token_calculator._detect_content_type(yaml_content)
        assert detected_type == FileType.YAML
    
    def test_detect_other_content(self, token_calculator):
        """Test detection of unknown content type"""
        other_content = "This is just plain text with no special patterns."
        detected_type = token_calculator._detect_content_type(other_content)
        assert detected_type == FileType.OTHER


class TestComplexityAnalysis:
    """Test content complexity analysis"""
    
    @pytest.fixture
    def token_calculator(self):
        """Create a test token calculator"""
        return TokenCalculator()
    
    def test_complexity_nested_structures(self, token_calculator):
        """Test complexity calculation for nested structures"""
        simple_content = "Hello world"
        complex_content = "{'nested': {'dict': {'with': ['arrays', {'inside': 'objects'}]}}}"
        
        simple_estimate = token_calculator._adjust_for_content_complexity(simple_content, 100)
        complex_estimate = token_calculator._adjust_for_content_complexity(complex_content, 100)
        
        # Complex content should have higher estimate
        assert complex_estimate >= simple_estimate
    
    def test_complexity_long_lines(self, token_calculator):
        """Test complexity calculation for long lines"""
        short_lines = "line1\nline2\nline3"
        long_lines = "a" * 150 + "\n" + "b" * 200  # Long lines
        
        short_estimate = token_calculator._adjust_for_content_complexity(short_lines, 100)
        long_estimate = token_calculator._adjust_for_content_complexity(long_lines, 100)
        
        # Long lines should increase complexity
        assert long_estimate >= short_estimate
    
    def test_complexity_special_characters(self, token_calculator):
        """Test complexity calculation for special characters"""
        simple_text = "Hello world this is simple text"
        special_text = "!@#$%^&*(){}[]|\\:;\"'<>?,./"
        
        simple_estimate = token_calculator._adjust_for_content_complexity(simple_text, 100)
        special_estimate = token_calculator._adjust_for_content_complexity(special_text, 100)
        
        # Special characters should increase complexity
        assert special_estimate >= simple_estimate
    
    def test_complexity_code_blocks(self, token_calculator):
        """Test complexity calculation for code blocks"""
        regular_text = "This is regular text without code blocks"
        code_text = "```python\nprint('hello')\n```\n```javascript\nconsole.log('hi');\n```"
        
        regular_estimate = token_calculator._adjust_for_content_complexity(regular_text, 100)
        code_estimate = token_calculator._adjust_for_content_complexity(code_text, 100)
        
        # Code blocks should increase complexity
        assert code_estimate >= regular_estimate


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])