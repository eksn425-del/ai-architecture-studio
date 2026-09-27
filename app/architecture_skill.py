from __future__ import annotations

from pathlib import Path


UPSTREAM_REVISION = "8be9ec80359cd90a7cfc5d9b03d2b0cf86188772"
UPSTREAM_NAME = "Mentat-Uran/sketchup-architect-skill"
VENDOR_ROOT = Path(__file__).resolve().parent / "vendor" / "sketchup_architect"
MAX_CONTEXT_CHARS = 12_500

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


def load_architecture_skill_context(*, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """Load a compact set of original upstream sections for an architecture turn."""
    if max_chars < 512:
        raise ValueError("Architecture skill context limit must be at least 512 characters.")
    blocks = [
        "Architecture workflow context (selectively reused under the MIT license).",
        f"Source: {UPSTREAM_NAME} @ {UPSTREAM_REVISION}; see app/vendor/sketchup_architect/LICENSE.",
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
