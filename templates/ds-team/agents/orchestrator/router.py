import sys
sys.path.insert(0, "/home/mfelkey/dev-team")
import json
from agents.orchestrator.orchestrator import log_event, save_context, notify_human

def route_project(context: dict) -> dict:
    """
    Takes a classified project context and routes it to the correct crew.
    Updates context with routing decision and next action.
    Returns updated context.
    """

    project_id = context["project_id"]
    classification = context["classification"]
    spec = context["structured_spec"]
    title = spec.get("title", "Untitled Project")
    complexity = spec.get("estimated_complexity", "UNKNOWN")
    handoff_direction = spec.get("handoff_direction", None)

    print(f"\n🔀 Routing project {project_id}: {title}")
    print(f"   Classification: {classification}")
    print(f"   Complexity: {complexity}")

    if classification == "DEV":
        context["assigned_crew"] = "DEV"
        context["crew_lead"] = "Product Manager"
        context["next_action"] = "DEV_CREW: Requirements and planning phase"
        context["status"] = "ROUTED_TO_DEV"
        log_event(context, "ROUTED", "Assigned to Dev Crew → Product Manager")

    elif classification == "DS":
        context["assigned_crew"] = "DS"
        context["crew_lead"] = "DS Project Lead"
        context["next_action"] = "DS_CREW: Data strategy and ingestion phase"
        context["status"] = "ROUTED_TO_DS"
        log_event(context, "ROUTED", "Assigned to DS Crew → DS Project Lead")

    elif classification == "JOINT":
        context["assigned_crew"] = "JOINT"
        context["crew_lead"] = "Master Orchestrator"
        context["handoff_direction"] = handoff_direction

        if handoff_direction == "DS_TO_DEV":
            context["phase_1_crew"] = "DS"
            context["phase_2_crew"] = "DEV"
            context["next_action"] = "DS_CREW: Data analysis phase (Phase 1 of 2)"
            context["status"] = "ROUTED_TO_DS_PHASE1"
            log_event(context, "ROUTED", "Joint project: DS Crew first → Dev Crew second")

        elif handoff_direction == "DEV_TO_DS":
            context["phase_1_crew"] = "DEV"
            context["phase_2_crew"] = "DS"
            context["next_action"] = "DEV_CREW: Build phase (Phase 1 of 2)"
            context["status"] = "ROUTED_TO_DEV_PHASE1"
            log_event(context, "ROUTED", "Joint project: Dev Crew first → DS Crew second")

        elif handoff_direction == "BIDIRECTIONAL":
            context["next_action"] = "MASTER_ORCHESTRATOR: Manual coordination required"
            context["status"] = "ROUTED_BIDIRECTIONAL"
            log_event(context, "ROUTED", "Bidirectional joint project: manual coordination")

    else:
        context["status"] = "ROUTING_FAILED"
        context["next_action"] = "HUMAN: Classification unclear, manual review needed"
        log_event(context, "ROUTING_FAILED", f"Unknown classification: {classification}")

    save_context(context)

    # Print routing summary
    print(f"\n{'='*60}")
    print(f"📋 ROUTING DECISION")
    print(f"{'='*60}")
    print(f"Project ID:    {project_id}")
    print(f"Title:         {title}")
    print(f"Crew:          {context.get('assigned_crew')}")
    print(f"Lead:          {context.get('crew_lead')}")
    print(f"Status:        {context['status']}")
    print(f"Next Action:   {context['next_action']}")
    if handoff_direction:
        print(f"Handoff:       {handoff_direction}")
    print(f"{'='*60}\n")

    return context


if __name__ == "__main__":
    # Test using the saved context from classify.py
    import os
    import glob

    # Find most recent project context
    logs = sorted(glob.glob("logs/PROJ-*.json"), key=os.path.getmtime, reverse=True)
    if not logs:
        print("No project context found. Run classify.py first.")
        exit(1)

    with open(logs[0]) as f:
        context = json.load(f)

    print(f"📂 Loaded context: {logs[0]}")
    context = route_project(context)
