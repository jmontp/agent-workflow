"""
Comprehensive test suite for Context Learning System.

Tests machine learning for context relevance improvement through pattern recognition,
feedback analysis, adaptive filtering strategies, and ensemble learning methods.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from collections import deque

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_learning import (
    ContextLearningSystem,
    LearningStrategy,
    FeatureType,
    LearningFeedback,
    FileFeatures,
    LearningPattern
)
from context.models import (
    ContextRequest,
    AgentContext,
    RelevanceScore,
    TDDState,
    FileType
)
from context.exceptions import ContextLearningError
from tdd_models import TDDTask


class TestLearningStrategy:
    """Test LearningStrategy enumeration"""
    
    def test_learning_strategy_values(self):
        """Test learning strategy enum values"""
        assert LearningStrategy.FEEDBACK_BASED.value == "feedback_based"
        assert LearningStrategy.USAGE_PATTERN.value == "usage_pattern"
        assert LearningStrategy.SIMILARITY_CLUSTERING.value == "similarity_clustering"
        assert LearningStrategy.REINFORCEMENT.value == "reinforcement"
        assert LearningStrategy.ENSEMBLE.value == "ensemble"
    
    def test_learning_strategy_count(self):
        """Test that all expected strategies are defined"""
        strategies = list(LearningStrategy)
        assert len(strategies) == 5


class TestFeatureType:
    """Test FeatureType enumeration"""
    
    def test_feature_type_values(self):
        """Test feature type enum values"""
        expected_types = [
            "file_path", "file_extension", "file_size", "last_modified",
            "content_keywords", "agent_type", "tdd_phase", "story_context",
            "dependency_count", "access_frequency"
        ]
        
        for feature_type in FeatureType:
            assert feature_type.value in expected_types
    
    def test_feature_type_count(self):
        """Test expected number of feature types"""
        feature_types = list(FeatureType)
        assert len(feature_types) == 10


class TestLearningFeedback:
    """Test LearningFeedback data class"""
    
    def test_learning_feedback_creation(self):
        """Test basic learning feedback creation"""
        feedback = LearningFeedback(
            context_id="ctx_123",
            agent_type="CodeAgent",
            story_id="story_456",
            file_path="/test/file.py",
            predicted_relevance=0.8,
            actual_relevance=0.7,
            feedback_type="usage",
            timestamp=datetime.utcnow()
        )
        
        assert feedback.context_id == "ctx_123"
        assert feedback.agent_type == "CodeAgent"
        assert feedback.story_id == "story_456"
        assert feedback.file_path == "/test/file.py"
        assert feedback.predicted_relevance == 0.8
        assert feedback.actual_relevance == 0.7
        assert feedback.feedback_type == "usage"
        assert isinstance(feedback.timestamp, datetime)
        assert len(feedback.metadata) == 0
    
    def test_relevance_error_calculation(self):
        """Test relevance error calculation"""
        feedback = LearningFeedback(
            context_id="ctx_123",
            agent_type="CodeAgent",
            story_id="story_456",
            file_path="/test/file.py",
            predicted_relevance=0.8,
            actual_relevance=0.6,
            feedback_type="usage",
            timestamp=datetime.utcnow()
        )
        
        assert feedback.relevance_error == 0.2
    
    def test_accuracy_assessment(self):
        """Test accuracy assessment"""
        # Accurate prediction
        accurate_feedback = LearningFeedback(
            context_id="ctx_123",
            agent_type="CodeAgent",
            story_id="story_456",
            file_path="/test/file.py",
            predicted_relevance=0.8,
            actual_relevance=0.85,
            feedback_type="usage",
            timestamp=datetime.utcnow()
        )
        
        assert accurate_feedback.is_accurate()
        assert accurate_feedback.is_accurate(threshold=0.1)
        
        # Inaccurate prediction
        inaccurate_feedback = LearningFeedback(
            context_id="ctx_123",
            agent_type="CodeAgent",
            story_id="story_456",
            file_path="/test/file.py",
            predicted_relevance=0.8,
            actual_relevance=0.3,
            feedback_type="usage",
            timestamp=datetime.utcnow()
        )
        
        assert not inaccurate_feedback.is_accurate()
        assert not inaccurate_feedback.is_accurate(threshold=0.1)
    
    def test_feedback_with_metadata(self):
        """Test feedback with metadata"""
        feedback = LearningFeedback(
            context_id="ctx_123",
            agent_type="CodeAgent",
            story_id="story_456",
            file_path="/test/file.py",
            predicted_relevance=0.8,
            actual_relevance=0.7,
            feedback_type="explicit",
            timestamp=datetime.utcnow(),
            metadata={"tdd_phase": TDDState.RED, "confidence": 0.9}
        )
        
        assert feedback.metadata["tdd_phase"] == TDDState.RED
        assert feedback.metadata["confidence"] == 0.9


class TestFileFeatures:
    """Test FileFeatures data class"""
    
    def test_file_features_creation(self):
        """Test basic file features creation"""
        features = FileFeatures(
            file_path="/test/file.py",
            features={"is_python": 1.0, "has_class": 0.5},
            last_updated=datetime.utcnow(),
            access_count=5
        )
        
        assert features.file_path == "/test/file.py"
        assert features.features["is_python"] == 1.0
        assert features.features["has_class"] == 0.5
        assert features.access_count == 5
        assert len(features.relevance_history) == 0
    
    def test_add_relevance_score(self):
        """Test adding relevance scores to history"""
        features = FileFeatures(
            file_path="/test/file.py",
            features={},
            last_updated=datetime.utcnow()
        )
        
        # Add scores
        features.add_relevance_score(0.8)
        features.add_relevance_score(0.7)
        features.add_relevance_score(0.9)
        
        assert len(features.relevance_history) == 3
        assert features.relevance_history == [0.8, 0.7, 0.9]
    
    def test_relevance_history_limit(self):
        """Test that relevance history is limited to 100 entries"""
        features = FileFeatures(
            file_path="/test/file.py",
            features={},
            last_updated=datetime.utcnow()
        )
        
        # Add more than 100 scores
        for i in range(150):
            features.add_relevance_score(i / 150.0)
        
        assert len(features.relevance_history) == 100
        # Should keep the last 100
        assert features.relevance_history[0] == 50 / 150.0  # First of last 100
        assert features.relevance_history[-1] == 149 / 150.0  # Last added
    
    def test_average_relevance_calculation(self):
        """Test average relevance calculation"""
        features = FileFeatures(
            file_path="/test/file.py",
            features={},
            last_updated=datetime.utcnow()
        )
        
        # Empty history
        assert features.average_relevance == 0.0
        
        # Add scores
        features.add_relevance_score(0.6)
        features.add_relevance_score(0.8)
        features.add_relevance_score(1.0)
        
        expected_avg = (0.6 + 0.8 + 1.0) / 3
        assert abs(features.average_relevance - expected_avg) < 0.001


class TestLearningPattern:
    """Test LearningPattern data class"""
    
    def test_learning_pattern_creation(self):
        """Test basic learning pattern creation"""
        pattern = LearningPattern(
            pattern_id="pattern_123",
            pattern_type="adaptive",
            agent_types={"CodeAgent", "QAAgent"},
            tdd_phases={TDDState.RED, TDDState.GREEN},
            feature_weights={"is_python": 0.8, "has_test": 0.6},
            success_rate=0.85,
            usage_count=50,
            confidence=0.9
        )
        
        assert pattern.pattern_id == "pattern_123"
        assert pattern.pattern_type == "adaptive"
        assert "CodeAgent" in pattern.agent_types
        assert "QAAgent" in pattern.agent_types
        assert TDDState.RED in pattern.tdd_phases
        assert TDDState.GREEN in pattern.tdd_phases
        assert pattern.feature_weights["is_python"] == 0.8
        assert pattern.success_rate == 0.85
        assert pattern.usage_count == 50
        assert pattern.confidence == 0.9
    
    def test_pattern_context_matching(self):
        """Test pattern context matching"""
        pattern = LearningPattern(
            pattern_id="test_pattern",
            pattern_type="base",
            agent_types={"CodeAgent"},
            tdd_phases={TDDState.GREEN},
            feature_weights={},
            success_rate=0.8
        )
        
        # Should match exact context
        assert pattern.matches_context("CodeAgent", TDDState.GREEN)
        
        # Should not match different agent
        assert not pattern.matches_context("QAAgent", TDDState.GREEN)
        
        # Should not match different phase
        assert not pattern.matches_context("CodeAgent", TDDState.RED)
        
        # Empty sets should match any
        universal_pattern = LearningPattern(
            pattern_id="universal",
            pattern_type="base",
            agent_types=set(),
            tdd_phases=set(),
            feature_weights={},
            success_rate=0.8
        )
        
        assert universal_pattern.matches_context("AnyAgent", TDDState.RED)
        assert universal_pattern.matches_context("AnyAgent", None)
    
    def test_calculate_relevance(self):
        """Test relevance calculation using pattern weights"""
        pattern = LearningPattern(
            pattern_id="test_pattern",
            pattern_type="base",
            agent_types=set(),
            tdd_phases=set(),
            feature_weights={
                "is_python": 0.8,
                "has_class": 0.6,
                "file_size": 0.2
            },
            success_rate=0.8
        )
        
        features = {
            "is_python": 1.0,
            "has_class": 0.5,
            "file_size": 0.3,
            "unknown_feature": 0.9  # Should be ignored
        }
        
        relevance = pattern.calculate_relevance(features)
        
        # Calculate expected: (1.0*0.8 + 0.5*0.6 + 0.3*0.2) / (0.8 + 0.6 + 0.2)
        expected = (0.8 + 0.3 + 0.06) / 1.6
        assert abs(relevance - expected) < 0.001
    
    def test_calculate_relevance_empty_features(self):
        """Test relevance calculation with empty features"""
        pattern = LearningPattern(
            pattern_id="test_pattern",
            pattern_type="base",
            agent_types=set(),
            tdd_phases=set(),
            feature_weights={"is_python": 0.8},
            success_rate=0.8
        )
        
        # No matching features
        relevance = pattern.calculate_relevance({})
        assert relevance == 0.0
        
        # No feature weights
        empty_pattern = LearningPattern(
            pattern_id="empty",
            pattern_type="base",
            agent_types=set(),
            tdd_phases=set(),
            feature_weights={},
            success_rate=0.8
        )
        
        relevance = empty_pattern.calculate_relevance({"is_python": 1.0})
        assert relevance == 0.0


class TestContextLearningSystemInit:
    """Test ContextLearningSystem initialization"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_init_with_defaults(self, temp_project):
        """Test initialization with default parameters"""
        learning_system = ContextLearningSystem(temp_project)
        
        assert learning_system.project_path == Path(temp_project)
        assert learning_system.learning_rate == 0.01
        assert learning_system.strategy == LearningStrategy.ENSEMBLE
        assert learning_system.feature_decay_days == 30
        assert learning_system.pattern_confidence_threshold == 0.7
        assert learning_system.enable_persistence is True
        
        assert isinstance(learning_system.file_features, dict)
        assert isinstance(learning_system.learning_patterns, dict)
        assert isinstance(learning_system.feedback_history, deque)
        assert len(learning_system.file_features) == 0
        assert len(learning_system.learning_patterns) == 0
        assert len(learning_system.feedback_history) == 0
    
    def test_init_with_custom_params(self, temp_project):
        """Test initialization with custom parameters"""
        learning_system = ContextLearningSystem(
            project_path=temp_project,
            learning_rate=0.05,
            strategy=LearningStrategy.FEEDBACK_BASED,
            feature_decay_days=60,
            pattern_confidence_threshold=0.8,
            enable_persistence=False
        )
        
        assert learning_system.learning_rate == 0.05
        assert learning_system.strategy == LearningStrategy.FEEDBACK_BASED
        assert learning_system.feature_decay_days == 60
        assert learning_system.pattern_confidence_threshold == 0.8
        assert learning_system.enable_persistence is False
    
    def test_persistence_directory_creation(self, temp_project):
        """Test that persistence directory is created"""
        learning_system = ContextLearningSystem(temp_project, enable_persistence=True)
        
        expected_dir = Path(temp_project) / ".orch-state" / "context_learning"
        assert learning_system.persistence_dir == expected_dir
        assert expected_dir.exists()
        
        # Check file paths
        assert learning_system.patterns_file == expected_dir / "patterns.pkl"
        assert learning_system.features_file == expected_dir / "features.pkl"
        assert learning_system.feedback_file == expected_dir / "feedback.json"
    
    def test_feature_extractors_initialization(self, temp_project):
        """Test feature extractors initialization"""
        learning_system = ContextLearningSystem(temp_project)
        
        assert isinstance(learning_system.feature_extractors, dict)
        assert len(learning_system.feature_extractors) > 0
        
        # Check for expected feature types
        expected_types = [
            FeatureType.FILE_PATH,
            FeatureType.FILE_EXTENSION,
            FeatureType.FILE_SIZE,
            FeatureType.LAST_MODIFIED,
            FeatureType.CONTENT_KEYWORDS,
            FeatureType.DEPENDENCY_COUNT
        ]
        
        for feature_type in expected_types:
            assert feature_type in learning_system.feature_extractors


class TestFeatureExtraction:
    """Test feature extraction functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project with test files"""
        temp_dir = tempfile.mkdtemp()
        
        # Create Python file
        python_file = Path(temp_dir) / "service.py"
        python_content = '''
import json
from datetime import datetime

class UserService:
    def create_user(self, data):
        return User(data)
    
    def validate_email(self, email):
        return "@" in email
'''
        python_file.write_text(python_content)
        
        # Create test file
        test_file = Path(temp_dir) / "tests" / "test_service.py"
        test_file.parent.mkdir(exist_ok=True)
        test_content = '''
import unittest
from service import UserService

class TestUserService(unittest.TestCase):
    def test_create_user(self):
        service = UserService()
        result = service.create_user({"name": "test"})
        self.assertIsNotNone(result)
'''
        test_file.write_text(test_content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def learning_system(self, temp_project):
        return ContextLearningSystem(temp_project)
    
    @pytest.mark.asyncio
    async def test_extract_file_features_python(self, learning_system, temp_project):
        """Test feature extraction for Python files"""
        python_file = str(Path(temp_project) / "service.py")
        
        features = await learning_system.extract_file_features(python_file)
        
        assert isinstance(features, dict)
        assert len(features) > 0
        
        # Check path-based features
        assert "path_depth" in features
        assert "is_src" in features
        
        # Check extension features
        assert "is_python" in features
        assert features["is_python"] == 1.0
        
        # Check content features
        assert "has_class" in features
        assert "has_function" in features
        assert "has_import" in features
        assert features["has_class"] == 1.0
        assert features["has_function"] == 1.0
        assert features["has_import"] == 1.0
    
    @pytest.mark.asyncio
    async def test_extract_file_features_test(self, learning_system, temp_project):
        """Test feature extraction for test files"""
        test_file = str(Path(temp_project) / "tests" / "test_service.py")
        
        features = await learning_system.extract_file_features(test_file)
        
        # Check test-specific features
        assert "is_test" in features
        assert features["is_test"] == 1.0
        assert "has_test" in features
        assert features["has_test"] == 1.0
    
    @pytest.mark.asyncio
    async def test_feature_caching(self, learning_system, temp_project):
        """Test that features are cached"""
        python_file = str(Path(temp_project) / "service.py")
        
        # First extraction
        features1 = await learning_system.extract_file_features(python_file)
        
        # Should be cached
        assert python_file in learning_system.file_features
        
        # Second extraction should use cache
        features2 = await learning_system.extract_file_features(python_file)
        
        assert features1 == features2
    
    @pytest.mark.asyncio
    async def test_feature_cache_invalidation(self, learning_system, temp_project):
        """Test feature cache invalidation on file changes"""
        python_file = Path(temp_project) / "service.py"
        python_file_str = str(python_file)
        
        # First extraction
        features1 = await learning_system.extract_file_features(python_file_str)
        
        # Modify file (simulate newer modification time)
        original_content = python_file.read_text()
        python_file.write_text(original_content + "\n# Modified")
        
        # Should detect change and re-extract
        features2 = await learning_system.extract_file_features(python_file_str)
        
        # Features might be different due to content change
        stored_features = learning_system.file_features[python_file_str]
        assert stored_features.last_updated > datetime.utcnow() - timedelta(seconds=10)
    
    @pytest.mark.asyncio
    async def test_extract_path_features(self, learning_system):
        """Test path-based feature extraction"""
        test_paths = [
            "/project/src/main.py",
            "/project/tests/test_main.py",
            "/project/config/settings.json",
            "/project/docs/README.md",
            "/project/deep/nested/path/file.py"
        ]
        
        for path in test_paths:
            features = learning_system._extract_path_features(path)
            
            assert "path_depth" in features
            assert isinstance(features["path_depth"], int)
            assert features["path_depth"] > 0
            
            # Check specific patterns
            if "test" in path:
                assert features["is_test"] == 1.0
            if "src" in path or "lib" in path:
                assert features["is_src"] == 1.0
            if "config" in path:
                assert features["is_config"] == 1.0
            if "doc" in path or "readme" in path.lower():
                assert features["is_docs"] == 1.0
    
    @pytest.mark.asyncio
    async def test_extract_extension_features(self, learning_system):
        """Test extension-based feature extraction"""
        test_files = [
            "script.py",
            "component.js",
            "types.ts",
            "README.md",
            "config.json",
            "settings.yaml",
            "data.yml",
            "setup.toml",
            "notes.txt"
        ]
        
        for filename in test_files:
            features = learning_system._extract_extension_features(filename)
            
            if filename.endswith(".py"):
                assert features["is_python"] == 1.0
            if filename.endswith((".js", ".ts")):
                assert features["is_javascript"] == 1.0
            if filename.endswith(".md"):
                assert features["is_markdown"] == 1.0
            if filename.endswith((".json", ".yaml", ".yml", ".toml")):
                assert features["is_config"] == 1.0
            if filename.endswith((".txt", ".md")):
                assert features["is_text"] == 1.0
    
    @pytest.mark.asyncio
    async def test_extract_size_features(self, learning_system, temp_project):
        """Test size-based feature extraction"""
        # Create files of different sizes
        small_file = Path(temp_project) / "small.py"
        small_file.write_text("def small(): pass")
        
        large_file = Path(temp_project) / "large.py"
        large_file.write_text("# Large file\n" + "x = 1\n" * 10000)
        
        # Test small file
        small_features = learning_system._extract_size_features(str(small_file))
        assert "file_size_normalized" in small_features
        assert "is_small_file" in small_features
        assert "is_large_file" in small_features
        assert small_features["is_small_file"] == 1.0
        assert small_features["is_large_file"] == 0.0
        
        # Test large file
        large_features = learning_system._extract_size_features(str(large_file))
        assert large_features["is_small_file"] == 0.0
        assert large_features["is_large_file"] == 1.0
    
    @pytest.mark.asyncio
    async def test_extract_modification_features(self, learning_system, temp_project):
        """Test modification time features"""
        # Create recent file
        recent_file = Path(temp_project) / "recent.py"
        recent_file.write_text("def recent(): pass")
        
        features = learning_system._extract_modification_features(str(recent_file))
        
        assert "file_recency" in features
        assert "is_recently_modified" in features
        assert features["file_recency"] > 0.8  # Should be very recent
        assert features["is_recently_modified"] == 1.0


class TestRelevancePrediction:
    """Test relevance prediction functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project"""
        temp_dir = tempfile.mkdtemp()
        
        python_file = Path(temp_dir) / "user_service.py"
        python_file.write_text('''
class UserService:
    def authenticate_user(self, credentials):
        return True
''')
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def learning_system(self, temp_project):
        return ContextLearningSystem(temp_project)
    
    @pytest.fixture
    def sample_request(self):
        task = TDDTask(
            id="test_task",
            description="Implement user authentication",
            cycle_id="cycle_1",
            current_state=TDDState.GREEN
        )
        
        return ContextRequest(
            agent_type="CodeAgent",
            story_id="story_auth",
            task=task,
            focus_areas=["authentication", "user"]
        )
    
    @pytest.mark.asyncio
    async def test_predict_relevance_basic(self, learning_system, sample_request, temp_project):
        """Test basic relevance prediction"""
        await learning_system.initialize()
        
        python_file = str(Path(temp_project) / "user_service.py")
        
        relevance = await learning_system.predict_relevance(python_file, sample_request)
        
        assert isinstance(relevance, float)
        assert 0.0 <= relevance <= 1.0
        assert learning_system.total_predictions > 0
    
    @pytest.mark.asyncio
    async def test_predict_relevance_with_patterns(self, learning_system, sample_request, temp_project):
        """Test relevance prediction with learned patterns"""
        await learning_system.initialize()
        
        # Should have base patterns after initialization
        assert len(learning_system.learning_patterns) > 0
        
        python_file = str(Path(temp_project) / "user_service.py")
        relevance = await learning_system.predict_relevance(python_file, sample_request)
        
        # Should use patterns for prediction
        assert relevance > 0.0
    
    @pytest.mark.asyncio
    async def test_predict_relevance_ensemble_strategy(self, learning_system, sample_request, temp_project):
        """Test ensemble strategy prediction"""
        learning_system.strategy = LearningStrategy.ENSEMBLE
        await learning_system.initialize()
        
        python_file = str(Path(temp_project) / "user_service.py")
        relevance = await learning_system.predict_relevance(python_file, sample_request)
        
        assert isinstance(relevance, float)
    
    @pytest.mark.asyncio
    async def test_predict_relevance_best_pattern_strategy(self, learning_system, sample_request, temp_project):
        """Test best pattern strategy prediction"""
        learning_system.strategy = LearningStrategy.FEEDBACK_BASED
        await learning_system.initialize()
        
        python_file = str(Path(temp_project) / "user_service.py")
        relevance = await learning_system.predict_relevance(python_file, sample_request)
        
        assert isinstance(relevance, float)
    
    @pytest.mark.asyncio
    async def test_predict_relevance_nonexistent_file(self, learning_system, sample_request):
        """Test prediction for non-existent file"""
        await learning_system.initialize()
        
        relevance = await learning_system.predict_relevance("/nonexistent/file.py", sample_request)
        
        # Should handle gracefully
        assert relevance == 0.0
    
    @pytest.mark.asyncio
    async def test_baseline_relevance_calculation(self, learning_system):
        """Test baseline relevance calculation"""
        features = {
            "is_python": 1.0,
            "has_function": 1.0,
            "has_class": 1.0,
            "file_recency": 0.8
        }
        
        code_request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_123",
            task=None,
            focus_areas=[]
        )
        
        relevance = learning_system._calculate_baseline_relevance(features, code_request)
        
        assert isinstance(relevance, float)
        assert relevance > 0.0
        assert relevance <= 1.0
    
    @pytest.mark.asyncio
    async def test_context_features_extraction(self, learning_system):
        """Test context feature extraction"""
        task = TDDTask(
            id="test_task",
            description="Test task",
            cycle_id="cycle_1",
            current_state=TDDState.RED
        )
        
        request = ContextRequest(
            agent_type="QAAgent",
            story_id="story_test",
            task=task,
            focus_areas=[]
        )
        
        features = learning_system._extract_context_features(request)
        
        assert isinstance(features, dict)
        assert "agent_qaagent" in features
        assert features["agent_qaagent"] == 1.0
        assert "phase_red" in features
        assert features["phase_red"] == 1.0
        assert "story_context" in features


class TestFeedbackRecording:
    """Test feedback recording and learning"""
    
    @pytest.fixture
    def learning_system(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextLearningSystem(temp_dir)
    
    @pytest.mark.asyncio
    async def test_record_feedback_basic(self, learning_system):
        """Test basic feedback recording"""
        await learning_system.initialize()
        
        file_relevance_scores = {
            "/test/file1.py": 0.8,
            "/test/file2.py": 0.6,
            "/test/file3.py": 0.9
        }
        
        initial_count = len(learning_system.feedback_history)
        
        await learning_system.record_feedback(
            context_id="ctx_123",
            agent_type="CodeAgent",
            story_id="story_456",
            file_relevance_scores=file_relevance_scores,
            feedback_type="usage"
        )
        
        # Should have added feedback for each file
        assert len(learning_system.feedback_history) == initial_count + 3
        
        # Check feedback content
        recent_feedback = list(learning_system.feedback_history)[-3:]
        for feedback in recent_feedback:
            assert feedback.context_id == "ctx_123"
            assert feedback.agent_type == "CodeAgent"
            assert feedback.story_id == "story_456"
            assert feedback.feedback_type == "usage"
            assert feedback.file_path in file_relevance_scores
            assert feedback.actual_relevance == file_relevance_scores[feedback.file_path]
    
    @pytest.mark.asyncio
    async def test_record_feedback_updates_features(self, learning_system):
        """Test that feedback updates file features"""
        await learning_system.initialize()
        
        file_path = "/test/file.py"
        
        # Create file features
        await learning_system.extract_file_features(file_path)
        
        initial_access_count = learning_system.file_features[file_path].access_count
        
        await learning_system.record_feedback(
            context_id="ctx_123",
            agent_type="CodeAgent",
            story_id="story_456",
            file_relevance_scores={file_path: 0.8}
        )
        
        # Should update access count and relevance history
        features = learning_system.file_features[file_path]
        assert features.access_count == initial_access_count + 1
        assert 0.8 in features.relevance_history
    
    @pytest.mark.asyncio
    async def test_record_feedback_accuracy_tracking(self, learning_system):
        """Test feedback accuracy tracking"""
        await learning_system.initialize()
        
        # Mock cached prediction
        with patch.object(learning_system, '_get_cached_prediction', return_value=0.75):
            await learning_system.record_feedback(
                context_id="ctx_123",
                agent_type="CodeAgent",
                story_id="story_456",
                file_relevance_scores={"/test/file.py": 0.8}  # Close to predicted 0.75
            )
            
            # Should track accurate prediction
            assert learning_system.accurate_predictions > 0


class TestPatternLearning:
    """Test pattern learning and updating"""
    
    @pytest.fixture
    def learning_system(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextLearningSystem(temp_dir)
    
    @pytest.mark.asyncio
    async def test_update_patterns_insufficient_data(self, learning_system):
        """Test pattern update with insufficient data"""
        await learning_system.initialize()
        
        # No feedback, should not update patterns
        updated_count = await learning_system.update_patterns()
        assert updated_count == 0
    
    @pytest.mark.asyncio
    async def test_update_patterns_with_feedback(self, learning_system):
        """Test pattern update with sufficient feedback"""
        await learning_system.initialize()
        
        # Add sufficient feedback data
        for i in range(20):
            feedback = LearningFeedback(
                context_id=f"ctx_{i}",
                agent_type="CodeAgent",
                story_id="story_test",
                file_path=f"/test/file_{i}.py",
                predicted_relevance=0.5 + (i % 3) * 0.1,
                actual_relevance=0.6 + (i % 3) * 0.1,
                feedback_type="usage",
                timestamp=datetime.utcnow() - timedelta(hours=i)
            )
            learning_system.feedback_history.append(feedback)
        
        initial_pattern_count = len(learning_system.learning_patterns)
        
        updated_count = await learning_system.update_patterns()
        
        # Should have updated patterns
        assert updated_count >= 0
        assert learning_system.learning_updates >= updated_count
    
    @pytest.mark.asyncio
    async def test_discover_new_patterns(self, learning_system):
        """Test new pattern discovery"""
        await learning_system.initialize()
        
        # Create pattern of accurate feedback
        for i in range(15):
            feedback = LearningFeedback(
                context_id=f"ctx_{i}",
                agent_type="QAAgent",
                story_id="story_test",
                file_path=f"/test/test_file_{i}.py",
                predicted_relevance=0.8,
                actual_relevance=0.8,  # Accurate predictions
                feedback_type="usage",
                timestamp=datetime.utcnow()
            )
            learning_system.feedback_history.append(feedback)
        
        initial_pattern_count = len(learning_system.learning_patterns)
        
        new_patterns = await learning_system.discover_new_patterns()
        
        if new_patterns > 0:
            assert len(learning_system.learning_patterns) > initial_pattern_count
            assert learning_system.pattern_discoveries >= new_patterns
    
    @pytest.mark.asyncio
    async def test_pattern_weight_adjustment(self, learning_system):
        """Test pattern weight adjustment based on feedback"""
        await learning_system.initialize()
        
        # Get a base pattern
        pattern_id = list(learning_system.learning_patterns.keys())[0]
        pattern = learning_system.learning_patterns[pattern_id]
        
        # Create feedback for weight adjustment
        feedback_list = []
        for i in range(5):
            feedback = LearningFeedback(
                context_id=f"ctx_{i}",
                agent_type="CodeAgent",
                story_id="story_test",
                file_path=f"/test/file_{i}.py",
                predicted_relevance=0.7,
                actual_relevance=0.8,
                feedback_type="usage",
                timestamp=datetime.utcnow()
            )
            feedback_list.append(feedback)
        
        original_weights = pattern.feature_weights.copy()
        original_usage_count = pattern.usage_count
        
        # Mock feature extraction
        with patch.object(learning_system, 'extract_file_features', return_value={"is_python": 1.0}):
            await learning_system._adjust_pattern_weights(pattern, feedback_list)
        
        # Should have updated usage count
        assert pattern.usage_count > original_usage_count
        
        # Success rate should be calculated
        assert 0.0 <= pattern.success_rate <= 1.0
    
    @pytest.mark.asyncio
    async def test_initialize_base_patterns(self, learning_system):
        """Test base pattern initialization"""
        # Should start with no patterns
        assert len(learning_system.learning_patterns) == 0
        
        await learning_system._initialize_base_patterns()
        
        # Should have base patterns for different agent types
        assert len(learning_system.learning_patterns) > 0
        
        pattern_types = set()
        for pattern in learning_system.learning_patterns.values():
            pattern_types.update(pattern.agent_types)
        
        assert "CodeAgent" in pattern_types
        assert "QAAgent" in pattern_types
        assert "DesignAgent" in pattern_types
    
    @pytest.mark.asyncio
    async def test_find_applicable_patterns(self, learning_system):
        """Test finding applicable patterns"""
        await learning_system.initialize()
        
        # Should find patterns for CodeAgent
        code_patterns = learning_system._find_applicable_patterns("CodeAgent", TDDState.GREEN)
        assert len(code_patterns) > 0
        
        # Should find patterns for QAAgent
        qa_patterns = learning_system._find_applicable_patterns("QAAgent", TDDState.RED)
        assert len(qa_patterns) > 0
        
        # Patterns should be sorted by confidence
        if len(code_patterns) > 1:
            for i in range(len(code_patterns) - 1):
                assert code_patterns[i].confidence >= code_patterns[i + 1].confidence


class TestLearningStatistics:
    """Test learning statistics and metrics"""
    
    @pytest.fixture
    def learning_system(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextLearningSystem(temp_dir)
    
    @pytest.mark.asyncio
    async def test_get_learning_statistics_initial(self, learning_system):
        """Test initial learning statistics"""
        await learning_system.initialize()
        
        stats = await learning_system.get_learning_statistics()
        
        assert isinstance(stats, dict)
        assert "total_predictions" in stats
        assert "accurate_predictions" in stats
        assert "accuracy_rate" in stats
        assert "learning_updates" in stats
        assert "pattern_discoveries" in stats
        assert "active_patterns" in stats
        assert "tracked_files" in stats
        assert "feedback_samples" in stats
        assert "pattern_details" in stats
        
        # Initial state
        assert stats["total_predictions"] == 0
        assert stats["accurate_predictions"] == 0
        assert stats["accuracy_rate"] == 0.0
        assert stats["active_patterns"] > 0  # Should have base patterns
    
    @pytest.mark.asyncio
    async def test_get_learning_statistics_with_activity(self, learning_system):
        """Test statistics after some learning activity"""
        await learning_system.initialize()
        
        # Simulate some predictions and feedback
        learning_system.total_predictions = 20
        learning_system.accurate_predictions = 16
        learning_system.learning_updates = 3
        learning_system.pattern_discoveries = 1
        
        # Add some file features
        learning_system.file_features["/test/file1.py"] = FileFeatures(
            file_path="/test/file1.py",
            features={"is_python": 1.0},
            last_updated=datetime.utcnow()
        )
        
        # Add some feedback
        feedback = LearningFeedback(
            context_id="ctx_1",
            agent_type="CodeAgent",
            story_id="story_1",
            file_path="/test/file1.py",
            predicted_relevance=0.8,
            actual_relevance=0.8,
            feedback_type="usage",
            timestamp=datetime.utcnow()
        )
        learning_system.feedback_history.append(feedback)
        
        stats = await learning_system.get_learning_statistics()
        
        assert stats["total_predictions"] == 20
        assert stats["accurate_predictions"] == 16
        assert stats["accuracy_rate"] == 0.8
        assert stats["learning_updates"] == 3
        assert stats["pattern_discoveries"] == 1
        assert stats["tracked_files"] == 1
        assert stats["feedback_samples"] == 1
    
    @pytest.mark.asyncio
    async def test_pattern_details_in_statistics(self, learning_system):
        """Test pattern details in statistics"""
        await learning_system.initialize()
        
        stats = await learning_system.get_learning_statistics()
        
        pattern_details = stats["pattern_details"]
        assert isinstance(pattern_details, dict)
        
        # Check that each pattern has expected fields
        for pattern_id, details in pattern_details.items():
            assert "type" in details
            assert "confidence" in details
            assert "success_rate" in details
            assert "usage_count" in details
            assert "agent_types" in details
            assert "feature_count" in details
            assert isinstance(details["agent_types"], list)


class TestPerformanceOptimization:
    """Test performance optimization features"""
    
    @pytest.fixture
    def learning_system(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextLearningSystem(temp_dir)
    
    @pytest.mark.asyncio
    async def test_optimize_performance_initial(self, learning_system):
        """Test performance optimization with no data"""
        await learning_system.initialize()
        
        optimizations = await learning_system.optimize_performance()
        
        assert isinstance(optimizations, dict)
        assert "patterns_pruned" in optimizations
        assert "features_cleaned" in optimizations
        assert "feedback_archived" in optimizations
        
        # No data to optimize initially
        assert optimizations["patterns_pruned"] == 0
        assert optimizations["features_cleaned"] == 0
        assert optimizations["feedback_archived"] == 0
    
    @pytest.mark.asyncio
    async def test_optimize_performance_with_data(self, learning_system):
        """Test performance optimization with data"""
        await learning_system.initialize()
        
        # Add low-performing pattern
        poor_pattern = LearningPattern(
            pattern_id="poor_pattern",
            pattern_type="discovered",
            agent_types={"TestAgent"},
            tdd_phases=set(),
            feature_weights={"test": 0.5},
            success_rate=0.3,  # Low success rate
            usage_count=15,  # High usage count
            confidence=0.2  # Low confidence
        )
        learning_system.learning_patterns["poor_pattern"] = poor_pattern
        
        # Add old file features
        old_time = datetime.utcnow() - timedelta(days=50)
        old_features = FileFeatures(
            file_path="/old/file.py",
            features={"old": 1.0},
            last_updated=old_time,
            access_count=0  # Never accessed
        )
        learning_system.file_features["/old/file.py"] = old_features
        
        # Add old feedback
        for i in range(15):
            old_feedback = LearningFeedback(
                context_id=f"old_ctx_{i}",
                agent_type="TestAgent",
                story_id="old_story",
                file_path="/old/file.py",
                predicted_relevance=0.5,
                actual_relevance=0.5,
                feedback_type="usage",
                timestamp=datetime.utcnow() - timedelta(days=40)
            )
            learning_system.feedback_history.append(old_feedback)
        
        optimizations = await learning_system.optimize_performance()
        
        # Should have pruned poor pattern
        assert optimizations["patterns_pruned"] == 1
        assert "poor_pattern" not in learning_system.learning_patterns
        
        # Should have cleaned old features
        assert optimizations["features_cleaned"] == 1
        assert "/old/file.py" not in learning_system.file_features
        
        # Should have archived old feedback
        assert optimizations["feedback_archived"] > 0


class TestPersistence:
    """Test persistence functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_persistence_disabled(self, temp_project):
        """Test learning system with persistence disabled"""
        learning_system = ContextLearningSystem(temp_project, enable_persistence=False)
        await learning_system.initialize()
        
        # Should not create persistence files
        persistence_dir = Path(temp_project) / ".orch-state" / "context_learning"
        assert not persistence_dir.exists()
    
    @pytest.mark.asyncio
    async def test_save_and_load_patterns(self, temp_project):
        """Test saving and loading patterns"""
        # Create first learning system
        learning_system1 = ContextLearningSystem(temp_project, enable_persistence=True)
        await learning_system1.initialize()
        
        # Add custom pattern
        custom_pattern = LearningPattern(
            pattern_id="custom_test_pattern",
            pattern_type="test",
            agent_types={"TestAgent"},
            tdd_phases={TDDState.GREEN},
            feature_weights={"test_feature": 0.9},
            success_rate=0.85,
            confidence=0.8
        )
        learning_system1.learning_patterns["custom_test_pattern"] = custom_pattern
        
        # Save patterns
        await learning_system1._persist_patterns()
        
        # Create second learning system and load
        learning_system2 = ContextLearningSystem(temp_project, enable_persistence=True)
        await learning_system2._load_persisted_data()
        
        # Should have loaded the custom pattern
        assert "custom_test_pattern" in learning_system2.learning_patterns
        loaded_pattern = learning_system2.learning_patterns["custom_test_pattern"]
        assert loaded_pattern.pattern_type == "test"
        assert loaded_pattern.success_rate == 0.85
        assert loaded_pattern.confidence == 0.8
    
    @pytest.mark.asyncio
    async def test_save_and_load_features(self, temp_project):
        """Test saving and loading file features"""
        learning_system1 = ContextLearningSystem(temp_project, enable_persistence=True)
        await learning_system1.initialize()
        
        # Add file features
        features = FileFeatures(
            file_path="/test/file.py",
            features={"is_python": 1.0, "has_class": 0.5},
            last_updated=datetime.utcnow(),
            access_count=10
        )
        features.add_relevance_score(0.8)
        features.add_relevance_score(0.9)
        learning_system1.file_features["/test/file.py"] = features
        
        # Save features
        await learning_system1._persist_patterns()
        
        # Load in new system
        learning_system2 = ContextLearningSystem(temp_project, enable_persistence=True)
        await learning_system2._load_persisted_data()
        
        # Should have loaded features
        assert "/test/file.py" in learning_system2.file_features
        loaded_features = learning_system2.file_features["/test/file.py"]
        assert loaded_features.features["is_python"] == 1.0
        assert loaded_features.access_count == 10
        assert len(loaded_features.relevance_history) == 2
    
    @pytest.mark.asyncio
    async def test_save_and_load_feedback(self, temp_project):
        """Test saving and loading feedback"""
        learning_system1 = ContextLearningSystem(temp_project, enable_persistence=True)
        await learning_system1.initialize()
        
        # Add feedback
        feedback = LearningFeedback(
            context_id="ctx_persist_test",
            agent_type="CodeAgent",
            story_id="story_persist",
            file_path="/test/file.py",
            predicted_relevance=0.7,
            actual_relevance=0.8,
            feedback_type="explicit",
            timestamp=datetime.utcnow(),
            metadata={"test": "value"}
        )
        learning_system1.feedback_history.append(feedback)
        
        # Save feedback
        await learning_system1._persist_patterns()
        
        # Load in new system
        learning_system2 = ContextLearningSystem(temp_project, enable_persistence=True)
        await learning_system2._load_persisted_data()
        
        # Should have loaded feedback
        assert len(learning_system2.feedback_history) > 0
        loaded_feedback = learning_system2.feedback_history[0]
        assert loaded_feedback.context_id == "ctx_persist_test"
        assert loaded_feedback.agent_type == "CodeAgent"
        assert loaded_feedback.predicted_relevance == 0.7
        assert loaded_feedback.actual_relevance == 0.8
        assert loaded_feedback.metadata["test"] == "value"
    
    @pytest.mark.asyncio
    async def test_persistence_error_handling(self, temp_project):
        """Test persistence error handling"""
        learning_system = ContextLearningSystem(temp_project, enable_persistence=True)
        await learning_system.initialize()
        
        # Create invalid persistence directory
        invalid_dir = Path(temp_project) / "invalid"
        invalid_dir.mkdir()
        (invalid_dir / "patterns.pkl").write_text("invalid pickle data")
        
        # Should handle errors gracefully
        learning_system.patterns_file = invalid_dir / "patterns.pkl"
        
        try:
            await learning_system._load_persisted_data()
            # Should not crash
        except Exception:
            # Even if it fails, should continue operation
            pass


class TestIntegrationScenarios:
    """Integration test scenarios"""
    
    @pytest.fixture
    def temp_project(self):
        """Create comprehensive project for integration testing"""
        temp_dir = tempfile.mkdtemp()
        
        # Create realistic project structure
        files = {
            "models/user.py": '''
class User:
    def __init__(self, username, email):
        self.username = username
        self.email = email
''',
            "services/auth_service.py": '''
from models.user import User

class AuthService:
    def authenticate_user(self, username, password):
        return True
    
    def create_user(self, data):
        return User(data["username"], data["email"])
''',
            "tests/test_auth.py": '''
import unittest
from services.auth_service import AuthService

class TestAuthService(unittest.TestCase):
    def test_authenticate_user(self):
        service = AuthService()
        result = service.authenticate_user("test", "pass")
        self.assertTrue(result)
''',
            "config.json": '''
{
    "database_url": "sqlite:///app.db",
    "secret_key": "secret"
}
'''
        }
        
        for filepath, content in files.items():
            full_path = Path(temp_dir) / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_complete_learning_cycle(self, temp_project):
        """Test complete learning cycle from prediction to improvement"""
        learning_system = ContextLearningSystem(temp_project)
        await learning_system.initialize()
        
        # Create context request
        task = TDDTask(
            id="integration_task",
            description="Implement user authentication system",
            cycle_id="cycle_1",
            current_state=TDDState.GREEN
        )
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_auth_integration",
            task=task,
            focus_areas=["authentication", "user"]
        )
        
        # Step 1: Make predictions
        auth_service_path = str(Path(temp_project) / "services" / "auth_service.py")
        user_model_path = str(Path(temp_project) / "models" / "user.py")
        test_file_path = str(Path(temp_project) / "tests" / "test_auth.py")
        config_path = str(Path(temp_project) / "config.json")
        
        predictions = {}
        for file_path in [auth_service_path, user_model_path, test_file_path, config_path]:
            relevance = await learning_system.predict_relevance(file_path, request)
            predictions[file_path] = relevance
        
        # Step 2: Provide feedback
        feedback_scores = {
            auth_service_path: 0.9,  # Highly relevant
            user_model_path: 0.7,   # Moderately relevant
            test_file_path: 0.4,    # Less relevant for GREEN phase
            config_path: 0.2        # Low relevance
        }
        
        await learning_system.record_feedback(
            context_id="integration_ctx",
            agent_type="CodeAgent",
            story_id="story_auth_integration",
            file_relevance_scores=feedback_scores
        )
        
        # Step 3: Update patterns based on feedback
        initial_pattern_count = len(learning_system.learning_patterns)
        await learning_system.update_patterns()
        
        # Step 4: Make new predictions (should be improved)
        new_predictions = {}
        for file_path in [auth_service_path, user_model_path, test_file_path, config_path]:
            relevance = await learning_system.predict_relevance(file_path, request)
            new_predictions[file_path] = relevance
        
        # Verify learning occurred
        assert learning_system.total_predictions > 0
        assert len(learning_system.feedback_history) > 0
        
        # Check that high-relevance files are predicted well
        assert new_predictions[auth_service_path] > 0.0
        assert new_predictions[user_model_path] > 0.0
    
    @pytest.mark.asyncio
    async def test_cross_agent_learning(self, temp_project):
        """Test learning across different agent types"""
        learning_system = ContextLearningSystem(temp_project)
        await learning_system.initialize()
        
        test_file = str(Path(temp_project) / "tests" / "test_auth.py")
        
        # QA Agent should favor test files
        qa_task = TDDTask(id="qa_task", description="Test authentication", cycle_id="c1", current_state=TDDState.RED)
        qa_request = ContextRequest(agent_type="QAAgent", story_id="qa_story", task=qa_task, focus_areas=["test"])
        
        qa_relevance = await learning_system.predict_relevance(test_file, qa_request)
        
        # Code Agent should favor implementation files
        code_task = TDDTask(id="code_task", description="Implement auth", cycle_id="c1", current_state=TDDState.GREEN)
        code_request = ContextRequest(agent_type="CodeAgent", story_id="code_story", task=code_task, focus_areas=["auth"])
        
        auth_service = str(Path(temp_project) / "services" / "auth_service.py")
        code_relevance = await learning_system.predict_relevance(auth_service, code_request)
        
        # Should have different relevance patterns
        assert isinstance(qa_relevance, float)
        assert isinstance(code_relevance, float)
    
    @pytest.mark.asyncio
    async def test_pattern_evolution_over_time(self, temp_project):
        """Test how patterns evolve with more feedback"""
        learning_system = ContextLearningSystem(temp_project)
        await learning_system.initialize()
        
        initial_patterns = len(learning_system.learning_patterns)
        
        # Simulate feedback over time
        for i in range(50):
            feedback = LearningFeedback(
                context_id=f"ctx_{i}",
                agent_type="CodeAgent",
                story_id="evolution_story",
                file_path=f"/test/file_{i % 5}.py",
                predicted_relevance=0.5 + (i % 2) * 0.2,
                actual_relevance=0.6 + (i % 2) * 0.2,
                feedback_type="usage",
                timestamp=datetime.utcnow() - timedelta(hours=i)
            )
            learning_system.feedback_history.append(feedback)
            
            # Periodically update patterns
            if i % 10 == 9:
                await learning_system.update_patterns()
        
        # Try to discover new patterns
        await learning_system.discover_new_patterns()
        
        # Should have learned from experience
        final_patterns = len(learning_system.learning_patterns)
        assert learning_system.learning_updates > 0
        
        # Statistics should reflect learning activity
        stats = await learning_system.get_learning_statistics()
        assert stats["feedback_samples"] == 50
        assert stats["learning_updates"] > 0


if __name__ == "__main__":
    pytest.main([__file__])