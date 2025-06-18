"""
Unit tests for Data Agent.

Tests the AI agent specialized in data processing, analysis, and metrics
generation including TDD-specific data analytics functionality.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.agents.data_agent import DataAgent
from lib.agents import Task, AgentResult, TDDState
from lib.agent_tool_config import AgentType


class TestDataAgent:
    """Test the DataAgent class."""
    
    @pytest.fixture
    def mock_claude_client(self):
        """Create a mock Claude client."""
        mock_client = Mock()
        mock_client.analyze_data = AsyncMock(return_value="AI-generated insights")
        return mock_client
    
    @pytest.fixture
    def data_agent(self, mock_claude_client):
        """Create a DataAgent for testing."""
        return DataAgent(claude_code_client=mock_claude_client)
    
    def test_data_agent_init(self, data_agent, mock_claude_client):
        """Test DataAgent initialization."""
        assert data_agent.name == "DataAgent"
        assert data_agent.claude_client == mock_claude_client
        
        # Check capabilities
        expected_capabilities = [
            "data_analysis",
            "pipeline_creation",
            "data_quality",
            "report_generation",
            "data_transformation",
            "metrics_analysis",
            "data_visualization",
            "tdd_metrics_tracking",
            "test_coverage_analysis",
            "code_quality_monitoring",
            "tdd_progress_reporting",
            "cycle_performance_analysis"
        ]
        
        for capability in expected_capabilities:
            assert capability in data_agent.capabilities

    @pytest.mark.asyncio
    async def test_analyze_data_dry_run(self, data_agent):
        """Test data analysis in dry run mode."""
        task = Task(
            id="test-1",
            agent_type="DataAgent",
            command="analyze dataset",
            context={
                "dataset": "user_data.csv",
                "analysis_type": "statistical",
                "goals": "Find patterns in user behavior"
            }
        )
        
        print(f"Task context type: {type(task.context)}")
        print(f"Task context: {task.context}")
        
        result = await data_agent.run(task, dry_run=True)
        
        print(f"Result: {result}")
        assert result.success
        assert "[DRY RUN]" in result.output
        assert "user_data.csv" in result.output
        assert "analysis_results.json" in result.artifacts
        assert "data_insights.md" in result.artifacts

    @pytest.mark.asyncio
    async def test_analyze_data_with_claude(self, data_agent, mock_claude_client):
        """Test data analysis using Claude client."""
        mock_claude_client.analyze_data.return_value = "Strong correlation found between X and Y"
        
        task = Task(
            id="test-2",
            agent_type="DataAgent",
            command="analyze customer data",
            context={
                "dataset": "customer_behavior.csv",
                "analysis_type": "predictive",
                "goals": "Predict customer churn"
            }
        )
        
        with patch.object(data_agent, '_perform_data_analysis', new_callable=AsyncMock) as mock_analysis:
            mock_analysis.return_value = {
                "insights": ["Insight 1", "Insight 2"],
                "statistics": {"mean_value": 5.2}
            }
            
            result = await data_agent.run(task, dry_run=False)
            
            assert result.success
            assert "2 insights generated" in result.output
            assert "analysis_results.json" in result.artifacts
            assert "data_insights.md" in result.artifacts
            mock_claude_client.analyze_data.assert_called_once()
            mock_analysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_data_fallback(self, data_agent, mock_claude_client):
        """Test data analysis fallback when Claude is unavailable."""
        mock_claude_client.analyze_data.side_effect = Exception("Claude unavailable")
        
        task = Task(
            id="test-3",
            agent_type="DataAgent",
            command="analyze sales data",
            context={
                "dataset": "sales.csv",
                "analysis_type": "descriptive"
            }
        )
        
        with patch.object(data_agent, '_perform_data_analysis', new_callable=AsyncMock) as mock_analysis:
            mock_analysis.return_value = {
                "insights": ["Sales trend insight"],
                "statistics": {"total_sales": 100000}
            }
            
            result = await data_agent.run(task, dry_run=False)
            
            assert result.success
            assert "1 insights generated" in result.output
            mock_analysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_pipeline_dry_run(self, data_agent):
        """Test pipeline creation in dry run mode."""
        task = Task(
            id="test-4",
            agent_type="DataAgent",
            command="create data pipeline",
            context={
                "specification": "ETL pipeline for user events",
                "source_type": "json"
            }
        )
        
        result = await data_agent.run(task, dry_run=True)
        
        assert result.success
        assert "[DRY RUN]" in result.output
        assert "json pipeline" in result.output
        assert "data_pipeline.py" in result.artifacts
        assert "pipeline_config.yaml" in result.artifacts

    @pytest.mark.asyncio
    async def test_create_pipeline(self, data_agent):
        """Test pipeline creation."""
        task = Task(
            id="test-5",
            agent_type="DataAgent",
            command="create pipeline for CSV processing",
            context={
                "specification": "Process customer data",
                "source_type": "csv"
            }
        )
        
        result = await data_agent.run(task, dry_run=False)
        
        assert result.success
        assert "csv processing" in result.output
        assert "data_pipeline.py" in result.artifacts
        assert "pipeline_config.yaml" in result.artifacts
        
        # Check pipeline code content
        pipeline_code = result.artifacts["data_pipeline.py"]
        assert "class DataPipeline:" in pipeline_code
        assert "def extract(" in pipeline_code
        assert "def transform(" in pipeline_code
        assert "def load(" in pipeline_code

    @pytest.mark.asyncio
    async def test_validate_quality_dry_run(self, data_agent):
        """Test quality validation in dry run mode."""
        task = Task(
            id="test-6",
            agent_type="DataAgent",
            command="validate data quality",
            context={
                "dataset": "test_data.csv",
                "rules": ["no_nulls", "unique_ids", "valid_emails"]
            }
        )
        
        result = await data_agent.run(task, dry_run=True)
        
        assert result.success
        assert "[DRY RUN]" in result.output
        assert "test_data.csv" in result.output

    @pytest.mark.asyncio
    async def test_validate_quality_high_score(self, data_agent):
        """Test quality validation with high quality score."""
        task = Task(
            id="test-7",
            agent_type="DataAgent",
            command="quality check on customer data",
            context={
                "dataset": "customers.csv",
                "rules": ["completeness", "accuracy"]
            }
        )
        
        with patch.object(data_agent, '_check_data_quality', new_callable=AsyncMock) as mock_quality:
            mock_quality.return_value = {
                "overall_score": 9.2,
                "issues": [],
                "recommendations": []
            }
            
            result = await data_agent.run(task, dry_run=False)
            
            assert result.success
            assert "9.2/10" in result.output
            assert "quality_report.json" in result.artifacts
            assert "quality_summary.md" in result.artifacts

    @pytest.mark.asyncio
    async def test_validate_quality_low_score(self, data_agent):
        """Test quality validation with low quality score."""
        task = Task(
            id="test-8",
            agent_type="DataAgent",
            command="validate quality",
            context={
                "dataset": "poor_quality.csv",
                "rules": ["consistency"]
            }
        )
        
        with patch.object(data_agent, '_check_data_quality', new_callable=AsyncMock) as mock_quality:
            mock_quality.return_value = {
                "overall_score": 5.1,
                "issues": [{"type": "missing_values", "count": 500}],
                "recommendations": ["Fix missing data"]
            }
            
            result = await data_agent.run(task, dry_run=False)
            
            assert not result.success  # Should fail with score < 7
            assert "5.1/10" in result.output

    @pytest.mark.asyncio
    async def test_generate_report(self, data_agent):
        """Test report generation."""
        task = Task(
            id="test-9",
            agent_type="DataAgent",
            command="report generation",  # Use "report" first to avoid other matches
            context={
                "report_type": "performance",
                "sources": ["sales.csv", "metrics.json", "events.log"]
            }
        )
        
        with patch.object(data_agent, '_create_data_report', new_callable=AsyncMock) as mock_report:
            mock_report.return_value = "# Performance Report\n\nData analysis complete."
            
            result = await data_agent.run(task, dry_run=False)
            
            assert result.success
            assert "3 data sources" in result.output
            assert "performance_report.md" in result.artifacts
            assert "report_data.json" in result.artifacts
            mock_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_transform_data(self, data_agent):
        """Test data transformation."""
        task = Task(
            id="test-10",
            agent_type="DataAgent",
            command="transform user data",
            context={
                "source": "raw_users.csv",
                "rules": {
                    "normalize_names": True,
                    "validate_emails": True,
                    "format_dates": "ISO"
                }
            }
        )
        
        with patch.object(data_agent, '_apply_transformations', new_callable=AsyncMock) as mock_transform:
            mock_transform.return_value = [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
            ]
            
            result = await data_agent.run(task, dry_run=False)
            
            assert result.success
            assert "2 records processed" in result.output
            assert "transformed_data.csv" in result.artifacts
            assert "transformation_log.txt" in result.artifacts
            mock_transform.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_metrics(self, data_agent):
        """Test metrics analysis."""
        task = Task(
            id="test-11",
            agent_type="DataAgent",
            command="metrics analysis",  # Use "metrics" first to avoid "analyze" match
            context={
                "metrics": {"cpu_usage": 75, "memory_usage": 60},
                "period": "last_month"
            }
        )
        
        with patch.object(data_agent, '_perform_metrics_analysis', new_callable=AsyncMock) as mock_metrics:
            mock_metrics.return_value = {
                "period": "last_month",
                "key_metrics": {
                    "cpu_usage": {"value": 75, "change": "+5%"}
                },
                "trends": ["CPU usage increasing"],
                "alerts": []
            }
            
            result = await data_agent.run(task, dry_run=False)
            
            assert result.success
            assert "last_month" in result.output
            assert "metrics_analysis.json" in result.artifacts
            assert "metrics_dashboard.md" in result.artifacts

    @pytest.mark.asyncio
    async def test_create_visualization(self, data_agent):
        """Test visualization creation."""
        task = Task(
            id="test-12",
            agent_type="DataAgent",
            command="visualize sales trends",
            context={
                "data": "sales_data.csv",
                "chart_type": "line"
            }
        )
        
        result = await data_agent.run(task, dry_run=False)
        
        assert result.success
        assert "line visualization" in result.output
        assert "visualization.py" in result.artifacts
        assert "chart_config.json" in result.artifacts
        
        # Check visualization code content
        viz_code = result.artifacts["visualization.py"]
        assert "import matplotlib.pyplot as plt" in viz_code
        assert "def create_visualization" in viz_code
        assert "line" in viz_code

    @pytest.mark.asyncio
    async def test_tdd_metrics_tracking(self, data_agent):
        """Test TDD metrics tracking functionality."""
        task = Task(
            id="test-13",
            agent_type="DataAgent",
            command="track_tdd_metrics",
            context={
                "story_id": "USER-123",
                "cycle_data": {"tests_written": 5, "tests_passing": 3}
            }
        )
        
        result = await data_agent.run(task, dry_run=False)
        
        # Should fail because method is not implemented yet
        assert not result.success
        assert "_track_tdd_metrics" in result.error

    @pytest.mark.asyncio
    async def test_general_data_task(self, data_agent):
        """Test handling of general data tasks."""
        task = Task(
            id="test-14",
            agent_type="DataAgent",
            command="custom data operation",
            context={}
        )
        
        result = await data_agent.run(task, dry_run=False)
        
        assert result.success
        assert "DataAgent executed: custom data operation" in result.output

    @pytest.mark.asyncio
    async def test_error_handling(self, data_agent):
        """Test error handling during task execution."""
        task = Task(
            id="test-15",
            agent_type="DataAgent",
            command="analyze data",
            context={"dataset": "test.csv"}
        )
        
        with patch.object(data_agent, '_analyze_data', side_effect=Exception("Test error")):
            result = await data_agent.run(task, dry_run=False)
            
            assert not result.success
            assert "Test error" in result.error
            assert result.execution_time > 0

    # Test helper methods
    
    @pytest.mark.asyncio
    async def test_perform_data_analysis(self, data_agent):
        """Test data analysis helper method."""
        result = await data_agent._perform_data_analysis("test.csv", "statistical")
        
        assert isinstance(result, dict)
        assert "dataset" in result
        assert "analysis_type" in result
        assert "insights" in result
        assert "statistics" in result
        assert result["dataset"] == "test.csv"
        assert result["analysis_type"] == "statistical"

    @pytest.mark.asyncio
    async def test_check_data_quality(self, data_agent):
        """Test data quality checking."""
        rules = ["no_nulls", "unique_ids"]
        result = await data_agent._check_data_quality("test.csv", rules)
        
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "issues" in result
        assert "recommendations" in result
        assert result["rules_checked"] == 2

    @pytest.mark.asyncio
    async def test_apply_transformations(self, data_agent):
        """Test data transformations."""
        rules = {"normalize": True, "validate": True}
        result = await data_agent._apply_transformations("source.csv", rules)
        
        assert isinstance(result, list)
        assert len(result) == 3  # Mock returns 3 records
        assert all("processed_field" in record for record in result)

    @pytest.mark.asyncio
    async def test_perform_metrics_analysis(self, data_agent):
        """Test metrics analysis."""
        metrics_data = {"response_time": 100, "error_rate": 0.1}
        result = await data_agent._perform_metrics_analysis(metrics_data, "last_week")
        
        assert isinstance(result, dict)
        assert "period" in result
        assert "key_metrics" in result
        assert "trends" in result
        assert "alerts" in result
        assert result["period"] == "last_week"

    def test_mock_analysis_results(self, data_agent):
        """Test mock analysis results generation."""
        result = data_agent._mock_analysis_results()
        
        assert isinstance(result, dict)
        assert "insights" in result
        assert "statistics" in result
        assert len(result["insights"]) == 2

    def test_mock_quality_results(self, data_agent):
        """Test mock quality results generation."""
        result = data_agent._mock_quality_results()
        
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "issues" in result
        assert "recommendations" in result
        assert result["overall_score"] == 8.5

    def test_generate_pipeline_code(self, data_agent):
        """Test pipeline code generation."""
        code = data_agent._generate_pipeline_code("Process user events", "json")
        
        assert isinstance(code, str)
        assert "class DataPipeline:" in code
        assert "def extract(" in code
        assert "def transform(" in code
        assert "def load(" in code
        assert "json" in code
        assert "Process user events" in code

    def test_generate_pipeline_config(self, data_agent):
        """Test pipeline configuration generation."""
        config = data_agent._generate_pipeline_config("ETL for sales data")
        
        assert isinstance(config, str)
        assert "ETL for sales data" in config
        assert "source:" in config
        assert "transformation:" in config
        assert "destination:" in config
        assert "quality_checks:" in config

    def test_format_insights_report(self, data_agent):
        """Test insights report formatting."""
        analysis_results = {
            "record_count": 1000,
            "column_count": 10,
            "analysis_type": "descriptive",
            "insights": [
                {"type": "trend", "description": "Upward trend detected"},
                {"type": "anomaly", "description": "Spike in values"}
            ],
            "statistics": {
                "mean_response_time": 1.5,
                "success_rate": 0.95,
                "data_quality_score": 8.2
            }
        }
        
        report = data_agent._format_insights_report(analysis_results)
        
        assert isinstance(report, str)
        assert "Data Analysis Report" in report
        assert "1000" in report
        assert "10" in report
        assert "descriptive" in report
        assert "Upward trend detected" in report
        assert "1.5s" in report
        assert "95.0%" in report

    def test_format_quality_report(self, data_agent):
        """Test quality report formatting."""
        quality_results = {
            "overall_score": 7.5,
            "issues": [
                {"type": "missing_values", "count": 50, "severity": "medium"},
                {"type": "duplicates", "count": 10, "severity": "low"}
            ],
            "recommendations": [
                "Implement data validation",
                "Add duplicate detection"
            ]
        }
        
        report = data_agent._format_quality_report(quality_results)
        
        assert isinstance(report, str)
        assert "Data Quality Report" in report
        assert "7.5/10" in report
        assert "missing_values" in report
        assert "50 instances" in report
        assert "Implement data validation" in report

    def test_format_csv_data(self, data_agent):
        """Test CSV data formatting."""
        data = [
            {"id": 1, "name": "John", "score": 85},
            {"id": 2, "name": "Jane", "score": 92}
        ]
        
        csv_output = data_agent._format_csv_data(data)
        
        assert isinstance(csv_output, str)
        lines = csv_output.split('\n')
        assert len(lines) == 3  # Header + 2 data rows
        assert "id,name,score" in lines[0]
        assert "1,John,85" in lines[1]
        assert "2,Jane,92" in lines[2]

    def test_format_csv_data_empty(self, data_agent):
        """Test CSV formatting with empty data."""
        result = data_agent._format_csv_data([])
        assert result == ""

    def test_create_transformation_log(self, data_agent):
        """Test transformation log creation."""
        rules = {"normalize_names": True, "validate_emails": True}
        log = data_agent._create_transformation_log(rules)
        
        assert isinstance(log, str)
        assert "Data Transformation Log" in log
        assert "normalize_names: True" in log
        assert "validate_emails: True" in log
        assert "Process Steps:" in log

    def test_create_metrics_dashboard(self, data_agent):
        """Test metrics dashboard creation."""
        analysis = {
            "period": "last_month",
            "key_metrics": {
                "user_engagement": {"value": 85.2, "change": "+5.3%"},
                "system_performance": {"value": 99.1, "change": "-0.2%"}
            },
            "trends": ["User engagement improving"],
            "alerts": ["Response time increase"]
        }
        
        dashboard = data_agent._create_metrics_dashboard(analysis)
        
        assert isinstance(dashboard, str)
        assert "Metrics Dashboard" in dashboard
        assert "last_month" in dashboard
        assert "85.2%" in dashboard
        assert "+5.3%" in dashboard
        assert "User engagement improving" in dashboard
        assert "⚠️ Response time increase" in dashboard

    def test_generate_visualization_code(self, data_agent):
        """Test visualization code generation."""
        code = data_agent._generate_visualization_code("sales.csv", "bar")
        
        assert isinstance(code, str)
        assert "import matplotlib.pyplot as plt" in code
        assert "import seaborn as sns" in code
        assert "def create_visualization" in code
        assert "sales.csv" in code
        assert '"bar"' in code
        assert "plt.bar(" in code

    def test_generate_visualization_code_line_chart(self, data_agent):
        """Test line chart visualization generation."""
        code = data_agent._generate_visualization_code("timeseries.csv", "line")
        
        assert isinstance(code, str)
        assert "plt.plot(" in code
        assert "Time Series Analysis" in code

    def test_generate_visualization_code_scatter_plot(self, data_agent):
        """Test scatter plot visualization generation."""
        code = data_agent._generate_visualization_code("correlation.csv", "scatter")
        
        assert isinstance(code, str)
        assert "plt.scatter(" in code
        assert "Correlation Analysis" in code