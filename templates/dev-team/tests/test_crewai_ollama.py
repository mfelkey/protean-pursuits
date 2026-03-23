import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai import LLM

load_dotenv("config/.env")

# Tier 1 model (reasoning)
tier1_llm = LLM(
    model="ollama/gpt-oss:120b",
    base_url="http://localhost:11434"
)

# Tier 2 model (coding)
tier2_llm = LLM(
    model="ollama/qwen3-coder:30b",
    base_url="http://localhost:11434"
)

# Agent 1: Product Manager (Tier 1)
pm = Agent(
    role="Product Manager",
    goal="Define clear software requirements from customer input",
    backstory="""You are an experienced Product Manager who translates
    business needs into actionable software requirements.""",
    llm=tier1_llm,
    verbose=True
)

# Agent 2: AI Developer (Tier 2)
dev = Agent(
    role="AI Developer",
    goal="Write clean, working Python code based on specifications",
    backstory="""You are a skilled AI Developer who writes
    production-quality Python code.""",
    llm=tier2_llm,
    verbose=True
)

# Task 1: Requirements
requirements_task = Task(
    description="""Write a concise one-paragraph technical specification
    for a Python function that takes a list of numbers and returns
    the mean, median, and mode. Handle empty lists gracefully.""",
    expected_output="A concise technical specification paragraph.",
    agent=pm
)

# Task 2: Implementation
coding_task = Task(
    description="""Implement the Python function from the specification.
    Include proper error handling and a docstring.""",
    expected_output="Complete working Python code.",
    agent=dev,
    context=[requirements_task]
)

# Assemble crew
crew = Crew(
    agents=[pm, dev],
    tasks=[requirements_task, coding_task],
    process=Process.sequential,
    verbose=True
)

print("\n🚀 Starting CrewAI + Ollama integration test...\n")
result = crew.kickoff()
print("\n✅ Integration test complete!")
print("\n--- FINAL OUTPUT ---")
print(result)
