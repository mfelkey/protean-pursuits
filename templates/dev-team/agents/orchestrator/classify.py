import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))
import json
from crewai import Task
from agents.orchestrator.orchestrator import build_devteam_orchestrator, create_project_context, log_event, save_context

def classify_project(natural_language_request: str) -> dict:
    """
    Takes a natural language project request, uses the Master Orchestrator
    to classify it and build a structured project spec.
    Returns a fully initialized project context object.
    """

    orchestrator = build_devteam_orchestrator()

    classification_task = Task(
        description=f"""
You have received the following project request from your human principal:

---
{natural_language_request}
---

Your job is to analyze this request and produce a structured project specification.

Follow these steps exactly:

1. CLASSIFY the project as one of:
   - DEV: Requires only the Software Development Crew
     (software, apps, dashboards, APIs, automation, tools)
   - DS: Requires only the Data Science Crew
     (data analysis, statistical modeling, ML, visualization, reporting)
   - JOINT: Requires both crews with a formal handoff
     (e.g., DS analyzes data then Dev builds a dashboard from the results)

2. EXTRACT the following fields from the request:
   - title: Short project title (5 words max)
   - description: One paragraph summary of what needs to be built
   - business_goal: Why this matters (one sentence)
   - deliverables: List of expected outputs
   - success_criteria: How we know it's done
   - estimated_complexity: LOW | MEDIUM | HIGH
   - data_required: true/false — does this project need existing data?
   - primary_crew: DEV | DS | JOINT
   - handoff_direction: (only for JOINT) DS_TO_DEV | DEV_TO_DS | BIDIRECTIONAL

3. OUTPUT valid JSON only. No explanation, no markdown, no preamble.
   Just the raw JSON object.

Example output format:
{{
  "title": "Project Dashboard",
  "description": "Build an interactive dashboard...",
  "business_goal": "Enable stakeholders to monitor key metrics.",
  "deliverables": ["React dashboard", "PostgreSQL backend", "API layer"],
  "success_criteria": ["Dashboard loads in under 2 seconds", "Shows trip data by month"],
  "estimated_complexity": "HIGH",
  "data_required": true,
  "primary_crew": "JOINT",
  "handoff_direction": "DS_TO_DEV"
}}
""",
        expected_output="A valid JSON object containing the structured project specification.",
        agent=orchestrator
    )

    from crewai import Crew, Process
    crew = Crew(
        agents=[orchestrator],
        tasks=[classification_task],
        process=Process.sequential,
        verbose=True
    )

    print(f"\n🔍 Classifying project request...\n")
    result = crew.kickoff()

    # Parse the JSON output
    try:
        raw = str(result).strip()
        # Strip markdown fences if model adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        structured_spec = json.loads(raw.strip())
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parse failed: {e}")
        print(f"Raw output: {result}")
        structured_spec = {"error": "Classification failed", "raw": str(result)}

    # Build project context
    classification = structured_spec.get("primary_crew", "UNKNOWN")
    context = create_project_context(natural_language_request, classification)
    context["structured_spec"] = structured_spec
    context["status"] = "CLASSIFIED"

    log_event(context, "PROJECT_CLASSIFIED", f"Type: {classification}")
    save_context(context)

    print(f"\n✅ Project classified as: {classification}")
    print(f"📋 Project ID: {context['project_id']}")
    print(f"\n{json.dumps(structured_spec, indent=2)}")

    return context


if __name__ == "__main__":
    # Quick test
    test_request = """
