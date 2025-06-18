"""
Token Calculator for Context Management System

Implements dynamic token budget allocation optimized for agent types and TDD phases.
Provides token usage tracking and optimization with integration to Claude Code limits.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field

try:
    from .context.models import TokenBudget, TokenUsage, FileType, CompressionLevel
    from .context.interfaces import ITokenCalculator
except ImportError:
    from context.models import TokenBudget, TokenUsage, FileType, CompressionLevel
    from context.interfaces import ITokenCalculator

# Import TDD models
try:
    from .tdd_models import TDDState, TDDTask, TDDCycle
except ImportError:
    from tdd_models import TDDState, TDDTask, TDDCycle

logger = logging.getLogger(__name__)


@dataclass
class AgentBudgetProfile:
    """Budget allocation profile for different agent types"""
    agent_type: str
    base_allocation: Dict[str, float]  # Percentage allocation
    tdd_phase_modifiers: Dict[TDDState, Dict[str, float]]  # Phase-specific adjustments
    minimum_allocations: Dict[str, int]  # Minimum token counts
    priority_factors: Dict[str, float]  # Context priority weights


class TokenCalculator(ITokenCalculator):
    """
    Advanced token budget calculator for context management.
    
    Provides dynamic allocation based on agent type, TDD phase, and content availability.
    Optimizes token usage through historical analysis and adaptive budgeting.
    """
    
    def __init__(self, max_tokens: int = 200000):
        """
        Initialize TokenCalculator.
        
        Args:
            max_tokens: Maximum token limit (Claude Code default)
        """
        self.max_tokens = max_tokens
        self.usage_history: List[TokenUsage] = []
        self.agent_profiles = self._create_agent_profiles()
        
        # Performance tracking
        self._budget_calculations = 0
        self._optimization_calls = 0
        self._token_estimations = 0
        
        logger.info(f"TokenCalculator initialized with max_tokens={max_tokens}")
    
    async def calculate_budget(
        self,
        total_tokens: int,
        agent_type: str,
        tdd_phase: Optional[TDDState] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TokenBudget:
        """
        Calculate optimal token budget allocation.
        
        Args:
            total_tokens: Total token budget available
            agent_type: Type of agent requesting budget
            tdd_phase: Current TDD phase
            metadata: Additional metadata for budget calculation
            
        Returns:
            TokenBudget with allocation breakdown
        """
        self._budget_calculations += 1
        start_time = datetime.utcnow()
        
        try:
            # Validate inputs
            total_tokens = min(total_tokens, self.max_tokens)
            if total_tokens <= 0:
                raise ValueError("Total tokens must be positive")
            
            # Get agent profile
            profile = self.agent_profiles.get(agent_type, self.agent_profiles["default"])
            
            # Base allocation percentages
            base_allocation = profile.base_allocation.copy()
            
            # Apply TDD phase modifiers
            if tdd_phase and tdd_phase in profile.tdd_phase_modifiers:
                phase_modifiers = profile.tdd_phase_modifiers[tdd_phase]
                for component, modifier in phase_modifiers.items():
                    if component in base_allocation:
                        base_allocation[component] *= modifier
            
            # Apply metadata-based adjustments
            if metadata:
                base_allocation = self._apply_metadata_adjustments(base_allocation, metadata)
            
            # Calculate absolute token amounts
            budget = TokenBudget(
                total_budget=total_tokens,
                core_task=int(total_tokens * base_allocation["core_task"]),
                historical=int(total_tokens * base_allocation["historical"]),
                dependencies=int(total_tokens * base_allocation["dependencies"]),
                agent_memory=int(total_tokens * base_allocation["agent_memory"]),
                buffer=int(total_tokens * base_allocation["buffer"])
            )
            
            # Ensure minimum allocations
            budget = self._enforce_minimum_allocations(budget, profile)
            
            # Optimize based on historical data
            budget = await self._optimize_based_on_history(budget, agent_type, tdd_phase)
            
            # Validate final budget
            budget = self._validate_and_adjust_budget(budget)
            
            calculation_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Budget calculated for {agent_type} in {calculation_time:.3f}s: "
                f"core={budget.core_task}, hist={budget.historical}, "
                f"deps={budget.dependencies}, mem={budget.agent_memory}, buf={budget.buffer}"
            )
            
            return budget
            
        except Exception as e:
            logger.error(f"Budget calculation failed: {str(e)}")
            # Return safe default budget
            return self._create_safe_default_budget(total_tokens)
    
    async def estimate_tokens(
        self,
        content: str,
        content_type: Optional[FileType] = None
    ) -> int:
        """
        Estimate token count for given content.
        
        Args:
            content: Content to analyze
            content_type: Type of content for more accurate estimation
            
        Returns:
            Estimated token count
        """
        self._token_estimations += 1
        
        if not content:
            return 0
        
        # Base estimation: ~4 characters per token (conservative)
        base_tokens = len(content) // 4
        
        # Apply content-type specific adjustments
        multiplier = self._get_content_type_multiplier(content_type, content)
        estimated_tokens = int(base_tokens * multiplier)
        
        # Additional adjustments based on content characteristics
        estimated_tokens = self._adjust_for_content_complexity(content, estimated_tokens)
        
        logger.debug(f"Token estimation: {len(content)} chars -> {estimated_tokens} tokens (type: {content_type})")
        
        return estimated_tokens
    
    async def optimize_allocation(
        self,
        current_budget: TokenBudget,
        actual_usage: TokenUsage,
        context_quality: float
    ) -> TokenBudget:
        """
        Optimize budget allocation based on usage patterns.
        
        Args:
            current_budget: Current budget allocation
            actual_usage: Actual token usage
            context_quality: Quality score of the context
            
        Returns:
            Optimized budget allocation
        """
        self._optimization_calls += 1
        
        # Store usage for historical analysis
        self.usage_history.append(actual_usage)
        
        # Keep only recent history (last 100 entries)
        if len(self.usage_history) > 100:
            self.usage_history = self.usage_history[-100:]
        
        # Calculate efficiency metrics
        efficiency = actual_usage.get_efficiency_score(current_budget)
        
        # Determine optimization strategy based on efficiency and quality
        if efficiency < 0.7:  # Under-utilization
            optimized_budget = self._optimize_for_underuse(current_budget, actual_usage)
        elif efficiency > 0.95:  # Over-utilization
            optimized_budget = self._optimize_for_overuse(current_budget, actual_usage)
        else:
            # Good utilization, minor adjustments based on quality
            optimized_budget = self._fine_tune_allocation(current_budget, actual_usage, context_quality)
        
        logger.info(
            f"Budget optimized: efficiency={efficiency:.2f}, quality={context_quality:.2f}, "
            f"adjustments applied"
        )
        
        return optimized_budget
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for token calculation"""
        total_usage = sum(usage.total_used for usage in self.usage_history)
        avg_efficiency = (
            sum(usage.compression_ratio for usage in self.usage_history) / len(self.usage_history)
            if self.usage_history else 0.0
        )
        
        return {
            "budget_calculations": self._budget_calculations,
            "optimization_calls": self._optimization_calls,
            "token_estimations": self._token_estimations,
            "total_tokens_processed": total_usage,
            "average_efficiency": avg_efficiency,
            "history_entries": len(self.usage_history)
        }
    
    # Private helper methods
    
    def _create_agent_profiles(self) -> Dict[str, AgentBudgetProfile]:
        """Create budget profiles for different agent types"""
        profiles = {}
        
        # Design Agent - Needs extensive historical context and documentation
        profiles["DesignAgent"] = AgentBudgetProfile(
            agent_type="DesignAgent",
            base_allocation={
                "core_task": 0.25,
                "historical": 0.35,
                "dependencies": 0.25,
                "agent_memory": 0.10,
                "buffer": 0.05
            },
            tdd_phase_modifiers={
                TDDState.DESIGN: {
                    "core_task": 1.4,
                    "historical": 1.2,
                    "dependencies": 1.1,
                    "agent_memory": 1.3
                }
            },
            minimum_allocations={
                "core_task": 10000,
                "historical": 15000,
                "dependencies": 8000,
                "agent_memory": 5000,
                "buffer": 2000
            },
            priority_factors={
                "architecture": 1.5,
                "specifications": 1.3,
                "documentation": 1.2
            }
        )
        
        # Code Agent - Needs current code and test context
        profiles["CodeAgent"] = AgentBudgetProfile(
            agent_type="CodeAgent",
            base_allocation={
                "core_task": 0.45,
                "historical": 0.20,
                "dependencies": 0.20,
                "agent_memory": 0.10,
                "buffer": 0.05
            },
            tdd_phase_modifiers={
                TDDState.CODE_GREEN: {
                    "core_task": 1.3,
                    "dependencies": 1.2,
                    "agent_memory": 1.1
                },
                TDDState.REFACTOR: {
                    "core_task": 1.2,
                    "historical": 1.1,
                    "agent_memory": 1.2
                }
            },
            minimum_allocations={
                "core_task": 20000,
                "historical": 8000,
                "dependencies": 10000,
                "agent_memory": 5000,
                "buffer": 2000
            },
            priority_factors={
                "implementation": 1.4,
                "tests": 1.3,
                "refactoring": 1.2
            }
        )
        
        # QA Agent - Needs test files and validation context
        profiles["QAAgent"] = AgentBudgetProfile(
            agent_type="QAAgent",
            base_allocation={
                "core_task": 0.40,
                "historical": 0.15,
                "dependencies": 0.30,
                "agent_memory": 0.10,
                "buffer": 0.05
            },
            tdd_phase_modifiers={
                TDDState.TEST_RED: {
                    "core_task": 1.4,
                    "dependencies": 1.3,
                    "agent_memory": 1.2
                }
            },
            minimum_allocations={
                "core_task": 15000,
                "historical": 5000,
                "dependencies": 12000,
                "agent_memory": 5000,
                "buffer": 2000
            },
            priority_factors={
                "testing": 1.5,
                "validation": 1.3,
                "quality": 1.2
            }
        )
        
        # Data Agent - Needs analysis context and data files
        profiles["DataAgent"] = AgentBudgetProfile(
            agent_type="DataAgent",
            base_allocation={
                "core_task": 0.35,
                "historical": 0.25,
                "dependencies": 0.25,
                "agent_memory": 0.10,
                "buffer": 0.05
            },
            tdd_phase_modifiers={},
            minimum_allocations={
                "core_task": 12000,
                "historical": 8000,
                "dependencies": 10000,
                "agent_memory": 5000,
                "buffer": 2000
            },
            priority_factors={
                "analysis": 1.4,
                "data": 1.3,
                "metrics": 1.2
            }
        )
        
        # Default profile for unknown agent types
        profiles["default"] = AgentBudgetProfile(
            agent_type="default",
            base_allocation={
                "core_task": 0.40,
                "historical": 0.25,
                "dependencies": 0.20,
                "agent_memory": 0.10,
                "buffer": 0.05
            },
            tdd_phase_modifiers={},
            minimum_allocations={
                "core_task": 15000,
                "historical": 8000,
                "dependencies": 8000,
                "agent_memory": 5000,
                "buffer": 2000
            },
            priority_factors={}
        )
        
        return profiles
    
    def _apply_metadata_adjustments(
        self, 
        base_allocation: Dict[str, float], 
        metadata: Dict[str, Any]
    ) -> Dict[str, float]:
        """Apply metadata-based adjustments to allocation"""
        adjusted = base_allocation.copy()
        
        # Adjust based on context hints
        if "focus_areas" in metadata:
            focus_areas = metadata["focus_areas"]
            if "historical" in focus_areas:
                adjusted["historical"] *= 1.2
                adjusted["core_task"] *= 0.9
            if "dependencies" in focus_areas:
                adjusted["dependencies"] *= 1.3
                adjusted["core_task"] *= 0.9
            if "memory" in focus_areas:
                adjusted["agent_memory"] *= 1.5
                adjusted["core_task"] *= 0.9
        
        # Adjust based on complexity indicators
        if "complexity" in metadata:
            complexity = metadata["complexity"]
            if complexity == "high":
                adjusted["core_task"] *= 1.2
                adjusted["buffer"] *= 1.5
            elif complexity == "low":
                adjusted["core_task"] *= 0.8
                adjusted["buffer"] *= 0.7
        
        # Normalize to ensure total doesn't exceed 1.0
        total = sum(adjusted.values())
        if total > 1.0:
            for key in adjusted:
                adjusted[key] /= total
        
        return adjusted
    
    def _enforce_minimum_allocations(
        self, 
        budget: TokenBudget, 
        profile: AgentBudgetProfile
    ) -> TokenBudget:
        """Ensure minimum allocations are met"""
        adjustments = {}
        total_needed = 0
        
        # Check each component
        for component, min_tokens in profile.minimum_allocations.items():
            current_value = getattr(budget, component)
            if current_value < min_tokens:
                adjustments[component] = min_tokens - current_value
                total_needed += adjustments[component]
        
        if total_needed > 0:
            # Need to adjust allocations
            available_buffer = budget.buffer
            
            if available_buffer >= total_needed:
                # Use buffer to meet minimums
                for component, needed in adjustments.items():
                    setattr(budget, component, getattr(budget, component) + needed)
                budget.buffer -= total_needed
            else:
                # Redistribute from other components
                budget = self._redistribute_for_minimums(budget, adjustments, profile)
        
        return budget
    
    def _redistribute_for_minimums(
        self, 
        budget: TokenBudget, 
        adjustments: Dict[str, int], 
        profile: AgentBudgetProfile
    ) -> TokenBudget:
        """Redistribute tokens to meet minimum requirements"""
        total_needed = sum(adjustments.values())
        
        # Calculate how much we can reduce from each component
        reducible = {}
        for component in ["core_task", "historical", "dependencies", "agent_memory"]:
            if component not in adjustments:  # Don't reduce components that need increases
                current = getattr(budget, component)
                minimum = profile.minimum_allocations.get(component, 0)
                reducible[component] = max(0, current - minimum)
        
        total_reducible = sum(reducible.values())
        
        if total_reducible >= total_needed:
            # Proportionally reduce components
            for component, reduction_capacity in reducible.items():
                if reduction_capacity > 0:
                    reduction = int((reduction_capacity / total_reducible) * total_needed)
                    setattr(budget, component, getattr(budget, component) - reduction)
            
            # Apply the increases
            for component, needed in adjustments.items():
                setattr(budget, component, getattr(budget, component) + needed)
        
        return budget
    
    def _get_content_type_multiplier(self, content_type: Optional[FileType], content: str) -> float:
        """Get token estimation multiplier for content type"""
        if not content_type:
            # Try to detect content type from content
            content_type = self._detect_content_type(content)
        
        multipliers = {
            FileType.PYTHON: 1.1,     # Code has more tokens per character
            FileType.TEST: 1.15,      # Test code is often more verbose
            FileType.MARKDOWN: 0.9,   # Documentation is more readable
            FileType.JSON: 0.8,       # Structured data is more compact
            FileType.YAML: 0.85,      # Configuration files
            FileType.CONFIG: 0.8,     # Config files are compact
            FileType.OTHER: 1.0       # Default
        }
        
        return multipliers.get(content_type, 1.0)
    
    def _detect_content_type(self, content: str) -> FileType:
        """Detect content type from content analysis"""
        content_lower = content.lower()
        
        # Check for Python patterns
        if any(keyword in content for keyword in ["def ", "class ", "import ", "from "]):
            if any(test_pattern in content_lower for test_pattern in ["test_", "assert", "pytest", "unittest"]):
                return FileType.TEST
            return FileType.PYTHON
        
        # Check for markdown patterns
        if any(pattern in content for pattern in ["# ", "## ", "```", "[", "]("]):
            return FileType.MARKDOWN
        
        # Check for JSON patterns
        if content.strip().startswith("{") and content.strip().endswith("}"):
            return FileType.JSON
        
        # Check for YAML patterns
        if re.search(r"^\s*\w+:\s", content, re.MULTILINE):
            return FileType.YAML
        
        return FileType.OTHER
    
    def _adjust_for_content_complexity(self, content: str, base_estimate: int) -> int:
        """Adjust token estimation based on content complexity"""
        complexity_indicators = {
            "nested_structures": len(re.findall(r"[\{\[\(]", content)),
            "long_lines": len([line for line in content.split("\n") if len(line) > 100]),
            "special_characters": len(re.findall(r"[^\w\s\n]", content)),
            "code_blocks": len(re.findall(r"```", content)),
        }
        
        # Calculate complexity score
        complexity_score = (
            complexity_indicators["nested_structures"] * 0.1 +
            complexity_indicators["long_lines"] * 0.05 +
            complexity_indicators["special_characters"] * 0.001 +
            complexity_indicators["code_blocks"] * 0.2
        )
        
        # Apply complexity adjustment (max 20% increase)
        complexity_multiplier = min(1.2, 1.0 + complexity_score * 0.001)
        
        return int(base_estimate * complexity_multiplier)
    
    async def _optimize_based_on_history(
        self, 
        budget: TokenBudget, 
        agent_type: str, 
        tdd_phase: Optional[TDDState]
    ) -> TokenBudget:
        """Optimize budget based on historical usage patterns"""
        if not self.usage_history:
            return budget
        
        # Filter relevant history
        relevant_history = [
            usage for usage in self.usage_history
            if usage.context_id.startswith(agent_type.lower()) or 
               (tdd_phase and str(tdd_phase.value) in usage.context_id)
        ]
        
        if not relevant_history:
            return budget
        
        # Calculate average usage patterns
        avg_usage = {
            "core_task": sum(u.core_task_used for u in relevant_history) / len(relevant_history),
            "historical": sum(u.historical_used for u in relevant_history) / len(relevant_history),
            "dependencies": sum(u.dependencies_used for u in relevant_history) / len(relevant_history),
            "agent_memory": sum(u.agent_memory_used for u in relevant_history) / len(relevant_history),
        }
        
        # Adjust budget based on historical patterns
        optimized_budget = TokenBudget(
            total_budget=budget.total_budget,
            core_task=self._adjust_component(budget.core_task, avg_usage["core_task"]),
            historical=self._adjust_component(budget.historical, avg_usage["historical"]),
            dependencies=self._adjust_component(budget.dependencies, avg_usage["dependencies"]),
            agent_memory=self._adjust_component(budget.agent_memory, avg_usage["agent_memory"]),
            buffer=budget.buffer
        )
        
        return self._validate_and_adjust_budget(optimized_budget)
    
    def _adjust_component(self, budgeted: int, historical_avg: float) -> int:
        """Adjust budget component based on historical usage"""
        if historical_avg == 0:
            return budgeted
        
        # Calculate adjustment factor (max 30% change)
        adjustment_factor = min(1.3, max(0.7, historical_avg / budgeted if budgeted > 0 else 1.0))
        
        return int(budgeted * adjustment_factor)
    
    def _validate_and_adjust_budget(self, budget: TokenBudget) -> TokenBudget:
        """Ensure budget is valid and within limits"""
        total_allocated = (
            budget.core_task + budget.historical + budget.dependencies + 
            budget.agent_memory + budget.buffer
        )
        
        if total_allocated > budget.total_budget:
            # Scale down proportionally
            scale_factor = budget.total_budget / total_allocated
            budget.core_task = int(budget.core_task * scale_factor)
            budget.historical = int(budget.historical * scale_factor)
            budget.dependencies = int(budget.dependencies * scale_factor)
            budget.agent_memory = int(budget.agent_memory * scale_factor)
            budget.buffer = int(budget.buffer * scale_factor)
        
        return budget
    
    def _create_safe_default_budget(self, total_tokens: int) -> TokenBudget:
        """Create a safe default budget when calculation fails"""
        return TokenBudget(
            total_budget=total_tokens,
            core_task=int(total_tokens * 0.40),
            historical=int(total_tokens * 0.25),
            dependencies=int(total_tokens * 0.20),
            agent_memory=int(total_tokens * 0.10),
            buffer=int(total_tokens * 0.05)
        )
    
    def _optimize_for_underuse(self, budget: TokenBudget, usage: TokenUsage) -> TokenBudget:
        """Optimize budget when tokens are under-utilized"""
        # Reduce allocations for under-used components
        optimized = TokenBudget(
            total_budget=budget.total_budget,
            core_task=max(usage.core_task_used * 2, budget.core_task // 2),
            historical=max(usage.historical_used * 2, budget.historical // 2),
            dependencies=max(usage.dependencies_used * 2, budget.dependencies // 2),
            agent_memory=max(usage.agent_memory_used * 2, budget.agent_memory // 2),
            buffer=budget.buffer
        )
        
        return self._validate_and_adjust_budget(optimized)
    
    def _optimize_for_overuse(self, budget: TokenBudget, usage: TokenUsage) -> TokenBudget:
        """Optimize budget when tokens are over-utilized"""
        # Increase allocations for over-used components
        optimized = TokenBudget(
            total_budget=budget.total_budget,
            core_task=min(usage.core_task_used * 1.5, budget.total_budget // 2),
            historical=min(usage.historical_used * 1.5, budget.total_budget // 4),
            dependencies=min(usage.dependencies_used * 1.5, budget.total_budget // 4),
            agent_memory=min(usage.agent_memory_used * 1.5, budget.total_budget // 8),
            buffer=budget.buffer
        )
        
        return self._validate_and_adjust_budget(optimized)
    
    def _fine_tune_allocation(self, budget: TokenBudget, usage: TokenUsage, quality: float) -> TokenBudget:
        """Fine-tune allocation based on quality score"""
        if quality > 0.8:
            # High quality, minor adjustments
            adjustment_factor = 1.05
        elif quality < 0.6:
            # Low quality, more significant adjustments
            adjustment_factor = 1.15
        else:
            # Medium quality, moderate adjustments
            adjustment_factor = 1.10
        
        # Adjust based on component usage efficiency
        optimized = TokenBudget(
            total_budget=budget.total_budget,
            core_task=int(budget.core_task * self._get_component_efficiency_factor(budget.core_task, usage.core_task_used) * adjustment_factor),
            historical=int(budget.historical * self._get_component_efficiency_factor(budget.historical, usage.historical_used) * adjustment_factor),
            dependencies=int(budget.dependencies * self._get_component_efficiency_factor(budget.dependencies, usage.dependencies_used) * adjustment_factor),
            agent_memory=int(budget.agent_memory * self._get_component_efficiency_factor(budget.agent_memory, usage.agent_memory_used) * adjustment_factor),
            buffer=budget.buffer
        )
        
        return self._validate_and_adjust_budget(optimized)
    
    def _get_component_efficiency_factor(self, budgeted: int, used: int) -> float:
        """Calculate efficiency factor for a budget component"""
        if budgeted == 0:
            return 1.0
        
        efficiency = used / budgeted
        
        if efficiency < 0.5:
            return 0.8  # Reduce allocation for under-used component
        elif efficiency > 0.9:
            return 1.2  # Increase allocation for heavily used component
        else:
            return 1.0  # Keep current allocation