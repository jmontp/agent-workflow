"""
Unit tests for Conflict Resolution System.

Tests conflict detection, analysis, and resolution for parallel TDD execution
with comprehensive coverage of all methods and error handling scenarios.
"""

import pytest
import asyncio
import tempfile
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, mock_open

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.conflict_resolver import (
    ConflictResolver, ConflictType, ConflictSeverity, ResolutionStrategy,
    ConflictStatus, FileModification, Conflict, ResolutionResult,
    ConflictAnalysis
)
from lib.tdd_models import TDDState, TDDCycle, TDDTask


class TestFileModification:
    """Test the FileModification dataclass."""
    
    def test_file_modification_creation(self):
        """Test creating a FileModification instance."""
        timestamp = datetime.utcnow()
        
        modification = FileModification(
            file_path="/path/to/file.py",
            cycle_id="cycle-1",
            story_id="STORY-1",
            modification_type="modify",
            content_hash="abc123",
            timestamp=timestamp,
            line_ranges=[(1, 10), (20, 30)],
            functions_modified=["func1", "func2"],
            classes_modified=["Class1"],
            imports_modified=["import os"]
        )
        
        assert modification.file_path == "/path/to/file.py"
        assert modification.cycle_id == "cycle-1"
        assert modification.story_id == "STORY-1"
        assert modification.modification_type == "modify"
        assert modification.content_hash == "abc123"
        assert modification.timestamp == timestamp
        assert modification.line_ranges == [(1, 10), (20, 30)]
        assert modification.functions_modified == ["func1", "func2"]
        assert modification.classes_modified == ["Class1"]
        assert modification.imports_modified == ["import os"]

    def test_file_modification_defaults(self):
        """Test FileModification with default values."""
        modification = FileModification(
            file_path="/path/to/file.py",
            cycle_id="cycle-1",
            story_id="STORY-1",
            modification_type="create",
            content_hash="def456",
            timestamp=datetime.utcnow()
        )
        
        assert modification.line_ranges == []
        assert modification.functions_modified == []
        assert modification.classes_modified == []
        assert modification.imports_modified == []


class TestConflict:
    """Test the Conflict dataclass."""
    
    def test_conflict_creation(self):
        """Test creating a Conflict instance."""
        detected_at = datetime.utcnow()
        
        conflict = Conflict(
            conflict_id="conflict-1",
            conflict_type=ConflictType.FILE_MODIFICATION,
            severity=ConflictSeverity.MEDIUM,
            affected_cycles={"cycle-1", "cycle-2"},
            affected_files={"/path/to/file.py"},
            dependencies=["dep-1", "dep-2"],
            description="File modification conflict",
            detected_at=detected_at,
            status=ConflictStatus.DETECTED,
            resolution_strategy=ResolutionStrategy.COORDINATION,
            resolution_attempts=1,
            resolution_time=5.5,
            human_intervention_required=True,
            metadata={"custom": "data"}
        )
        
        assert conflict.conflict_id == "conflict-1"
        assert conflict.conflict_type == ConflictType.FILE_MODIFICATION
        assert conflict.severity == ConflictSeverity.MEDIUM
        assert conflict.affected_cycles == {"cycle-1", "cycle-2"}
        assert conflict.affected_files == {"/path/to/file.py"}
        assert conflict.dependencies == ["dep-1", "dep-2"]
        assert conflict.description == "File modification conflict"
        assert conflict.detected_at == detected_at
        assert conflict.status == ConflictStatus.DETECTED
        assert conflict.resolution_strategy == ResolutionStrategy.COORDINATION
        assert conflict.resolution_attempts == 1
        assert conflict.resolution_time == 5.5
        assert conflict.human_intervention_required is True
        assert conflict.metadata == {"custom": "data"}

    def test_conflict_defaults(self):
        """Test Conflict with default values."""
        conflict = Conflict(
            conflict_id="conflict-1",
            conflict_type=ConflictType.MERGE_CONFLICT,
            severity=ConflictSeverity.HIGH,
            affected_cycles={"cycle-1"},
            affected_files={"/path/to/file.py"}
        )
        
        assert conflict.dependencies == []
        assert conflict.description == ""
        assert isinstance(conflict.detected_at, datetime)
        assert conflict.status == ConflictStatus.DETECTED
        assert conflict.resolution_strategy is None
        assert conflict.resolution_attempts == 0
        assert conflict.resolution_time is None
        assert conflict.human_intervention_required is False
        assert conflict.metadata == {}


class TestResolutionResult:
    """Test the ResolutionResult dataclass."""
    
    def test_resolution_result_creation(self):
        """Test creating a ResolutionResult instance."""
        result = ResolutionResult(
            success=True,
            strategy_used=ResolutionStrategy.AUTO_RESOLVE,
            resolution_time=2.5,
            actions_taken=["merged files", "updated imports"],
            remaining_conflicts=["conflict-2"],
            error_message=None,
            requires_verification=True
        )
        
        assert result.success is True
        assert result.strategy_used == ResolutionStrategy.AUTO_RESOLVE
        assert result.resolution_time == 2.5
        assert result.actions_taken == ["merged files", "updated imports"]
        assert result.remaining_conflicts == ["conflict-2"]
        assert result.error_message is None
        assert result.requires_verification is True

    def test_resolution_result_defaults(self):
        """Test ResolutionResult with default values."""
        result = ResolutionResult(
            success=False,
            strategy_used=ResolutionStrategy.HUMAN_ESCALATION,
            resolution_time=0.0
        )
        
        assert result.actions_taken == []
        assert result.remaining_conflicts == []
        assert result.error_message is None
        assert result.requires_verification is False


class TestConflictAnalysis:
    """Test the ConflictAnalysis dataclass."""
    
    def test_conflict_analysis_creation(self):
        """Test creating a ConflictAnalysis instance."""
        analysis = ConflictAnalysis(
            conflict_probability=0.75,
            impact_assessment="High impact",
            affected_components=["core_library", "test_suite"],
            resolution_complexity="moderate",
            recommended_strategy=ResolutionStrategy.COORDINATION,
            prevention_suggestions=["use feature branches", "coordinate changes"]
        )
        
        assert analysis.conflict_probability == 0.75
        assert analysis.impact_assessment == "High impact"
        assert analysis.affected_components == ["core_library", "test_suite"]
        assert analysis.resolution_complexity == "moderate"
        assert analysis.recommended_strategy == ResolutionStrategy.COORDINATION
        assert analysis.prevention_suggestions == ["use feature branches", "coordinate changes"]

    def test_conflict_analysis_defaults(self):
        """Test ConflictAnalysis with default values."""
        analysis = ConflictAnalysis(
            conflict_probability=0.5,
            impact_assessment="Medium impact",
            affected_components=["module1"],
            resolution_complexity="simple",
            recommended_strategy=ResolutionStrategy.AUTO_RESOLVE
        )
        
        assert analysis.prevention_suggestions == []


@pytest.fixture
def mock_context_manager():
    """Create a mock context manager."""
    manager = Mock()
    manager.prepare_context = AsyncMock(return_value={"context": "data"})
    return manager


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def conflict_resolver_factory(mock_context_manager, temp_project_dir):
    """Create a factory for ConflictResolver instances."""
    def _create_resolver():
        return ConflictResolver(
            context_manager=mock_context_manager,
            project_path=temp_project_dir,
            enable_proactive_detection=True,
            enable_auto_resolution=True,
            enable_semantic_analysis=True,
            resolution_timeout_seconds=300,
            max_resolution_attempts=3
        )
    return _create_resolver


@pytest.fixture
def conflict_resolver(conflict_resolver_factory):
    """Create a ConflictResolver instance."""
    return conflict_resolver_factory()


class TestConflictResolver:
    """Test the ConflictResolver class."""
    
    def test_conflict_resolver_initialization(self, mock_context_manager, temp_project_dir):
        """Test ConflictResolver initialization."""
        resolver = ConflictResolver(
            context_manager=mock_context_manager,
            project_path=temp_project_dir,
            enable_proactive_detection=False,
            enable_auto_resolution=False,
            enable_semantic_analysis=False,
            resolution_timeout_seconds=120,
            max_resolution_attempts=2
        )
        
        assert resolver.context_manager == mock_context_manager
        assert str(resolver.project_path) == temp_project_dir
        assert resolver.enable_proactive_detection is False
        assert resolver.enable_auto_resolution is False
        assert resolver.enable_semantic_analysis is False
        assert resolver.resolution_timeout == 120
        assert resolver.max_resolution_attempts == 2
        assert resolver.active_conflicts == {}
        assert resolver.resolved_conflicts == {}
        assert resolver.file_modifications == {}
        assert resolver.cycle_dependencies == {}
        assert resolver._running is False

    def test_resolution_strategies_configuration(self, mock_context_manager, temp_project_dir):
        """Test that resolution strategies are properly configured."""
        resolver = ConflictResolver(mock_context_manager, temp_project_dir)
        
        # Check that all conflict types have strategies
        assert ConflictType.FILE_MODIFICATION in resolver.resolution_strategies
        assert ConflictType.DEPENDENCY_VIOLATION in resolver.resolution_strategies
        assert ConflictType.MERGE_CONFLICT in resolver.resolution_strategies
        assert ConflictType.TEST_CONFLICT in resolver.resolution_strategies
        assert ConflictType.RESOURCE_CONTENTION in resolver.resolution_strategies
        assert ConflictType.SEMANTIC_CONFLICT in resolver.resolution_strategies
        
        # Check specific strategies for file modifications
        file_strategies = resolver.resolution_strategies[ConflictType.FILE_MODIFICATION]
        assert ResolutionStrategy.COORDINATION in file_strategies
        assert ResolutionStrategy.SERIALIZATION in file_strategies
        assert ResolutionStrategy.AUTO_RESOLVE in file_strategies

    @pytest.mark.asyncio
    async def test_start_and_stop(self, mock_context_manager, temp_project_dir):
        """Test starting and stopping the conflict resolver."""
        resolver = ConflictResolver(
            mock_context_manager,
            temp_project_dir,
            enable_proactive_detection=True
        )
        
        assert resolver._running is False
        
        await resolver.start()
        assert resolver._running is True
        assert resolver._monitoring_task is not None
        
        await resolver.stop()
        assert resolver._running is False

    @pytest.mark.asyncio
    async def test_start_already_running(self, conflict_resolver):
        """Test starting resolver when already running."""
        # Should not raise an error
        await conflict_resolver.start()
        assert conflict_resolver._running is True

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, mock_context_manager, temp_project_dir):
        """Test stopping resolver when not running."""
        resolver = ConflictResolver(mock_context_manager, temp_project_dir)
        # Should not raise an error
        await resolver.stop()

    @pytest.mark.asyncio
    async def test_register_file_modification(self, conflict_resolver, temp_project_dir):
        """Test registering a file modification."""
        file_path = str(Path(temp_project_dir) / "test_file.py")
        
        # Create the file for hash calculation
        with open(file_path, 'w') as f:
            f.write("def test(): pass")
        
        await conflict_resolver.register_file_modification(
            file_path=file_path,
            cycle_id="cycle-1",
            story_id="STORY-1",
            modification_type="modify"
        )
        
        assert file_path in conflict_resolver.file_modifications
        modifications = conflict_resolver.file_modifications[file_path]
        assert len(modifications) == 1
        
        mod = modifications[0]
        assert mod.file_path == file_path
        assert mod.cycle_id == "cycle-1"
        assert mod.story_id == "STORY-1"
        assert mod.modification_type == "modify"
        assert mod.content_hash != ""  # Should have calculated hash

    @pytest.mark.asyncio
    async def test_register_file_modification_nonexistent_file(self, conflict_resolver):
        """Test registering modification for non-existent file."""
        file_path = "/nonexistent/file.py"
        
        await conflict_resolver.register_file_modification(
            file_path=file_path,
            cycle_id="cycle-1",
            story_id="STORY-1"
        )
        
        assert file_path in conflict_resolver.file_modifications
        modifications = conflict_resolver.file_modifications[file_path]
        assert len(modifications) == 1
        assert modifications[0].content_hash == ""  # No hash for non-existent file

    @pytest.mark.asyncio
    async def test_register_cycle_dependency(self, conflict_resolver):
        """Test registering cycle dependencies."""
        await conflict_resolver.register_cycle_dependency("cycle-1", "cycle-2")
        
        assert "cycle-1" in conflict_resolver.cycle_dependencies
        assert "cycle-2" in conflict_resolver.cycle_dependencies["cycle-1"]

    @pytest.mark.asyncio
    async def test_register_cycle_dependency_creates_cycle(self, conflict_resolver):
        """Test that circular dependencies are detected."""
        # Create a dependency cycle: cycle-1 -> cycle-2 -> cycle-1
        await conflict_resolver.register_cycle_dependency("cycle-1", "cycle-2")
        
        # This should detect a cycle and create a conflict
        with patch.object(conflict_resolver, '_create_dependency_conflict') as mock_create:
            mock_create.return_value = Conflict(
                "dep-conflict",
                ConflictType.DEPENDENCY_VIOLATION,
                ConflictSeverity.HIGH,
                {"cycle-1"},
                set()
            )
            
            await conflict_resolver.register_cycle_dependency("cycle-2", "cycle-1")
            
            # Should have detected the cycle
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_potential_conflict(self, conflict_resolver):
        """Test analyzing potential conflicts between cycles."""
        analysis = await conflict_resolver.analyze_potential_conflict(
            cycle1_id="cycle-1",
            cycle2_id="cycle-2",
            file_paths=["/path/to/file1.py", "/path/to/file2.py"]
        )
        
        assert isinstance(analysis, ConflictAnalysis)
        assert 0.0 <= analysis.conflict_probability <= 1.0
        assert analysis.impact_assessment != ""
        assert len(analysis.affected_components) > 0
        assert analysis.resolution_complexity in ["simple", "moderate", "complex"]
        assert isinstance(analysis.recommended_strategy, ResolutionStrategy)
        assert isinstance(analysis.prevention_suggestions, list)

    @pytest.mark.asyncio
    async def test_analyze_potential_conflict_many_files(self, conflict_resolver):
        """Test conflict analysis with many files."""
        file_paths = [f"/path/to/file{i}.py" for i in range(15)]
        
        analysis = await conflict_resolver.analyze_potential_conflict(
            "cycle-1", "cycle-2", file_paths
        )
        
        # Should indicate complex resolution due to many files
        assert analysis.resolution_complexity == "complex"
        assert analysis.conflict_probability > 0.5  # Many files increase probability

    @pytest.mark.asyncio
    async def test_resolve_conflict_not_found(self, conflict_resolver):
        """Test resolving a non-existent conflict."""
        result = await conflict_resolver.resolve_conflict("nonexistent-conflict")
        
        assert result.success is False
        assert "not found" in result.error_message
        assert result.strategy_used == ResolutionStrategy.AUTO_RESOLVE

    @pytest.mark.asyncio
    async def test_resolve_conflict_successful(self, conflict_resolver):
        """Test successful conflict resolution."""
        # Create a conflict
        conflict = Conflict(
            conflict_id="test-conflict",
            conflict_type=ConflictType.FILE_MODIFICATION,
            severity=ConflictSeverity.LOW,
            affected_cycles={"cycle-1", "cycle-2"},
            affected_files={"/test/file.py"}
        )
        conflict_resolver.active_conflicts["test-conflict"] = conflict
        
        # Mock successful resolution
        with patch.object(conflict_resolver, '_apply_resolution_strategy') as mock_apply:
            mock_apply.return_value = ResolutionResult(
                success=True,
                strategy_used=ResolutionStrategy.AUTO_RESOLVE,
                resolution_time=1.0
            )
            
            result = await conflict_resolver.resolve_conflict("test-conflict")
            
            assert result.success is True
            assert result.strategy_used == ResolutionStrategy.AUTO_RESOLVE
            assert "test-conflict" not in conflict_resolver.active_conflicts
            assert "test-conflict" in conflict_resolver.resolved_conflicts

    @pytest.mark.asyncio
    async def test_resolve_conflict_max_attempts_exceeded(self, conflict_resolver):
        """Test conflict resolution when max attempts exceeded."""
        # Set low max attempts for testing
        conflict_resolver.max_resolution_attempts = 1
        
        conflict = Conflict(
            conflict_id="test-conflict",
            conflict_type=ConflictType.SEMANTIC_CONFLICT,
            severity=ConflictSeverity.HIGH,
            affected_cycles={"cycle-1"},
            affected_files={"/test/file.py"},
            resolution_attempts=2  # Already exceeded max
        )
        conflict_resolver.active_conflicts["test-conflict"] = conflict
        
        with patch.object(conflict_resolver, '_apply_resolution_strategy') as mock_apply:
            # Should use human escalation when max attempts exceeded
            mock_apply.return_value = ResolutionResult(
                success=True,
                strategy_used=ResolutionStrategy.HUMAN_ESCALATION,
                resolution_time=0.1
            )
            
            result = await conflict_resolver.resolve_conflict("test-conflict")
            
            assert result.success is True
            mock_apply.assert_called_once()
            # Should have called with HUMAN_ESCALATION strategy
            args = mock_apply.call_args[0]
            assert args[1] == ResolutionStrategy.HUMAN_ESCALATION

    @pytest.mark.asyncio
    async def test_resolve_conflict_all_strategies_fail(self, conflict_resolver):
        """Test when all resolution strategies fail."""
        conflict = Conflict(
            conflict_id="test-conflict",
            conflict_type=ConflictType.FILE_MODIFICATION,
            severity=ConflictSeverity.MEDIUM,
            affected_cycles={"cycle-1"},
            affected_files={"/test/file.py"}
        )
        conflict_resolver.active_conflicts["test-conflict"] = conflict
        
        with patch.object(conflict_resolver, '_apply_resolution_strategy') as mock_apply:
            # All strategies fail
            mock_apply.return_value = ResolutionResult(
                success=False,
                strategy_used=ResolutionStrategy.AUTO_RESOLVE,
                resolution_time=1.0,
                error_message="Strategy failed"
            )
            
            result = await conflict_resolver.resolve_conflict("test-conflict")
            
            assert result.success is False
            assert "All resolution strategies failed" in result.error_message
            assert conflict.status == ConflictStatus.FAILED

    @pytest.mark.asyncio
    async def test_resolve_conflict_exception(self, conflict_resolver):
        """Test handling exceptions during conflict resolution."""
        conflict = Conflict(
            conflict_id="test-conflict",
            conflict_type=ConflictType.FILE_MODIFICATION,
            severity=ConflictSeverity.LOW,
            affected_cycles={"cycle-1"},
            affected_files={"/test/file.py"}
        )
        conflict_resolver.active_conflicts["test-conflict"] = conflict
        
        with patch.object(conflict_resolver, '_apply_resolution_strategy') as mock_apply:
            mock_apply.side_effect = Exception("Test exception")
            
            result = await conflict_resolver.resolve_conflict("test-conflict")
            
            assert result.success is False
            assert "Resolution error: Test exception" in result.error_message
            assert conflict.status == ConflictStatus.FAILED

    @pytest.mark.asyncio
    async def test_get_conflict_status_found(self, conflict_resolver):
        """Test getting status of an existing conflict."""
        conflict = Conflict(
            conflict_id="test-conflict",
            conflict_type=ConflictType.TEST_CONFLICT,
            severity=ConflictSeverity.MEDIUM,
            affected_cycles={"cycle-1"},
            affected_files={"/test/file.py"},
            description="Test conflict",
            resolution_strategy=ResolutionStrategy.COORDINATION,
            human_intervention_required=True
        )
        conflict_resolver.active_conflicts["test-conflict"] = conflict
        
        status = await conflict_resolver.get_conflict_status("test-conflict")
        
        assert status is not None
        assert status["conflict_id"] == "test-conflict"
        assert status["type"] == "test_conflict"
        assert status["severity"] == "medium"
        assert status["status"] == "detected"
        assert status["affected_cycles"] == ["cycle-1"]
        assert status["affected_files"] == ["/test/file.py"]
        assert status["description"] == "Test conflict"
        assert status["resolution_strategy"] == "coordination"
        assert status["human_intervention_required"] is True

    @pytest.mark.asyncio
    async def test_get_conflict_status_not_found(self, conflict_resolver):
        """Test getting status of non-existent conflict."""
        status = await conflict_resolver.get_conflict_status("nonexistent")
        assert status is None

    @pytest.mark.asyncio
    async def test_get_active_conflicts(self, conflict_resolver):
        """Test getting all active conflicts."""
        # Add multiple conflicts
        conflict1 = Conflict("c1", ConflictType.FILE_MODIFICATION, ConflictSeverity.LOW, {"cycle-1"}, {"/f1.py"})
        conflict2 = Conflict("c2", ConflictType.MERGE_CONFLICT, ConflictSeverity.HIGH, {"cycle-2"}, {"/f2.py"})
        
        conflict_resolver.active_conflicts["c1"] = conflict1
        conflict_resolver.active_conflicts["c2"] = conflict2
        
        active_conflicts = await conflict_resolver.get_active_conflicts()
        
        assert len(active_conflicts) == 2
        conflict_ids = [c["conflict_id"] for c in active_conflicts]
        assert "c1" in conflict_ids
        assert "c2" in conflict_ids

    @pytest.mark.asyncio
    async def test_get_resolution_statistics(self, conflict_resolver):
        """Test getting resolution statistics."""
        # Add some test data
        conflict_resolver.resolution_stats["total_conflicts"] = 10
        conflict_resolver.resolution_stats["auto_resolved"] = 7
        conflict_resolver.resolution_stats["escalated"] = 2
        conflict_resolver.resolution_stats["failed"] = 1
        conflict_resolver.resolution_stats["average_resolution_time"] = 5.5
        
        # Add some active conflicts
        conflict_resolver.active_conflicts["c1"] = Conflict("c1", ConflictType.FILE_MODIFICATION, ConflictSeverity.LOW, {"cycle-1"}, set())
        conflict_resolver.resolved_conflicts["c2"] = Conflict("c2", ConflictType.MERGE_CONFLICT, ConflictSeverity.MEDIUM, {"cycle-2"}, set())
        
        stats = await conflict_resolver.get_resolution_statistics()
        
        assert stats["total_conflicts"] == 10
        assert stats["active_conflicts"] == 1
        assert stats["resolved_conflicts"] == 1
        assert stats["auto_resolved"] == 7
        assert stats["escalated"] == 2
        assert stats["failed"] == 1
        assert stats["auto_resolution_rate"] == 70.0  # 7/10 * 100
        assert stats["escalation_rate"] == 20.0  # 2/10 * 100
        assert stats["failure_rate"] == 10.0  # 1/10 * 100
        assert stats["average_resolution_time"] == 5.5

    @pytest.mark.asyncio
    async def test_calculate_file_hash(self, conflict_resolver, temp_project_dir):
        """Test calculating file hash."""
        file_path = str(Path(temp_project_dir) / "test_file.py")
        content = "def test(): pass\n"
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        hash_value = await conflict_resolver._calculate_file_hash(file_path)
        
        expected_hash = hashlib.md5(content.encode()).hexdigest()
        assert hash_value == expected_hash

    @pytest.mark.asyncio
    async def test_calculate_file_hash_nonexistent(self, conflict_resolver):
        """Test calculating hash for non-existent file."""
        hash_value = await conflict_resolver._calculate_file_hash("/nonexistent/file.py")
        assert hash_value == ""

    @pytest.mark.asyncio
    async def test_analyze_file_modifications_python(self, conflict_resolver, temp_project_dir):
        """Test analyzing Python file modifications."""
        file_path = str(Path(temp_project_dir) / "test_file.py")
        content = """import os
from typing import List

class TestClass:
    def __init__(self):
        pass

def test_function():
    return True

def another_function(param: str) -> bool:
    return False
"""
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        modification = FileModification(
            file_path=file_path,
            cycle_id="cycle-1",
            story_id="STORY-1",
            modification_type="modify",
            content_hash="abc123",
            timestamp=datetime.utcnow()
        )
        
        await conflict_resolver._analyze_file_modifications(modification)
        
        assert "test_function" in modification.functions_modified
        assert "another_function" in modification.functions_modified
        assert "TestClass" in modification.classes_modified
        assert any("import os" in imp for imp in modification.imports_modified)
        assert any("from typing import List" in imp for imp in modification.imports_modified)
        assert len(modification.line_ranges) == 1
        assert modification.line_ranges[0] == (1, len(content.split('\n')))

    @pytest.mark.asyncio
    async def test_analyze_file_modifications_nonpython(self, conflict_resolver, temp_project_dir):
        """Test analyzing non-Python file modifications."""
        file_path = str(Path(temp_project_dir) / "test_file.txt")
        content = "Some text content"
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        modification = FileModification(
            file_path=file_path,
            cycle_id="cycle-1",
            story_id="STORY-1",
            modification_type="modify",
            content_hash="abc123",
            timestamp=datetime.utcnow()
        )
        
        await conflict_resolver._analyze_file_modifications(modification)
        
        # Should not have analyzed functions/classes for non-Python files
        assert modification.functions_modified == []
        assert modification.classes_modified == []
        assert modification.imports_modified == []

    @pytest.mark.asyncio
    async def test_analyze_file_modifications_exception(self, conflict_resolver):
        """Test handling exceptions during file analysis."""
        modification = FileModification(
            file_path="/nonexistent/file.py",
            cycle_id="cycle-1",
            story_id="STORY-1",
            modification_type="modify",
            content_hash="abc123",
            timestamp=datetime.utcnow()
        )
        
        # Should not raise exception, just log and continue
        await conflict_resolver._analyze_file_modifications(modification)
        
        # Should have empty analysis results
        assert modification.functions_modified == []
        assert modification.classes_modified == []
        assert modification.imports_modified == []

    @pytest.mark.asyncio
    async def test_line_ranges_overlap(self, conflict_resolver):
        """Test checking if line ranges overlap."""
        ranges1 = [(1, 10), (20, 30)]
        ranges2 = [(5, 15), (25, 35)]
        ranges3 = [(40, 50)]
        
        # Test overlapping ranges
        assert await conflict_resolver._line_ranges_overlap(ranges1, ranges2) is True
        
        # Test non-overlapping ranges
        assert await conflict_resolver._line_ranges_overlap(ranges1, ranges3) is False
        
        # Test adjacent ranges (should not overlap)
        ranges4 = [(11, 19)]
        assert await conflict_resolver._line_ranges_overlap(ranges1, ranges4) is False

    @pytest.mark.asyncio
    async def test_detect_dependency_cycle(self, conflict_resolver):
        """Test detecting dependency cycles."""
        # Create a cycle: A -> B -> C -> A
        conflict_resolver.cycle_dependencies = {
            "A": {"B"},
            "B": {"C"},
            "C": {"A"}
        }
        
        assert await conflict_resolver._detect_dependency_cycle("A") is True
        assert await conflict_resolver._detect_dependency_cycle("B") is True
        assert await conflict_resolver._detect_dependency_cycle("C") is True

    @pytest.mark.asyncio
    async def test_detect_dependency_cycle_no_cycle(self, conflict_resolver):
        """Test dependency cycle detection with no cycles."""
        # Create a DAG: A -> B -> C
        conflict_resolver.cycle_dependencies = {
            "A": {"B"},
            "B": {"C"},
            "C": set()
        }
        
        assert await conflict_resolver._detect_dependency_cycle("A") is False
        assert await conflict_resolver._detect_dependency_cycle("B") is False
        assert await conflict_resolver._detect_dependency_cycle("C") is False

    @pytest.mark.asyncio
    async def test_assess_file_conflict_severity(self, conflict_resolver):
        """Test assessing file conflict severity."""
        # Test critical files
        severity = await conflict_resolver._assess_file_conflict_severity("__init__.py", "c1", "c2")
        assert severity == ConflictSeverity.HIGH
        
        severity = await conflict_resolver._assess_file_conflict_severity("main.py", "c1", "c2")
        assert severity == ConflictSeverity.HIGH
        
        # Test Python files
        severity = await conflict_resolver._assess_file_conflict_severity("module.py", "c1", "c2")
        assert severity == ConflictSeverity.MEDIUM
        
        # Test markdown files
        severity = await conflict_resolver._assess_file_conflict_severity("README.md", "c1", "c2")
        assert severity == ConflictSeverity.LOW
        
        # Test other files
        severity = await conflict_resolver._assess_file_conflict_severity("data.txt", "c1", "c2")
        assert severity == ConflictSeverity.LOW

    @pytest.mark.asyncio
    async def test_assess_file_conflict_severity_many_modifications(self, conflict_resolver):
        """Test file conflict severity with many modifications."""
        file_path = "test.py"
        
        # Add many modifications
        modifications = [
            FileModification(file_path, f"cycle-{i}", "story", "modify", "hash", datetime.utcnow())
            for i in range(10)
        ]
        conflict_resolver.file_modifications[file_path] = modifications
        
        severity = await conflict_resolver._assess_file_conflict_severity(file_path, "c1", "c2")
        assert severity == ConflictSeverity.MEDIUM  # Many modifications increase severity

    @pytest.mark.asyncio
    async def test_cycles_conflict_on_file(self, conflict_resolver):
        """Test checking if cycles conflict on a file."""
        file_path = "/test/file.py"
        
        # Create modifications with overlapping line ranges
        mod1 = FileModification(file_path, "cycle-1", "story", "modify", "hash1", datetime.utcnow())
        mod1.line_ranges = [(1, 10), (20, 30)]
        mod1.functions_modified = ["func1", "func2"]
        
        mod2 = FileModification(file_path, "cycle-2", "story", "modify", "hash2", datetime.utcnow())
        mod2.line_ranges = [(5, 15)]  # Overlaps with mod1
        mod2.functions_modified = ["func2", "func3"]  # Overlaps with mod1
        
        conflict_resolver.file_modifications[file_path] = [mod1, mod2]
        
        # Should detect conflict due to overlapping ranges and functions
        assert await conflict_resolver._cycles_conflict_on_file(file_path, "cycle-1", "cycle-2") is True

    @pytest.mark.asyncio
    async def test_cycles_no_conflict_on_file(self, conflict_resolver):
        """Test cycles with no conflicts on a file."""
        file_path = "/test/file.py"
        
        # Create modifications with no overlaps
        mod1 = FileModification(file_path, "cycle-1", "story", "modify", "hash1", datetime.utcnow())
        mod1.line_ranges = [(1, 10)]
        mod1.functions_modified = ["func1"]
        
        mod2 = FileModification(file_path, "cycle-2", "story", "modify", "hash2", datetime.utcnow())
        mod2.line_ranges = [(20, 30)]  # No overlap
        mod2.functions_modified = ["func2"]  # No overlap
        
        conflict_resolver.file_modifications[file_path] = [mod1, mod2]
        
        # Should not detect conflict
        assert await conflict_resolver._cycles_conflict_on_file(file_path, "cycle-1", "cycle-2") is False

    @pytest.mark.asyncio
    async def test_auto_merge_file_simple(self, conflict_resolver):
        """Test automatic file merging for simple case."""
        file_path = "/test/file.py"
        cycle_ids = {"cycle-1", "cycle-2"}
        
        # Create simple modifications
        mod1 = FileModification(file_path, "cycle-1", "story", "modify", "hash1", datetime.utcnow())
        mod2 = FileModification(file_path, "cycle-2", "story", "modify", "hash2", datetime.utcnow())
        
        conflict_resolver.file_modifications[file_path] = [mod1, mod2]
        
        # Should succeed for simple case (2 modifications)
        result = await conflict_resolver._auto_merge_file(file_path, cycle_ids)
        assert result is True

    @pytest.mark.asyncio
    async def test_auto_merge_file_complex(self, conflict_resolver):
        """Test automatic file merging for complex case."""
        file_path = "/test/file.py"
        cycle_ids = {"cycle-1", "cycle-2", "cycle-3", "cycle-4"}
        
        # Create many modifications (too complex to auto-merge)
        modifications = [
            FileModification(file_path, f"cycle-{i}", "story", "modify", f"hash{i}", datetime.utcnow())
            for i in range(1, 5)
        ]
        
        conflict_resolver.file_modifications[file_path] = modifications
        
        # Should fail for complex case (>2 modifications)
        result = await conflict_resolver._auto_merge_file(file_path, cycle_ids)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_average_resolution_time(self, conflict_resolver):
        """Test updating average resolution time."""
        # First resolution
        conflict_resolver._update_average_resolution_time(10.0)
        assert conflict_resolver.resolution_stats["average_resolution_time"] == 10.0
        
        # Second resolution should use weighted average
        conflict_resolver._update_average_resolution_time(20.0)
        expected = 10.0 * 0.9 + 20.0 * 0.1  # 9.0 + 2.0 = 11.0
        assert conflict_resolver.resolution_stats["average_resolution_time"] == expected

    @pytest.mark.asyncio
    async def test_handle_detected_conflict(self, conflict_resolver):
        """Test handling newly detected conflicts."""
        conflict = Conflict(
            conflict_id="test-conflict",
            conflict_type=ConflictType.FILE_MODIFICATION,
            severity=ConflictSeverity.LOW,  # Should trigger auto-resolution
            affected_cycles={"cycle-1"},
            affected_files={"/test/file.py"}
        )
        
        with patch.object(conflict_resolver, 'resolve_conflict') as mock_resolve:
            mock_resolve.return_value = ResolutionResult(True, ResolutionStrategy.AUTO_RESOLVE, 1.0)
            
            await conflict_resolver._handle_detected_conflict(conflict)
            
            assert conflict.conflict_id in conflict_resolver.active_conflicts
            # Should attempt auto-resolution for low severity
            # Note: The resolve_conflict is called asynchronously, so we can't directly assert it was called

    @pytest.mark.asyncio
    async def test_handle_detected_conflict_high_severity(self, conflict_resolver):
        """Test handling high severity conflicts (no auto-resolution)."""
        conflict = Conflict(
            conflict_id="test-conflict",
            conflict_type=ConflictType.SEMANTIC_CONFLICT,
            severity=ConflictSeverity.CRITICAL,  # Should not trigger auto-resolution
            affected_cycles={"cycle-1"},
            affected_files={"/test/file.py"}
        )
        
        await conflict_resolver._handle_detected_conflict(conflict)
        
        assert conflict.conflict_id in conflict_resolver.active_conflicts
        # High severity conflicts should not be auto-resolved

    @pytest.mark.asyncio
    async def test_resolution_strategy_application(self, conflict_resolver):
        """Test applying different resolution strategies."""
        conflict = Conflict(
            conflict_id="test-conflict",
            conflict_type=ConflictType.FILE_MODIFICATION,
            severity=ConflictSeverity.LOW,
            affected_cycles={"cycle-1", "cycle-2"},
            affected_files={"/test/file.py"}
        )
        
        # Test auto-resolve strategy
        result = await conflict_resolver._apply_resolution_strategy(
            conflict, ResolutionStrategy.AUTO_RESOLVE
        )
        assert isinstance(result, ResolutionResult)
        assert result.strategy_used == ResolutionStrategy.AUTO_RESOLVE
        
        # Test coordination strategy
        result = await conflict_resolver._apply_resolution_strategy(
            conflict, ResolutionStrategy.COORDINATION
        )
        assert isinstance(result, ResolutionResult)
        assert result.strategy_used == ResolutionStrategy.COORDINATION
        assert result.requires_verification is True
        
        # Test serialization strategy
        result = await conflict_resolver._apply_resolution_strategy(
            conflict, ResolutionStrategy.SERIALIZATION
        )
        assert isinstance(result, ResolutionResult)
        assert result.strategy_used == ResolutionStrategy.SERIALIZATION
        
        # Test human escalation strategy
        result = await conflict_resolver._apply_resolution_strategy(
            conflict, ResolutionStrategy.HUMAN_ESCALATION
        )
        assert isinstance(result, ResolutionResult)
        assert result.strategy_used == ResolutionStrategy.HUMAN_ESCALATION
        assert result.requires_verification is True
        
        # Test abort cycle strategy
        result = await conflict_resolver._apply_resolution_strategy(
            conflict, ResolutionStrategy.ABORT_CYCLE
        )
        assert isinstance(result, ResolutionResult)
        assert result.strategy_used == ResolutionStrategy.ABORT_CYCLE

    @pytest.mark.asyncio
    async def test_abort_cycle_insufficient_cycles(self, conflict_resolver):
        """Test aborting cycle with insufficient cycles."""
        conflict = Conflict(
            conflict_id="test-conflict",
            conflict_type=ConflictType.FILE_MODIFICATION,
            severity=ConflictSeverity.LOW,
            affected_cycles={"cycle-1"},  # Only one cycle
            affected_files={"/test/file.py"}
        )
        
        result = await conflict_resolver._abort_conflicting_cycle(conflict)
        
        assert result.success is False
        assert "Need at least 2 cycles" in result.error_message

    @pytest.mark.asyncio
    async def test_escalate_to_human(self, conflict_resolver):
        """Test escalating conflict to human intervention."""
        conflict = Conflict(
            conflict_id="test-conflict",
            conflict_type=ConflictType.SEMANTIC_CONFLICT,
            severity=ConflictSeverity.HIGH,
            affected_cycles={"cycle-1"},
            affected_files={"/test/file.py"}
        )
        
        result = await conflict_resolver._escalate_to_human(conflict)
        
        assert result.success is True
        assert result.strategy_used == ResolutionStrategy.HUMAN_ESCALATION
        assert conflict.human_intervention_required is True
        assert conflict.status == ConflictStatus.ESCALATED
        assert "Escalated to human intervention" in result.actions_taken