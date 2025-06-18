"""
Conflict Resolution System

File conflict detection, dependency resolution, and merge conflict prevention
for parallel TDD execution. Integrates with Context Management System for
intelligent conflict analysis and resolution strategies.
"""

import asyncio
import logging
import time
import hashlib
import os
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json
import difflib

# Import required systems
try:
    from .tdd_models import TDDState, TDDCycle, TDDTask
    from .context_manager import ContextManager
    from .agents import BaseAgent
except ImportError:
    from tdd_models import TDDState, TDDCycle, TDDTask
    from context_manager import ContextManager
    from agents import BaseAgent

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts that can occur"""
    FILE_MODIFICATION = "file_modification"    # Multiple cycles modifying same file
    DEPENDENCY_VIOLATION = "dependency_violation"  # Dependency ordering issues
    MERGE_CONFLICT = "merge_conflict"          # Git merge conflicts
    TEST_CONFLICT = "test_conflict"           # Test file conflicts
    RESOURCE_CONTENTION = "resource_contention"  # Resource access conflicts
    SEMANTIC_CONFLICT = "semantic_conflict"    # Semantic code conflicts


class ConflictSeverity(Enum):
    """Severity levels for conflicts"""
    LOW = "low"           # Minor conflicts, can be auto-resolved
    MEDIUM = "medium"     # Moderate conflicts, require coordination
    HIGH = "high"         # Major conflicts, need human intervention
    CRITICAL = "critical"  # Blocking conflicts, halt execution


class ResolutionStrategy(Enum):
    """Conflict resolution strategies"""
    AUTO_RESOLVE = "auto_resolve"        # Automatic resolution
    COORDINATION = "coordination"        # Coordinate between cycles
    SERIALIZATION = "serialization"     # Serialize conflicting operations
    HUMAN_ESCALATION = "human_escalation"  # Escalate to human
    ABORT_CYCLE = "abort_cycle"         # Abort conflicting cycle


class ConflictStatus(Enum):
    """Status of conflict resolution"""
    DETECTED = "detected"
    ANALYZING = "analyzing"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    FAILED = "failed"


@dataclass
class FileModification:
    """Information about file modifications"""
    file_path: str
    cycle_id: str
    story_id: str
    modification_type: str  # create, modify, delete, rename
    content_hash: str
    timestamp: datetime
    line_ranges: List[Tuple[int, int]] = field(default_factory=list)  # Modified line ranges
    functions_modified: List[str] = field(default_factory=list)
    classes_modified: List[str] = field(default_factory=list)
    imports_modified: List[str] = field(default_factory=list)


@dataclass
class Conflict:
    """Conflict information"""
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    affected_cycles: Set[str]
    affected_files: Set[str]
    dependencies: List[str] = field(default_factory=list)
    description: str = ""
    detected_at: datetime = field(default_factory=datetime.utcnow)
    status: ConflictStatus = ConflictStatus.DETECTED
    resolution_strategy: Optional[ResolutionStrategy] = None
    resolution_attempts: int = 0
    resolution_time: Optional[float] = None
    human_intervention_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolutionResult:
    """Result of conflict resolution attempt"""
    success: bool
    strategy_used: ResolutionStrategy
    resolution_time: float
    actions_taken: List[str] = field(default_factory=list)
    remaining_conflicts: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    requires_verification: bool = False


@dataclass
class ConflictAnalysis:
    """Analysis of a potential conflict"""
    conflict_probability: float  # 0.0 to 1.0
    impact_assessment: str
    affected_components: List[str]
    resolution_complexity: str  # simple, moderate, complex
    recommended_strategy: ResolutionStrategy
    prevention_suggestions: List[str] = field(default_factory=list)


class ConflictResolver:
    """
    Conflict Resolution System for Parallel TDD Execution.
    
    Detects, analyzes, and resolves conflicts between parallel TDD cycles
    with intelligent prevention and resolution strategies.
    """
    
    def __init__(
        self,
        context_manager: ContextManager,
        project_path: str,
        enable_proactive_detection: bool = True,
        enable_auto_resolution: bool = True,
        enable_semantic_analysis: bool = True,
        resolution_timeout_seconds: int = 300,
        max_resolution_attempts: int = 3
    ):
        """
        Initialize Conflict Resolver.
        
        Args:
            context_manager: Context manager for intelligent analysis
            project_path: Project root path
            enable_proactive_detection: Enable proactive conflict detection
            enable_auto_resolution: Enable automatic resolution
            enable_semantic_analysis: Enable semantic conflict analysis
            resolution_timeout_seconds: Timeout for resolution attempts
            max_resolution_attempts: Maximum resolution attempts per conflict
        """
        self.context_manager = context_manager
        self.project_path = Path(project_path)
        self.enable_proactive_detection = enable_proactive_detection
        self.enable_auto_resolution = enable_auto_resolution
        self.enable_semantic_analysis = enable_semantic_analysis
        self.resolution_timeout = resolution_timeout_seconds
        self.max_resolution_attempts = max_resolution_attempts
        
        # Conflict tracking
        self.active_conflicts: Dict[str, Conflict] = {}
        self.resolved_conflicts: Dict[str, Conflict] = {}
        self.file_modifications: Dict[str, List[FileModification]] = {}  # file_path -> modifications
        self.cycle_dependencies: Dict[str, Set[str]] = {}  # cycle_id -> dependency cycle_ids
        
        # Resolution strategies
        self.resolution_strategies: Dict[ConflictType, List[ResolutionStrategy]] = {
            ConflictType.FILE_MODIFICATION: [
                ResolutionStrategy.COORDINATION,
                ResolutionStrategy.SERIALIZATION,
                ResolutionStrategy.AUTO_RESOLVE
            ],
            ConflictType.DEPENDENCY_VIOLATION: [
                ResolutionStrategy.SERIALIZATION,
                ResolutionStrategy.COORDINATION
            ],
            ConflictType.MERGE_CONFLICT: [
                ResolutionStrategy.AUTO_RESOLVE,
                ResolutionStrategy.HUMAN_ESCALATION
            ],
            ConflictType.TEST_CONFLICT: [
                ResolutionStrategy.COORDINATION,
                ResolutionStrategy.AUTO_RESOLVE
            ],
            ConflictType.RESOURCE_CONTENTION: [
                ResolutionStrategy.SERIALIZATION,
                ResolutionStrategy.COORDINATION
            ],
            ConflictType.SEMANTIC_CONFLICT: [
                ResolutionStrategy.HUMAN_ESCALATION,
                ResolutionStrategy.COORDINATION
            ]
        }
        
        # Performance tracking
        self.resolution_stats = {
            "total_conflicts": 0,
            "auto_resolved": 0,
            "escalated": 0,
            "failed": 0,
            "average_resolution_time": 0.0,
            "prevention_success_rate": 0.0
        }
        
        # Background monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(
            f"ConflictResolver initialized for project: {project_path} "
            f"(proactive: {enable_proactive_detection}, auto_resolve: {enable_auto_resolution})"
        )
    
    async def start(self) -> None:
        """Start the conflict resolution system"""
        if self._running:
            logger.warning("Conflict resolver already running")
            return
        
        self._running = True
        logger.info("Starting conflict resolution system")
        
        # Start background monitoring
        if self.enable_proactive_detection:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Conflict resolution system started")
    
    async def stop(self) -> None:
        """Stop the conflict resolution system"""
        if not self._running:
            return
        
        logger.info("Stopping conflict resolution system")
        self._running = False
        
        # Cancel monitoring task
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Conflict resolution system stopped")
    
    async def register_file_modification(
        self,
        file_path: str,
        cycle_id: str,
        story_id: str,
        modification_type: str = "modify"
    ) -> None:
        """
        Register a file modification for conflict tracking.
        
        Args:
            file_path: Path to the modified file
            cycle_id: ID of the TDD cycle making the modification
            story_id: ID of the story
            modification_type: Type of modification (create, modify, delete, rename)
        """
        # Calculate content hash if file exists
        content_hash = ""
        if Path(file_path).exists():
            content_hash = await self._calculate_file_hash(file_path)
        
        modification = FileModification(
            file_path=file_path,
            cycle_id=cycle_id,
            story_id=story_id,
            modification_type=modification_type,
            content_hash=content_hash,
            timestamp=datetime.utcnow()
        )
        
        # Analyze file content for detailed modification info
        if self.enable_semantic_analysis and Path(file_path).exists():
            await self._analyze_file_modifications(modification)
        
        # Store modification
        if file_path not in self.file_modifications:
            self.file_modifications[file_path] = []
        self.file_modifications[file_path].append(modification)
        
        # Check for immediate conflicts
        conflicts = await self._detect_file_conflicts(file_path)
        for conflict in conflicts:
            await self._handle_detected_conflict(conflict)
        
        logger.debug(f"Registered {modification_type} for {file_path} by cycle {cycle_id}")
    
    async def register_cycle_dependency(self, cycle_id: str, dependency_cycle_id: str) -> None:
        """Register a dependency between cycles"""
        if cycle_id not in self.cycle_dependencies:
            self.cycle_dependencies[cycle_id] = set()
        
        self.cycle_dependencies[cycle_id].add(dependency_cycle_id)
        
        # Check for dependency cycles
        if await self._detect_dependency_cycle(cycle_id):
            conflict = await self._create_dependency_conflict(cycle_id)
            await self._handle_detected_conflict(conflict)
    
    async def analyze_potential_conflict(
        self,
        cycle1_id: str,
        cycle2_id: str,
        file_paths: List[str]
    ) -> ConflictAnalysis:
        """
        Analyze potential conflict between two cycles.
        
        Args:
            cycle1_id: First cycle ID
            cycle2_id: Second cycle ID
            file_paths: Files that both cycles might modify
            
        Returns:
            ConflictAnalysis with probability and recommendations
        """
        analysis_start = time.time()
        
        # Calculate conflict probability
        conflict_probability = await self._calculate_conflict_probability(
            cycle1_id, cycle2_id, file_paths
        )
        
        # Assess impact
        impact_assessment = await self._assess_conflict_impact(
            cycle1_id, cycle2_id, file_paths
        )
        
        # Identify affected components
        affected_components = await self._identify_affected_components(file_paths)
        
        # Determine resolution complexity
        resolution_complexity = await self._assess_resolution_complexity(
            cycle1_id, cycle2_id, file_paths
        )
        
        # Recommend strategy
        recommended_strategy = await self._recommend_resolution_strategy(
            conflict_probability, impact_assessment, resolution_complexity
        )
        
        # Generate prevention suggestions
        prevention_suggestions = await self._generate_prevention_suggestions(
            cycle1_id, cycle2_id, file_paths
        )
        
        analysis = ConflictAnalysis(
            conflict_probability=conflict_probability,
            impact_assessment=impact_assessment,
            affected_components=affected_components,
            resolution_complexity=resolution_complexity,
            recommended_strategy=recommended_strategy,
            prevention_suggestions=prevention_suggestions
        )
        
        analysis_time = time.time() - analysis_start
        logger.debug(f"Conflict analysis completed in {analysis_time:.2f}s: {conflict_probability:.2f} probability")
        
        return analysis
    
    async def resolve_conflict(self, conflict_id: str) -> ResolutionResult:
        """
        Resolve a specific conflict.
        
        Args:
            conflict_id: ID of the conflict to resolve
            
        Returns:
            ResolutionResult with resolution outcome
        """
        if conflict_id not in self.active_conflicts:
            return ResolutionResult(
                success=False,
                strategy_used=ResolutionStrategy.AUTO_RESOLVE,
                resolution_time=0.0,
                error_message=f"Conflict {conflict_id} not found"
            )
        
        conflict = self.active_conflicts[conflict_id]
        conflict.status = ConflictStatus.RESOLVING
        conflict.resolution_attempts += 1
        
        resolution_start = time.time()
        
        try:
            # Try resolution strategies in order of preference
            strategies = self.resolution_strategies.get(
                conflict.conflict_type,
                [ResolutionStrategy.HUMAN_ESCALATION]
            )
            
            for strategy in strategies:
                if conflict.resolution_attempts > self.max_resolution_attempts:
                    strategy = ResolutionStrategy.HUMAN_ESCALATION
                
                result = await self._apply_resolution_strategy(conflict, strategy)
                
                if result.success:
                    conflict.status = ConflictStatus.RESOLVED
                    conflict.resolution_strategy = strategy
                    conflict.resolution_time = time.time() - resolution_start
                    
                    # Move to resolved conflicts
                    self.resolved_conflicts[conflict_id] = conflict
                    del self.active_conflicts[conflict_id]
                    
                    # Update statistics
                    self.resolution_stats["total_conflicts"] += 1
                    if strategy == ResolutionStrategy.AUTO_RESOLVE:
                        self.resolution_stats["auto_resolved"] += 1
                    elif strategy == ResolutionStrategy.HUMAN_ESCALATION:
                        self.resolution_stats["escalated"] += 1
                    
                    self._update_average_resolution_time(conflict.resolution_time)
                    
                    logger.info(f"Resolved conflict {conflict_id} using {strategy.value}")
                    return result
                
                # Log failed attempt
                logger.warning(f"Failed to resolve conflict {conflict_id} using {strategy.value}")
            
            # All strategies failed
            conflict.status = ConflictStatus.FAILED
            self.resolution_stats["failed"] += 1
            
            return ResolutionResult(
                success=False,
                strategy_used=strategies[-1] if strategies else ResolutionStrategy.HUMAN_ESCALATION,
                resolution_time=time.time() - resolution_start,
                error_message="All resolution strategies failed"
            )
            
        except Exception as e:
            conflict.status = ConflictStatus.FAILED
            self.resolution_stats["failed"] += 1
            
            return ResolutionResult(
                success=False,
                strategy_used=ResolutionStrategy.AUTO_RESOLVE,
                resolution_time=time.time() - resolution_start,
                error_message=f"Resolution error: {str(e)}"
            )
    
    async def get_conflict_status(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a conflict"""
        conflict = self.active_conflicts.get(conflict_id) or self.resolved_conflicts.get(conflict_id)
        
        if not conflict:
            return None
        
        return {
            "conflict_id": conflict_id,
            "type": conflict.conflict_type.value,
            "severity": conflict.severity.value,
            "status": conflict.status.value,
            "affected_cycles": list(conflict.affected_cycles),
            "affected_files": list(conflict.affected_files),
            "dependencies": conflict.dependencies,
            "description": conflict.description,
            "detected_at": conflict.detected_at.isoformat(),
            "resolution_strategy": conflict.resolution_strategy.value if conflict.resolution_strategy else None,
            "resolution_attempts": conflict.resolution_attempts,
            "resolution_time": conflict.resolution_time,
            "human_intervention_required": conflict.human_intervention_required,
            "metadata": conflict.metadata
        }
    
    async def get_active_conflicts(self) -> List[Dict[str, Any]]:
        """Get all active conflicts"""
        return [
            await self.get_conflict_status(conflict_id)
            for conflict_id in self.active_conflicts.keys()
        ]
    
    async def get_resolution_statistics(self) -> Dict[str, Any]:
        """Get conflict resolution statistics"""
        total_conflicts = self.resolution_stats["total_conflicts"]
        
        return {
            "total_conflicts": total_conflicts,
            "active_conflicts": len(self.active_conflicts),
            "resolved_conflicts": len(self.resolved_conflicts),
            "auto_resolved": self.resolution_stats["auto_resolved"],
            "escalated": self.resolution_stats["escalated"],
            "failed": self.resolution_stats["failed"],
            "auto_resolution_rate": (
                self.resolution_stats["auto_resolved"] / max(total_conflicts, 1) * 100
            ),
            "escalation_rate": (
                self.resolution_stats["escalated"] / max(total_conflicts, 1) * 100
            ),
            "failure_rate": (
                self.resolution_stats["failed"] / max(total_conflicts, 1) * 100
            ),
            "average_resolution_time": self.resolution_stats["average_resolution_time"],
            "prevention_success_rate": self.resolution_stats["prevention_success_rate"],
            "file_modification_tracking": len(self.file_modifications),
            "dependency_tracking": len(self.cycle_dependencies)
        }
    
    # Private conflict detection methods
    
    async def _detect_file_conflicts(self, file_path: str) -> List[Conflict]:
        """Detect conflicts for a specific file"""
        conflicts = []
        modifications = self.file_modifications.get(file_path, [])
        
        if len(modifications) < 2:
            return conflicts
        
        # Group modifications by cycle
        cycle_modifications = {}
        for mod in modifications:
            if mod.cycle_id not in cycle_modifications:
                cycle_modifications[mod.cycle_id] = []
            cycle_modifications[mod.cycle_id].append(mod)
        
        # Check for conflicts between different cycles
        cycle_ids = list(cycle_modifications.keys())
        for i, cycle1 in enumerate(cycle_ids):
            for cycle2 in cycle_ids[i+1:]:
                if await self._cycles_conflict_on_file(file_path, cycle1, cycle2):
                    conflict = await self._create_file_conflict(file_path, cycle1, cycle2)
                    conflicts.append(conflict)
        
        return conflicts
    
    async def _cycles_conflict_on_file(self, file_path: str, cycle1: str, cycle2: str) -> bool:
        """Check if two cycles conflict on a specific file"""
        mods1 = [m for m in self.file_modifications[file_path] if m.cycle_id == cycle1]
        mods2 = [m for m in self.file_modifications[file_path] if m.cycle_id == cycle2]
        
        # Check for overlapping modifications
        for mod1 in mods1:
            for mod2 in mods2:
                # Check for line range overlaps
                if await self._line_ranges_overlap(mod1.line_ranges, mod2.line_ranges):
                    return True
                
                # Check for function/class conflicts
                if (set(mod1.functions_modified) & set(mod2.functions_modified) or
                    set(mod1.classes_modified) & set(mod2.classes_modified)):
                    return True
                
                # Check for import conflicts
                if set(mod1.imports_modified) & set(mod2.imports_modified):
                    return True
        
        return False
    
    async def _line_ranges_overlap(
        self, 
        ranges1: List[Tuple[int, int]], 
        ranges2: List[Tuple[int, int]]
    ) -> bool:
        """Check if line ranges overlap"""
        for start1, end1 in ranges1:
            for start2, end2 in ranges2:
                if not (end1 < start2 or end2 < start1):
                    return True
        return False
    
    async def _detect_dependency_cycle(self, cycle_id: str) -> bool:
        """Detect if adding a dependency creates a cycle"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.cycle_dependencies.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        return has_cycle(cycle_id)
    
    # Private conflict creation methods
    
    async def _create_file_conflict(self, file_path: str, cycle1: str, cycle2: str) -> Conflict:
        """Create a file modification conflict"""
        conflict_id = f"file_{hashlib.md5(f'{file_path}_{cycle1}_{cycle2}'.encode()).hexdigest()[:8]}"
        
        severity = await self._assess_file_conflict_severity(file_path, cycle1, cycle2)
        
        return Conflict(
            conflict_id=conflict_id,
            conflict_type=ConflictType.FILE_MODIFICATION,
            severity=severity,
            affected_cycles={cycle1, cycle2},
            affected_files={file_path},
            description=f"File modification conflict on {file_path} between cycles {cycle1} and {cycle2}",
            metadata={
                "file_path": file_path,
                "conflicting_cycles": [cycle1, cycle2],
                "modification_count": len(self.file_modifications.get(file_path, []))
            }
        )
    
    async def _create_dependency_conflict(self, cycle_id: str) -> Conflict:
        """Create a dependency cycle conflict"""
        conflict_id = f"dep_{hashlib.md5(f'dependency_{cycle_id}'.encode()).hexdigest()[:8]}"
        
        return Conflict(
            conflict_id=conflict_id,
            conflict_type=ConflictType.DEPENDENCY_VIOLATION,
            severity=ConflictSeverity.HIGH,
            affected_cycles={cycle_id},
            affected_files=set(),
            description=f"Dependency cycle detected involving cycle {cycle_id}",
            metadata={
                "cycle_id": cycle_id,
                "dependencies": list(self.cycle_dependencies.get(cycle_id, set()))
            }
        )
    
    # Private analysis methods
    
    async def _calculate_conflict_probability(
        self, 
        cycle1_id: str, 
        cycle2_id: str, 
        file_paths: List[str]
    ) -> float:
        """Calculate probability of conflict between cycles"""
        probability_factors = []
        
        # File overlap factor
        shared_files = len(file_paths)
        if shared_files > 0:
            probability_factors.append(min(shared_files / 10.0, 0.8))
        
        # Temporal factor (if cycles run concurrently)
        probability_factors.append(0.5)
        
        # Complexity factor (based on file types)
        complexity_score = 0
        for file_path in file_paths:
            if file_path.endswith('.py'):
                complexity_score += 0.3
            elif file_path.endswith('.md'):
                complexity_score += 0.1
            else:
                complexity_score += 0.2
        probability_factors.append(min(complexity_score, 0.7))
        
        # Calculate weighted average
        if not probability_factors:
            return 0.0
        
        return sum(probability_factors) / len(probability_factors)
    
    async def _assess_conflict_impact(
        self, 
        cycle1_id: str, 
        cycle2_id: str, 
        file_paths: List[str]
    ) -> str:
        """Assess the impact of a potential conflict"""
        critical_files = [f for f in file_paths if 'test' in f or '__init__' in f]
        
        if len(critical_files) > 2:
            return "High impact: Multiple critical files affected"
        elif len(file_paths) > 5:
            return "Medium impact: Many files affected"
        elif critical_files:
            return "Medium impact: Critical files affected"
        else:
            return "Low impact: Standard files affected"
    
    async def _identify_affected_components(self, file_paths: List[str]) -> List[str]:
        """Identify software components affected by file changes"""
        components = set()
        
        for file_path in file_paths:
            path_parts = Path(file_path).parts
            
            # Identify by directory structure
            if 'tests' in path_parts:
                components.add('test_suite')
            if 'lib' in path_parts:
                components.add('core_library')
            if 'scripts' in path_parts:
                components.add('scripts')
            if 'docs' in path_parts:
                components.add('documentation')
            
            # Identify by file type
            suffix = Path(file_path).suffix
            if suffix == '.py':
                components.add('python_code')
            elif suffix in ['.md', '.rst']:
                components.add('documentation')
            elif suffix in ['.yml', '.yaml']:
                components.add('configuration')
        
        return list(components)
    
    async def _assess_resolution_complexity(
        self, 
        cycle1_id: str, 
        cycle2_id: str, 
        file_paths: List[str]
    ) -> str:
        """Assess complexity of resolving potential conflict"""
        if len(file_paths) > 10:
            return "complex"
        elif len(file_paths) > 3:
            return "moderate"
        else:
            return "simple"
    
    async def _recommend_resolution_strategy(
        self,
        probability: float,
        impact: str,
        complexity: str
    ) -> ResolutionStrategy:
        """Recommend resolution strategy based on analysis"""
        if probability > 0.8 or "High impact" in impact:
            return ResolutionStrategy.HUMAN_ESCALATION
        elif probability > 0.5 or "Medium impact" in impact:
            return ResolutionStrategy.COORDINATION
        elif complexity == "simple":
            return ResolutionStrategy.AUTO_RESOLVE
        else:
            return ResolutionStrategy.SERIALIZATION
    
    async def _generate_prevention_suggestions(
        self,
        cycle1_id: str,
        cycle2_id: str,
        file_paths: List[str]
    ) -> List[str]:
        """Generate suggestions to prevent conflicts"""
        suggestions = []
        
        if len(file_paths) > 5:
            suggestions.append("Consider breaking down tasks into smaller, more focused units")
        
        test_files = [f for f in file_paths if 'test' in f]
        if test_files:
            suggestions.append("Coordinate test file modifications to avoid conflicts")
        
        if any('__init__' in f for f in file_paths):
            suggestions.append("Be careful with module initialization files")
        
        suggestions.append("Use feature branches to isolate changes")
        suggestions.append("Communicate with other developers about shared files")
        
        return suggestions
    
    # Private resolution methods
    
    async def _apply_resolution_strategy(
        self, 
        conflict: Conflict, 
        strategy: ResolutionStrategy
    ) -> ResolutionResult:
        """Apply a specific resolution strategy"""
        resolution_start = time.time()
        
        try:
            if strategy == ResolutionStrategy.AUTO_RESOLVE:
                return await self._auto_resolve_conflict(conflict)
            elif strategy == ResolutionStrategy.COORDINATION:
                return await self._coordinate_cycles(conflict)
            elif strategy == ResolutionStrategy.SERIALIZATION:
                return await self._serialize_operations(conflict)
            elif strategy == ResolutionStrategy.HUMAN_ESCALATION:
                return await self._escalate_to_human(conflict)
            elif strategy == ResolutionStrategy.ABORT_CYCLE:
                return await self._abort_conflicting_cycle(conflict)
            else:
                return ResolutionResult(
                    success=False,
                    strategy_used=strategy,
                    resolution_time=time.time() - resolution_start,
                    error_message=f"Unknown strategy: {strategy.value}"
                )
        except Exception as e:
            return ResolutionResult(
                success=False,
                strategy_used=strategy,
                resolution_time=time.time() - resolution_start,
                error_message=f"Strategy execution failed: {str(e)}"
            )
    
    async def _auto_resolve_conflict(self, conflict: Conflict) -> ResolutionResult:
        """Attempt automatic conflict resolution"""
        actions_taken = []
        
        if conflict.conflict_type == ConflictType.FILE_MODIFICATION:
            # For file conflicts, try to merge changes automatically
            for file_path in conflict.affected_files:
                merge_result = await self._auto_merge_file(file_path, conflict.affected_cycles)
                if merge_result:
                    actions_taken.append(f"Auto-merged changes in {file_path}")
                else:
                    return ResolutionResult(
                        success=False,
                        strategy_used=ResolutionStrategy.AUTO_RESOLVE,
                        resolution_time=0.0,
                        error_message=f"Failed to auto-merge {file_path}"
                    )
        
        return ResolutionResult(
            success=True,
            strategy_used=ResolutionStrategy.AUTO_RESOLVE,
            resolution_time=0.0,
            actions_taken=actions_taken
        )
    
    async def _coordinate_cycles(self, conflict: Conflict) -> ResolutionResult:
        """Coordinate between conflicting cycles"""
        actions_taken = []
        
        # Send coordination messages to affected cycles
        for cycle_id in conflict.affected_cycles:
            actions_taken.append(f"Sent coordination request to cycle {cycle_id}")
        
        return ResolutionResult(
            success=True,
            strategy_used=ResolutionStrategy.COORDINATION,
            resolution_time=0.0,
            actions_taken=actions_taken,
            requires_verification=True
        )
    
    async def _serialize_operations(self, conflict: Conflict) -> ResolutionResult:
        """Serialize conflicting operations"""
        actions_taken = []
        
        # Sort cycles by priority and serialize their operations
        cycle_list = list(conflict.affected_cycles)
        cycle_list.sort()  # Simple ordering by cycle ID
        
        for i, cycle_id in enumerate(cycle_list[1:], 1):
            actions_taken.append(f"Delayed cycle {cycle_id} (position {i})")
        
        return ResolutionResult(
            success=True,
            strategy_used=ResolutionStrategy.SERIALIZATION,
            resolution_time=0.0,
            actions_taken=actions_taken
        )
    
    async def _escalate_to_human(self, conflict: Conflict) -> ResolutionResult:
        """Escalate conflict to human intervention"""
        conflict.human_intervention_required = True
        conflict.status = ConflictStatus.ESCALATED
        
        return ResolutionResult(
            success=True,  # Escalation is considered successful
            strategy_used=ResolutionStrategy.HUMAN_ESCALATION,
            resolution_time=0.0,
            actions_taken=["Escalated to human intervention"],
            requires_verification=True
        )
    
    async def _abort_conflicting_cycle(self, conflict: Conflict) -> ResolutionResult:
        """Abort the cycle with lower priority"""
        if len(conflict.affected_cycles) < 2:
            return ResolutionResult(
                success=False,
                strategy_used=ResolutionStrategy.ABORT_CYCLE,
                resolution_time=0.0,
                error_message="Need at least 2 cycles to abort one"
            )
        
        # Simple priority: abort the cycle with higher ID (later in time)
        cycle_to_abort = max(conflict.affected_cycles)
        
        return ResolutionResult(
            success=True,
            strategy_used=ResolutionStrategy.ABORT_CYCLE,
            resolution_time=0.0,
            actions_taken=[f"Aborted cycle {cycle_to_abort}"]
        )
    
    # Private utility methods
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate hash of file content"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception:
            return ""
    
    async def _analyze_file_modifications(self, modification: FileModification) -> None:
        """Analyze file for detailed modification information"""
        try:
            if not Path(modification.file_path).exists():
                return
            
            with open(modification.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple analysis for Python files
            if modification.file_path.endswith('.py'):
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    # Detect function definitions
                    if line.startswith('def '):
                        func_name = line.split('(')[0].replace('def ', '')
                        modification.functions_modified.append(func_name)
                    
                    # Detect class definitions
                    elif line.startswith('class '):
                        class_name = line.split('(')[0].split(':')[0].replace('class ', '')
                        modification.classes_modified.append(class_name)
                    
                    # Detect imports
                    elif line.startswith('import ') or line.startswith('from '):
                        modification.imports_modified.append(line)
                
                # For now, assume entire file is modified
                modification.line_ranges = [(1, len(lines))]
        
        except Exception as e:
            logger.debug(f"Failed to analyze file {modification.file_path}: {str(e)}")
    
    async def _assess_file_conflict_severity(
        self, 
        file_path: str, 
        cycle1: str, 
        cycle2: str
    ) -> ConflictSeverity:
        """Assess severity of file conflict"""
        # Check if file is critical
        if any(critical in file_path for critical in ['__init__', 'main', 'setup']):
            return ConflictSeverity.HIGH
        
        # Check modification count
        modification_count = len(self.file_modifications.get(file_path, []))
        if modification_count > 5:
            return ConflictSeverity.MEDIUM
        
        # Check file type
        if file_path.endswith('.py'):
            return ConflictSeverity.MEDIUM
        elif file_path.endswith('.md'):
            return ConflictSeverity.LOW
        
        return ConflictSeverity.LOW
    
    async def _auto_merge_file(self, file_path: str, cycle_ids: Set[str]) -> bool:
        """Attempt to automatically merge file changes"""
        # This is a simplified implementation
        # In a real system, this would use sophisticated merge algorithms
        
        modifications = [
            m for m in self.file_modifications.get(file_path, [])
            if m.cycle_id in cycle_ids
        ]
        
        # For now, just check if modifications don't overlap significantly
        if len(modifications) <= 2:
            return True
        
        return False
    
    async def _handle_detected_conflict(self, conflict: Conflict) -> None:
        """Handle a newly detected conflict"""
        self.active_conflicts[conflict.conflict_id] = conflict
        
        logger.warning(
            f"Detected {conflict.conflict_type.value} conflict {conflict.conflict_id}: "
            f"{conflict.description}"
        )
        
        # Attempt auto-resolution if enabled
        if self.enable_auto_resolution and conflict.severity in [ConflictSeverity.LOW, ConflictSeverity.MEDIUM]:
            asyncio.create_task(self.resolve_conflict(conflict.conflict_id))
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring for proactive conflict detection"""
        logger.info("Started conflict monitoring loop")
        
        while self._running:
            try:
                await self._perform_proactive_detection()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {str(e)}")
                await asyncio.sleep(60)  # Back-off on error
    
    async def _perform_proactive_detection(self) -> None:
        """Perform proactive conflict detection"""
        # Check for potential conflicts in file modifications
        for file_path, modifications in self.file_modifications.items():
            if len(modifications) > 1:
                recent_modifications = [
                    m for m in modifications
                    if (datetime.utcnow() - m.timestamp).total_seconds() < 300  # Last 5 minutes
                ]
                
                if len(recent_modifications) > 1:
                    conflicts = await self._detect_file_conflicts(file_path)
                    for conflict in conflicts:
                        if conflict.conflict_id not in self.active_conflicts:
                            await self._handle_detected_conflict(conflict)
    
    def _update_average_resolution_time(self, resolution_time: float) -> None:
        """Update average resolution time statistic"""
        current_avg = self.resolution_stats["average_resolution_time"]
        if current_avg == 0:
            self.resolution_stats["average_resolution_time"] = resolution_time
        else:
            # Weighted average with 90% weight on previous average
            self.resolution_stats["average_resolution_time"] = (
                current_avg * 0.9 + resolution_time * 0.1
            )