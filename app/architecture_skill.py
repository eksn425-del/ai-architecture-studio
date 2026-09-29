from __future__ import annotations

from pathlib import Path


UPSTREAM_REVISION = "8be9ec80359cd90a7cfc5d9b03d2b0cf86188772"
UPSTREAM_NAME = "Mentat-Uran/sketchup-architect-skill"
VENDOR_ROOT = Path(__file__).resolve().parent / "vendor" / "sketchup_architect"
SUPEX_GUIDE_PATH = Path(__file__).resolve().parent / "vendor" / "supex_agent_guide" / "WORKFLOW_EXCERPT.md"
MAX_CONTEXT_CHARS = 12_500

# The upstream skill correctly warns against blindly copying a precedent, but the
# product also serves workflows where the user deliberately asks for a strong
# formal adaptation of a named case study. Earlier thesis-parity runs over-weighted
# the anti-copy wording and the agent explicitly avoided the precedent's key roof /
# silhouette language. Keep authorship with the user: strong adaptation is allowed
# when it is requested, while taskbook/site constraints still win.
_PRECEDENT_FIDELITY_NOTE = """
## User-controlled precedent fidelity

Precedent use is controlled by the user's design intent, not by a blanket anti-copy rule.
If the user asks only for principles, transfer principles. If the user asks for a strong adaptation
of a specific precedent, it is acceptable to carry over concrete massing,
silhouette, roof, bridge, platform, facade-rhythm, circulation, and spatial-sequence logic
and then transform it to fit the actual site, program, dimensions, access, and regulations.
Do not flatten a requested strong-form reference into generic boxes merely to make it look
less similar. Never let precedent fidelity override explicit project constraints or pretend
that a copied detail is technically verified.
""".strip()

_EXECUTION_REUSE_NOTE = """
## Execution-tool preference

Use mature semantic tools before inventing geometry code. When several tools can perform the
same operation, prefer in this order: a namespaced reusable OSS semantic tool (for example
`saie__...`) when available; an existing named Kongxing SketchUp tool; guarded project Ruby
only for genuinely project-specific geometry that the mature tools cannot express. Prefer
stable semantic IDs, batch operations, model queries, and screenshot/readback verification.
Do not compensate for a missing capability by assuming the result succeeded or by reducing a
requested complex form to a generic box.
""".strip()

_CODEX_PARITY_NOTE = """
## Persistent project-coding loop

For non-trivial SketchUp design work, behave like an agentic coding environment rather than a
one-shot tool caller. The current working directory is the project's persistent agent workspace.
Read its README.md before a developed modeling task. Keep durable design decisions in
`notes/design_notes.md`. Author project-specific Ruby under `scripts/`, then execute and revise
that same file with `sketchup_run_workspace_ruby` instead of repeatedly emitting large disposable
inline snippets. Ordinary walls/openings/slabs/roofs should still prefer proven semantic OSS tools.
After every meaningful modeling pass, inspect model state and multiple useful views. Compare the
result against the brief, site, section/circulation logic and requested precedent fidelity, then
revise the same model/scripts. A first-pass rough massing model is not completion when the user
asked for a developed building with recognizable formal/spatial reference logic.
""".strip()

_SECTIONS: tuple[tuple[str, tuple[tuple[str, int], ...]], ...] = (
    ("references/architectural-design.md", (
        ("Establish the design basis", 750),
        ("Program and area balance", 900),
        ("Organize relations before shapes", 850),
        ("Develop plan and section together", 1_150),
        ("Make form, facade and site follow the scheme", 650),
    )),
    ("references/precedent-research.md", (
        ("Synthesize before designing", 950),
    )),
    ("references/project-continuity.md", (
        ("Identity and ownership", 750),
        ("Revision protocol", 900),
    )),
    ("references/ruby-modeling.md", (
        ("Prepare and inspect", 650),
        ("Coordinates and geometry", 750),
        ("Transaction and revision helper", 1_050),
        ("Model organization and views", 800),
    )),
    ("references/model-qa-delivery.md", (
        ("Two complementary reviews", 800),
        ("Iterate against evidence", 500),
        ("Completion report", 500),
    )),
)


def _extract_h2(document: str, title: str) -> str:
    lines = document.splitlines()
    target = f"## {title}"
    start = next((index for index, line in enumerate(lines) if line.strip() == target), None)
    if start is None:
        return ""
    end = next(
        (index for index in range(start + 1, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end]).strip()


def _excerpt_section(section: str, max_chars: int) -> str:
    paragraphs = section.split("\n\n")
    if not paragraphs:
        return ""
    output = [paragraphs[0]]
    used = len(paragraphs[0])
    for paragraph in paragraphs[1:]:
        candidate = "\n\n" + paragraph
        if used + len(candidate) <= max_chars:
            output.append(candidate)
            used += len(candidate)
            continue
        remaining = max_chars - used - 2
        if remaining >= 120 and not paragraph.lstrip().startswith("```"):
            fragment = paragraph[:remaining]
            boundaries = [fragment.rfind(mark) for mark in (". ", ".\n", "; ", "? ", "! ")]
            boundary = max(boundaries)
            if boundary >= min(remaining // 2, 160):
                output.append("\n\n" + fragment[:boundary + 1].rstrip())
        break
    return "".join(output).strip()


def _load_supex_workflow_excerpt() -> str:
    if not SUPEX_GUIDE_PATH.is_file():
        raise FileNotFoundError("Vendored Supex workflow excerpt is missing.")
    return SUPEX_GUIDE_PATH.read_text(encoding="utf-8").strip()


def load_architecture_skill_context(*, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """Load compact reusable architecture + agentic SketchUp workflow context."""
    if max_chars < 512:
        raise ValueError("Architecture skill context limit must be at least 512 characters.")
    blocks = [
        "Architecture workflow context (selectively reused under open-source licenses).",
        f"Architecture source: {UPSTREAM_NAME} @ {UPSTREAM_REVISION}; see app/vendor/sketchup_architect/LICENSE.",
        "Agentic SketchUp workflow source: darwin/supex selected guidance; see app/vendor/supex_agent_guide/LICENSE.",
        _PRECEDENT_FIDELITY_NOTE,
        _EXECUTION_REUSE_NOTE,
        _CODEX_PARITY_NOTE,
        _load_supex_workflow_excerpt(),
    ]
    remaining = max_chars - sum(len(item) + 2 for item in blocks)
    for relative_path, headings in _SECTIONS:
        path = VENDOR_ROOT / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Vendored architecture skill source is missing: {relative_path}")
        document = path.read_text(encoding="utf-8")
        for heading, section_limit in headings:
            section = _extract_h2(document, heading)
            if not section:
                raise ValueError(f"Vendored architecture skill section is missing: {heading}")
            excerpt = _excerpt_section(section, section_limit)
            block = f"\n\n{excerpt}"
            if len(block) > remaining:
                return "\n".join(blocks).rstrip()
            blocks.append(block)
            remaining -= len(block)
    return "\n".join(blocks).rstrip()
