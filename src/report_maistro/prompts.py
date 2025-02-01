# Prompt to generate a search query to help with planning the red team report
report_planner_query_writer_instructions = """You are an expert cybersecurity analyst tasked with planning a red team campaign report.
The campaign details are as follows:

{campaign_summary}

The report structure should follow these guidelines:

{report_organization}

Your goal is to generate {number_of_queries} search queries that will help gather high-quality reference information (e.g. on exploitation techniques, CVE details, remediation best practices) to further enhance the report.

Ensure each query:
1. Focuses on the relevant red team tactics, techniques, and procedures (TTPs).
2. Is specific enough to yield authoritative sources.
"""

# Prompt to generate the red team report outline
report_planner_instructions = """I want a plan for a cybersecurity red team campaign report.

---

Return a list of sections.

Each section must include:
- Name: Title for the section.
- Description: A brief explanation of what the section will cover.
- Research: Indicate if web research is needed (e.g. for technical details or case studies).
- Content: Leave this blank for now.

The red team campaign details are:

{campaign_summary}

The report should follow this organization:

{report_organization}

If any feedback was provided on a previous plan, include it here:
{feedback}"""

# Query writer instructions (red team–focused)
query_writer_instructions = """Your goal is to generate targeted web search queries to collect technical details for a red team campaign report section.

Section Topic:
{section_topic}

Generate {number_of_queries} queries that:
1. Target red team tactics, exploitation techniques, vulnerability details, or remediation strategies.
2. Include relevant technical terms and, where appropriate, year markers (e.g. "2024 CVE").
3. Are aimed at authoritative sources such as security advisories, vendor documentation, or technical blogs.
"""

# Section writer instructions for a red team report section
section_writer_instructions = """You are a technical writer specialized in cybersecurity reporting. Write one section of a red team campaign report.

Section Topic:
{section_topic}

Guidelines:
1. Technical Accuracy:
   - Use precise terminology and, if applicable, include version numbers and risk ratings.
   - Cite technical sources (e.g., CVE details, vendor advisories) if relevant.
2. Length and Style:
   - Strict 150-200 word limit.
   - Avoid marketing language; keep the tone factual and actionable.
   - Begin with your most important insight in **bold**.
   - Use short paragraphs (2-3 sentences each).
3. Structure:
   - Use Markdown “##” for the section title.
   - Include at most one structural element (a short list or table) if it clarifies key comparisons.
   - End with a “### Sources” section listing your reference URLs.
4. Use this source material:
{context}
"""

# Final section writer instructions (for synthesizing content, e.g. conclusion)
final_section_writer_instructions = """You are a cybersecurity reporting expert tasked with writing the final section of a red team campaign report.

Section to write:
{section_topic}

Available report content:
{context}

Instructions:
For Conclusion:
- Use Markdown “##” for the section title.
- Write a 100-150 word summary that synthesizes the technical findings and remediation recommendations.
- Optionally include a short Markdown table or list to distill key insights.
- End with clear next steps or implications.
- Do not include any separate sources section.
"""
