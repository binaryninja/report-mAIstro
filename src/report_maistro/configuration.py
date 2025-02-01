import os
from dataclasses import dataclass, field, fields
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from typing_extensions import Annotated

DEFAULT_REPORT_STRUCTURE = """Red Team Campaign Report Structure:
1. Executive Summary
   - Brief overview of the campaign, including the campaign name, scope, and overall risk.
2. Campaign Details
   - Campaign Name, Description, Objectives, and Timeline.
3. Technical Findings
   - Detailed findings including vulnerabilities exploited, techniques used, evidence, and risk ratings.
4. Remediation Recommendations
   - Actionable recommendations to mitigate identified weaknesses.
5. Conclusion
   - Summary of findings and next steps for improving security posture.
"""

@dataclass(kw_only=True)
class Configuration:
    """Configurable fields for the red team reporting tool."""
    report_structure: str = DEFAULT_REPORT_STRUCTURE
    number_of_queries: int = 2
    tavily_topic: str = "cybersecurity"
    tavily_days: Optional[str] = None
    planner_model: str = "o3-mini"
    writer_model: str = "claude-3-5-sonnet-latest"

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})
