# React Native Developer Agent — Output Guard Patch

## Problem
The React Native Developer agent completed valid implementation (sections 1-14) but then
entered an infinite loop, repeating identical README boilerplate 100+ times. No stop
condition or token cap was in place.

## Fix 1: Add max_tokens to Task Config (YAML)

In your CrewAI task YAML (e.g., `~/dev-team/agents/mobile/tasks.yaml` or wherever your
mobile sub-team tasks are defined), add `max_tokens` to the React Native Implementation
Report task:

```yaml
react_native_implementation_report:
  description: >
    Generate a complete React Native Implementation Report (RNIR) for the
    assigned project. Include all screens, components, services, stores,
    navigation, and dependency configuration.

    IMPORTANT CONSTRAINTS:
    - Do NOT repeat any section once it has been written.
    - Stop immediately after the "Project Structure Summary" section.
    - Do NOT generate README content, boilerplate, or filler text.
    - Maximum output: one complete implementation report with no duplicates.
  expected_output: >
    A structured implementation report with numbered sections covering:
    screens, shared components, services, state management, navigation,
    styling constants, and dependency list. No repeated sections.
  max_tokens: 4096
  agent: react_native_developer
```

## Fix 2: Add Stop Instruction to Agent Backstory/Goal

In your agent YAML (e.g., `~/dev-team/agents/mobile/agents.yaml`):

```yaml
react_native_developer:
  role: React Native Developer
  goal: >
    Implement mobile applications using React Native and Expo with
    production-quality code, proper state management, and VA design
    language compliance.
  backstory: >
    You are a senior React Native developer specializing in Expo-based
    mobile applications for government healthcare systems. You write
    clean, well-structured code following VA design standards.

    OUTPUT DISCIPLINE: You produce exactly one implementation report
    per task. Once all sections are complete, you STOP. You never
    repeat sections, generate README boilerplate, or produce filler
    content. If you find yourself writing the same content twice,
    stop immediately.
```

## Fix 3: Add Output Validation in Orchestrator (Python)

In your orchestrator (`~/dev-team/agents/orchestrator/orchestrator.py`), add a
post-processing check:

```python
def validate_agent_output(output: str, max_repeats: int = 3) -> str:
    """Detect and truncate runaway repeated output."""
    lines = output.split('\n')
    seen_blocks = {}
    clean_lines = []
    repeat_count = 0

    for line in lines:
        stripped = line.strip()
        if len(stripped) > 20:  # Only check substantial lines
            if stripped in seen_blocks:
                seen_blocks[stripped] += 1
                if seen_blocks[stripped] > max_repeats:
                    repeat_count += 1
                    if repeat_count > 10:
                        clean_lines.append("\n[OUTPUT TRUNCATED: Repetition detected]")
                        break
                    continue
            else:
                seen_blocks[stripped] = 1
        clean_lines.append(line)

    return '\n'.join(clean_lines)
```

Call it after the crew executes:

```python
result = crew.kickoff(inputs=task_inputs)
# Validate output before saving
cleaned_output = validate_agent_output(str(result))
```

## Recommended: Apply All Three

1. **Task YAML** — `max_tokens: 4096` + explicit stop instructions
2. **Agent YAML** — Output discipline in backstory
3. **Orchestrator** — Python safety net for runaway output

The YAML changes prevent the problem. The Python validation catches it if it happens anyway.
