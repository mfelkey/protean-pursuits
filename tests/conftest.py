"""
tests/conftest.py

Shared pytest setup for the Protean Pursuits umbrella test suite.
Puts the umbrella root on sys.path so imports like
`agents.leads.training.training_lead` work from tests.

Also installs lightweight stubs for heavy third-party deps (crewai)
so tests can exercise pure-Python logic without requiring the full
CrewAI+Ollama stack to be installed. Production code is unaffected —
the real crewai resolves first when it's available.
"""
import sys
import types
from pathlib import Path

UMBRELLA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(UMBRELLA_ROOT))


def _install_crewai_stub_if_missing():
    """Minimal crewai shim so agents.leads.* imports succeed without the
    real package present. Only installs if the real package is unavailable."""
    try:
        import crewai  # noqa: F401
        return
    except ImportError:
        pass

    stub = types.ModuleType("crewai")

    class _Noop:
        def __init__(self, *args, **kwargs):
            pass

    stub.Agent = _Noop
    stub.Task = _Noop
    stub.Crew = _Noop
    stub.LLM = _Noop
    stub.Process = types.SimpleNamespace(sequential="sequential")
    sys.modules["crewai"] = stub


_install_crewai_stub_if_missing()
