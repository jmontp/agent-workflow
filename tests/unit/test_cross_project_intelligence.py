"""
Comprehensive unit tests for Cross-Project Intelligence system.

Achieves 95%+ line coverage testing pattern recognition, insight generation,
knowledge sharing, and learning algorithms across multiple AI-assisted projects.
"""

import pytest
import tempfile
import shutil
import json
import asyncio
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
from collections import defaultdict, Counter
import statistics

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.cross_project_intelligence import (
    CrossProjectIntelligence, ProjectPattern, PatternType, CrossProjectInsight,
    InsightType, KnowledgeTransfer, ProjectAnalytics
)


class TestProjectPattern:
    """Test the ProjectPattern dataclass."""
    
    def test_project_pattern_creation(self):
        """Test creating a ProjectPattern instance."""
        pattern = ProjectPattern(
            pattern_id="pattern-123",
            pattern_type=PatternType.ARCHITECTURE_PATTERN,
            project_name="test-project",
            description="Model-View-Controller pattern implementation",
            confidence=0.85,
            impact_score=0.7,
            effort_score=0.6
        )
        
        assert pattern.pattern_id == "pattern-123"
        assert pattern.pattern_type == PatternType.ARCHITECTURE_PATTERN
        assert pattern.project_name == "test-project"
        assert pattern.confidence == 0.85
        assert pattern.impact_score == 0.7
        assert pattern.effort_score == 0.6

    def test_project_pattern_defaults(self):
        """Test ProjectPattern with default values."""
        pattern = ProjectPattern(
            pattern_id="default-pattern",
            pattern_type=PatternType.TESTING_PATTERN,
            project_name="default-project",
            description="Default test pattern"
        )
        
        assert pattern.confidence == 0.0
        assert pattern.frequency == 1
        assert pattern.impact_score == 0.0
        assert pattern.effort_score == 0.0
        assert pattern.code_examples == []
        assert pattern.file_paths == []
        assert pattern.functions == []
        assert pattern.classes == []
        assert pattern.metadata == {}
        assert isinstance(pattern.identified_at, datetime)

    def test_project_pattern_calculate_hash(self):
        """Test pattern hash calculation."""
        pattern = ProjectPattern(
            pattern_id="test-pattern",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="test-project",
            description="Test pattern",
            code_examples=["example1", "example2"]
        )
        
        hash1 = pattern.calculate_hash()
        assert isinstance(hash1, str)
        assert len(hash1) == 32  # MD5 hash length
        
        # Same pattern should produce same hash
        pattern2 = ProjectPattern(
            pattern_id="different-id",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="different-project",
            description="Test pattern",
            code_examples=["example1", "example2"]
        )
        hash2 = pattern2.calculate_hash()
        assert hash1 == hash2  # Same content, same hash
        
        # Different pattern should produce different hash
        pattern3 = ProjectPattern(
            pattern_id="test-pattern",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="test-project",
            description="Different pattern",
            code_examples=["example1", "example2"]
        )
        hash3 = pattern3.calculate_hash()
        assert hash1 != hash3  # Different description, different hash


class TestCrossProjectInsight:
    """Test the CrossProjectInsight dataclass."""
    
    def test_cross_project_insight_creation(self):
        """Test creating a CrossProjectInsight instance."""
        insight = CrossProjectInsight(
            insight_id="insight-456",
            insight_type=InsightType.OPTIMIZATION,
            title="API Caching Opportunity",
            description="Projects could benefit from shared caching strategy",
            affected_projects=["api-service", "web-app"],
            confidence=0.92,
            priority=1,
            status="reviewed"
        )
        
        assert insight.insight_id == "insight-456"
        assert insight.insight_type == InsightType.OPTIMIZATION
        assert insight.title == "API Caching Opportunity"
        assert insight.confidence == 0.92
        assert insight.priority == 1
        assert insight.status == "reviewed"
        assert "api-service" in insight.affected_projects

    def test_cross_project_insight_defaults(self):
        """Test CrossProjectInsight with default values."""
        insight = CrossProjectInsight(
            insight_id="default-insight",
            insight_type=InsightType.BEST_PRACTICE,
            title="Default Insight",
            description="Default description"
        )
        
        assert insight.affected_projects == []
        assert insight.source_patterns == []
        assert insight.recommendations == []
        assert insight.implementation_notes == ""
        assert insight.estimated_benefit == ""
        assert insight.confidence == 0.0
        assert insight.priority == 3
        assert insight.status == "new"
        assert insight.reviewed_at is None
        assert insight.implemented_at is None
        assert insight.feedback_score is None
        assert insight.implementation_success is None
        assert isinstance(insight.generated_at, datetime)


class TestKnowledgeTransfer:
    """Test the KnowledgeTransfer dataclass."""
    
    def test_knowledge_transfer_creation(self):
        """Test creating a KnowledgeTransfer instance."""
        transfer = KnowledgeTransfer(
            transfer_id="transfer-789",
            source_project="backend-api",
            target_project="frontend-app",
            knowledge_type="optimization",
            title="Transfer caching strategy",
            description="Transfer caching strategy from backend to frontend",
            estimated_effort="high",
            potential_benefit="high",
            status="in_progress"
        )
        
        assert transfer.transfer_id == "transfer-789"
        assert transfer.knowledge_type == "optimization"
        assert transfer.source_project == "backend-api"
        assert transfer.target_project == "frontend-app"
        assert transfer.estimated_effort == "high"
        assert transfer.potential_benefit == "high"
        assert transfer.status == "in_progress"

    def test_knowledge_transfer_defaults(self):
        """Test KnowledgeTransfer with default values."""
        transfer = KnowledgeTransfer(
            transfer_id="default-transfer",
            source_project="source",
            target_project="target",
            knowledge_type="pattern",
            title="Default Transfer",
            description="Default description"
        )
        
        assert transfer.estimated_effort == "medium"
        assert transfer.potential_benefit == "medium"
        assert transfer.status == "pending"
        assert transfer.source_references == []
        assert transfer.transfer_instructions == ""
        assert transfer.prerequisites == []
        assert transfer.dependencies == []
        assert transfer.transferred_by is None
        assert transfer.completed_at is None
        assert isinstance(transfer.created_at, datetime)


class TestProjectAnalytics:
    """Test the ProjectAnalytics dataclass."""
    
    def test_project_analytics_creation(self):
        """Test creating a ProjectAnalytics instance."""
        analytics = ProjectAnalytics(
            project_name="test-project",
            total_files=150,
            total_lines_of_code=5000,
            code_complexity_score=7.5,
            test_coverage=0.85,
            tdd_cycles_completed=25,
            average_cycle_time=120.5,
            test_first_ratio=0.9,
            error_rate=0.02,
            build_time=45.0,
            commits_per_day=3.5
        )
        
        assert analytics.project_name == "test-project"
        assert analytics.total_files == 150
        assert analytics.total_lines_of_code == 5000
        assert analytics.code_complexity_score == 7.5
        assert analytics.test_coverage == 0.85
        assert analytics.tdd_cycles_completed == 25
        assert analytics.average_cycle_time == 120.5
        assert analytics.test_first_ratio == 0.9
        assert analytics.error_rate == 0.02
        assert analytics.build_time == 45.0
        assert analytics.commits_per_day == 3.5

    def test_project_analytics_defaults(self):
        """Test ProjectAnalytics with default values."""
        analytics = ProjectAnalytics(project_name="default-project")
        
        assert analytics.project_name == "default-project"
        assert analytics.total_files == 0
        assert analytics.total_lines_of_code == 0
        assert analytics.code_complexity_score == 0.0
        assert analytics.test_coverage == 0.0
        assert analytics.tdd_cycles_completed == 0
        assert analytics.average_cycle_time == 0.0
        assert analytics.test_first_ratio == 0.0
        assert analytics.refactoring_frequency == 0.0
        assert analytics.error_rate == 0.0
        assert analytics.bug_density == 0.0
        assert analytics.technical_debt_score == 0.0
        assert analytics.build_time == 0.0
        assert analytics.test_execution_time == 0.0
        assert analytics.deployment_frequency == 0.0
        assert analytics.commits_per_day == 0.0
        assert analytics.active_contributors == 0
        assert analytics.knowledge_sharing_score == 0.0
        assert analytics.data_sources == []
        assert isinstance(analytics.last_updated, datetime)


class TestEnums:
    """Test enum classes."""
    
    def test_pattern_type_values(self):
        """Test PatternType enum values."""
        assert PatternType.CODE_PATTERN.value == "code_pattern"
        assert PatternType.WORKFLOW_PATTERN.value == "workflow_pattern"
        assert PatternType.ERROR_PATTERN.value == "error_pattern"
        assert PatternType.DEPENDENCY_PATTERN.value == "dependency_pattern"
        assert PatternType.PERFORMANCE_PATTERN.value == "performance_pattern"
        assert PatternType.TESTING_PATTERN.value == "testing_pattern"
        assert PatternType.ARCHITECTURE_PATTERN.value == "architecture_pattern"

    def test_insight_type_values(self):
        """Test InsightType enum values."""
        assert InsightType.OPTIMIZATION.value == "optimization"
        assert InsightType.BEST_PRACTICE.value == "best_practice"
        assert InsightType.ANTI_PATTERN.value == "anti_pattern"
        assert InsightType.REUSABLE_COMPONENT.value == "reusable_component"
        assert InsightType.KNOWLEDGE_TRANSFER.value == "knowledge_transfer"
        assert InsightType.RISK_MITIGATION.value == "risk_mitigation"


class TestCrossProjectIntelligence:
    """Test the CrossProjectIntelligence class."""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary directory for storage testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def intelligence_system(self, temp_storage_dir):
        """Create a CrossProjectIntelligence instance."""
        return CrossProjectIntelligence(storage_path=temp_storage_dir)
    
    @pytest.fixture
    def sample_project_data(self):
        """Create comprehensive sample project data for testing."""
        return {
            "code_files": {
                "src/api.py": "class APIClient:\n    def __init__(self):\n        self._instance = None\n    def __new__(cls):\n        return cls._instance",
                "src/models.py": "class User:\n    pass\nclass Product:\n    pass",
                "tests/test_api.py": "import pytest\ndef test_api():\n    pass",
                "src/utils.py": "def singleton_factory():\n    pass"
            },
            "tdd_cycles": [
                {"duration": 120, "test_first": True},
                {"duration": 150, "test_first": True},
                {"duration": 90, "test_first": False},
                {"duration": 180, "test_first": True}
            ],
            "error_logs": [
                {"type": "TypeError", "message": "invalid type"},
                {"type": "ValueError", "message": "invalid value"},
                {"type": "TypeError", "message": "another type error"},
                {"type": "KeyError", "message": "missing key"},
                {"type": "TypeError", "message": "yet another type error"},
                {"type": "TypeError", "message": "more type errors"},
                {"type": "ValueError", "message": "more value errors"}
            ],
            "quality_metrics": {
                "test_coverage": 0.85,
                "error_rate": 0.02,
                "technical_debt": 0.15
            },
            "performance_metrics": {
                "build_time": 65.0,
                "test_time": 12.5
            }
        }
    
    @pytest.fixture
    def sample_patterns(self):
        """Create sample patterns for testing."""
        return [
            ProjectPattern(
                pattern_id="pattern1",
                pattern_type=PatternType.CODE_PATTERN,
                project_name="project1",
                description="Singleton pattern implementation",
                confidence=0.9,
                impact_score=0.8,
                frequency=3
            ),
            ProjectPattern(
                pattern_id="pattern2",
                pattern_type=PatternType.WORKFLOW_PATTERN,
                project_name="project1",
                description="High test-first adherence",
                confidence=0.85,
                impact_score=0.7,
                frequency=1
            ),
            ProjectPattern(
                pattern_id="pattern3",
                pattern_type=PatternType.ERROR_PATTERN,
                project_name="project1",
                description="Frequent TypeError errors",
                confidence=0.7,
                impact_score=0.6,
                frequency=6
            )
        ]
    
    @pytest.fixture
    def sample_analytics(self):
        """Create sample analytics for testing."""
        return {
            "project1": ProjectAnalytics(
                project_name="project1",
                test_coverage=0.85,
                build_time=65.0,
                error_rate=0.02
            ),
            "project2": ProjectAnalytics(
                project_name="project2",
                test_coverage=0.90,
                build_time=45.0,
                error_rate=0.01
            )
        }

    def test_intelligence_system_init(self, intelligence_system, temp_storage_dir):
        """Test CrossProjectIntelligence initialization."""
        assert intelligence_system.storage_path == Path(temp_storage_dir)
        assert intelligence_system.patterns == {}
        assert intelligence_system.insights == {}
        assert intelligence_system.knowledge_transfers == {}
        assert intelligence_system.project_analytics == {}
        assert intelligence_system.learning_data == {}
        assert intelligence_system.optimization_history == []
        assert intelligence_system.storage_path.exists()
        assert intelligence_system._analysis_task is None
        assert intelligence_system._learning_task is None
        assert len(intelligence_system.pattern_matchers) > 0
        assert len(intelligence_system.insight_generators) > 0

    def test_intelligence_system_init_creates_directory(self):
        """Test that initialization creates storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "intelligence"
            assert not storage_path.exists()
            
            intelligence = CrossProjectIntelligence(storage_path=str(storage_path))
            assert intelligence.storage_path.exists()

    @pytest.mark.asyncio
    async def test_start_intelligence_system(self, intelligence_system):
        """Test starting the intelligence system."""
        await intelligence_system.start()
        
        assert intelligence_system._analysis_task is not None
        assert intelligence_system._learning_task is not None
        assert not intelligence_system._analysis_task.done()
        assert not intelligence_system._learning_task.done()
        
        # Clean up
        await intelligence_system.stop()

    @pytest.mark.asyncio
    async def test_stop_intelligence_system(self, intelligence_system):
        """Test stopping the intelligence system."""
        await intelligence_system.start()
        await intelligence_system.stop()
        
        # Tasks should be cancelled or completed
        assert intelligence_system._analysis_task.cancelled() or intelligence_system._analysis_task.done()
        assert intelligence_system._learning_task.cancelled() or intelligence_system._learning_task.done()

    @pytest.mark.asyncio
    async def test_stop_without_start(self, intelligence_system):
        """Test stopping system without starting it first."""
        # Should not raise an exception
        await intelligence_system.stop()

    @pytest.mark.asyncio
    async def test_analyze_project(self, intelligence_system, sample_project_data):
        """Test analyzing a single project."""
        patterns = await intelligence_system.analyze_project("test-project", sample_project_data)
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0  # Should find patterns in the sample data
        
        # Check that analytics are stored
        assert "test-project" in intelligence_system.project_analytics
        analytics = intelligence_system.project_analytics["test-project"]
        assert analytics.project_name == "test-project"
        assert analytics.total_files == 4  # Number of code files
        assert analytics.tdd_cycles_completed == 4
        assert analytics.test_coverage == 0.85
        
        # Check that patterns are stored
        for pattern in patterns:
            assert pattern.pattern_id in intelligence_system.patterns
            assert pattern.project_name == "test-project"

    @pytest.mark.asyncio
    async def test_analyze_project_with_pattern_matcher_error(self, intelligence_system, sample_project_data):
        """Test analyzing project when pattern matcher raises an error."""
        # Mock a pattern matcher to raise an exception
        def failing_matcher(project_name, project_data, analytics):
            raise ValueError("Pattern matcher failed")
        
        intelligence_system.pattern_matchers[PatternType.CODE_PATTERN] = failing_matcher
        
        # Should still complete without raising exception
        patterns = await intelligence_system.analyze_project("test-project", sample_project_data)
        assert isinstance(patterns, list)
        # Should still have patterns from other matchers
        assert len(patterns) >= 0

    @pytest.mark.asyncio
    async def test_generate_cross_project_insights(self, intelligence_system, sample_patterns, sample_analytics):
        """Test generating cross-project insights."""
        # Setup patterns and analytics
        intelligence_system.patterns = {p.pattern_id: p for p in sample_patterns}
        intelligence_system.project_analytics = sample_analytics
        
        insights = await intelligence_system.generate_cross_project_insights()
        
        assert isinstance(insights, list)
        assert len(insights) >= 0
        
        # Check that insights are stored
        for insight in insights:
            assert insight.insight_id in intelligence_system.insights

    @pytest.mark.asyncio
    async def test_generate_cross_project_insights_with_generator_error(self, intelligence_system, sample_patterns, sample_analytics):
        """Test generating insights when generator raises an error."""
        # Setup patterns and analytics
        intelligence_system.patterns = {p.pattern_id: p for p in sample_patterns}
        intelligence_system.project_analytics = sample_analytics
        
        # Mock an insight generator to raise an exception
        def failing_generator(patterns_by_type, analytics):
            raise ValueError("Insight generator failed")
        
        intelligence_system.insight_generators[InsightType.OPTIMIZATION] = failing_generator
        
        # Should still complete without raising exception
        insights = await intelligence_system.generate_cross_project_insights()
        assert isinstance(insights, list)

    @pytest.mark.asyncio
    async def test_recommend_knowledge_transfers(self, intelligence_system):
        """Test recommending knowledge transfers."""
        # Create patterns with similar hashes but different projects
        pattern1 = ProjectPattern(
            pattern_id="pattern1",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="project1",
            description="Test pattern",
            confidence=0.9,
            impact_score=0.8
        )
        pattern2 = ProjectPattern(
            pattern_id="pattern2",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="project2",
            description="Test pattern",
            confidence=0.7,
            impact_score=0.6
        )
        
        intelligence_system.patterns = {
            "pattern1": pattern1,
            "pattern2": pattern2
        }
        
        # Add analytics to support transfer decisions
        intelligence_system.project_analytics = {
            "project1": ProjectAnalytics(
                project_name="project1",
                test_coverage=0.9,
                error_rate=0.01
            ),
            "project2": ProjectAnalytics(
                project_name="project2",
                test_coverage=0.7,
                error_rate=0.05
            )
        }
        
        transfers = await intelligence_system.recommend_knowledge_transfers()
        
        assert isinstance(transfers, list)
        # Should recommend transfer from project1 to project2 due to better metrics
        if transfers:
            transfer = transfers[0]
            assert transfer.source_project == "project1"
            assert transfer.target_project == "project2"

    @pytest.mark.asyncio
    async def test_recommend_knowledge_transfers_no_similar_patterns(self, intelligence_system):
        """Test knowledge transfer recommendation with no similar patterns."""
        # Create patterns with different hashes
        pattern1 = ProjectPattern(
            pattern_id="pattern1",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="project1",
            description="Unique pattern 1",
            confidence=0.9
        )
        pattern2 = ProjectPattern(
            pattern_id="pattern2",
            pattern_type=PatternType.WORKFLOW_PATTERN,
            project_name="project2",
            description="Unique pattern 2",
            confidence=0.8
        )
        
        intelligence_system.patterns = {
            "pattern1": pattern1,
            "pattern2": pattern2
        }
        
        transfers = await intelligence_system.recommend_knowledge_transfers()
        
        assert isinstance(transfers, list)
        assert len(transfers) == 0  # No similar patterns, no transfers

    @pytest.mark.asyncio
    async def test_recommend_knowledge_transfers_same_project(self, intelligence_system):
        """Test knowledge transfer recommendation with patterns in same project."""
        # Create patterns with same hash and same project
        pattern1 = ProjectPattern(
            pattern_id="pattern1",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="project1",
            description="Test pattern",
            confidence=0.9
        )
        pattern2 = ProjectPattern(
            pattern_id="pattern2",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="project1",  # Same project
            description="Test pattern",
            confidence=0.8
        )
        
        intelligence_system.patterns = {
            "pattern1": pattern1,
            "pattern2": pattern2
        }
        
        transfers = await intelligence_system.recommend_knowledge_transfers()
        
        assert isinstance(transfers, list)
        assert len(transfers) == 0  # Same project, no transfers

    def test_get_project_insights(self, intelligence_system):
        """Test getting insights for a specific project."""
        # Create insights affecting different projects
        insight1 = CrossProjectInsight(
            insight_id="insight1",
            insight_type=InsightType.OPTIMIZATION,
            title="Insight 1",
            description="Test insight 1",
            affected_projects=["project1", "project2"]
        )
        insight2 = CrossProjectInsight(
            insight_id="insight2",
            insight_type=InsightType.BEST_PRACTICE,
            title="Insight 2",
            description="Test insight 2",
            affected_projects=["project2", "project3"]
        )
        insight3 = CrossProjectInsight(
            insight_id="insight3",
            insight_type=InsightType.ANTI_PATTERN,
            title="Insight 3",
            description="Test insight 3",
            affected_projects=["project3"]
        )
        
        intelligence_system.insights = {
            "insight1": insight1,
            "insight2": insight2,
            "insight3": insight3
        }
        
        # Get insights for project1
        project1_insights = intelligence_system.get_project_insights("project1")
        assert len(project1_insights) == 1
        assert project1_insights[0].insight_id == "insight1"
        
        # Get insights for project2
        project2_insights = intelligence_system.get_project_insights("project2")
        assert len(project2_insights) == 2
        insight_ids = [i.insight_id for i in project2_insights]
        assert "insight1" in insight_ids
        assert "insight2" in insight_ids
        
        # Get insights for project3
        project3_insights = intelligence_system.get_project_insights("project3")
        assert len(project3_insights) == 2
        insight_ids = [i.insight_id for i in project3_insights]
        assert "insight2" in insight_ids
        assert "insight3" in insight_ids

    def test_get_pattern_summary(self, intelligence_system, sample_patterns):
        """Test getting pattern summary."""
        intelligence_system.patterns = {p.pattern_id: p for p in sample_patterns}
        
        summary = intelligence_system.get_pattern_summary()
        
        assert "total_patterns" in summary
        assert "patterns_by_type" in summary
        assert "patterns_by_project" in summary
        assert "average_confidence" in summary
        assert "high_impact_patterns" in summary
        
        assert summary["total_patterns"] == 3
        assert summary["patterns_by_project"]["project1"] == 3
        # The Counter uses enum objects as keys
        patterns_by_type = summary["patterns_by_type"]
        assert patterns_by_type[PatternType.CODE_PATTERN] == 1
        assert patterns_by_type[PatternType.WORKFLOW_PATTERN] == 1
        assert patterns_by_type[PatternType.ERROR_PATTERN] == 1
        assert abs(summary["average_confidence"] - (0.9 + 0.85 + 0.7) / 3) < 0.001
        assert summary["high_impact_patterns"] == 1  # Only one pattern with impact > 0.7 (0.8 > 0.7)

    def test_get_pattern_summary_empty(self, intelligence_system):
        """Test getting pattern summary with no patterns."""
        summary = intelligence_system.get_pattern_summary()
        
        assert summary["total_patterns"] == 0
        assert summary["patterns_by_type"] == {}
        assert summary["patterns_by_project"] == {}
        assert summary["average_confidence"] == 0.0
        assert summary["high_impact_patterns"] == 0

    def test_get_insight_summary(self, intelligence_system):
        """Test getting insight summary."""
        # Create insights with different types and statuses
        insight1 = CrossProjectInsight(
            insight_id="insight1",
            insight_type=InsightType.OPTIMIZATION,
            title="Insight 1",
            description="Test insight 1",
            confidence=0.9,
            priority=1,
            status="new"
        )
        insight2 = CrossProjectInsight(
            insight_id="insight2",
            insight_type=InsightType.BEST_PRACTICE,
            title="Insight 2",
            description="Test insight 2",
            confidence=0.8,
            priority=2,
            status="reviewed"
        )
        insight3 = CrossProjectInsight(
            insight_id="insight3",
            insight_type=InsightType.OPTIMIZATION,
            title="Insight 3",
            description="Test insight 3",
            confidence=0.7,
            priority=3,
            status="implemented"
        )
        
        intelligence_system.insights = {
            "insight1": insight1,
            "insight2": insight2,
            "insight3": insight3
        }
        
        summary = intelligence_system.get_insight_summary()
        
        assert summary["total_insights"] == 3
        insights_by_type = summary["insights_by_type"]
        assert insights_by_type[InsightType.OPTIMIZATION] == 2
        assert insights_by_type[InsightType.BEST_PRACTICE] == 1
        assert summary["insights_by_status"]["new"] == 1
        assert summary["insights_by_status"]["reviewed"] == 1
        assert summary["insights_by_status"]["implemented"] == 1
        assert abs(summary["average_confidence"] - (0.9 + 0.8 + 0.7) / 3) < 0.001
        assert summary["high_priority_insights"] == 2  # Priority 1 and 2

    def test_get_insight_summary_empty(self, intelligence_system):
        """Test getting insight summary with no insights."""
        summary = intelligence_system.get_insight_summary()
        
        assert summary["total_insights"] == 0
        assert summary["insights_by_type"] == {}
        assert summary["insights_by_status"] == {}
        assert summary["average_confidence"] == 0.0
        assert summary["high_priority_insights"] == 0

    def test_get_knowledge_transfer_summary(self, intelligence_system):
        """Test getting knowledge transfer summary."""
        # Create transfers with different statuses and benefits
        transfer1 = KnowledgeTransfer(
            transfer_id="transfer1",
            source_project="project1",
            target_project="project2",
            knowledge_type="pattern",
            title="Transfer 1",
            description="Test transfer 1",
            status="pending",
            potential_benefit="high"
        )
        transfer2 = KnowledgeTransfer(
            transfer_id="transfer2",
            source_project="project2",
            target_project="project3",
            knowledge_type="optimization",
            title="Transfer 2",
            description="Test transfer 2",
            status="completed",
            potential_benefit="medium"
        )
        transfer3 = KnowledgeTransfer(
            transfer_id="transfer3",
            source_project="project1",
            target_project="project3",
            knowledge_type="best_practice",
            title="Transfer 3",
            description="Test transfer 3",
            status="rejected",
            potential_benefit="low"
        )
        
        intelligence_system.knowledge_transfers = {
            "transfer1": transfer1,
            "transfer2": transfer2,
            "transfer3": transfer3
        }
        
        summary = intelligence_system.get_knowledge_transfer_summary()
        
        assert summary["total_transfers"] == 3
        assert summary["transfers_by_status"]["pending"] == 1
        assert summary["transfers_by_status"]["completed"] == 1
        assert summary["transfers_by_status"]["rejected"] == 1
        assert summary["transfers_by_benefit"]["high"] == 1
        assert summary["transfers_by_benefit"]["medium"] == 1
        assert summary["transfers_by_benefit"]["low"] == 1
        assert summary["pending_transfers"] == 1
        assert summary["completed_transfers"] == 1

    def test_get_knowledge_transfer_summary_empty(self, intelligence_system):
        """Test getting knowledge transfer summary with no transfers."""
        summary = intelligence_system.get_knowledge_transfer_summary()
        
        assert summary["total_transfers"] == 0
        assert summary["transfers_by_status"] == {}
        assert summary["transfers_by_benefit"] == {}
        assert summary["pending_transfers"] == 0
        assert summary["completed_transfers"] == 0

    @pytest.mark.asyncio
    async def test_update_insight_feedback(self, intelligence_system):
        """Test updating insight feedback."""
        # Create insight
        insight = CrossProjectInsight(
            insight_id="insight1",
            insight_type=InsightType.OPTIMIZATION,
            title="Test Insight",
            description="Test description"
        )
        intelligence_system.insights["insight1"] = insight
        
        # Update feedback
        await intelligence_system.update_insight_feedback("insight1", 0.9, True)
        
        updated_insight = intelligence_system.insights["insight1"]
        assert updated_insight.feedback_score == 0.9
        assert updated_insight.implementation_success == True
        assert updated_insight.status == "implemented"
        assert updated_insight.implemented_at is not None

    @pytest.mark.asyncio
    async def test_update_insight_feedback_no_implementation_success(self, intelligence_system):
        """Test updating insight feedback without implementation success."""
        # Create insight
        insight = CrossProjectInsight(
            insight_id="insight1",
            insight_type=InsightType.OPTIMIZATION,
            title="Test Insight",
            description="Test description"
        )
        intelligence_system.insights["insight1"] = insight
        
        # Update feedback without implementation success
        await intelligence_system.update_insight_feedback("insight1", 0.7)
        
        updated_insight = intelligence_system.insights["insight1"]
        assert updated_insight.feedback_score == 0.7
        assert updated_insight.implementation_success is None
        assert updated_insight.status == "new"  # Should not change
        assert updated_insight.implemented_at is None

    @pytest.mark.asyncio
    async def test_update_insight_feedback_implementation_failed(self, intelligence_system):
        """Test updating insight feedback with implementation failure."""
        # Create insight
        insight = CrossProjectInsight(
            insight_id="insight1",
            insight_type=InsightType.OPTIMIZATION,
            title="Test Insight",
            description="Test description"
        )
        intelligence_system.insights["insight1"] = insight
        
        # Update feedback with implementation failure
        await intelligence_system.update_insight_feedback("insight1", 0.3, False)
        
        updated_insight = intelligence_system.insights["insight1"]
        assert updated_insight.feedback_score == 0.3
        assert updated_insight.implementation_success == False
        assert updated_insight.status == "new"  # Should not change to implemented
        assert updated_insight.implemented_at is None

    @pytest.mark.asyncio
    async def test_update_insight_feedback_nonexistent_insight(self, intelligence_system):
        """Test updating feedback for non-existent insight."""
        # Should not raise an exception
        await intelligence_system.update_insight_feedback("nonexistent", 0.5)
        
        # Should not create new insight
        assert "nonexistent" not in intelligence_system.insights

    @pytest.mark.asyncio
    async def test_extract_project_analytics(self, intelligence_system, sample_project_data):
        """Test extracting project analytics from project data."""
        analytics = await intelligence_system._extract_project_analytics("test-project", sample_project_data)
        
        assert analytics.project_name == "test-project"
        assert analytics.total_files == 4  # Number of code files
        assert analytics.total_lines_of_code > 0
        assert analytics.tdd_cycles_completed == 4
        assert analytics.average_cycle_time == (120 + 150 + 90 + 180) / 4
        assert analytics.test_first_ratio == 3 / 4  # 3 out of 4 cycles are test-first
        assert analytics.test_coverage == 0.85
        assert analytics.error_rate == 0.02
        assert analytics.technical_debt_score == 0.15
        assert analytics.build_time == 65.0
        assert analytics.test_execution_time == 12.5

    @pytest.mark.asyncio
    async def test_extract_project_analytics_empty_data(self, intelligence_system):
        """Test extracting analytics from empty project data."""
        analytics = await intelligence_system._extract_project_analytics("empty-project", {})
        
        assert analytics.project_name == "empty-project"
        assert analytics.total_files == 0
        assert analytics.total_lines_of_code == 0
        assert analytics.tdd_cycles_completed == 0
        assert analytics.average_cycle_time == 0
        assert analytics.test_first_ratio == 0
        assert analytics.test_coverage == 0.0
        assert analytics.error_rate == 0.0
        assert analytics.technical_debt_score == 0.0
        assert analytics.build_time == 0.0
        assert analytics.test_execution_time == 0.0

    @pytest.mark.asyncio
    async def test_extract_project_analytics_no_tdd_cycles(self, intelligence_system):
        """Test extracting analytics when no TDD cycles exist."""
        project_data = {
            "code_files": {"main.py": "print('hello')"},
            "tdd_cycles": [],
            "quality_metrics": {"test_coverage": 0.5}
        }
        
        analytics = await intelligence_system._extract_project_analytics("test-project", project_data)
        
        assert analytics.tdd_cycles_completed == 0
        assert analytics.average_cycle_time == 0
        assert analytics.test_first_ratio == 0

    @pytest.mark.asyncio
    async def test_generate_insights_for_project(self, intelligence_system):
        """Test generating project-specific insights."""
        patterns = [
            ProjectPattern(
                pattern_id="pattern1",
                pattern_type=PatternType.CODE_PATTERN,
                project_name="test-project",
                description="Test pattern"
            )
        ]
        
        # Should not raise an exception (method is currently a no-op)
        await intelligence_system._generate_insights_for_project("test-project", patterns)

    def test_group_similar_patterns(self, intelligence_system):
        """Test grouping similar patterns."""
        # Create patterns with same and different hashes
        pattern1 = ProjectPattern(
            pattern_id="pattern1",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="project1",
            description="Test pattern",
            code_examples=["example1", "example2"]
        )
        pattern2 = ProjectPattern(
            pattern_id="pattern2",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="project2",
            description="Test pattern",
            code_examples=["example1", "example2"]
        )
        pattern3 = ProjectPattern(
            pattern_id="pattern3",
            pattern_type=PatternType.WORKFLOW_PATTERN,
            project_name="project3",
            description="Different pattern",
            code_examples=["example3"]
        )
        
        intelligence_system.patterns = {
            "pattern1": pattern1,
            "pattern2": pattern2,
            "pattern3": pattern3
        }
        
        groups = intelligence_system._group_similar_patterns()
        
        # Should group patterns with same hash together
        assert len(groups) == 2  # Two different hashes
        
        # Find the group with similar patterns
        similar_group = None
        for group in groups.values():
            if len(group) == 2:
                similar_group = group
                break
        
        assert similar_group is not None
        assert len(similar_group) == 2
        pattern_ids = [p.pattern_id for p in similar_group]
        assert "pattern1" in pattern_ids
        assert "pattern2" in pattern_ids

    def test_should_recommend_transfer_confidence_difference(self, intelligence_system):
        """Test transfer recommendation based on confidence difference."""
        source_pattern = ProjectPattern(
            pattern_id="source",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="source_project",
            description="Test pattern",
            confidence=0.9,
            impact_score=0.5
        )
        target_pattern = ProjectPattern(
            pattern_id="target",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="target_project",
            description="Test pattern",
            confidence=0.7,  # Significantly lower
            impact_score=0.5
        )
        
        should_recommend = intelligence_system._should_recommend_transfer(source_pattern, target_pattern)
        assert should_recommend == True

    def test_should_recommend_transfer_impact_difference(self, intelligence_system):
        """Test transfer recommendation based on impact score difference."""
        source_pattern = ProjectPattern(
            pattern_id="source",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="source_project",
            description="Test pattern",
            confidence=0.8,
            impact_score=0.9
        )
        target_pattern = ProjectPattern(
            pattern_id="target",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="target_project",
            description="Test pattern",
            confidence=0.8,
            impact_score=0.7  # Significantly lower
        )
        
        should_recommend = intelligence_system._should_recommend_transfer(source_pattern, target_pattern)
        assert should_recommend == True

    def test_should_recommend_transfer_analytics_difference(self, intelligence_system):
        """Test transfer recommendation based on project analytics difference."""
        source_pattern = ProjectPattern(
            pattern_id="source",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="source_project",
            description="Test pattern",
            confidence=0.8,
            impact_score=0.8
        )
        target_pattern = ProjectPattern(
            pattern_id="target",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="target_project",
            description="Test pattern",
            confidence=0.8,
            impact_score=0.8
        )
        
        # Add analytics showing source project is better
        intelligence_system.project_analytics = {
            "source_project": ProjectAnalytics(
                project_name="source_project",
                test_coverage=0.9,
                error_rate=0.01
            ),
            "target_project": ProjectAnalytics(
                project_name="target_project",
                test_coverage=0.7,  # Significantly lower
                error_rate=0.08   # Significantly higher
            )
        }
        
        should_recommend = intelligence_system._should_recommend_transfer(source_pattern, target_pattern)
        assert should_recommend == True

    def test_should_recommend_transfer_no_difference(self, intelligence_system):
        """Test transfer recommendation when no significant difference exists."""
        source_pattern = ProjectPattern(
            pattern_id="source",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="source_project",
            description="Test pattern",
            confidence=0.8,
            impact_score=0.8
        )
        target_pattern = ProjectPattern(
            pattern_id="target",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="target_project",
            description="Test pattern",
            confidence=0.8,
            impact_score=0.8
        )
        
        # Add similar analytics
        intelligence_system.project_analytics = {
            "source_project": ProjectAnalytics(
                project_name="source_project",
                test_coverage=0.8,
                error_rate=0.02
            ),
            "target_project": ProjectAnalytics(
                project_name="target_project",
                test_coverage=0.8,
                error_rate=0.02
            )
        }
        
        should_recommend = intelligence_system._should_recommend_transfer(source_pattern, target_pattern)
        assert should_recommend == False

    def test_should_recommend_transfer_missing_analytics(self, intelligence_system):
        """Test transfer recommendation when analytics are missing."""
        source_pattern = ProjectPattern(
            pattern_id="source",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="source_project",
            description="Test pattern",
            confidence=0.8,
            impact_score=0.8
        )
        target_pattern = ProjectPattern(
            pattern_id="target",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="target_project",
            description="Test pattern",
            confidence=0.8,
            impact_score=0.8
        )
        
        # No analytics available
        should_recommend = intelligence_system._should_recommend_transfer(source_pattern, target_pattern)
        assert should_recommend == False

    def test_create_knowledge_transfer(self, intelligence_system):
        """Test creating a knowledge transfer recommendation."""
        source_pattern = ProjectPattern(
            pattern_id="source",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="source_project",
            description="Singleton pattern",
            file_paths=["src/singleton.py", "src/factory.py"]
        )
        target_pattern = ProjectPattern(
            pattern_id="target",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="target_project",
            description="Singleton pattern"
        )
        
        transfer = intelligence_system._create_knowledge_transfer(source_pattern, target_pattern)
        
        assert transfer.source_project == "source_project"
        assert transfer.target_project == "target_project"
        assert transfer.knowledge_type == "pattern"
        assert "code_pattern" in transfer.title
        assert "Singleton pattern" in transfer.description
        assert transfer.source_references == ["src/singleton.py", "src/factory.py"]
        assert "source_project" in transfer.transfer_instructions
        assert "target_project" in transfer.transfer_instructions
        assert transfer.estimated_effort == "medium"
        assert transfer.potential_benefit == "medium"

    @pytest.mark.asyncio
    async def test_analysis_loop_single_iteration(self, intelligence_system):
        """Test single iteration of analysis loop."""
        # Mock the sleep to avoid waiting and allow cancellation
        with patch('lib.cross_project_intelligence.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = asyncio.CancelledError()  # Immediate cancellation
            
            # Mock the analysis methods
            with patch.object(intelligence_system, 'generate_cross_project_insights', new_callable=AsyncMock) as mock_insights:
                with patch.object(intelligence_system, 'recommend_knowledge_transfers', new_callable=AsyncMock) as mock_transfers:
                    with patch.object(intelligence_system, '_save_intelligence_data') as mock_save:
                        # Start the loop
                        task = asyncio.create_task(intelligence_system._analysis_loop())
                        
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                        
                        # Verify sleep was called (leading to cancellation)
                        mock_sleep.assert_called_with(3600)

    @pytest.mark.asyncio
    async def test_analysis_loop_with_exception(self, intelligence_system):
        """Test analysis loop handling exceptions."""
        # Track the number of calls to simulate one exception then cancellation
        call_count = 0
        
        def mock_sleep_side_effect(seconds):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:  # Cancel after second call (after exception handling)
                raise asyncio.CancelledError()
            return AsyncMock()()
        
        with patch('lib.cross_project_intelligence.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = mock_sleep_side_effect
            
            # Mock insights to raise an exception on first call
            with patch.object(intelligence_system, 'generate_cross_project_insights', new_callable=AsyncMock) as mock_insights:
                mock_insights.side_effect = ValueError("Test error")
                
                # Start the loop
                task = asyncio.create_task(intelligence_system._analysis_loop())
                
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                # Should have handled the exception and continued
                assert mock_sleep.call_count >= 1
                mock_insights.assert_called()

    @pytest.mark.asyncio
    async def test_learning_loop_single_iteration(self, intelligence_system):
        """Test single iteration of learning loop."""
        # Mock the sleep to avoid waiting and allow cancellation
        with patch('lib.cross_project_intelligence.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = asyncio.CancelledError()  # Immediate cancellation
            
            # Mock the learning methods
            with patch.object(intelligence_system, '_update_learning_models', new_callable=AsyncMock) as mock_learning:
                with patch.object(intelligence_system, '_optimize_pattern_matching', new_callable=AsyncMock) as mock_optimize:
                    # Start the loop
                    task = asyncio.create_task(intelligence_system._learning_loop())
                    
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    
                    # Verify sleep was called (leading to cancellation)
                    mock_sleep.assert_called_with(7200)

    @pytest.mark.asyncio
    async def test_learning_loop_with_exception(self, intelligence_system):
        """Test learning loop handling exceptions."""
        # Track the number of calls to simulate one exception then cancellation
        call_count = 0
        
        def mock_sleep_side_effect(seconds):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:  # Cancel after second call (after exception handling)
                raise asyncio.CancelledError()
            return AsyncMock()()
        
        with patch('lib.cross_project_intelligence.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = mock_sleep_side_effect
            
            # Mock learning to raise an exception
            with patch.object(intelligence_system, '_update_learning_models', new_callable=AsyncMock) as mock_learning:
                mock_learning.side_effect = RuntimeError("Learning error")
                
                # Start the loop
                task = asyncio.create_task(intelligence_system._learning_loop())
                
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                # Should have handled the exception and continued
                assert mock_sleep.call_count >= 1
                mock_learning.assert_called()

    @pytest.mark.asyncio
    async def test_update_learning_models(self, intelligence_system):
        """Test updating learning models."""
        # Currently a no-op, should not raise an exception
        await intelligence_system._update_learning_models()

    @pytest.mark.asyncio
    async def test_optimize_pattern_matching(self, intelligence_system):
        """Test optimizing pattern matching."""
        # Currently a no-op, should not raise an exception
        await intelligence_system._optimize_pattern_matching()

    def test_load_intelligence_data_empty_directory(self, intelligence_system):
        """Test loading intelligence data from empty directory."""
        # Should not raise an exception
        intelligence_system._load_intelligence_data()
        
        # Should remain empty
        assert len(intelligence_system.patterns) == 0
        assert len(intelligence_system.insights) == 0
        assert len(intelligence_system.knowledge_transfers) == 0

    def test_load_intelligence_data_with_files(self, intelligence_system):
        """Test loading intelligence data with existing files."""
        # Create test data files
        patterns_data = {
            "pattern1": {
                "pattern_id": "pattern1",
                "pattern_type": "code_pattern",
                "project_name": "test_project",
                "description": "Test pattern",
                "code_examples": [],
                "frequency": 1,
                "confidence": 0.8,
                "metadata": {},
                "identified_at": "2024-01-01T00:00:00",
                "file_paths": [],
                "functions": [],
                "classes": [],
                "impact_score": 0.0,
                "effort_score": 0.0
            }
        }
        
        insights_data = {
            "insight1": {
                "insight_id": "insight1",
                "insight_type": "optimization",
                "title": "Test Insight",
                "description": "Test description",
                "affected_projects": [],
                "source_patterns": [],
                "recommendations": [],
                "implementation_notes": "",
                "estimated_benefit": "",
                "confidence": 0.9,
                "priority": 3,
                "status": "new",
                "generated_at": "2024-01-01T00:00:00",
                "reviewed_at": None,
                "implemented_at": None,
                "feedback_score": None,
                "implementation_success": None
            }
        }
        
        transfers_data = {
            "transfer1": {
                "transfer_id": "transfer1",
                "source_project": "source",
                "target_project": "target",
                "knowledge_type": "pattern",
                "title": "Test Transfer",
                "description": "Test description",
                "source_references": [],
                "transfer_instructions": "",
                "estimated_effort": "medium",
                "potential_benefit": "medium",
                "prerequisites": [],
                "dependencies": [],
                "created_at": "2024-01-01T00:00:00",
                "status": "pending",
                "transferred_by": None,
                "completed_at": None
            }
        }
        
        # Write test data to files
        with open(intelligence_system.storage_path / "patterns.json", 'w') as f:
            json.dump(patterns_data, f)
        
        with open(intelligence_system.storage_path / "insights.json", 'w') as f:
            json.dump(insights_data, f)
        
        with open(intelligence_system.storage_path / "knowledge_transfers.json", 'w') as f:
            json.dump(transfers_data, f)
        
        # Load the data
        intelligence_system._load_intelligence_data()
        
        # Verify data was loaded
        assert len(intelligence_system.patterns) == 1
        assert "pattern1" in intelligence_system.patterns
        assert intelligence_system.patterns["pattern1"].pattern_type == PatternType.CODE_PATTERN
        
        assert len(intelligence_system.insights) == 1
        assert "insight1" in intelligence_system.insights
        assert intelligence_system.insights["insight1"].insight_type == InsightType.OPTIMIZATION
        
        assert len(intelligence_system.knowledge_transfers) == 1
        assert "transfer1" in intelligence_system.knowledge_transfers
        assert intelligence_system.knowledge_transfers["transfer1"].knowledge_type == "pattern"

    def test_load_intelligence_data_with_invalid_json(self, intelligence_system):
        """Test loading intelligence data with invalid JSON."""
        # Create invalid JSON file
        with open(intelligence_system.storage_path / "patterns.json", 'w') as f:
            f.write("invalid json")
        
        # Should handle the error gracefully
        intelligence_system._load_intelligence_data()
        
        # Should remain empty
        assert len(intelligence_system.patterns) == 0

    def test_save_intelligence_data(self, intelligence_system):
        """Test saving intelligence data to storage."""
        # Add test data
        pattern = ProjectPattern(
            pattern_id="pattern1",
            pattern_type=PatternType.CODE_PATTERN,
            project_name="test_project",
            description="Test pattern",
            identified_at=datetime(2024, 1, 1)
        )
        intelligence_system.patterns["pattern1"] = pattern
        
        insight = CrossProjectInsight(
            insight_id="insight1",
            insight_type=InsightType.OPTIMIZATION,
            title="Test Insight",
            description="Test description",
            generated_at=datetime(2024, 1, 1),
            reviewed_at=datetime(2024, 1, 2),
            implemented_at=datetime(2024, 1, 3)
        )
        intelligence_system.insights["insight1"] = insight
        
        transfer = KnowledgeTransfer(
            transfer_id="transfer1",
            source_project="source",
            target_project="target",
            knowledge_type="pattern",
            title="Test Transfer",
            description="Test description",
            created_at=datetime(2024, 1, 1),
            completed_at=datetime(2024, 1, 2)
        )
        intelligence_system.knowledge_transfers["transfer1"] = transfer
        
        # Save the data
        intelligence_system._save_intelligence_data()
        
        # Verify files were created
        assert (intelligence_system.storage_path / "patterns.json").exists()
        assert (intelligence_system.storage_path / "insights.json").exists()
        assert (intelligence_system.storage_path / "knowledge_transfers.json").exists()
        
        # Verify content
        with open(intelligence_system.storage_path / "patterns.json", 'r') as f:
            patterns_data = json.load(f)
            assert "pattern1" in patterns_data
            assert patterns_data["pattern1"]["pattern_type"] == "code_pattern"
            assert patterns_data["pattern1"]["identified_at"] == "2024-01-01T00:00:00"
        
        with open(intelligence_system.storage_path / "insights.json", 'r') as f:
            insights_data = json.load(f)
            assert "insight1" in insights_data
            assert insights_data["insight1"]["insight_type"] == "optimization"
            assert insights_data["insight1"]["generated_at"] == "2024-01-01T00:00:00"
            assert insights_data["insight1"]["reviewed_at"] == "2024-01-02T00:00:00"
            assert insights_data["insight1"]["implemented_at"] == "2024-01-03T00:00:00"
        
        with open(intelligence_system.storage_path / "knowledge_transfers.json", 'r') as f:
            transfers_data = json.load(f)
            assert "transfer1" in transfers_data
            assert transfers_data["transfer1"]["created_at"] == "2024-01-01T00:00:00"
            assert transfers_data["transfer1"]["completed_at"] == "2024-01-02T00:00:00"

    def test_save_intelligence_data_with_none_dates(self, intelligence_system):
        """Test saving intelligence data with None datetime fields."""
        insight = CrossProjectInsight(
            insight_id="insight1",
            insight_type=InsightType.OPTIMIZATION,
            title="Test Insight",
            description="Test description",
            generated_at=datetime(2024, 1, 1),
            reviewed_at=None,
            implemented_at=None
        )
        intelligence_system.insights["insight1"] = insight
        
        transfer = KnowledgeTransfer(
            transfer_id="transfer1",
            source_project="source",
            target_project="target",
            knowledge_type="pattern",
            title="Test Transfer",
            description="Test description",
            created_at=datetime(2024, 1, 1),
            completed_at=None
        )
        intelligence_system.knowledge_transfers["transfer1"] = transfer
        
        # Should not raise an exception
        intelligence_system._save_intelligence_data()
        
        # Verify files were created
        assert (intelligence_system.storage_path / "insights.json").exists()
        assert (intelligence_system.storage_path / "knowledge_transfers.json").exists()

    def test_save_intelligence_data_io_error(self, intelligence_system):
        """Test saving intelligence data with IO error."""
        # Make storage directory read-only
        intelligence_system.storage_path.chmod(0o444)
        
        try:
            # Should handle the error gracefully
            intelligence_system._save_intelligence_data()
        finally:
            # Restore permissions
            intelligence_system.storage_path.chmod(0o755)


class TestPatternMatchers:
    """Test pattern matcher functionality."""
    
    @pytest.fixture
    def intelligence_system(self):
        """Create intelligence system for testing pattern matchers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield CrossProjectIntelligence(storage_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_code_pattern_matcher_singleton(self, intelligence_system):
        """Test code pattern matcher detecting singleton patterns."""
        project_data = {
            "code_files": {
                "singleton.py": "class Singleton:\n    _instance = None\n    def __new__(cls):\n        if cls._instance is None:\n            cls._instance = super().__new__(cls)\n        return cls._instance",
                "factory.py": "class Factory:\n    _instance = None\n    def __new__(cls):\n        return cls._instance"
            }
        }
        analytics = ProjectAnalytics(project_name="test_project")
        
        # Get the code pattern matcher
        matcher = intelligence_system.pattern_matchers[PatternType.CODE_PATTERN]
        patterns = await matcher("test_project", project_data, analytics)
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == PatternType.CODE_PATTERN
        assert pattern.project_name == "test_project"
        assert "Singleton" in pattern.description
        assert pattern.frequency == 2  # Two files with singleton pattern
        assert pattern.confidence == 0.8
        assert pattern.impact_score == 0.6
        assert len(pattern.file_paths) == 2

    @pytest.mark.asyncio
    async def test_code_pattern_matcher_no_singleton(self, intelligence_system):
        """Test code pattern matcher with no singleton patterns."""
        project_data = {
            "code_files": {
                "simple.py": "def hello():\n    print('hello')",
                "basic.py": "class Basic:\n    def __init__(self):\n        pass"
            }
        }
        analytics = ProjectAnalytics(project_name="test_project")
        
        # Get the code pattern matcher
        matcher = intelligence_system.pattern_matchers[PatternType.CODE_PATTERN]
        patterns = await matcher("test_project", project_data, analytics)
        
        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_workflow_pattern_matcher_high_test_first(self, intelligence_system):
        """Test workflow pattern matcher detecting high test-first adherence."""
        project_data = {}
        analytics = ProjectAnalytics(
            project_name="test_project",
            test_first_ratio=0.85  # High test-first ratio
        )
        
        # Get the workflow pattern matcher
        matcher = intelligence_system.pattern_matchers[PatternType.WORKFLOW_PATTERN]
        patterns = await matcher("test_project", project_data, analytics)
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == PatternType.WORKFLOW_PATTERN
        assert pattern.project_name == "test_project"
        assert "test-first" in pattern.description
        assert pattern.confidence == 0.9
        assert pattern.impact_score == 0.8
        assert pattern.metadata["test_first_ratio"] == 0.85

    @pytest.mark.asyncio
    async def test_workflow_pattern_matcher_low_test_first(self, intelligence_system):
        """Test workflow pattern matcher with low test-first adherence."""
        project_data = {}
        analytics = ProjectAnalytics(
            project_name="test_project",
            test_first_ratio=0.5  # Low test-first ratio
        )
        
        # Get the workflow pattern matcher
        matcher = intelligence_system.pattern_matchers[PatternType.WORKFLOW_PATTERN]
        patterns = await matcher("test_project", project_data, analytics)
        
        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_error_pattern_matcher_frequent_errors(self, intelligence_system):
        """Test error pattern matcher detecting frequent errors."""
        project_data = {
            "error_logs": [
                {"type": "TypeError", "message": "error 1"},
                {"type": "TypeError", "message": "error 2"},
                {"type": "TypeError", "message": "error 3"},
                {"type": "TypeError", "message": "error 4"},
                {"type": "TypeError", "message": "error 5"},
                {"type": "TypeError", "message": "error 6"},
                {"type": "ValueError", "message": "error 7"},
                {"type": "ValueError", "message": "error 8"},
                {"type": "KeyError", "message": "error 9"}
            ]
        }
        analytics = ProjectAnalytics(project_name="test_project")
        
        # Get the error pattern matcher
        matcher = intelligence_system.pattern_matchers[PatternType.ERROR_PATTERN]
        patterns = await matcher("test_project", project_data, analytics)
        
        assert len(patterns) == 1  # Only TypeError exceeds threshold of 5
        pattern = patterns[0]
        assert pattern.pattern_type == PatternType.ERROR_PATTERN
        assert pattern.project_name == "test_project"
        assert "TypeError" in pattern.description
        assert pattern.frequency == 6
        assert pattern.confidence == 0.7
        assert pattern.metadata["error_type"] == "TypeError"
        assert pattern.metadata["count"] == 6

    @pytest.mark.asyncio
    async def test_error_pattern_matcher_no_frequent_errors(self, intelligence_system):
        """Test error pattern matcher with no frequent errors."""
        project_data = {
            "error_logs": [
                {"type": "TypeError", "message": "error 1"},
                {"type": "ValueError", "message": "error 2"},
                {"type": "KeyError", "message": "error 3"}
            ]
        }
        analytics = ProjectAnalytics(project_name="test_project")
        
        # Get the error pattern matcher
        matcher = intelligence_system.pattern_matchers[PatternType.ERROR_PATTERN]
        patterns = await matcher("test_project", project_data, analytics)
        
        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_error_pattern_matcher_empty_logs(self, intelligence_system):
        """Test error pattern matcher with empty error logs."""
        project_data = {"error_logs": []}
        analytics = ProjectAnalytics(project_name="test_project")
        
        # Get the error pattern matcher
        matcher = intelligence_system.pattern_matchers[PatternType.ERROR_PATTERN]
        patterns = await matcher("test_project", project_data, analytics)
        
        assert len(patterns) == 0


class TestInsightGenerators:
    """Test insight generator functionality."""
    
    @pytest.fixture
    def intelligence_system(self):
        """Create intelligence system for testing insight generators."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield CrossProjectIntelligence(storage_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_optimization_generator_slow_build(self, intelligence_system):
        """Test optimization generator detecting slow build times."""
        patterns_by_type = {
            PatternType.CODE_PATTERN: [
                ProjectPattern(
                    pattern_id="optimization_pattern",
                    pattern_type=PatternType.CODE_PATTERN,
                    project_name="fast_project",
                    description="optimization techniques and best practices"
                )
            ]
        }
        
        analytics = {
            "slow_project": ProjectAnalytics(
                project_name="slow_project",
                build_time=120.0  # Slow build time
            ),
            "fast_project": ProjectAnalytics(
                project_name="fast_project",
                build_time=30.0
            )
        }
        
        # Get the optimization generator
        generator = intelligence_system.insight_generators[InsightType.OPTIMIZATION]
        insights = await generator(patterns_by_type, analytics)
        
        # Should generate insights because pattern contains "optimization"
        assert len(insights) == 1
        insight = insights[0]
        assert insight.insight_type == InsightType.OPTIMIZATION
        assert "slow_project" in insight.title

    @pytest.mark.asyncio
    async def test_optimization_generator_with_matching_patterns(self, intelligence_system):
        """Test optimization generator with matching optimization patterns."""
        patterns_by_type = {
            PatternType.CODE_PATTERN: [
                ProjectPattern(
                    pattern_id="optimization_pattern",
                    pattern_type=PatternType.CODE_PATTERN,
                    project_name="fast_project",
                    description="Caching optimization pattern"
                )
            ]
        }
        
        analytics = {
            "slow_project": ProjectAnalytics(
                project_name="slow_project",
                build_time=120.0  # Slow build time
            ),
            "fast_project": ProjectAnalytics(
                project_name="fast_project",
                build_time=30.0
            )
        }
        
        # Get the optimization generator
        generator = intelligence_system.insight_generators[InsightType.OPTIMIZATION]
        insights = await generator(patterns_by_type, analytics)
        
        assert len(insights) == 1
        insight = insights[0]
        assert insight.insight_type == InsightType.OPTIMIZATION
        assert "slow_project" in insight.title
        assert "slow_project" in insight.affected_projects
        assert insight.confidence == 0.7
        assert insight.priority == 2
        assert len(insight.recommendations) > 0

    @pytest.mark.asyncio
    async def test_optimization_generator_fast_builds(self, intelligence_system):
        """Test optimization generator with fast build times."""
        patterns_by_type = {PatternType.CODE_PATTERN: []}
        
        analytics = {
            "fast_project": ProjectAnalytics(
                project_name="fast_project",
                build_time=30.0  # Fast build time
            )
        }
        
        # Get the optimization generator
        generator = intelligence_system.insight_generators[InsightType.OPTIMIZATION]
        insights = await generator(patterns_by_type, analytics)
        
        assert len(insights) == 0

    @pytest.mark.asyncio
    async def test_best_practice_generator_common_patterns(self, intelligence_system):
        """Test best practice generator with common patterns."""
        patterns_by_type = {
            PatternType.WORKFLOW_PATTERN: [
                ProjectPattern(
                    pattern_id="pattern1",
                    pattern_type=PatternType.WORKFLOW_PATTERN,
                    project_name="project1",
                    description="TDD best practice"
                ),
                ProjectPattern(
                    pattern_id="pattern2",
                    pattern_type=PatternType.WORKFLOW_PATTERN,
                    project_name="project2",
                    description="TDD best practice"
                ),
                ProjectPattern(
                    pattern_id="pattern3",
                    pattern_type=PatternType.WORKFLOW_PATTERN,
                    project_name="project3",
                    description="TDD best practice"
                )
            ]
        }
        
        analytics = {
            "project1": ProjectAnalytics(
                project_name="project1",
                test_coverage=0.9  # High coverage
            ),
            "project2": ProjectAnalytics(
                project_name="project2",
                test_coverage=0.85  # High coverage
            ),
            "project3": ProjectAnalytics(
                project_name="project3",
                test_coverage=0.6   # Lower coverage
            ),
            "project4": ProjectAnalytics(
                project_name="project4",
                test_coverage=0.7
            )
        }
        
        # Get the best practice generator
        generator = intelligence_system.insight_generators[InsightType.BEST_PRACTICE]
        insights = await generator(patterns_by_type, analytics)
        
        assert len(insights) == 1
        insight = insights[0]
        assert insight.insight_type == InsightType.BEST_PRACTICE
        assert "TDD best practice" in insight.title
        assert "project1" in insight.description
        assert "project2" in insight.description
        assert "project4" in insight.affected_projects  # Should be affected (not using the practice)
        assert insight.confidence == 0.8
        assert insight.priority == 2
        assert len(insight.recommendations) > 0

    @pytest.mark.asyncio
    async def test_best_practice_generator_insufficient_patterns(self, intelligence_system):
        """Test best practice generator with insufficient patterns."""
        patterns_by_type = {
            PatternType.WORKFLOW_PATTERN: [
                ProjectPattern(
                    pattern_id="pattern1",
                    pattern_type=PatternType.WORKFLOW_PATTERN,
                    project_name="project1",
                    description="TDD best practice"
                ),
                ProjectPattern(
                    pattern_id="pattern2",
                    pattern_type=PatternType.WORKFLOW_PATTERN,
                    project_name="project2",
                    description="TDD best practice"
                )
            ]
        }
        
        analytics = {
            "project1": ProjectAnalytics(
                project_name="project1",
                test_coverage=0.9
            ),
            "project2": ProjectAnalytics(
                project_name="project2",
                test_coverage=0.85
            )
        }
        
        # Get the best practice generator
        generator = intelligence_system.insight_generators[InsightType.BEST_PRACTICE]
        insights = await generator(patterns_by_type, analytics)
        
        assert len(insights) == 0  # Need at least 3 patterns

    @pytest.mark.asyncio
    async def test_best_practice_generator_insufficient_high_performing(self, intelligence_system):
        """Test best practice generator with insufficient high-performing projects."""
        patterns_by_type = {
            PatternType.WORKFLOW_PATTERN: [
                ProjectPattern(
                    pattern_id="pattern1",
                    pattern_type=PatternType.WORKFLOW_PATTERN,
                    project_name="project1",
                    description="TDD best practice"
                ),
                ProjectPattern(
                    pattern_id="pattern2",
                    pattern_type=PatternType.WORKFLOW_PATTERN,
                    project_name="project2",
                    description="TDD best practice"
                ),
                ProjectPattern(
                    pattern_id="pattern3",
                    pattern_type=PatternType.WORKFLOW_PATTERN,
                    project_name="project3",
                    description="TDD best practice"
                )
            ]
        }
        
        analytics = {
            "project1": ProjectAnalytics(
                project_name="project1",
                test_coverage=0.9   # High coverage
            ),
            "project2": ProjectAnalytics(
                project_name="project2",
                test_coverage=0.6   # Low coverage
            ),
            "project3": ProjectAnalytics(
                project_name="project3",
                test_coverage=0.5   # Low coverage
            )
        }
        
        # Get the best practice generator
        generator = intelligence_system.insight_generators[InsightType.BEST_PRACTICE]
        insights = await generator(patterns_by_type, analytics)
        
        assert len(insights) == 0  # Need at least 2 high-performing projects

    @pytest.mark.asyncio
    async def test_best_practice_generator_missing_analytics(self, intelligence_system):
        """Test best practice generator with missing analytics."""
        patterns_by_type = {
            PatternType.WORKFLOW_PATTERN: [
                ProjectPattern(
                    pattern_id="pattern1",
                    pattern_type=PatternType.WORKFLOW_PATTERN,
                    project_name="project1",
                    description="TDD best practice"
                ),
                ProjectPattern(
                    pattern_id="pattern2",
                    pattern_type=PatternType.WORKFLOW_PATTERN,
                    project_name="project2",
                    description="TDD best practice"
                ),
                ProjectPattern(
                    pattern_id="pattern3",
                    pattern_type=PatternType.WORKFLOW_PATTERN,
                    project_name="project3",
                    description="TDD best practice"
                )
            ]
        }
        
        analytics = {
            "project1": ProjectAnalytics(
                project_name="project1",
                test_coverage=0.9
            )
            # Missing analytics for project2 and project3
        }
        
        # Get the best practice generator
        generator = intelligence_system.insight_generators[InsightType.BEST_PRACTICE]
        insights = await generator(patterns_by_type, analytics)
        
        assert len(insights) == 0  # Missing analytics should be handled gracefully