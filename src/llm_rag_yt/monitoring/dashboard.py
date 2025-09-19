"""Monitoring dashboard with analytics charts."""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from loguru import logger
from plotly.subplots import make_subplots

from .feedback_collector import FeedbackCollector


class MonitoringDashboard:
    """Creates monitoring dashboard with multiple charts."""

    def __init__(self, feedback_db_path: Path):
        """Initialize dashboard."""
        self.feedback_collector = FeedbackCollector(feedback_db_path)

    def generate_dashboard_html(self, output_path: Path) -> str:
        """Generate complete monitoring dashboard HTML."""
        logger.info("Generating monitoring dashboard...")

        # Get data
        feedback_stats = self.feedback_collector.get_feedback_stats()
        recent_feedback = self.feedback_collector.get_recent_feedback(100)

        # Create charts
        charts = []

        # Chart 1: Rating Distribution
        charts.append(self._create_rating_distribution_chart(feedback_stats))

        # Chart 2: Feedback Over Time
        charts.append(self._create_feedback_timeline_chart(recent_feedback))

        # Chart 3: Response Time Distribution
        charts.append(self._create_response_time_chart(recent_feedback))

        # Chart 4: Query Length vs Rating
        charts.append(self._create_query_length_chart(recent_feedback))

        # Chart 5: Daily Metrics Summary
        charts.append(self._create_daily_metrics_chart(recent_feedback))

        # Chart 6: Top Issues (Low Rated Queries)
        charts.append(self._create_issues_chart(recent_feedback))

        # Generate HTML
        html_content = self._generate_html_template(charts, feedback_stats)

        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Dashboard saved to {output_path}")
        return str(output_path)

    def _create_rating_distribution_chart(self, stats: dict[str, Any]) -> str:
        """Create rating distribution pie chart."""
        rating_dist = stats.get("rating_distribution", {})

        if not rating_dist:
            return "<div>No rating data available</div>"

        fig = px.pie(
            values=list(rating_dist.values()),
            names=[f"{k} star{'s' if k != 1 else ''}" for k in rating_dist.keys()],
            title="User Rating Distribution",
        )

        return fig.to_html(include_plotlyjs=False, div_id="rating_dist")

    def _create_feedback_timeline_chart(self, feedback: list[dict[str, Any]]) -> str:
        """Create feedback timeline chart."""
        if not feedback:
            return "<div>No feedback data available</div>"

        df = pd.DataFrame(feedback)
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date

        daily_feedback = (
            df.groupby("date").agg({"rating": ["count", "mean"]}).reset_index()
        )

        daily_feedback.columns = ["date", "count", "avg_rating"]

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=daily_feedback["date"],
                y=daily_feedback["count"],
                name="Feedback Count",
                mode="lines+markers",
            ),
            secondary_y=False,
        )

        fig.add_trace(
            go.Scatter(
                x=daily_feedback["date"],
                y=daily_feedback["avg_rating"],
                name="Avg Rating",
                mode="lines+markers",
            ),
            secondary_y=True,
        )

        fig.update_layout(title="Feedback Timeline")
        fig.update_yaxes(title_text="Feedback Count", secondary_y=False)
        fig.update_yaxes(title_text="Average Rating", secondary_y=True)

        return fig.to_html(include_plotlyjs=False, div_id="timeline")

    def _create_response_time_chart(self, feedback: list[dict[str, Any]]) -> str:
        """Create response time distribution chart."""
        df = pd.DataFrame(feedback)
        response_times = df[df["response_time"].notna()]["response_time"]

        if response_times.empty:
            return "<div>No response time data available</div>"

        fig = px.histogram(
            x=response_times,
            title="Response Time Distribution",
            labels={"x": "Response Time (seconds)", "y": "Count"},
        )

        return fig.to_html(include_plotlyjs=False, div_id="response_time")

    def _create_query_length_chart(self, feedback: list[dict[str, Any]]) -> str:
        """Create query length vs rating scatter plot."""
        df = pd.DataFrame(feedback)
        df["query_length"] = df["query"].str.len()

        fig = px.scatter(
            df,
            x="query_length",
            y="rating",
            title="Query Length vs Rating",
            labels={
                "query_length": "Query Length (characters)",
                "rating": "User Rating",
            },
        )

        return fig.to_html(include_plotlyjs=False, div_id="query_length")

    def _create_daily_metrics_chart(self, feedback: list[dict[str, Any]]) -> str:
        """Create daily metrics heatmap."""
        if not feedback:
            return "<div>No feedback data available</div>"

        df = pd.DataFrame(feedback)
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour

        hourly_metrics = (
            df.groupby(["date", "hour"])
            .agg({"rating": "mean", "id": "count"})
            .reset_index()
        )

        # Create heatmap data
        pivot_data = hourly_metrics.pivot(index="hour", columns="date", values="rating")

        fig = px.imshow(
            pivot_data,
            title="Daily Rating Heatmap (by Hour)",
            labels={"x": "Date", "y": "Hour of Day", "color": "Avg Rating"},
        )

        return fig.to_html(include_plotlyjs=False, div_id="daily_metrics")

    def _create_issues_chart(self, feedback: list[dict[str, Any]]) -> str:
        """Create chart showing queries with issues (low ratings)."""
        df = pd.DataFrame(feedback)
        low_rated = df[df["rating"] <= 2]

        if low_rated.empty:
            return "<div>No low-rated queries found (great job!)</div>"

        # Count common issues
        issues_count = len(low_rated)
        avg_low_rating = low_rated["rating"].mean()

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=["Low Rated Queries", "Avg Low Rating"],
                y=[issues_count, avg_low_rating],
                text=[f"{issues_count}", f"{avg_low_rating:.1f}"],
                textposition="auto",
            )
        )

        fig.update_layout(title="Issues Analysis", yaxis_title="Count / Rating")

        return fig.to_html(include_plotlyjs=False, div_id="issues")

    def _generate_html_template(self, charts: list[str], stats: dict[str, Any]) -> str:
        """Generate complete HTML template with all charts."""
        plotly_js = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'

        stats_html = f"""
        <div style="background: #f0f0f0; padding: 20px; margin: 20px 0; border-radius: 5px;">
            <h2>📊 System Overview</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                <div><strong>Total Feedback:</strong> {stats.get("total_feedback", 0)}</div>
                <div><strong>Average Rating:</strong> {stats.get("average_rating", 0):.2f}/5</div>
                <div><strong>Recent Feedback (7d):</strong> {stats.get("recent_feedback_7days", 0)}</div>
                <div><strong>Avg Response Time:</strong> {stats.get("average_response_time", 0):.2f}s</div>
            </div>
        </div>
        """

        charts_html = "\n".join(
            f'<div style="margin: 30px 0;">{chart}</div>' for chart in charts
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LLM RAG YouTube - Monitoring Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            {plotly_js}
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; text-align: center; }}
                .chart-container {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>🚀 LLM RAG YouTube - Monitoring Dashboard</h1>
            <p style="text-align: center; color: #666;">
                Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </p>

            {stats_html}

            <div class="chart-container">
                {charts_html}
            </div>

            <footer style="text-align: center; margin-top: 50px; color: #999;">
                <p>Dashboard auto-refreshes every hour • Last updated: {datetime.now().strftime("%H:%M")}</p>
            </footer>
        </body>
        </html>
        """
