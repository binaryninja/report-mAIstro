from typing import Annotated, List, TypedDict
from pydantic import BaseModel, Field
from enum import Enum
import operator

class Section(BaseModel):
    name: str = Field(
        description="Section title for the red team report.",
    )
    description: str = Field(
        description="Brief overview of the main topics covered in this section.",
    )
    research: bool = Field(
        description="Whether to perform additional research for this section (e.g. to gather technical details)."
    )
    content: str = Field(
        description="The content of the section."
    )

class Sections(BaseModel):
    sections: List[Section] = Field(
        description="Sections of the red team report.",
    )

class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Query for web search.")

class Queries(BaseModel):
    queries: List[SearchQuery] = Field(
        description="List of search queries.",
    )

class ReportStateInput(TypedDict):
    campaign_name: str  # Red team campaign name
    campaign_description: str  # Description of the campaign
    objectives: str  # Objectives of the campaign
    feedback_on_report_plan: str  # Feedback on the report plan
    accept_report_plan: bool  # Whether the plan is accepted

class ReportStateOutput(TypedDict):
    final_report: str  # Final red team report

class ReportState(TypedDict):
    campaign_name: str
    campaign_description: str
    objectives: str
    feedback_on_report_plan: str
    accept_report_plan: bool
    sections: list[Section]
    completed_sections: list  # Accumulated completed sections
    report_sections_from_research: str  # Combined text from researched sections
    final_report: str  # Final compiled report

class SectionState(TypedDict):
    section: Section  # A single report section
    search_queries: list[SearchQuery]  # Generated search queries
    source_str: str  # Formatted string from web research
    report_sections_from_research: str  # Combined researched sections (for context)
    completed_sections: list[Section]  # Updated section content

class SectionOutputState(TypedDict):
    completed_sections: list[Section]  # Completed sections to merge
