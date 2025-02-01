from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from langgraph.constants import Send
from langgraph.graph import START, END, StateGraph

from src.report_maistro.state import ReportStateInput, ReportStateOutput, Sections, ReportState, SectionState, SectionOutputState, Queries
from src.report_maistro.prompts import (report_planner_query_writer_instructions, report_planner_instructions,
                                         query_writer_instructions, section_writer_instructions, final_section_writer_instructions)
from src.report_maistro.configuration import Configuration
from src.report_maistro.utils import tavily_search_async, deduplicate_and_format_sources, format_sections

# LLMs
planner_model = ChatOpenAI(model=Configuration.planner_model, reasoning_effort="medium")
writer_model = ChatAnthropic(model=Configuration.writer_model, temperature=0)

# Nodes
async def generate_report_plan(state: ReportState, config: RunnableConfig):
    """Generate the red team campaign report plan."""
    # Build campaign summary from input fields
    campaign_name = state["campaign_name"]
    campaign_description = state["campaign_description"]
    objectives = state["objectives"]
    feedback = state.get("feedback_on_report_plan", None)

    campaign_summary = f"Campaign Name: {campaign_name}\nDescription: {campaign_description}\nObjectives: {objectives}"

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    report_structure = configurable.report_structure
    number_of_queries = configurable.number_of_queries
    tavily_topic = configurable.tavily_topic
    tavily_days = configurable.tavily_days

    # Ensure report_structure is a string
    if isinstance(report_structure, dict):
        report_structure = str(report_structure)

    # Generate search queries for planning (if needed)
    structured_llm = writer_model.with_structured_output(Queries)
    system_instructions_query = report_planner_query_writer_instructions.format(
        campaign_summary=campaign_summary,
        report_organization=report_structure,
        number_of_queries=number_of_queries
    )

    results = structured_llm.invoke(
        [SystemMessage(content=system_instructions_query)] +
        [HumanMessage(content="Generate search queries to help plan the red team report sections.")]
    )

    query_list = [query.search_query for query in results.queries]
    search_docs = await tavily_search_async(query_list, tavily_topic, tavily_days)
    source_str = deduplicate_and_format_sources(search_docs, max_tokens_per_source=1000, include_raw_content=False)

    system_instructions_sections = report_planner_instructions.format(
        campaign_summary=campaign_summary,
        report_organization=report_structure,
        context=source_str,
        feedback=feedback
    )

    structured_llm = planner_model.with_structured_output(Sections)
    report_sections = structured_llm.invoke(
        [SystemMessage(content=system_instructions_sections)] +
        [HumanMessage(content="Generate the red team report sections. Your response must include a 'sections' field with a list of sections. Each section must have: name, description, research, and content fields.")]
    )

    return {"sections": report_sections.sections}

def human_feedback(state: ReportState):
    """No-op node to capture human feedback (to be updated via UI)."""
    pass

def generate_queries(state: SectionState, config: RunnableConfig):
    """Generate search queries for a given red team report section."""
    section = state["section"]
    configurable = Configuration.from_runnable_config(config)
    number_of_queries = configurable.number_of_queries
    structured_llm = writer_model.with_structured_output(Queries)
    system_instructions = query_writer_instructions.format(
        section_topic=section.description,
        number_of_queries=number_of_queries
    )
    queries = structured_llm.invoke(
        [SystemMessage(content=system_instructions)] +
        [HumanMessage(content="Generate targeted search queries for this red team report section.")]
    )
    return {"search_queries": queries.queries}

async def search_web(state: SectionState, config: RunnableConfig):
    """Search the web for additional red team–related technical content."""
    search_queries = state["search_queries"]
    configurable = Configuration.from_runnable_config(config)
    tavily_topic = configurable.tavily_topic
    tavily_days = configurable.tavily_days
    query_list = [query.search_query for query in search_queries]
    search_docs = await tavily_search_async(query_list, tavily_topic, tavily_days)
    source_str = deduplicate_and_format_sources(search_docs, max_tokens_per_source=5000, include_raw_content=True)
    return {"source_str": source_str}

def write_section(state: SectionState):
    """Write a red team report section using gathered sources."""
    section = state["section"]
    source_str = state["source_str"]
    system_instructions = section_writer_instructions.format(
        section_title=section.name,
        section_topic=section.description,
        context=source_str
    )
    section_content = writer_model.invoke(
        [SystemMessage(content=system_instructions)] +
        [HumanMessage(content="Generate the red team report section content based on the provided sources.")]
    )
    section.content = section_content.content
    return {"completed_sections": [section]}

def initiate_section_writing(state: ReportState):
    """Decide whether to proceed with section writing or to update the report plan."""
    feedback = state.get("feedback_on_report_plan", None)
    if not state.get("accept_report_plan") and feedback:
        return "generate_report_plan"
    else:
        return [
            Send("build_section_with_web_research", {"section": s})
            for s in state["sections"]
            if s.research
        ]

def write_final_sections(state: SectionState):
    """Write sections that do not require further research."""
    section = state["section"]
    completed_report_sections = state["report_sections_from_research"]
    system_instructions = final_section_writer_instructions.format(
        section_title=section.name,
        section_topic=section.description,
        context=completed_report_sections
    )
    section_content = writer_model.invoke(
        [SystemMessage(content=system_instructions)] +
        [HumanMessage(content="Generate the final red team report section content.")]
    )
    section.content = section_content.content
    return {"completed_sections": [section]}

def gather_completed_sections(state: ReportState):
    """Aggregate the content of completed sections for final report synthesis."""
    completed_sections = state["completed_sections"]
    completed_report_sections = format_sections(completed_sections)
    return {"report_sections_from_research": completed_report_sections}

def initiate_final_section_writing(state: ReportState):
    """Initiate writing of final sections (those not requiring additional research)."""
    return [
        Send("write_final_sections", {"section": s, "report_sections_from_research": state["report_sections_from_research"]})
        for s in state["sections"]
        if not s.research
    ]

def write_all_findings(state: ReportState):
    """Generate detailed write-ups for each finding in the campaign."""
    findings = state.get("findings", [])
    finding_writeups = []

    for finding in findings:
        prompt = finding_writer_instructions.format(
            title=finding.title,
            description=finding.description,
            impact=finding.impact,
            remediation=finding.remediation,
            evidence=finding.evidence
        )
        writeup = writer_model.invoke(
            [SystemMessage(content=prompt)] +
            [HumanMessage(content="Generate a detailed write-up for this finding.")]
        )
        finding_writeups.append(f"**{finding.title}**\n\n{writeup.content}")

    # Combine all individual write-ups into a single text block
    combined_findings = "\n\n---\n\n".join(finding_writeups)
    return {"findings_writeup": combined_findings}

def integrate_findings(state: ReportState):
    """Incorporate the generated findings write-up into the Technical Findings section."""
    findings_writeup = state.get("findings_writeup", "")
    # Find the section intended for Technical Findings and update its content
    for section in state["sections"]:
        if "Technical Findings" in section.name:
            section.content = findings_writeup
    return state


def compile_final_report(state: ReportState):
    """Combine all sections into the final red team report."""
    sections = state["sections"]
    completed_sections = {s.name: s.content for s in state["completed_sections"]}
    for section in sections:
        section.content = completed_sections[section.name]
    all_sections = "\n\n".join([s.content for s in sections])
    return {"final_report": all_sections}

# Build the sub-graph for sections
section_builder = StateGraph(SectionState, output=SectionOutputState)
section_builder.add_node("generate_queries", generate_queries)
section_builder.add_node("search_web", search_web)
section_builder.add_node("write_section", write_section)
section_builder.add_edge(START, "generate_queries")
section_builder.add_edge("generate_queries", "search_web")
section_builder.add_edge("search_web", "write_section")
section_builder.add_edge("write_section", END)

# Build the outer graph
builder = StateGraph(ReportState, input=ReportStateInput, output=ReportStateOutput, config_schema=Configuration)
builder.add_node("generate_report_plan", generate_report_plan)
builder.add_node("human_feedback", human_feedback)
builder.add_node("build_section_with_web_research", section_builder.compile())
builder.add_node("gather_completed_sections", gather_completed_sections)
builder.add_node("write_final_sections", write_final_sections)
builder.add_node("compile_final_report", compile_final_report)
builder.add_edge(START, "generate_report_plan")
builder.add_edge("generate_report_plan", "human_feedback")
builder.add_conditional_edges("human_feedback", initiate_section_writing, ["build_section_with_web_research", "generate_report_plan"])
builder.add_edge("build_section_with_web_research", "gather_completed_sections")
builder.add_conditional_edges("gather_completed_sections", initiate_final_section_writing, ["write_final_sections"])

# Findings
#
# Findings
builder.add_node("write_all_findings", write_all_findings)
builder.add_node("integrate_findings", integrate_findings)
# Chain these nodes before compiling the final report:
builder.add_edge("gather_completed_sections", "write_all_findings")
builder.add_edge("write_all_findings", "integrate_findings")
builder.add_edge("integrate_findings", "write_final_sections")

builder.add_edge("write_final_sections", "compile_final_report")
builder.add_edge("compile_final_report", END)

graph = builder.compile(interrupt_before=['human_feedback'])
