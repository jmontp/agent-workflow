"""
Cross-Project Intelligence and Knowledge Sharing System

Advanced system for analyzing patterns, sharing insights, and learning
across multiple AI-assisted development projects to improve overall efficiency.
"""

import asyncio
import logging
import json
import hashlib
import statistics
from typing import Dict, List, Optional, Any, Set, Tuple, Pattern
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import re
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns that can be identified"""
    CODE_PATTERN = "code_pattern"           # Common code structures
    WORKFLOW_PATTERN = "workflow_pattern"   # TDD workflow patterns
    ERROR_PATTERN = "error_pattern"         # Common error patterns
    DEPENDENCY_PATTERN = "dependency_pattern" # Dependency usage patterns
    PERFORMANCE_PATTERN = "performance_pattern" # Performance optimization patterns
    TESTING_PATTERN = "testing_pattern"     # Testing strategy patterns
    ARCHITECTURE_PATTERN = "architecture_pattern" # Architectural patterns


class InsightType(Enum):
    """Types of insights that can be generated"""
    OPTIMIZATION = "optimization"           # Performance optimization opportunities
    BEST_PRACTICE = "best_practice"        # Recommended best practices
    ANTI_PATTERN = "anti_pattern"          # Patterns to avoid
    REUSABLE_COMPONENT = "reusable_component" # Components that could be reused
    KNOWLEDGE_TRANSFER = "knowledge_transfer" # Knowledge from one project to another
    RISK_MITIGATION = "risk_mitigation"    # Risk mitigation strategies


@dataclass
class ProjectPattern:
    """A pattern identified within a project"""
    pattern_id: str
    pattern_type: PatternType
    project_name: str
    description: str
    code_examples: List[str] = field(default_factory=list)
    frequency: int = 1
    confidence: float = 0.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    identified_at: datetime = field(default_factory=datetime.utcnow)
    
    # Context information
    file_paths: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    
    # Impact assessment
    impact_score: float = 0.0  # Potential impact if applied elsewhere
    effort_score: float = 0.0  # Effort required to implement
    
    def calculate_hash(self) -> str:
        """Calculate unique hash for pattern matching"""
        content = f"{self.pattern_type.value}:{self.description}:{':'.join(sorted(self.code_examples))}"
        return hashlib.md5(content.encode()).hexdigest()


@dataclass
class CrossProjectInsight:
    """An insight derived from cross-project analysis"""
    insight_id: str
    insight_type: InsightType
    title: str
    description: str
    affected_projects: List[str] = field(default_factory=list)
    source_patterns: List[str] = field(default_factory=list)  # Pattern IDs
    
    # Actionable information
    recommendations: List[str] = field(default_factory=list)
    implementation_notes: str = ""
    estimated_benefit: str = ""  # High/Medium/Low
    
    # Tracking
    confidence: float = 0.0
    priority: int = 3  # 1=high, 2=medium, 3=low
    status: str = "new"  # new, reviewed, implementing, implemented, rejected
    generated_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None
    
    # Feedback and validation
    feedback_score: Optional[float] = None  # User feedback on usefulness
    implementation_success: Optional[bool] = None


@dataclass
class KnowledgeTransfer:
    """Knowledge transfer recommendation between projects"""
    transfer_id: str
    source_project: str
    target_project: str
    knowledge_type: str  # "pattern", "component", "practice", "solution"
    title: str
    description: str
    
    # Transfer details
    source_references: List[str] = field(default_factory=list)  # File paths, functions, etc.
    transfer_instructions: str = ""
    estimated_effort: str = "medium"  # low, medium, high
    potential_benefit: str = "medium"  # low, medium, high
    
    # Prerequisites and dependencies
    prerequisites: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, approved, in_progress, completed, rejected
    transferred_by: Optional[str] = None
    completed_at: Optional[datetime] = None


@dataclass
class ProjectAnalytics:
    """Analytics data for a project"""
    project_name: str
    
    # Code metrics
    total_files: int = 0
    total_lines_of_code: int = 0
    code_complexity_score: float = 0.0
    test_coverage: float = 0.0
    
    # TDD metrics
    tdd_cycles_completed: int = 0
    average_cycle_time: float = 0.0
    test_first_ratio: float = 0.0  # Percentage of tests written before code
    refactoring_frequency: float = 0.0
    
    # Quality metrics
    error_rate: float = 0.0
    bug_density: float = 0.0
    technical_debt_score: float = 0.0
    
    # Performance metrics
    build_time: float = 0.0
    test_execution_time: float = 0.0
    deployment_frequency: float = 0.0
    
    # Team metrics
    commits_per_day: float = 0.0
    active_contributors: int = 0
    knowledge_sharing_score: float = 0.0
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.utcnow)
    data_sources: List[str] = field(default_factory=list)


class CrossProjectIntelligence:
    """
    Cross-project intelligence system for pattern recognition,
    insight generation, and knowledge sharing across projects.
    """
    
    def __init__(self, storage_path: str = ".orch-global/intelligence"):
        """
        Initialize cross-project intelligence system.
        
        Args:
            storage_path: Path to store intelligence data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Pattern and insight storage
        self.patterns: Dict[str, ProjectPattern] = {}
        self.insights: Dict[str, CrossProjectInsight] = {}
        self.knowledge_transfers: Dict[str, KnowledgeTransfer] = {}
        self.project_analytics: Dict[str, ProjectAnalytics] = {}
        
        # Pattern matching and analysis
        self.pattern_matchers: Dict[PatternType, callable] = {}
        self.insight_generators: Dict[InsightType, callable] = {}
        
        # Machine learning and optimization
        self.learning_data: Dict[str, Any] = {}
        self.optimization_history: List[Dict[str, Any]] = []
        
        # Background processing
        self._analysis_task: Optional[asyncio.Task] = None
        self._learning_task: Optional[asyncio.Task] = None
        
        # Setup pattern matchers and insight generators
        self._setup_pattern_matchers()
        self._setup_insight_generators()
        
        # Load existing data
        self._load_intelligence_data()
        
        logger.info("Cross-project intelligence system initialized")
    
    async def start(self) -> None:
        """Start the intelligence system"""
        self._analysis_task = asyncio.create_task(self._analysis_loop())
        self._learning_task = asyncio.create_task(self._learning_loop())
        logger.info("Cross-project intelligence system started")
    
    async def stop(self) -> None:
        """Stop the intelligence system"""
        tasks = [self._analysis_task, self._learning_task]
        for task in tasks:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Save data before stopping
        self._save_intelligence_data()
        logger.info("Cross-project intelligence system stopped")
    
    async def analyze_project(self, project_name: str, project_data: Dict[str, Any]) -> List[ProjectPattern]:
        """
        Analyze a project for patterns and insights.
        
        Args:
            project_name: Name of the project
            project_data: Project data including code, metrics, etc.
            
        Returns:
            List of identified patterns
        """
        identified_patterns = []
        
        # Extract project analytics
        analytics = await self._extract_project_analytics(project_name, project_data)
        self.project_analytics[project_name] = analytics
        
        # Run pattern matchers
        for pattern_type, matcher in self.pattern_matchers.items():
            try:
                patterns = await matcher(project_name, project_data, analytics)
                for pattern in patterns:
                    pattern.pattern_id = f"{project_name}_{pattern_type.value}_{len(identified_patterns)}"
                    self.patterns[pattern.pattern_id] = pattern
                    identified_patterns.append(pattern)
            except Exception as e:
                logger.error(f"Pattern matcher {pattern_type.value} failed: {str(e)}")
        
        # Generate insights based on new patterns
        await self._generate_insights_for_project(project_name, identified_patterns)
        
        logger.info(f"Analyzed project {project_name}: {len(identified_patterns)} patterns identified")
        return identified_patterns
    
    async def generate_cross_project_insights(self) -> List[CrossProjectInsight]:
        """Generate insights by analyzing patterns across all projects"""
        new_insights = []
        
        # Group patterns by type for cross-project analysis
        patterns_by_type = defaultdict(list)
        for pattern in self.patterns.values():
            patterns_by_type[pattern.pattern_type].append(pattern)
        
        # Run insight generators
        for insight_type, generator in self.insight_generators.items():
            try:
                insights = await generator(patterns_by_type, self.project_analytics)
                for insight in insights:
                    insight.insight_id = f"cross_{insight_type.value}_{len(self.insights)}"
                    self.insights[insight.insight_id] = insight
                    new_insights.append(insight)
            except Exception as e:
                logger.error(f"Insight generator {insight_type.value} failed: {str(e)}")
        
        logger.info(f"Generated {len(new_insights)} cross-project insights")
        return new_insights
    
    async def recommend_knowledge_transfers(self) -> List[KnowledgeTransfer]:
        """Recommend knowledge transfers between projects"""
        recommendations = []
        
        # Find similar patterns across projects
        pattern_groups = self._group_similar_patterns()
        
        for pattern_hash, patterns in pattern_groups.items():
            if len(patterns) <= 1:
                continue  # Skip patterns that only exist in one project
            
            # Find projects that could benefit from each other's implementations
            for i, source_pattern in enumerate(patterns):
                for j, target_pattern in enumerate(patterns):
                    if i >= j or source_pattern.project_name == target_pattern.project_name:
                        continue
                    
                    # Check if source has better implementation
                    if self._should_recommend_transfer(source_pattern, target_pattern):
                        transfer = self._create_knowledge_transfer(source_pattern, target_pattern)
                        self.knowledge_transfers[transfer.transfer_id] = transfer
                        recommendations.append(transfer)
        
        logger.info(f"Generated {len(recommendations)} knowledge transfer recommendations")
        return recommendations
    
    def get_project_insights(self, project_name: str) -> List[CrossProjectInsight]:
        """Get insights relevant to a specific project"""
        return [
            insight for insight in self.insights.values()
            if project_name in insight.affected_projects
        ]
    
    def get_pattern_summary(self) -> Dict[str, Any]:
        """Get summary of identified patterns"""
        pattern_counts = Counter(p.pattern_type for p in self.patterns.values())
        project_counts = Counter(p.project_name for p in self.patterns.values())
        
        return {
            "total_patterns": len(self.patterns),
            "patterns_by_type": dict(pattern_counts),
            "patterns_by_project": dict(project_counts),
            "average_confidence": statistics.mean([p.confidence for p in self.patterns.values()]) if self.patterns else 0.0,
            "high_impact_patterns": len([p for p in self.patterns.values() if p.impact_score > 0.7])
        }
    
    def get_insight_summary(self) -> Dict[str, Any]:
        """Get summary of generated insights"""
        insight_counts = Counter(i.insight_type for i in self.insights.values())
        status_counts = Counter(i.status for i in self.insights.values())
        
        return {
            "total_insights": len(self.insights),
            "insights_by_type": dict(insight_counts),
            "insights_by_status": dict(status_counts),
            "average_confidence": statistics.mean([i.confidence for i in self.insights.values()]) if self.insights else 0.0,
            "high_priority_insights": len([i for i in self.insights.values() if i.priority <= 2])
        }
    
    def get_knowledge_transfer_summary(self) -> Dict[str, Any]:
        """Get summary of knowledge transfer recommendations"""
        status_counts = Counter(kt.status for kt in self.knowledge_transfers.values())
        benefit_counts = Counter(kt.potential_benefit for kt in self.knowledge_transfers.values())
        
        return {
            "total_transfers": len(self.knowledge_transfers),
            "transfers_by_status": dict(status_counts),
            "transfers_by_benefit": dict(benefit_counts),
            "pending_transfers": len([kt for kt in self.knowledge_transfers.values() if kt.status == "pending"]),
            "completed_transfers": len([kt for kt in self.knowledge_transfers.values() if kt.status == "completed"])
        }
    
    async def update_insight_feedback(self, insight_id: str, feedback_score: float, implementation_success: Optional[bool] = None):
        """Update feedback for an insight"""
        if insight_id in self.insights:
            insight = self.insights[insight_id]
            insight.feedback_score = feedback_score
            if implementation_success is not None:
                insight.implementation_success = implementation_success
                if implementation_success:
                    insight.implemented_at = datetime.utcnow()
                    insight.status = "implemented"
    
    # Private methods
    
    def _setup_pattern_matchers(self):
        """Setup pattern matchers for different pattern types"""
        
        async def code_pattern_matcher(project_name: str, project_data: Dict[str, Any], analytics: ProjectAnalytics) -> List[ProjectPattern]:
            """Identify common code patterns"""
            patterns = []
            
            # Look for common design patterns in code
            code_files = project_data.get("code_files", {})
            
            # Singleton pattern detection
            singleton_patterns = []
            for file_path, content in code_files.items():
                if "class " in content and "_instance" in content and "__new__" in content:
                    singleton_patterns.append(file_path)
            
            if singleton_patterns:
                pattern = ProjectPattern(
                    pattern_id="",
                    pattern_type=PatternType.CODE_PATTERN,
                    project_name=project_name,
                    description="Singleton pattern implementation",
                    file_paths=singleton_patterns,
                    frequency=len(singleton_patterns),
                    confidence=0.8,
                    impact_score=0.6
                )
                patterns.append(pattern)
            
            return patterns
        
        async def workflow_pattern_matcher(project_name: str, project_data: Dict[str, Any], analytics: ProjectAnalytics) -> List[ProjectPattern]:
            """Identify TDD workflow patterns"""
            patterns = []
            
            # Analyze TDD cycle patterns
            tdd_data = project_data.get("tdd_cycles", [])
            
            if analytics.test_first_ratio > 0.8:
                pattern = ProjectPattern(
                    pattern_id="",
                    pattern_type=PatternType.WORKFLOW_PATTERN,
                    project_name=project_name,
                    description="High test-first adherence",
                    confidence=0.9,
                    impact_score=0.8,
                    metadata={"test_first_ratio": analytics.test_first_ratio}
                )
                patterns.append(pattern)
            
            return patterns
        
        async def error_pattern_matcher(project_name: str, project_data: Dict[str, Any], analytics: ProjectAnalytics) -> List[ProjectPattern]:
            """Identify common error patterns"""
            patterns = []
            
            # Analyze error logs and exception patterns
            error_logs = project_data.get("error_logs", [])
            
            # Group similar errors
            error_groups = defaultdict(int)
            for error in error_logs:
                error_type = error.get("type", "unknown")
                error_groups[error_type] += 1
            
            # Identify frequent error patterns
            for error_type, count in error_groups.items():
                if count > 5:  # Threshold for pattern recognition
                    pattern = ProjectPattern(
                        pattern_id="",
                        pattern_type=PatternType.ERROR_PATTERN,
                        project_name=project_name,
                        description=f"Frequent {error_type} errors",
                        frequency=count,
                        confidence=0.7,
                        metadata={"error_type": error_type, "count": count}
                    )
                    patterns.append(pattern)
            
            return patterns
        
        # Register pattern matchers
        self.pattern_matchers = {
            PatternType.CODE_PATTERN: code_pattern_matcher,
            PatternType.WORKFLOW_PATTERN: workflow_pattern_matcher,
            PatternType.ERROR_PATTERN: error_pattern_matcher
        }
    
    def _setup_insight_generators(self):
        """Setup insight generators for different insight types"""
        
        async def optimization_generator(patterns_by_type: Dict[PatternType, List[ProjectPattern]], analytics: Dict[str, ProjectAnalytics]) -> List[CrossProjectInsight]:
            """Generate optimization insights"""
            insights = []
            
            # Find projects with performance issues that could benefit from patterns in other projects
            code_patterns = patterns_by_type.get(PatternType.CODE_PATTERN, [])
            
            for project_name, project_analytics in analytics.items():
                if project_analytics.build_time > 60:  # Slow build time
                    # Look for optimization patterns in other projects
                    optimization_patterns = [p for p in code_patterns if p.project_name != project_name and "optimization" in p.description.lower()]
                    
                    if optimization_patterns:
                        insight = CrossProjectInsight(
                            insight_id="",
                            insight_type=InsightType.OPTIMIZATION,
                            title=f"Build Time Optimization for {project_name}",
                            description=f"Project {project_name} has slow build times ({project_analytics.build_time}s). Consider applying optimization patterns from other projects.",
                            affected_projects=[project_name],
                            source_patterns=[p.pattern_id for p in optimization_patterns],
                            recommendations=[
                                "Review build optimization patterns from similar projects",
                                "Consider implementing caching strategies",
                                "Analyze dependency structure for optimization opportunities"
                            ],
                            confidence=0.7,
                            priority=2
                        )
                        insights.append(insight)
            
            return insights
        
        async def best_practice_generator(patterns_by_type: Dict[PatternType, List[ProjectPattern]], analytics: Dict[str, ProjectAnalytics]) -> List[CrossProjectInsight]:
            """Generate best practice insights"""
            insights = []
            
            # Find patterns that appear in multiple high-performing projects
            workflow_patterns = patterns_by_type.get(PatternType.WORKFLOW_PATTERN, [])
            
            # Group patterns by description to find common practices
            pattern_groups = defaultdict(list)
            for pattern in workflow_patterns:
                pattern_groups[pattern.description].append(pattern)
            
            for description, patterns in pattern_groups.items():
                if len(patterns) >= 3:  # Pattern appears in 3+ projects
                    high_performing_projects = [
                        p.project_name for p in patterns
                        if analytics.get(p.project_name) and analytics[p.project_name].test_coverage > 0.8
                    ]
                    
                    if len(high_performing_projects) >= 2:
                        all_projects = list(analytics.keys())
                        affected_projects = [p for p in all_projects if p not in high_performing_projects]
                        
                        insight = CrossProjectInsight(
                            insight_id="",
                            insight_type=InsightType.BEST_PRACTICE,
                            title=f"Best Practice: {description}",
                            description=f"This practice is consistently used in high-performing projects: {', '.join(high_performing_projects)}",
                            affected_projects=affected_projects,
                            source_patterns=[p.pattern_id for p in patterns],
                            recommendations=[
                                f"Consider adopting '{description}' practice",
                                "Review implementation in high-performing projects",
                                "Measure impact after implementation"
                            ],
                            confidence=0.8,
                            priority=2
                        )
                        insights.append(insight)
            
            return insights
        
        # Register insight generators
        self.insight_generators = {
            InsightType.OPTIMIZATION: optimization_generator,
            InsightType.BEST_PRACTICE: best_practice_generator
        }
    
    async def _extract_project_analytics(self, project_name: str, project_data: Dict[str, Any]) -> ProjectAnalytics:
        """Extract analytics from project data"""
        analytics = ProjectAnalytics(project_name=project_name)
        
        # Extract code metrics
        code_files = project_data.get("code_files", {})
        analytics.total_files = len(code_files)
        analytics.total_lines_of_code = sum(len(content.split('\n')) for content in code_files.values())
        
        # Extract TDD metrics
        tdd_cycles = project_data.get("tdd_cycles", [])
        analytics.tdd_cycles_completed = len(tdd_cycles)
        
        if tdd_cycles:
            cycle_times = [cycle.get("duration", 0) for cycle in tdd_cycles]
            analytics.average_cycle_time = statistics.mean(cycle_times)
            
            test_first_cycles = [cycle for cycle in tdd_cycles if cycle.get("test_first", False)]
            analytics.test_first_ratio = len(test_first_cycles) / len(tdd_cycles)
        
        # Extract quality metrics from project data
        quality_data = project_data.get("quality_metrics", {})
        analytics.test_coverage = quality_data.get("test_coverage", 0.0)
        analytics.error_rate = quality_data.get("error_rate", 0.0)
        analytics.technical_debt_score = quality_data.get("technical_debt", 0.0)
        
        # Extract performance metrics
        perf_data = project_data.get("performance_metrics", {})
        analytics.build_time = perf_data.get("build_time", 0.0)
        analytics.test_execution_time = perf_data.get("test_time", 0.0)
        
        return analytics
    
    async def _generate_insights_for_project(self, project_name: str, patterns: List[ProjectPattern]):
        """Generate insights specific to a project based on its patterns"""
        # This would analyze project-specific patterns and generate targeted insights
        pass
    
    def _group_similar_patterns(self) -> Dict[str, List[ProjectPattern]]:
        """Group similar patterns across projects"""
        pattern_groups = defaultdict(list)
        
        for pattern in self.patterns.values():
            pattern_hash = pattern.calculate_hash()
            pattern_groups[pattern_hash].append(pattern)
        
        return pattern_groups
    
    def _should_recommend_transfer(self, source_pattern: ProjectPattern, target_pattern: ProjectPattern) -> bool:
        """Determine if knowledge transfer should be recommended"""
        # Check if source pattern has better metrics
        if source_pattern.confidence > target_pattern.confidence + 0.1:
            return True
        
        if source_pattern.impact_score > target_pattern.impact_score + 0.1:
            return True
        
        # Check if source project has better overall metrics
        source_analytics = self.project_analytics.get(source_pattern.project_name)
        target_analytics = self.project_analytics.get(target_pattern.project_name)
        
        if source_analytics and target_analytics:
            if (source_analytics.test_coverage > target_analytics.test_coverage + 0.1 or
                source_analytics.error_rate < target_analytics.error_rate - 0.05):
                return True
        
        return False
    
    def _create_knowledge_transfer(self, source_pattern: ProjectPattern, target_pattern: ProjectPattern) -> KnowledgeTransfer:
        """Create a knowledge transfer recommendation"""
        transfer_id = f"transfer_{source_pattern.project_name}_{target_pattern.project_name}_{len(self.knowledge_transfers)}"
        
        return KnowledgeTransfer(
            transfer_id=transfer_id,
            source_project=source_pattern.project_name,
            target_project=target_pattern.project_name,
            knowledge_type="pattern",
            title=f"Transfer {source_pattern.pattern_type.value} pattern",
            description=f"Transfer improved implementation of '{source_pattern.description}' from {source_pattern.project_name} to {target_pattern.project_name}",
            source_references=source_pattern.file_paths,
            transfer_instructions=f"Review the implementation in {source_pattern.project_name} and adapt it for {target_pattern.project_name}",
            estimated_effort="medium",
            potential_benefit="medium"
        )
    
    async def _analysis_loop(self):
        """Background analysis loop"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run analysis every hour
                
                # Generate cross-project insights
                await self.generate_cross_project_insights()
                
                # Recommend knowledge transfers
                await self.recommend_knowledge_transfers()
                
                # Save updated data
                self._save_intelligence_data()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Analysis loop error: {str(e)}")
    
    async def _learning_loop(self):
        """Background learning and optimization loop"""
        while True:
            try:
                await asyncio.sleep(7200)  # Run learning every 2 hours
                
                # Update learning models based on feedback
                await self._update_learning_models()
                
                # Optimize pattern matching algorithms
                await self._optimize_pattern_matching()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Learning loop error: {str(e)}")
    
    async def _update_learning_models(self):
        """Update learning models based on feedback"""
        # This would implement machine learning model updates
        # based on user feedback and implementation success
        pass
    
    async def _optimize_pattern_matching(self):
        """Optimize pattern matching algorithms"""
        # This would optimize pattern matching based on historical performance
        pass
    
    def _load_intelligence_data(self):
        """Load intelligence data from storage"""
        try:
            # Load patterns
            patterns_file = self.storage_path / "patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                    for pattern_id, pattern_dict in patterns_data.items():
                        # Convert datetime strings back to datetime objects
                        if 'identified_at' in pattern_dict:
                            pattern_dict['identified_at'] = datetime.fromisoformat(pattern_dict['identified_at'])
                        pattern_dict['pattern_type'] = PatternType(pattern_dict['pattern_type'])
                        self.patterns[pattern_id] = ProjectPattern(**pattern_dict)
            
            # Load insights
            insights_file = self.storage_path / "insights.json"
            if insights_file.exists():
                with open(insights_file, 'r') as f:
                    insights_data = json.load(f)
                    for insight_id, insight_dict in insights_data.items():
                        # Convert datetime strings back to datetime objects
                        for date_field in ['generated_at', 'reviewed_at', 'implemented_at']:
                            if insight_dict.get(date_field):
                                insight_dict[date_field] = datetime.fromisoformat(insight_dict[date_field])
                        insight_dict['insight_type'] = InsightType(insight_dict['insight_type'])
                        self.insights[insight_id] = CrossProjectInsight(**insight_dict)
            
            # Load knowledge transfers
            transfers_file = self.storage_path / "knowledge_transfers.json"
            if transfers_file.exists():
                with open(transfers_file, 'r') as f:
                    transfers_data = json.load(f)
                    for transfer_id, transfer_dict in transfers_data.items():
                        # Convert datetime strings back to datetime objects
                        for date_field in ['created_at', 'completed_at']:
                            if transfer_dict.get(date_field):
                                transfer_dict[date_field] = datetime.fromisoformat(transfer_dict[date_field])
                        self.knowledge_transfers[transfer_id] = KnowledgeTransfer(**transfer_dict)
            
            logger.info(f"Loaded intelligence data: {len(self.patterns)} patterns, {len(self.insights)} insights, {len(self.knowledge_transfers)} transfers")
            
        except Exception as e:
            logger.error(f"Failed to load intelligence data: {str(e)}")
    
    def _save_intelligence_data(self):
        """Save intelligence data to storage"""
        try:
            # Save patterns
            patterns_data = {}
            for pattern_id, pattern in self.patterns.items():
                pattern_dict = asdict(pattern)
                pattern_dict['identified_at'] = pattern.identified_at.isoformat()
                pattern_dict['pattern_type'] = pattern.pattern_type.value
                patterns_data[pattern_id] = pattern_dict
            
            with open(self.storage_path / "patterns.json", 'w') as f:
                json.dump(patterns_data, f, indent=2)
            
            # Save insights
            insights_data = {}
            for insight_id, insight in self.insights.items():
                insight_dict = asdict(insight)
                insight_dict['generated_at'] = insight.generated_at.isoformat()
                if insight.reviewed_at:
                    insight_dict['reviewed_at'] = insight.reviewed_at.isoformat()
                if insight.implemented_at:
                    insight_dict['implemented_at'] = insight.implemented_at.isoformat()
                insight_dict['insight_type'] = insight.insight_type.value
                insights_data[insight_id] = insight_dict
            
            with open(self.storage_path / "insights.json", 'w') as f:
                json.dump(insights_data, f, indent=2)
            
            # Save knowledge transfers
            transfers_data = {}
            for transfer_id, transfer in self.knowledge_transfers.items():
                transfer_dict = asdict(transfer)
                transfer_dict['created_at'] = transfer.created_at.isoformat()
                if transfer.completed_at:
                    transfer_dict['completed_at'] = transfer.completed_at.isoformat()
                transfers_data[transfer_id] = transfer_dict
            
            with open(self.storage_path / "knowledge_transfers.json", 'w') as f:
                json.dump(transfers_data, f, indent=2)
            
            logger.debug("Saved intelligence data to storage")
            
        except Exception as e:
            logger.error(f"Failed to save intelligence data: {str(e)}")