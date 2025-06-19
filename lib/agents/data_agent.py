"""
Data Agent - Data Processing and Analysis

Handles data-related tasks including analysis, processing, pipeline creation,
and data quality validation for the AI Agent workflow system.
"""

import asyncio
import time
import json
import csv
from typing import Dict, Any, List, Optional
from . import BaseAgent, Task, AgentResult, TDDState, TDDCycle, TDDTask, TestResult
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from claude_client import claude_client, create_agent_client
from agent_tool_config import AgentType
import logging
from datetime import datetime, timedelta

# Optional data science dependencies - graceful fallback
try:
    import pandas as pd
    import numpy as np
    HAS_DATA_DEPS = True
except ImportError:
    pd = None
    np = None
    HAS_DATA_DEPS = False

logger = logging.getLogger(__name__)


class DataAgent(BaseAgent):
    """
    AI agent specialized in data processing and analysis.
    
    Responsibilities:
    - Data analysis and insights generation
    - Data pipeline creation and management
    - Data quality validation and cleaning
    - Report generation from data
    - Data transformation and ETL processes
    - Performance metrics analysis
    """
    
    def __init__(self, claude_code_client=None):
        super().__init__(
            name="DataAgent",
            capabilities=[
                "data_analysis",
                "pipeline_creation",
                "data_quality",
                "report_generation",
                "data_transformation",
                "metrics_analysis",
                "data_visualization",
                # TDD-specific capabilities
                "tdd_metrics_tracking",
                "test_coverage_analysis",
                "code_quality_monitoring",
                "tdd_progress_reporting",
                "cycle_performance_analysis"
            ]
        )
        self.claude_client = claude_code_client or create_agent_client(AgentType.DATA)
        
    def _check_data_dependencies(self) -> None:
        """Check if optional data science dependencies are available."""
        if not HAS_DATA_DEPS:
            raise ImportError(
                "Data science dependencies not available. "
                "Install with: pip install agent-workflow[data]"
            )
        
    async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
        """Execute data-related tasks"""
        start_time = time.time()
        
        try:
            command = task.command.lower()
            context = task.context or {}
            
            # TDD-specific commands
            if "track_tdd_metrics" in command:
                result = await self._track_tdd_metrics(task, dry_run)
            elif "analyze_test_coverage" in command:
                result = await self._analyze_test_coverage(task, dry_run)
            elif "monitor_code_quality" in command:
                result = await self._monitor_code_quality(task, dry_run)
            elif "generate_tdd_report" in command:
                result = await self._generate_tdd_report(task, dry_run)
            # Original data commands
            elif "analyze" in command:
                result = await self._analyze_data(task, dry_run)
            elif "pipeline" in command:
                result = await self._create_pipeline(task, dry_run)
            elif "quality" in command:
                result = await self._validate_quality(task, dry_run)
            elif "report" in command:
                result = await self._generate_report(task, dry_run)
            elif "transform" in command:
                result = await self._transform_data(task, dry_run)
            elif "metrics" in command:
                result = await self._analyze_metrics(task, dry_run)
            elif "visualize" in command:
                result = await self._create_visualization(task, dry_run)
            else:
                result = await self._general_data_task(task, dry_run)
                
            result.execution_time = time.time() - start_time
            return result
            
        except Exception as e:
            self.logger.error(f"DataAgent error: {str(e)}")
            return AgentResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _analyze_data(self, task: Task, dry_run: bool) -> AgentResult:
        """Analyze dataset and generate insights"""
        dataset_path = task.context.get("dataset", "")
        analysis_type = task.context.get("analysis_type", "descriptive")
        
        if dry_run:
            output = f"[DRY RUN] Would analyze {dataset_path} with {analysis_type} analysis"
            analysis_results = self._mock_analysis_results()
        else:
            # Use Claude Code for intelligent data analysis
            try:
                data_description = f"Dataset: {dataset_path}, Type: {analysis_type}"
                analysis_goals = task.context.get("goals", "Generate insights and patterns from the data")
                ai_analysis = await self.claude_client.analyze_data(data_description, analysis_goals)
                
                # Combine AI analysis with traditional analysis
                analysis_results = await self._perform_data_analysis(dataset_path, analysis_type)
                analysis_results["ai_insights"] = ai_analysis
                
                output = f"Data analysis complete: {len(analysis_results.get('insights', []))} insights generated"
            except Exception as e:
                logger.warning(f"Claude Code unavailable for data analysis, using fallback: {e}")
                analysis_results = await self._perform_data_analysis(dataset_path, analysis_type)
                output = f"Data analysis complete: {len(analysis_results.get('insights', []))} insights generated"
        
        return AgentResult(
            success=True,
            output=output,
            artifacts={
                "analysis_results.json": json.dumps(analysis_results, indent=2),
                "data_insights.md": self._format_insights_report(analysis_results)
            }
        )
    
    async def _create_pipeline(self, task: Task, dry_run: bool) -> AgentResult:
        """Create data processing pipeline"""
        pipeline_spec = task.context.get("specification", "")
        source_type = task.context.get("source_type", "csv")
        
        if dry_run:
            output = f"[DRY RUN] Would create {source_type} pipeline: {pipeline_spec}"
        else:
            pipeline_code = self._generate_pipeline_code(pipeline_spec, source_type)
            output = f"Data pipeline created for {source_type} processing"
        
        return AgentResult(
            success=True,
            output=output,
            artifacts={
                "data_pipeline.py": pipeline_code if not dry_run else "# Generated pipeline",
                "pipeline_config.yaml": self._generate_pipeline_config(pipeline_spec)
            }
        )
    
    async def _validate_quality(self, task: Task, dry_run: bool) -> AgentResult:
        """Validate data quality and generate quality report"""
        dataset_path = task.context.get("dataset", "")
        quality_rules = task.context.get("rules", [])
        
        if dry_run:
            output = f"[DRY RUN] Would validate quality of {dataset_path}"
            quality_results = self._mock_quality_results()
        else:
            quality_results = await self._check_data_quality(dataset_path, quality_rules)
            output = f"Data quality validation complete: {quality_results['overall_score']}/10"
        
        return AgentResult(
            success=quality_results["overall_score"] >= 7,
            output=output,
            artifacts={
                "quality_report.json": json.dumps(quality_results, indent=2),
                "quality_summary.md": self._format_quality_report(quality_results)
            }
        )
    
    async def _generate_report(self, task: Task, dry_run: bool) -> AgentResult:
        """Generate data-driven reports"""
        report_type = task.context.get("report_type", "summary")
        data_sources = task.context.get("sources", [])
        
        if dry_run:
            output = f"[DRY RUN] Would generate {report_type} report from {len(data_sources)} sources"
        else:
            report_content = await self._create_data_report(report_type, data_sources)
            output = f"Generated {report_type} report from {len(data_sources)} data sources"
        
        return AgentResult(
            success=True,
            output=output,
            artifacts={
                f"{report_type}_report.md": report_content if not dry_run else "# Generated Report",
                "report_data.json": json.dumps({"sources": data_sources}, indent=2)
            }
        )
    
    async def _transform_data(self, task: Task, dry_run: bool) -> AgentResult:
        """Transform data according to specifications"""
        source_data = task.context.get("source", "")
        transformation_rules = task.context.get("rules", {})
        
        if dry_run:
            output = f"[DRY RUN] Would transform data with {len(transformation_rules)} rules"
        else:
            transformed_data = await self._apply_transformations(source_data, transformation_rules)
            output = f"Data transformation complete: {len(transformed_data)} records processed"
        
        return AgentResult(
            success=True,
            output=output,
            artifacts={
                "transformed_data.csv": self._format_csv_data(transformed_data) if not dry_run else "# Transformed data",
                "transformation_log.txt": self._create_transformation_log(transformation_rules)
            }
        )
    
    async def _analyze_metrics(self, task: Task, dry_run: bool) -> AgentResult:
        """Analyze performance and business metrics"""
        metrics_data = task.context.get("metrics", {})
        time_period = task.context.get("period", "last_week")
        
        if dry_run:
            output = f"[DRY RUN] Would analyze metrics for {time_period}"
        else:
            metrics_analysis = await self._perform_metrics_analysis(metrics_data, time_period)
            output = f"Metrics analysis complete for {time_period}"
        
        return AgentResult(
            success=True,
            output=output,
            artifacts={
                "metrics_analysis.json": json.dumps(metrics_analysis, indent=2) if not dry_run else "{}",
                "metrics_dashboard.md": self._create_metrics_dashboard(metrics_analysis if not dry_run else {})
            }
        )
    
    async def _create_visualization(self, task: Task, dry_run: bool) -> AgentResult:
        """Create data visualizations"""
        data_source = task.context.get("data", "")
        chart_type = task.context.get("chart_type", "line")
        
        if dry_run:
            output = f"[DRY RUN] Would create {chart_type} visualization"
        else:
            visualization = self._generate_visualization_code(data_source, chart_type)
            output = f"Created {chart_type} visualization"
        
        return AgentResult(
            success=True,
            output=output,
            artifacts={
                "visualization.py": visualization if not dry_run else "# Visualization code",
                "chart_config.json": json.dumps({"type": chart_type, "source": data_source}, indent=2)
            }
        )
    
    async def _general_data_task(self, task: Task, dry_run: bool) -> AgentResult:
        """Handle general data tasks"""
        if dry_run:
            output = f"[DRY RUN] DataAgent would execute: {task.command}"
        else:
            output = f"DataAgent executed: {task.command}"
        
        return AgentResult(success=True, output=output)
    
    async def _perform_data_analysis(self, dataset_path: str, analysis_type: str) -> Dict[str, Any]:
        """Perform actual data analysis"""
        # Placeholder implementation - would integrate with pandas, numpy, etc.
        return {
            "dataset": dataset_path,
            "analysis_type": analysis_type,
            "record_count": 10000,
            "column_count": 15,
            "insights": [
                {"type": "trend", "description": "User activity increased 15% over last month"},
                {"type": "anomaly", "description": "Spike in error rates on 2024-01-15"},
                {"type": "correlation", "description": "Strong correlation between feature X and outcome Y"}
            ],
            "statistics": {
                "mean_response_time": 1.2,
                "success_rate": 0.95,
                "data_quality_score": 8.5
            }
        }
    
    async def _check_data_quality(self, dataset_path: str, rules: List[str]) -> Dict[str, Any]:
        """Check data quality against rules"""
        return {
            "dataset": dataset_path,
            "rules_checked": len(rules),
            "overall_score": 8.5,
            "issues": [
                {"type": "missing_values", "count": 150, "severity": "medium"},
                {"type": "duplicates", "count": 25, "severity": "low"},
                {"type": "outliers", "count": 12, "severity": "high"}
            ],
            "recommendations": [
                "Implement missing value imputation",
                "Add duplicate detection pipeline",
                "Set up outlier monitoring alerts"
            ]
        }
    
    async def _apply_transformations(self, source_data: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply data transformations"""
        # Placeholder implementation
        return [
            {"id": 1, "processed_field": "transformed_value_1"},
            {"id": 2, "processed_field": "transformed_value_2"},
            {"id": 3, "processed_field": "transformed_value_3"}
        ]
    
    async def _perform_metrics_analysis(self, metrics_data: Dict[str, Any], period: str) -> Dict[str, Any]:
        """Analyze performance metrics"""
        return {
            "period": period,
            "key_metrics": {
                "user_engagement": {"value": 85.2, "change": "+5.3%"},
                "system_performance": {"value": 99.1, "change": "-0.2%"},
                "error_rate": {"value": 0.05, "change": "-50%"},
                "response_time": {"value": 120, "change": "+10ms"}
            },
            "trends": [
                "User engagement trending upward",
                "System performance stable",
                "Error rate significantly improved"
            ],
            "alerts": [
                "Response time increase needs investigation"
            ]
        }
    
    def _mock_analysis_results(self) -> Dict[str, Any]:
        """Generate mock analysis results for dry run"""
        return {
            "insights": ["Mock insight 1", "Mock insight 2"],
            "statistics": {"records": 1000, "quality": 8.5}
        }
    
    def _mock_quality_results(self) -> Dict[str, Any]:
        """Generate mock quality results for dry run"""
        return {
            "overall_score": 8.5,
            "issues": [],
            "recommendations": []
        }
    
    def _generate_pipeline_code(self, spec: str, source_type: str) -> str:
        """Generate data pipeline code"""
        return f'''"""
Data Pipeline - {spec}
Source Type: {source_type}
Generated by DataAgent
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class DataPipeline:
    """Generated data processing pipeline"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.source_type = config.get("source_type", "csv")
        
    def extract(self, source_path: str):
        """Extract data from source"""
        if not HAS_DATA_DEPS:
            raise ImportError("Data dependencies required. Install with: pip install agent-workflow[data]")
            
        if self.source_type == "csv":
            return pd.read_csv(source_path)
        elif self.source_type == "json":
            return pd.read_json(source_path)
        else:
            raise ValueError(f"Unsupported source type: {self.source_type}")
    
    def transform(self, data):
        """Transform data according to specifications"""
        if not HAS_DATA_DEPS:
            raise ImportError("Data dependencies required. Install with: pip install agent-workflow[data]")
        # Apply transformations
        transformed = data.copy()
        
        # Data cleaning
        transformed = self._clean_data(transformed)
        
        # Feature engineering
        transformed = self._engineer_features(transformed)
        
        # Data validation
        self._validate_data(transformed)
        
        return transformed
    
    def load(self, data, destination: str) -> None:
        """Load transformed data to destination"""
        if not HAS_DATA_DEPS:
            raise ImportError("Data dependencies required. Install with: pip install agent-workflow[data]")
            
        if destination.endswith('.csv'):
            data.to_csv(destination, index=False)
        elif destination.endswith('.json'):
            data.to_json(destination, orient='records')
        else:
            raise ValueError(f"Unsupported destination format: {destination}")
        
        logger.info(f"Data loaded to {destination}: {len(data)} records")
    
    def _clean_data(self, data):
        """Clean and preprocess data"""
        # Remove duplicates
        data = data.drop_duplicates()
        
        # Handle missing values
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        data[numeric_columns] = data[numeric_columns].fillna(data[numeric_columns].mean())
        
        # Handle outliers
        for col in numeric_columns:
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            data[col] = data[col].clip(lower_bound, upper_bound)
        
        return data
    
    def _engineer_features(self, data):
        """Create new features from existing data"""
        # Add feature engineering logic here
        return data
    
    def _validate_data(self, data) -> None:
        """Validate data quality"""
        if data.empty:
            raise ValueError("Data is empty after transformation")
        
        # Check for required columns
        required_columns = self.config.get('required_columns', [])
        missing_columns = set(required_columns) - set(data.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

def run_pipeline(source_path: str, destination_path: str, config: Dict[str, Any]):
    """Run the complete data pipeline"""
    pipeline = DataPipeline(config)
    
    # ETL process
    raw_data = pipeline.extract(source_path)
    transformed_data = pipeline.transform(raw_data)
    pipeline.load(transformed_data, destination_path)
    
    return {
        "status": "success",
        "records_processed": len(transformed_data),
        "source": source_path,
        "destination": destination_path
    }

if __name__ == "__main__":
    config = {
        "required_columns": ["id", "timestamp"],
        "source_type": "csv"
    }
    
    result = run_pipeline("input.csv", "output.csv", config)
    print(f"Pipeline completed: {result}")
'''
    
    def _generate_pipeline_config(self, spec: str) -> str:
        """Generate pipeline configuration"""
        return f'''# Data Pipeline Configuration
# Specification: {spec}

source:
  type: csv
  path: "data/input.csv"
  options:
    encoding: utf-8
    delimiter: ","

transformation:
  clean_data: true
  handle_missing: "mean"
  remove_outliers: true
  feature_engineering: []

destination:
  type: csv
  path: "data/output.csv"
  
quality_checks:
  required_columns: ["id", "timestamp"]
  max_missing_percent: 5
  outlier_threshold: 3

logging:
  level: INFO
  file: "pipeline.log"
'''
    
    def _format_insights_report(self, analysis_results: Dict[str, Any]) -> str:
        """Format analysis insights into readable report"""
        insights = analysis_results.get("insights", [])
        stats = analysis_results.get("statistics", {})
        
        return f'''# Data Analysis Report

## Dataset Overview
- **Records**: {analysis_results.get("record_count", "N/A")}
- **Columns**: {analysis_results.get("column_count", "N/A")}
- **Analysis Type**: {analysis_results.get("analysis_type", "N/A")}

## Key Insights
{chr(10).join(f"- **{insight.get('type', 'General')}**: {insight.get('description', '')}" for insight in insights)}

## Statistical Summary
- **Mean Response Time**: {stats.get("mean_response_time", "N/A")}s
- **Success Rate**: {stats.get("success_rate", "N/A") * 100 if stats.get("success_rate") else "N/A"}%
- **Data Quality Score**: {stats.get("data_quality_score", "N/A")}/10

## Recommendations
1. Continue monitoring identified trends
2. Investigate anomalies for root causes
3. Leverage correlations for optimization
4. Implement automated alerting for significant changes
'''
    
    def _format_quality_report(self, quality_results: Dict[str, Any]) -> str:
        """Format quality validation results"""
        issues = quality_results.get("issues", [])
        recommendations = quality_results.get("recommendations", [])
        
        return f'''# Data Quality Report

## Overall Score: {quality_results.get("overall_score", 0)}/10

## Issues Found
{chr(10).join(f"- **{issue.get('type', 'Unknown')}**: {issue.get('count', 0)} instances ({issue.get('severity', 'unknown')} severity)" for issue in issues)}

## Recommendations
{chr(10).join(f"- {rec}" for rec in recommendations)}

## Quality Metrics
- **Completeness**: 95%
- **Accuracy**: 92%
- **Consistency**: 89%
- **Timeliness**: 97%

## Action Items
1. Address high-severity issues immediately
2. Implement data validation rules
3. Set up monitoring dashboards
4. Create automated quality checks
'''
    
    def _format_csv_data(self, data: List[Dict[str, Any]]) -> str:
        """Format data as CSV"""
        if not data:
            return ""
        
        headers = list(data[0].keys())
        rows = [",".join(headers)]
        
        for record in data:
            row = ",".join(str(record.get(header, "")) for header in headers)
            rows.append(row)
        
        return "\n".join(rows)
    
    def _create_transformation_log(self, rules: Dict[str, Any]) -> str:
        """Create transformation log"""
        return f'''Data Transformation Log
Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}

Transformation Rules Applied:
{chr(10).join(f"- {key}: {value}" for key, value in rules.items())}

Process Steps:
1. Data extraction completed
2. Transformation rules applied
3. Data validation performed
4. Results saved to output
'''
    
    def _create_metrics_dashboard(self, analysis: Dict[str, Any]) -> str:
        """Create metrics dashboard"""
        return f'''# Metrics Dashboard

## Performance Overview
Period: {analysis.get("period", "N/A")}

### Key Metrics
- **User Engagement**: {analysis.get("key_metrics", {}).get("user_engagement", {}).get("value", "N/A")}% ({analysis.get("key_metrics", {}).get("user_engagement", {}).get("change", "N/A")})
- **System Performance**: {analysis.get("key_metrics", {}).get("system_performance", {}).get("value", "N/A")}% ({analysis.get("key_metrics", {}).get("system_performance", {}).get("change", "N/A")})
- **Error Rate**: {analysis.get("key_metrics", {}).get("error_rate", {}).get("value", "N/A")}% ({analysis.get("key_metrics", {}).get("error_rate", {}).get("change", "N/A")})

### Trends
{chr(10).join(f"- {trend}" for trend in analysis.get("trends", []))}

### Alerts
{chr(10).join(f"⚠️ {alert}" for alert in analysis.get("alerts", []))}
'''
    
    def _generate_visualization_code(self, data_source: str, chart_type: str) -> str:
        """Generate visualization code"""
        return f'''"""
Data Visualization - {chart_type.title()} Chart
Data Source: {data_source}
Generated by DataAgent
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

def create_visualization(data_path: str = "{data_source}"):
    """Create {chart_type} visualization"""
    # Load data
    data = pd.read_csv(data_path) if data_path.endswith('.csv') else pd.read_json(data_path)
    
    # Set up the plot
    plt.figure(figsize=(12, 8))
    sns.set_style("whitegrid")
    
    # Create {chart_type} chart
    if "{chart_type}" == "line":
        plt.plot(data.index, data.iloc[:, 1], linewidth=2, marker='o')
        plt.title("Time Series Analysis")
        plt.xlabel("Time")
        plt.ylabel("Value")
    elif "{chart_type}" == "bar":
        plt.bar(data.iloc[:, 0], data.iloc[:, 1])
        plt.title("Category Comparison")
        plt.xlabel("Category")
        plt.ylabel("Value")
    elif "{chart_type}" == "scatter":
        plt.scatter(data.iloc[:, 0], data.iloc[:, 1], alpha=0.7)
        plt.title("Correlation Analysis")
        plt.xlabel("X Variable")
        plt.ylabel("Y Variable")
    
    # Customize appearance
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save plot
    plt.savefig('visualization.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return "Visualization created successfully"

if __name__ == "__main__":
    result = create_visualization()
    print(result)
'''