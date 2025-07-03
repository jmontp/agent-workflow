"""
Context Learning - Machine Learning for Context Relevance Improvement

Advanced learning system that improves context relevance over time through
pattern recognition, feedback analysis, and adaptive filtering strategies.
"""

import asyncio
import logging
import json
import pickle
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum

try:
    from .context.models import (
        ContextRequest,
        AgentContext,
        RelevanceScore,
        TDDState,
        FileType
    )
    from .context.exceptions import ContextLearningError
except ImportError:
    from context.models import (
        ContextRequest,
        AgentContext,
        RelevanceScore,
        TDDState,
        FileType
    )
    from context.exceptions import ContextLearningError

logger = logging.getLogger(__name__)


class LearningStrategy(Enum):
    """Learning strategy options"""
    FEEDBACK_BASED = "feedback_based"
    USAGE_PATTERN = "usage_pattern"
    SIMILARITY_CLUSTERING = "similarity_clustering"
    REINFORCEMENT = "reinforcement"
    ENSEMBLE = "ensemble"


class FeatureType(Enum):
    """Types of features to extract"""
    FILE_PATH = "file_path"
    FILE_EXTENSION = "file_extension"
    FILE_SIZE = "file_size"
    LAST_MODIFIED = "last_modified"
    CONTENT_KEYWORDS = "content_keywords"
    AGENT_TYPE = "agent_type"
    TDD_PHASE = "tdd_phase"
    STORY_CONTEXT = "story_context"
    DEPENDENCY_COUNT = "dependency_count"
    ACCESS_FREQUENCY = "access_frequency"


@dataclass
class LearningFeedback:
    """Feedback data for learning system"""
    
    context_id: str
    agent_type: str
    story_id: str
    file_path: str
    predicted_relevance: float
    actual_relevance: float  # Based on usage/feedback
    feedback_type: str  # "usage", "explicit", "implicit"
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def relevance_error(self) -> float:
        """Calculate prediction error"""
        return abs(self.predicted_relevance - self.actual_relevance)
    
    @property
    def is_accurate(self, threshold: float = 0.2) -> bool:
        """Check if prediction was accurate within threshold"""
        return self.relevance_error <= threshold


@dataclass
class FileFeatures:
    """Feature vector for a file"""
    
    file_path: str
    features: Dict[str, float]
    last_updated: datetime
    access_count: int = 0
    relevance_history: List[float] = field(default_factory=list)
    
    def add_relevance_score(self, score: float) -> None:
        """Add a relevance score to history"""
        self.relevance_history.append(score)
        if len(self.relevance_history) > 100:  # Keep last 100 scores
            self.relevance_history = self.relevance_history[-100:]
    
    @property
    def average_relevance(self) -> float:
        """Calculate average relevance score"""
        return sum(self.relevance_history) / len(self.relevance_history) if self.relevance_history else 0.0


@dataclass
class LearningPattern:
    """Learned pattern for context relevance"""
    
    pattern_id: str
    pattern_type: str
    agent_types: Set[str]
    tdd_phases: Set[TDDState]
    feature_weights: Dict[str, float]
    success_rate: float
    usage_count: int = 0
    last_used: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 0.0
    
    def matches_context(self, agent_type: str, tdd_phase: Optional[TDDState]) -> bool:
        """Check if pattern matches given context"""
        agent_match = not self.agent_types or agent_type in self.agent_types
        phase_match = not self.tdd_phases or (tdd_phase and tdd_phase in self.tdd_phases)
        return agent_match and phase_match
    
    def calculate_relevance(self, features: Dict[str, float]) -> float:
        """Calculate relevance score using learned weights"""
        score = 0.0
        total_weight = 0.0
        
        for feature_name, weight in self.feature_weights.items():
            if feature_name in features:
                score += features[feature_name] * weight
                total_weight += abs(weight)
        
        return score / total_weight if total_weight > 0 else 0.0


class ContextLearningSystem:
    """
    Advanced learning system for context relevance improvement.
    
    Features:
    - Feature extraction from files and contexts
    - Pattern learning from usage feedback
    - Adaptive weight adjustment
    - Multi-strategy ensemble learning
    - Performance tracking and optimization
    """
    
    def __init__(
        self,
        project_path: str,
        learning_rate: float = 0.01,
        strategy: LearningStrategy = LearningStrategy.ENSEMBLE,
        feature_decay_days: int = 30,
        pattern_confidence_threshold: float = 0.7,
        enable_persistence: bool = True
    ):
        """
        Initialize the context learning system.
        
        Args:
            project_path: Path to the project
            learning_rate: Learning rate for weight updates
            strategy: Learning strategy to use
            feature_decay_days: Days after which to decay old features
            pattern_confidence_threshold: Minimum confidence for pattern usage
            enable_persistence: Whether to persist learned patterns
        """
        self.project_path = Path(project_path)
        self.learning_rate = learning_rate
        self.strategy = strategy
        self.feature_decay_days = feature_decay_days
        self.pattern_confidence_threshold = pattern_confidence_threshold
        self.enable_persistence = enable_persistence
        
        # Learning data storage
        self.file_features: Dict[str, FileFeatures] = {}
        self.learning_patterns: Dict[str, LearningPattern] = {}
        self.feedback_history: deque[LearningFeedback] = deque(maxlen=10000)
        
        # Feature extractors
        self.feature_extractors = self._initialize_feature_extractors()
        
        # Learning statistics
        self.total_predictions = 0
        self.accurate_predictions = 0
        self.learning_updates = 0
        self.pattern_discoveries = 0
        
        # Persistence paths
        if self.enable_persistence:
            self.persistence_dir = self.project_path / ".orch-state" / "context_learning"
            self.persistence_dir.mkdir(parents=True, exist_ok=True)
            self.patterns_file = self.persistence_dir / "patterns.pkl"
            self.features_file = self.persistence_dir / "features.pkl"
            self.feedback_file = self.persistence_dir / "feedback.json"
        
        logger.info(f"ContextLearningSystem initialized with strategy: {strategy.value}")
    
    async def initialize(self) -> None:
        """Initialize and load persisted learning data"""
        if self.enable_persistence:
            await self._load_persisted_data()
        
        # Initialize base patterns if none exist
        if not self.learning_patterns:
            await self._initialize_base_patterns()
        
        logger.info(f"Learning system initialized with {len(self.learning_patterns)} patterns")
    
    async def extract_file_features(self, file_path: str) -> Dict[str, float]:
        """
        Extract feature vector for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary of feature name to value
        """
        try:
            if file_path in self.file_features:
                features = self.file_features[file_path]
                
                # Check if features need updating
                file_modified = Path(file_path).stat().st_mtime
                if features.last_updated.timestamp() < file_modified:
                    features.features = await self._extract_features_internal(file_path)
                    features.last_updated = datetime.utcnow()
                
                return features.features
            else:
                # Extract new features
                feature_vector = await self._extract_features_internal(file_path)
                
                # Store features
                self.file_features[file_path] = FileFeatures(
                    file_path=file_path,
                    features=feature_vector,
                    last_updated=datetime.utcnow()
                )
                
                return feature_vector
                
        except Exception as e:
            logger.error(f"Error extracting features for {file_path}: {str(e)}")
            return {}
    
    async def predict_relevance(
        self,
        file_path: str,
        request: ContextRequest
    ) -> float:
        """
        Predict relevance score for a file given a context request.
        
        Args:
            file_path: Path to the file
            request: Context request
            
        Returns:
            Predicted relevance score (0.0 to 1.0)
        """
        self.total_predictions += 1
        
        try:
            # Extract file features
            features = await self.extract_file_features(file_path)
            if not features:
                return 0.0
            
            # Add context features
            context_features = self._extract_context_features(request)
            combined_features = {**features, **context_features}
            
            # Find applicable patterns
            applicable_patterns = self._find_applicable_patterns(
                request.agent_type,
                self._extract_tdd_phase(request.task)
            )
            
            if not applicable_patterns:
                # Use baseline relevance calculation
                return self._calculate_baseline_relevance(combined_features, request)
            
            # Calculate ensemble prediction
            if self.strategy == LearningStrategy.ENSEMBLE:
                return self._calculate_ensemble_relevance(combined_features, applicable_patterns)
            else:
                # Use best pattern
                best_pattern = max(applicable_patterns, key=lambda p: p.confidence)
                return best_pattern.calculate_relevance(combined_features)
                
        except Exception as e:
            logger.error(f"Error predicting relevance for {file_path}: {str(e)}")
            return 0.0
    
    async def record_feedback(
        self,
        context_id: str,
        agent_type: str,
        story_id: str,
        file_relevance_scores: Dict[str, float],
        feedback_type: str = "usage"
    ) -> None:
        """
        Record feedback for learning system.
        
        Args:
            context_id: Context identifier
            agent_type: Agent type
            story_id: Story identifier
            file_relevance_scores: Actual relevance scores for files
            feedback_type: Type of feedback
        """
        try:
            for file_path, actual_relevance in file_relevance_scores.items():
                # Get predicted relevance (if available)
                predicted_relevance = await self._get_cached_prediction(context_id, file_path)
                
                feedback = LearningFeedback(
                    context_id=context_id,
                    agent_type=agent_type,
                    story_id=story_id,
                    file_path=file_path,
                    predicted_relevance=predicted_relevance,
                    actual_relevance=actual_relevance,
                    feedback_type=feedback_type,
                    timestamp=datetime.utcnow()
                )
                
                self.feedback_history.append(feedback)
                
                # Update file features with relevance score
                if file_path in self.file_features:
                    self.file_features[file_path].add_relevance_score(actual_relevance)
                    self.file_features[file_path].access_count += 1
                
                # Check prediction accuracy
                if feedback.is_accurate():
                    self.accurate_predictions += 1
            
            # Trigger learning update
            await self._update_learning_patterns(agent_type, story_id)
            
        except Exception as e:
            logger.error(f"Error recording feedback: {str(e)}")
    
    async def update_patterns(self) -> int:
        """
        Update learning patterns based on recent feedback.
        
        Returns:
            Number of patterns updated
        """
        try:
            updated_count = 0
            
            # Analyze recent feedback for pattern updates
            recent_feedback = [
                f for f in self.feedback_history 
                if (datetime.utcnow() - f.timestamp).days <= 7
            ]
            
            if len(recent_feedback) < 10:  # Need sufficient data
                return 0
            
            # Group feedback by agent type and TDD phase
            feedback_groups = defaultdict(list)
            for feedback in recent_feedback:
                key = (feedback.agent_type, self._extract_phase_from_metadata(feedback))
                feedback_groups[key].append(feedback)
            
            # Update patterns for each group
            for (agent_type, tdd_phase), group_feedback in feedback_groups.items():
                if len(group_feedback) >= 5:  # Minimum feedback for pattern update
                    await self._update_pattern_for_group(agent_type, tdd_phase, group_feedback)
                    updated_count += 1
            
            self.learning_updates += updated_count
            
            # Persist updated patterns
            if self.enable_persistence and updated_count > 0:
                await self._persist_patterns()
            
            logger.info(f"Updated {updated_count} learning patterns")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating patterns: {str(e)}")
            return 0
    
    async def discover_new_patterns(self) -> int:
        """
        Discover new patterns from feedback data.
        
        Returns:
            Number of new patterns discovered
        """
        try:
            new_patterns = 0
            
            # Analyze feedback for emerging patterns
            pattern_candidates = await self._analyze_pattern_candidates()
            
            for candidate in pattern_candidates:
                if candidate["confidence"] >= self.pattern_confidence_threshold:
                    pattern = LearningPattern(
                        pattern_id=f"discovered_{len(self.learning_patterns)}_{int(datetime.utcnow().timestamp())}",
                        pattern_type="discovered",
                        agent_types=set(candidate["agent_types"]),
                        tdd_phases=set(candidate["tdd_phases"]),
                        feature_weights=candidate["feature_weights"],
                        success_rate=candidate["success_rate"],
                        confidence=candidate["confidence"]
                    )
                    
                    self.learning_patterns[pattern.pattern_id] = pattern
                    new_patterns += 1
                    self.pattern_discoveries += 1
            
            if new_patterns > 0:
                logger.info(f"Discovered {new_patterns} new patterns")
            
            return new_patterns
            
        except Exception as e:
            logger.error(f"Error discovering patterns: {str(e)}")
            return 0
    
    async def get_learning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics"""
        accuracy_rate = (
            self.accurate_predictions / self.total_predictions
            if self.total_predictions > 0 else 0.0
        )
        
        pattern_stats = {}
        for pattern_id, pattern in self.learning_patterns.items():
            pattern_stats[pattern_id] = {
                "type": pattern.pattern_type,
                "confidence": pattern.confidence,
                "success_rate": pattern.success_rate,
                "usage_count": pattern.usage_count,
                "agent_types": list(pattern.agent_types),
                "feature_count": len(pattern.feature_weights)
            }
        
        return {
            "total_predictions": self.total_predictions,
            "accurate_predictions": self.accurate_predictions,
            "accuracy_rate": accuracy_rate,
            "learning_updates": self.learning_updates,
            "pattern_discoveries": self.pattern_discoveries,
            "active_patterns": len(self.learning_patterns),
            "tracked_files": len(self.file_features),
            "feedback_samples": len(self.feedback_history),
            "pattern_details": pattern_stats
        }
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """Optimize learning system performance"""
        optimizations = {
            "patterns_pruned": 0,
            "features_cleaned": 0,
            "feedback_archived": 0
        }
        
        try:
            # Remove low-performing patterns
            patterns_to_remove = []
            for pattern_id, pattern in self.learning_patterns.items():
                if (pattern.usage_count > 10 and 
                    pattern.success_rate < 0.5 and 
                    pattern.confidence < 0.3):
                    patterns_to_remove.append(pattern_id)
            
            for pattern_id in patterns_to_remove:
                del self.learning_patterns[pattern_id]
                optimizations["patterns_pruned"] += 1
            
            # Clean old file features
            cutoff_date = datetime.utcnow() - timedelta(days=self.feature_decay_days)
            features_to_remove = []
            
            for file_path, features in self.file_features.items():
                if (features.last_updated < cutoff_date and 
                    features.access_count == 0):
                    features_to_remove.append(file_path)
            
            for file_path in features_to_remove:
                del self.file_features[file_path]
                optimizations["features_cleaned"] += 1
            
            # Archive old feedback
            old_feedback_count = len(self.feedback_history)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # Keep recent feedback
            recent_feedback = deque([
                f for f in self.feedback_history 
                if f.timestamp >= cutoff_date
            ], maxlen=10000)
            
            self.feedback_history = recent_feedback
            optimizations["feedback_archived"] = old_feedback_count - len(self.feedback_history)
            
            logger.info(f"Performance optimization completed: {optimizations}")
            return optimizations
            
        except Exception as e:
            logger.error(f"Error optimizing performance: {str(e)}")
            return optimizations
    
    # Private methods
    
    def _initialize_feature_extractors(self) -> Dict[str, Any]:
        """Initialize feature extraction functions"""
        return {
            FeatureType.FILE_PATH: self._extract_path_features,
            FeatureType.FILE_EXTENSION: self._extract_extension_features,
            FeatureType.FILE_SIZE: self._extract_size_features,
            FeatureType.LAST_MODIFIED: self._extract_modification_features,
            FeatureType.CONTENT_KEYWORDS: self._extract_content_features,
            FeatureType.DEPENDENCY_COUNT: self._extract_dependency_features
        }
    
    async def _extract_features_internal(self, file_path: str) -> Dict[str, float]:
        """Internal feature extraction implementation"""
        features = {}
        
        try:
            file_path_obj = Path(file_path)
            
            # Path-based features
            features.update(self._extract_path_features(file_path))
            features.update(self._extract_extension_features(file_path))
            
            if file_path_obj.exists():
                # File system features
                features.update(self._extract_size_features(file_path))
                features.update(self._extract_modification_features(file_path))
                
                # Content features (for text files)
                if file_path_obj.suffix in ['.py', '.js', '.ts', '.md', '.txt']:
                    features.update(await self._extract_content_features(file_path))
            
            return features
            
        except Exception as e:
            logger.warning(f"Error extracting features for {file_path}: {str(e)}")
            return {}
    
    def _extract_path_features(self, file_path: str) -> Dict[str, float]:
        """Extract features from file path"""
        path = Path(file_path)
        features = {}
        
        # Directory depth
        features["path_depth"] = len(path.parts)
        
        # Common directory patterns
        path_str = str(path).lower()
        features["is_test"] = 1.0 if "test" in path_str else 0.0
        features["is_src"] = 1.0 if any(p in path_str for p in ["src", "lib"]) else 0.0
        features["is_config"] = 1.0 if any(p in path_str for p in ["config", "conf"]) else 0.0
        features["is_docs"] = 1.0 if any(p in path_str for p in ["doc", "readme"]) else 0.0
        
        return features
    
    def _extract_extension_features(self, file_path: str) -> Dict[str, float]:
        """Extract features from file extension"""
        extension = Path(file_path).suffix.lower()
        
        features = {}
        features["is_python"] = 1.0 if extension == ".py" else 0.0
        features["is_javascript"] = 1.0 if extension in [".js", ".ts"] else 0.0
        features["is_markdown"] = 1.0 if extension == ".md" else 0.0
        features["is_config"] = 1.0 if extension in [".json", ".yaml", ".yml", ".toml"] else 0.0
        features["is_text"] = 1.0 if extension in [".txt", ".md", ".rst"] else 0.0
        
        return features
    
    def _extract_size_features(self, file_path: str) -> Dict[str, float]:
        """Extract features from file size"""
        try:
            size = Path(file_path).stat().st_size
            
            # Normalize size (log scale)
            size_normalized = np.log10(max(size, 1)) / 10.0  # Scale to roughly 0-1
            
            return {
                "file_size_normalized": min(size_normalized, 1.0),
                "is_small_file": 1.0 if size < 1000 else 0.0,
                "is_large_file": 1.0 if size > 100000 else 0.0
            }
        except OSError:
            return {"file_size_normalized": 0.0, "is_small_file": 0.0, "is_large_file": 0.0}
    
    def _extract_modification_features(self, file_path: str) -> Dict[str, float]:
        """Extract features from modification time"""
        try:
            mtime = Path(file_path).stat().st_mtime
            now = datetime.utcnow().timestamp()
            
            # Time since modification (normalized)
            days_since_modified = (now - mtime) / (24 * 3600)
            recency = max(0.0, 1.0 - days_since_modified / 30.0)  # 30 days max
            
            return {
                "file_recency": recency,
                "is_recently_modified": 1.0 if days_since_modified < 7 else 0.0
            }
        except OSError:
            return {"file_recency": 0.0, "is_recently_modified": 0.0}
    
    async def _extract_content_features(self, file_path: str) -> Dict[str, float]:
        """Extract features from file content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            features = {}
            content_lower = content.lower()
            
            # Keyword presence
            features["has_class"] = 1.0 if "class " in content_lower else 0.0
            features["has_function"] = 1.0 if any(kw in content_lower for kw in ["def ", "function "]) else 0.0
            features["has_import"] = 1.0 if any(kw in content_lower for kw in ["import ", "from ", "require("]) else 0.0
            features["has_test"] = 1.0 if any(kw in content_lower for kw in ["test_", "def test", "it("]) else 0.0
            
            # Content length
            features["content_length_normalized"] = min(len(content) / 10000.0, 1.0)
            features["line_count_normalized"] = min(len(content.split('\n')) / 1000.0, 1.0)
            
            return features
            
        except Exception:
            return {}
    
    def _extract_dependency_features(self, file_path: str) -> Dict[str, float]:
        """Extract dependency-based features"""
        # Placeholder for dependency analysis
        # This would integrate with the context index for dependency information
        return {
            "dependency_count_normalized": 0.5,  # Placeholder
            "is_core_module": 0.0
        }
    
    def _extract_context_features(self, request: ContextRequest) -> Dict[str, float]:
        """Extract features from context request"""
        features = {}
        
        # Agent type features
        features[f"agent_{request.agent_type.lower()}"] = 1.0
        
        # TDD phase features
        tdd_phase = self._extract_tdd_phase(request.task)
        if tdd_phase:
            features[f"phase_{tdd_phase.value.lower()}"] = 1.0
        
        # Story context
        features["story_context"] = hash(request.story_id) % 1000 / 1000.0  # Normalized hash
        
        return features
    
    def _extract_tdd_phase(self, task: Any) -> Optional[TDDState]:
        """Extract TDD phase from task"""
        if hasattr(task, 'current_state'):
            return task.current_state
        elif isinstance(task, dict) and 'current_state' in task:
            return task['current_state']
        return None
    
    def _extract_phase_from_metadata(self, feedback: LearningFeedback) -> Optional[TDDState]:
        """Extract TDD phase from feedback metadata"""
        return feedback.metadata.get('tdd_phase')
    
    def _find_applicable_patterns(
        self,
        agent_type: str,
        tdd_phase: Optional[TDDState]
    ) -> List[LearningPattern]:
        """Find patterns applicable to the given context"""
        applicable = []
        
        for pattern in self.learning_patterns.values():
            if (pattern.matches_context(agent_type, tdd_phase) and
                pattern.confidence >= self.pattern_confidence_threshold):
                applicable.append(pattern)
        
        return sorted(applicable, key=lambda p: p.confidence, reverse=True)
    
    def _calculate_baseline_relevance(
        self,
        features: Dict[str, float],
        request: ContextRequest
    ) -> float:
        """Calculate baseline relevance when no patterns available"""
        score = 0.0
        
        # Simple heuristic scoring
        if request.agent_type == "CodeAgent":
            score += features.get("is_python", 0) * 0.3
            score += features.get("has_function", 0) * 0.2
            score += features.get("has_class", 0) * 0.2
        elif request.agent_type == "QAAgent":
            score += features.get("is_test", 0) * 0.4
            score += features.get("has_test", 0) * 0.3
        elif request.agent_type == "DesignAgent":
            score += features.get("is_markdown", 0) * 0.3
            score += features.get("is_docs", 0) * 0.2
        
        # Recency bonus
        score += features.get("file_recency", 0) * 0.1
        
        return min(score, 1.0)
    
    def _calculate_ensemble_relevance(
        self,
        features: Dict[str, float],
        patterns: List[LearningPattern]
    ) -> float:
        """Calculate ensemble relevance from multiple patterns"""
        if not patterns:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for pattern in patterns:
            relevance = pattern.calculate_relevance(features)
            weight = pattern.confidence * pattern.success_rate
            
            weighted_sum += relevance * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    async def _get_cached_prediction(self, context_id: str, file_path: str) -> float:
        """Get cached prediction for feedback comparison"""
        # This would be implemented with a prediction cache
        return 0.5  # Placeholder
    
    async def _update_learning_patterns(self, agent_type: str, story_id: str) -> None:
        """Update learning patterns based on recent feedback"""
        # Find recent feedback for this context
        recent_feedback = [
            f for f in self.feedback_history
            if (f.agent_type == agent_type and
                f.story_id == story_id and
                (datetime.utcnow() - f.timestamp).hours < 24)
        ]
        
        if len(recent_feedback) < 5:
            return
        
        # Update pattern weights based on feedback
        for pattern in self.learning_patterns.values():
            if pattern.matches_context(agent_type, None):
                await self._adjust_pattern_weights(pattern, recent_feedback)
    
    async def _adjust_pattern_weights(
        self,
        pattern: LearningPattern,
        feedback: List[LearningFeedback]
    ) -> None:
        """Adjust pattern weights based on feedback"""
        for fb in feedback:
            if fb.relevance_error > 0:
                # Extract features for this file
                features = await self.extract_file_features(fb.file_path)
                
                # Calculate gradient
                prediction_error = fb.predicted_relevance - fb.actual_relevance
                
                # Update weights
                for feature_name, feature_value in features.items():
                    if feature_name in pattern.feature_weights:
                        gradient = prediction_error * feature_value
                        pattern.feature_weights[feature_name] -= self.learning_rate * gradient
                
                pattern.usage_count += 1
        
        # Update success rate
        accurate_count = sum(1 for fb in feedback if fb.is_accurate())
        pattern.success_rate = accurate_count / len(feedback)
        pattern.confidence = min(pattern.success_rate * (pattern.usage_count / 100.0), 1.0)
    
    async def _update_pattern_for_group(
        self,
        agent_type: str,
        tdd_phase: Optional[TDDState],
        feedback_list: List[LearningFeedback]
    ) -> None:
        """Update pattern for a specific agent/phase group"""
        # Find or create pattern for this group
        pattern_id = f"{agent_type}_{tdd_phase.value if tdd_phase else 'general'}"
        
        if pattern_id not in self.learning_patterns:
            self.learning_patterns[pattern_id] = LearningPattern(
                pattern_id=pattern_id,
                pattern_type="adaptive",
                agent_types={agent_type},
                tdd_phases={tdd_phase} if tdd_phase else set(),
                feature_weights={},
                success_rate=0.0
            )
        
        pattern = self.learning_patterns[pattern_id]
        await self._adjust_pattern_weights(pattern, feedback_list)
    
    async def _analyze_pattern_candidates(self) -> List[Dict[str, Any]]:
        """Analyze feedback for potential new patterns"""
        candidates = []
        
        # Group feedback by various criteria
        groups = defaultdict(list)
        
        for feedback in self.feedback_history:
            # Group by agent type and accuracy
            if feedback.is_accurate():
                key = (feedback.agent_type, "accurate")
                groups[key].append(feedback)
        
        # Analyze each group for pattern potential
        for (agent_type, accuracy), group_feedback in groups.items():
            if len(group_feedback) >= 10:  # Minimum size for pattern
                candidate = await self._analyze_feedback_group(agent_type, group_feedback)
                if candidate:
                    candidates.append(candidate)
        
        return candidates
    
    async def _analyze_feedback_group(
        self,
        agent_type: str,
        feedback_list: List[LearningFeedback]
    ) -> Optional[Dict[str, Any]]:
        """Analyze a group of feedback for pattern extraction"""
        try:
            # Calculate feature importance
            feature_weights = defaultdict(float)
            feature_counts = defaultdict(int)
            
            for feedback in feedback_list:
                features = await self.extract_file_features(feedback.file_path)
                
                for feature_name, feature_value in features.items():
                    feature_weights[feature_name] += feature_value * feedback.actual_relevance
                    feature_counts[feature_name] += 1
            
            # Normalize weights
            normalized_weights = {}
            for feature_name, total_weight in feature_weights.items():
                if feature_counts[feature_name] > 0:
                    normalized_weights[feature_name] = total_weight / feature_counts[feature_name]
            
            # Calculate success rate
            success_rate = sum(1 for fb in feedback_list if fb.is_accurate()) / len(feedback_list)
            
            # Extract TDD phases
            tdd_phases = set()
            for feedback in feedback_list:
                phase = self._extract_phase_from_metadata(feedback)
                if phase:
                    tdd_phases.add(phase)
            
            return {
                "agent_types": [agent_type],
                "tdd_phases": list(tdd_phases),
                "feature_weights": normalized_weights,
                "success_rate": success_rate,
                "confidence": min(success_rate * (len(feedback_list) / 50.0), 1.0),
                "sample_count": len(feedback_list)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing feedback group: {str(e)}")
            return None
    
    async def _initialize_base_patterns(self) -> None:
        """Initialize base patterns for different agent types"""
        base_patterns = [
            {
                "pattern_id": "code_agent_base",
                "agent_types": {"CodeAgent"},
                "feature_weights": {
                    "is_python": 0.4,
                    "has_function": 0.3,
                    "has_class": 0.2,
                    "file_recency": 0.1
                }
            },
            {
                "pattern_id": "qa_agent_base",
                "agent_types": {"QAAgent"},
                "feature_weights": {
                    "is_test": 0.5,
                    "has_test": 0.3,
                    "is_python": 0.2
                }
            },
            {
                "pattern_id": "design_agent_base",
                "agent_types": {"DesignAgent"},
                "feature_weights": {
                    "is_markdown": 0.4,
                    "is_docs": 0.3,
                    "is_config": 0.2,
                    "file_recency": 0.1
                }
            }
        ]
        
        for pattern_data in base_patterns:
            pattern = LearningPattern(
                pattern_id=pattern_data["pattern_id"],
                pattern_type="base",
                agent_types=pattern_data["agent_types"],
                tdd_phases=set(),
                feature_weights=pattern_data["feature_weights"],
                success_rate=0.8,  # Base success rate
                confidence=0.6  # Base confidence
            )
            
            self.learning_patterns[pattern.pattern_id] = pattern
    
    async def _load_persisted_data(self) -> None:
        """Load persisted learning data"""
        try:
            # Load patterns
            if self.patterns_file.exists():
                with open(self.patterns_file, 'rb') as f:
                    self.learning_patterns = pickle.load(f)
            
            # Load features
            if self.features_file.exists():
                with open(self.features_file, 'rb') as f:
                    self.file_features = pickle.load(f)
            
            # Load feedback
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r') as f:
                    feedback_data = json.load(f)
                    for fb_data in feedback_data:
                        feedback = LearningFeedback(
                            context_id=fb_data['context_id'],
                            agent_type=fb_data['agent_type'],
                            story_id=fb_data['story_id'],
                            file_path=fb_data['file_path'],
                            predicted_relevance=fb_data['predicted_relevance'],
                            actual_relevance=fb_data['actual_relevance'],
                            feedback_type=fb_data['feedback_type'],
                            timestamp=datetime.fromisoformat(fb_data['timestamp']),
                            metadata=fb_data.get('metadata', {})
                        )
                        self.feedback_history.append(feedback)
            
            logger.info("Loaded persisted learning data")
            
        except Exception as e:
            logger.warning(f"Error loading persisted data: {str(e)}")
    
    async def _persist_patterns(self) -> None:
        """Persist learning patterns to disk"""
        try:
            if self.enable_persistence:
                # Persist patterns
                with open(self.patterns_file, 'wb') as f:
                    pickle.dump(self.learning_patterns, f)
                
                # Persist features
                with open(self.features_file, 'wb') as f:
                    pickle.dump(self.file_features, f)
                
                # Persist recent feedback
                recent_feedback = [
                    {
                        'context_id': fb.context_id,
                        'agent_type': fb.agent_type,
                        'story_id': fb.story_id,
                        'file_path': fb.file_path,
                        'predicted_relevance': fb.predicted_relevance,
                        'actual_relevance': fb.actual_relevance,
                        'feedback_type': fb.feedback_type,
                        'timestamp': fb.timestamp.isoformat(),
                        'metadata': fb.metadata
                    }
                    for fb in list(self.feedback_history)[-1000:]  # Keep last 1000
                ]
                
                with open(self.feedback_file, 'w') as f:
                    json.dump(recent_feedback, f, indent=2)
                
                logger.debug("Persisted learning data")
                
        except Exception as e:
            logger.error(f"Error persisting learning data: {str(e)}")