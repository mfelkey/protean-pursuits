"""
core/doc_publisher.py

Protean Pursuits — Document Publisher

Converts agent markdown output to PDF + keeps .md source,
saves both to ~/projects/parallaxedge/docs/ (flat structure).

Naming convention:
  YYYY-MM-DD_{TEAM}_{SLUG}_{RUN_ID}.pdf
  YYYY-MM-DD_{TEAM}_{SLUG}_{RUN_ID}.md

Usage from any team flow:
    from core.doc_publisher import publish_document
    publish_document(
        md_path="output/reports/DS-ABC123_BRIEF_20260323.md",
        team="ds",
        title="PDB-02 StatsBomb Evaluation",
        run_id="DS-ABC123"
    )

Or publish an existing .md file directly:
    python3.11 core/doc_publisher.py --file path/to/doc.md --team legal --title "My Doc"
"""

import os
import re
import sys
import shutil
import argparse
from datetime import datetime, date
from pathlib import Path

from dotenv import load_dotenv
load_dotenv("config/.env")

# Where finished documents go
PARALLAXEDGE_DOCS = Path(
    os.getenv("PARALLAXEDGE_REPO_PATH",
              os.path.expanduser("~/projects/parallaxedge"))
) / "docs"

# Team display names and accent colors (hex)
TEAM_CONFIG = {
    "legal":     {"name": "Legal Team",      "color": "#0A1628", "accent": "#C8962D"},
    "ds":        {"name": "Data Science",    "color": "#1A3A5C", "accent": "#4A90D9"},
    "dev":       {"name": "Dev Team",        "color": "#1A3A2C", "accent": "#4AAD6A"},
    "marketing": {"name": "Marketing",       "color": "#3A1A2C", "accent": "#D94A7A"},
    "strategy":  {"name": "Strategy",        "color": "#2C1A3A", "accent": "#9A4AD9"},
    "design":    {"name": "Design",          "color": "#3A2A1A", "accent": "#D9844A"},
    "qa":        {"name": "QA Team",         "color": "#1A2A3A", "accent": "#4AD9D9"},
    "protean":   {"name": "Protean Pursuits","color": "#0A1628", "accent": "#C8962D"},
}


def slugify(text: str) -> str:
    """Convert title to filename-safe slug."""
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')[:60]


def clean_for_pdf(text: str) -> str:
    """Escape special chars for ReportLab XML."""
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<b><i>\1</i></b>', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;)', '&amp;', text)
    text = text.replace('<', '&lt;').replace('>', '&gt;') \
               .replace('&amp;lt;', '<').replace('&amp;gt;', '>') \
               .replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>') \
               .replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>') \
               .replace('&lt;font', '<font').replace('&lt;/font&gt;', '</font>') \
               .replace('name=&quot;', 'name="').replace('&quot;&gt;', '">')
    return text.strip()


def md_to_pdf(md_content: str, output_path: str, title: str,
              team: str, run_id: str, doc_date: str) -> None:
    """Convert markdown content to a styled PDF."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak,
        HRFlowable, Table, TableStyle
    )

    cfg = TEAM_CONFIG.get(team, TEAM_CONFIG["protean"])
    PRIMARY   = HexColor(cfg["color"])
    ACCENT    = HexColor(cfg["accent"])
    TEXT      = HexColor("#1A1A1A")
    LIGHT     = HexColor("#F5F5F5")
    MID_GREY  = HexColor("#888888")

    # Styles
    styles = getSampleStyleSheet()
    S = lambda name, **kw: ParagraphStyle(name, **kw)

    H1 = S("ppH1", fontName="Helvetica-Bold", fontSize=15, textColor=PRIMARY,
            leading=19, spaceBefore=14, spaceAfter=5)
    H2 = S("ppH2", fontName="Helvetica-Bold", fontSize=12, textColor=PRIMARY,
            leading=16, spaceBefore=10, spaceAfter=3)
    H3 = S("ppH3", fontName="Helvetica-BoldOblique", fontSize=11,
            textColor=HexColor("#444444"), leading=15, spaceBefore=8, spaceAfter=2)
    BODY = S("ppBody", fontName="Helvetica", fontSize=10, textColor=TEXT,
             leading=15, spaceBefore=2, spaceAfter=2)
    BULLET = S("ppBullet", fontName="Helvetica", fontSize=10, textColor=TEXT,
               leading=15, leftIndent=14, spaceBefore=2, spaceAfter=2)
    CODE = S("ppCode", fontName="Courier", fontSize=9, textColor=HexColor("#333333"),
             leading=13, leftIndent=14, backColor=LIGHT)
    DISC = S("ppDisc", fontName="Helvetica-Oblique", fontSize=8, textColor=MID_GREY,
             leading=11)

    def page_deco(canvas, doc):
        canvas.saveState()
        w, h = letter
        if doc.page >= 1:
            # Header bar
            canvas.setFillColor(PRIMARY)
            canvas.rect(0, h - 0.45*inch, w, 0.45*inch, fill=1, stroke=0)
            canvas.setFont("Helvetica-Bold", 8)
            canvas.setFillColor(white)
            canvas.drawString(0.5*inch, h - 0.28*inch, f"ParallaxEdge — {cfg['name']}")
            canvas.setFillColor(ACCENT)
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(w - 0.5*inch, h - 0.28*inch,
                                   f"{run_id}  |  {doc_date}")
            # Footer
            canvas.setFillColor(PRIMARY)
            canvas.rect(0, 0, w, 0.35*inch, fill=1, stroke=0)
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(HexColor("#AAAAAA"))
            canvas.drawString(0.5*inch, 0.12*inch,
                "Protean Pursuits LLC — AI-generated output, not professional advice")
            canvas.setFillColor(ACCENT)
            canvas.drawRightString(w - 0.5*inch, 0.12*inch, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.65*inch, rightMargin=0.65*inch,
        topMargin=0.65*inch, bottomMargin=0.55*inch,
        title=title, author="Protean Pursuits AI",
        subject=f"ParallaxEdge — {cfg['name']}"
    )

    story = []

    # Title block
    hdr_data = [[
        Paragraph(cfg["name"].upper(), S("t1", fontName="Helvetica-Bold",
                  fontSize=9, textColor=ACCENT, leading=12)),
    ],[
        Paragraph(title, S("t2", fontName="Helvetica-Bold", fontSize=20,
                  textColor=white, leading=24)),
    ],[
        Paragraph(f"Run ID: {run_id}  |  Date: {doc_date}  |  Project: ParallaxEdge",
                  S("t3", fontName="Helvetica", fontSize=9,
                    textColor=HexColor("#BBBBBB"), leading=13)),
    ]]
    hdr = Table(hdr_data, colWidths=[7.2*inch])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), PRIMARY),
        ("LEFTPADDING", (0,0), (-1,-1), 20),
        ("TOPPADDING", (0,0), (0,0), 16),
        ("TOPPADDING", (0,1), (0,1), 6),
        ("TOPPADDING", (0,2), (0,2), 4),
        ("BOTTOMPADDING", (0,2), (0,2), 14),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 12))

    # Parse markdown
    lines = md_content.split('\n')
    i = 0
    table_buf = []
    in_table = False

    while i < len(lines):
        line = lines[i]

        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                in_table = True
                table_buf = []
            table_buf.append(line)
            i += 1
            continue
        elif in_table:
            story.extend(_render_table(table_buf, BODY, H3, LIGHT, PRIMARY))
            table_buf = []
            in_table = False

        s = line.strip()
        if not s:
            story.append(Spacer(1, 4))
        elif s.startswith('#### '):
            story.append(Paragraph(clean_for_pdf(s[5:]), H3))
        elif s.startswith('### '):
            story.append(Paragraph(clean_for_pdf(s[4:]), H2))
        elif s.startswith('## '):
            story.append(Paragraph(clean_for_pdf(s[3:]), H1))
        elif s.startswith('# '):
            story.append(Paragraph(clean_for_pdf(s[2:]), H1))
        elif s.startswith('- ') or s.startswith('* '):
            story.append(Paragraph(f"• {clean_for_pdf(s[2:])}", BULLET))
        elif re.match(r'^\d+\.\s', s):
            story.append(Paragraph(f"• {clean_for_pdf(s)}", BULLET))
        elif s.startswith('---'):
            story.append(HRFlowable(width="100%", thickness=0.5,
                                     color=HexColor("#DDDDDD")))
        elif s.startswith('```'):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            if code_lines:
                code_text = '\n'.join(code_lines)
                story.append(Paragraph(
                    code_text.replace('&', '&amp;').replace('<','&lt;').replace('>','&gt;'),
                    CODE))
        else:
            if s:
                story.append(Paragraph(clean_for_pdf(s), BODY))
        i += 1

    if in_table and table_buf:
        story.extend(_render_table(table_buf, BODY, H3, LIGHT, PRIMARY))

    doc.build(story, onFirstPage=page_deco, onLaterPages=page_deco)


def _render_table(lines, body_style, header_style, light, primary):
    from reportlab.platypus import Table, TableStyle, Spacer, Paragraph
    from reportlab.lib.units import inch
    from reportlab.lib.colors import white

    rows = []
    for line in lines:
        if re.match(r'^\s*\|[-:| ]+\|\s*$', line):
            continue
        cells = [clean_for_pdf(c.strip()) for c in
                 line.strip().strip('|').split('|')]
        rows.append(cells)

    if not rows:
        return []

    col_count = max(len(r) for r in rows)
    rows = [r + [''] * (col_count - len(r)) for r in rows]
    col_w = 7.2 * inch / col_count

    para_rows = []
    for ri, row in enumerate(rows):
        st = header_style if ri == 0 else body_style
        para_rows.append([Paragraph(c, st) for c in row])

    from reportlab.lib.colors import HexColor
    t = Table(para_rows, colWidths=[col_w]*col_count, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), primary),
        ("TEXTCOLOR", (0,0), (-1,0), white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [light, white]),
        ("GRID", (0,0), (-1,-1), 0.4, HexColor("#CCCCCC")),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    return [Spacer(1, 6), t, Spacer(1, 6)]


def publish_document(md_path: str, team: str, title: str,
                     run_id: str = None, project: str = "PROJ-PARALLAXEDGE") -> dict:
    """
    Publish a markdown document to parallaxedge/docs/ as PDF + .md.

    Returns dict with pdf_path and md_path in the docs folder.
    """
    PARALLAXEDGE_DOCS.mkdir(parents=True, exist_ok=True)

    md_path = Path(md_path)
    if not md_path.exists():
        print(f"⚠️  Source file not found: {md_path}")
        return {}

    content = md_path.read_text(encoding="utf-8")
    today   = date.today().strftime("%Y-%m-%d")
    run_id  = run_id or md_path.stem.split('_')[0]
    slug    = slugify(title)

    base_name = f"{today}_{team.upper()}_{slug}_{run_id}"
    dest_md   = PARALLAXEDGE_DOCS / f"{base_name}.md"
    dest_pdf  = PARALLAXEDGE_DOCS / f"{base_name}.pdf"

    # Copy .md
    shutil.copy2(md_path, dest_md)

    # Generate PDF
    try:
        md_to_pdf(content, str(dest_pdf), title, team, run_id, today)
        print(f"✅ Published:")
        print(f"   PDF: {dest_pdf}")
        print(f"   MD:  {dest_md}")
        return {"pdf": str(dest_pdf), "md": str(dest_md)}
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        return {"md": str(dest_md)}


def publish_all_pending(teams_dir: str = None) -> list:
    """
    Scan all team output directories and publish any .md files
    not yet in parallaxedge/docs/.
    """
    if teams_dir is None:
        # Try to find protean-pursuits teams directory
        candidates = [
            Path.home() / "projects" / "protean-pursuits" / "teams",
            Path(__file__).resolve().parents[2] / "teams",
        ]
        teams_dir = next((p for p in candidates if p.exists()), None)
        if not teams_dir:
            print("⚠️  Could not locate teams directory")
            return []

    teams_dir = Path(teams_dir)
    published = []
    existing = {p.stem for p in PARALLAXEDGE_DOCS.glob("*.md")}

    team_map = {
        "legal-team": "legal", "ds-team": "ds", "dev-team": "dev",
        "marketing-team": "marketing", "strategy-team": "strategy",
        "design-team": "design", "qa-team": "qa"
    }

    for team_dir in sorted(teams_dir.iterdir()):
        team_key = team_map.get(team_dir.name)
        if not team_key:
            continue
        output_dir = team_dir / "output"
        if not output_dir.exists():
            continue
        for md_file in sorted(output_dir.rglob("*.md")):
            if md_file.name.startswith('.'):
                continue
            run_id = md_file.stem.split('_')[0]
            # Check if already published (by run_id)
            if any(run_id in e for e in existing):
                continue
            title = md_file.stem.replace('_', ' ').replace('-', ' ')
            result = publish_document(str(md_file), team_key, title, run_id)
            if result:
                published.append(result)

    print(f"\n✅ Published {len(published)} new document(s) to parallaxedge/docs/")
    return published


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Protean Pursuits document publisher"
    )
    parser.add_argument("--file", type=str, default=None,
                        help="Path to .md file to publish")
    parser.add_argument("--team", type=str, default="protean",
                        help=f"Team: {list(TEAM_CONFIG.keys())}")
    parser.add_argument("--title", type=str, default=None,
                        help="Document title (defaults to filename)")
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument("--all", action="store_true",
                        help="Publish all pending documents from all teams")
    args = parser.parse_args()

    if args.all:
        publish_all_pending()
    elif args.file:
        title = args.title or Path(args.file).stem.replace('_', ' ')
        publish_document(args.file, args.team, title, args.run_id)
    else:
        print(__doc__)
