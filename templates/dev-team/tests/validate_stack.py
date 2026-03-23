import sys

checks = []

# 1. Ollama API
try:
    import ollama
    models = ollama.list()
    model_names = [m['model'] for m in models.get('models', [])]
    has_tier1 = any('gpt-oss:120b' in n for n in model_names)
    has_tier2 = any('qwen3-coder:30b' in n for n in model_names)
    has_light = any('gpt-oss:20b' in n for n in model_names)
    checks.append(("Ollama API", True, f"{len(model_names)} models loaded"))
    checks.append(("Tier 1 model (gpt-oss:120b)", has_tier1, ""))
    checks.append(("Tier 2 model (qwen3-coder:30b)", has_tier2, ""))
    checks.append(("Tier 2 Light (gpt-oss:20b)", has_light, ""))
except Exception as e:
    checks.append(("Ollama API", False, str(e)))

# 2. CrewAI
try:
    import crewai
    checks.append(("CrewAI", True, f"v{crewai.__version__}"))
except Exception as e:
    checks.append(("CrewAI", False, str(e)))

# 3. LiteLLM
try:
    import litellm
    checks.append(("LiteLLM", True, "installed"))
except Exception as e:
    checks.append(("LiteLLM", False, str(e)))

# 4. ChromaDB
try:
    import chromadb
    checks.append(("ChromaDB", True, f"v{chromadb.__version__}"))
except Exception as e:
    checks.append(("ChromaDB", False, str(e)))

# 5. GitHub
try:
    from dotenv import load_dotenv
    import os
    from github import Github, Auth
    load_dotenv("config/.env")
    auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
    g = Github(auth=auth)
    user = g.get_user()
    checks.append(("GitHub API", True, f"Connected as {user.login}"))
except Exception as e:
    checks.append(("GitHub API", False, str(e)))

# 6. Python version
version = sys.version_info
checks.append(("Python 3.10-3.13",
    3.10 <= float(f"{version.major}.{version.minor}") <= 3.13,
    f"Python {version.major}.{version.minor}.{version.micro}"))

# Report
print("\n========= STACK VALIDATION REPORT =========")
all_pass = True
for name, passed, note in checks:
    icon = "✅" if passed else "❌"
    print(f"{icon}  {name:<35} {note}")
    if not passed:
        all_pass = False
print("=" * 44)
if all_pass:
    print("🎉 ALL CHECKS PASSED — Ready to build agents!")
else:
    print("⚠️  Some checks failed. Resolve before proceeding.")
