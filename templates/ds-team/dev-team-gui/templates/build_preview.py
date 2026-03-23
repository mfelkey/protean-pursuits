"""Build standalone preview.html with embedded sample data."""
import json, sys, os, re

sys.path.insert(0, os.path.dirname(__file__))
os.environ['DEVTEAM_PROJECT_DIR'] = '/home/claude/dev-team/logs'

from app import PIPELINE, AGENT_DETAILS

# Load template
with open('templates/index.html', 'r') as f:
    html = f.read()

# Load sample project
with open('/home/claude/dev-team/logs/PROJ-TEMPLATE.json', 'r') as f:
    sample_project = json.load(f)

# Build embedded data
pipeline_json = json.dumps(PIPELINE)
agents_json = json.dumps(AGENT_DETAILS)
project_json = json.dumps(sample_project)
projects_list = json.dumps([{
    'id': sample_project['project_id'],
    'status': sample_project['status'],
    'classification': sample_project['classification'],
    'title': sample_project['structured_spec']['title'],
    'created_at': sample_project['created_at'],
    'artifact_count': len(sample_project['artifacts']),
    'checkpoint_count': len(sample_project['checkpoints']),
}])

status_json = json.dumps({
    'project_id': 'PROJ-TEMPLATE',
    'completed_steps': [
        'classify', 'route', 'product_mgr', 'biz_analyst', 'scrum_master',
        'architect', 'security', 'ux_designer', 'ux_content', 'senior_dev', 'backend_dev'
    ],
    'total_web_steps': 16,
    'total_mobile_steps': 10,
})

# Build the replacement fetchJSON
new_fetch = f"""async function fetchJSON(url) {{
  // STANDALONE PREVIEW — embedded data, no server needed
  const EMBEDDED_PIPELINE = {pipeline_json};
  const EMBEDDED_AGENTS = {agents_json};
  const EMBEDDED_PROJECTS = {projects_list};
  const EMBEDDED_PROJECT = {project_json};
  const EMBEDDED_STATUS = {status_json};

  if (url === '/api/pipeline') return EMBEDDED_PIPELINE;
  if (url === '/api/agents') return EMBEDDED_AGENTS;
  if (url === '/api/projects') return EMBEDDED_PROJECTS;
  if (url.includes('/status')) return EMBEDDED_STATUS;
  if (url.includes('/api/projects/')) return EMBEDDED_PROJECT;
  return null;
}}"""

# Replace the original fetchJSON using string search
marker_start = 'async function fetchJSON(url) {'
start_idx = html.index(marker_start)
# Find the closing brace by counting braces
depth = 0
end_idx = start_idx
for i in range(start_idx, len(html)):
    if html[i] == '{':
        depth += 1
    elif html[i] == '}':
        depth -= 1
        if depth == 0:
            end_idx = i + 1
            break
result = html[:start_idx] + new_fetch + html[end_idx:]

# Write preview
with open('preview.html', 'w') as f:
    f.write(result)

# Verify
with open('preview.html', 'r') as f:
    content = f.read()
    assert 'STANDALONE PREVIEW' in content, "Replacement failed!"
    assert 'PROJ-TEMPLATE' in content, "Project data not embedded!"

print("✓ preview.html built successfully")
print(f"  Size: {len(content):,} bytes")
print(f"  Embedded: {len(PIPELINE['web'])} web steps, {len(PIPELINE['mobile'])} mobile steps")
print(f"  Embedded: {len(AGENT_DETAILS)} agent profiles")
