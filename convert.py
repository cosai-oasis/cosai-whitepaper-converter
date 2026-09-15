"""CoSAI Whitepaper Converter - Transform Markdown to branded PDFs.

This module provides the main conversion pipeline for transforming Markdown
files into professionally formatted PDFs with CoSAI branding. It handles:
- Mermaid diagram rendering to SVG
- Remote image downloading
- Unicode normalization for different LaTeX engines
- HTML to LaTeX conversion (br tags, anchors)
- Table of contents generation
"""

import sys
import os
import re
import shutil
import subprocess
import tempfile
import argparse
import urllib.request
import frontmatter
import json
from typing import Iterable

# LaTeX engine configuration constants
VALID_LATEX_ENGINES = ["tectonic", "pdflatex", "xelatex", "lualatex"]
DEFAULT_LATEX_ENGINE = "tectonic"
CONFIG_FILE_NAME = "converter_config.json"


class ConversionError(Exception):
    """Typed exception for conversion pipeline failures.

    Carries a user-facing message, an optional technical detail, and an
    optional reference to the input file that triggered the error.

    Attributes:
        user_message: Short, human-readable description of the problem.
        detail: Optional longer technical detail (e.g. raw exception text).
        input_file: Optional path to the file that caused the error.
    """

    def __init__(
        self,
        user_message: str,
        detail: str | None = None,
        input_file: str | None = None,
    ) -> None:
        super().__init__(user_message)
        self.user_message = user_message
        self.detail = detail
        self.input_file = input_file

    def __str__(self) -> str:
        return self.user_message


def format_pandoc_error(
    stderr: str,
    input_file: str,
    engine: str,
    debug: bool = False,
) -> str:
    """Format raw pandoc stderr into actionable user-facing text.

    Applies these transformations:
    - Replaces ``processed.md`` with the user's actual input filename.
    - Replaces ``/tmp/cosai_convert_*/`` temp paths with ``<temp>/``.
    - Appends YAML colon-quoting guidance when a YAML parse error is detected.
    - Truncates to 40 lines and appends a ``--debug`` hint when ``debug=False``
      and the stderr exceeds 40 lines.

    Args:
        stderr: Raw stderr output from pandoc.
        input_file: User-supplied input filename shown in place of ``processed.md``.
        engine: LaTeX engine name (currently unused; reserved for future use).
        debug: When True, preserve full stderr without truncation hint.

    Returns:
        Formatted error string, or empty string if ``stderr`` is empty.
    """
    if not stderr:
        return ""

    # Replace internal temp filenames with user-visible names
    text = stderr.replace("processed.md", input_file)

    # Replace temp directory paths with a short placeholder
    text = re.sub(r"/tmp/cosai_convert_[^/]+/", "<temp>/", text)

    # Detect YAML parse errors and append quoting guidance
    if "YAML" in text or "mapping values" in text:
        text += (
            "\nHint: YAML frontmatter values that contain colons must be quoted, "
            'e.g.  title: "My Title: A Subtitle"'
        )

    # Truncate long output when not in debug mode
    lines = text.splitlines()
    if not debug and len(lines) > 40:
        text = (
            "\n".join(lines[:40])
            + "\n(output truncated — rerun with --debug for full output)"
        )

    return text


def format_mermaid_error(stderr: str, index: int, mermaid_code: str) -> str:
    """Format mermaid-cli stderr into a diagnostic message with diagram context.

    Args:
        stderr: Raw stderr output from mermaid-cli.
        index: Zero-based diagram index; displayed to the user as 1-based.
        mermaid_code: Raw Mermaid source code for the failing diagram.

    Returns:
        A formatted error string containing the diagram number, a 3-line
        preview of the source code, and the stderr detail (if any).
    """
    diagram_number = index + 1
    preview_lines = mermaid_code.splitlines()[:3]
    preview = "\n".join(preview_lines)

    parts = [f"Failed to render diagram {diagram_number}:"]
    parts.append(f"  Preview:\n{preview}")
    if stderr:
        parts.append(f"  Error: {stderr}")

    return "\n".join(parts)


def get_asset_path(filename: str) -> str:
    """
    Get asset path, checking assets/ first, then root for backward compat.

    Args:
        filename: Name of the asset file

    Returns:
        Absolute path to the asset file
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_path = os.path.join(script_dir, "assets", filename)
    if os.path.exists(assets_path):
        return assets_path
    return os.path.join(script_dir, filename)  # fallback


def normalize_unicode_for_latex(content: str, engine: str | None) -> str:
    """
    Normalize Unicode characters for LaTeX compatibility.

    For pdflatex, replaces Unicode punctuation with LaTeX commands.
    For Unicode engines (tectonic, xelatex, lualatex), returns content unchanged.

    Args:
        content: Text content to normalize
        engine: LaTeX engine name (case-insensitive). If None, empty, or unknown,
                preserves Unicode (safe default for modern engines).

    Returns:
        Content with Unicode characters normalized for the specified engine.
    """
    # Safe default: preserve Unicode for unknown/None/empty engines
    if not engine or engine.lower() not in ("pdflatex",):
        return content

    replacements = {
        "\u2026": r"\ldots{}",  # … ellipsis
        "\u2019": "'",  # ' right single quote
        "\u2018": "`",  # ' left single quote
        "\u201c": "``",  # " left double quote
        "\u201d": "''",  # " right double quote
        "\u2014": "---",  # — em dash
        "\u2013": "--",  # – en dash
        "\u00a0": "~",  # non-breaking space
    }

    # Replacement order is safe - no single-char replacements overlap or conflict
    for char, replacement in replacements.items():
        content = content.replace(char, replacement)
    return content


def load_converter_config(config_path: str | None = None) -> dict:
    """
    Load converter configuration from JSON file.

    Args:
        config_path: Path to configuration file (converter_config.json)

    Returns:
        Configuration dictionary or empty dict if file missing/invalid
    """
    if config_path is None:
        return {}

    try:
        with open(config_path, "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def get_latex_engine(
    cli_engine: str | None = None, config_path: str | None = None
) -> str:
    """
    Determine LaTeX engine based on priority: CLI > env var > config file > default.

    Args:
        cli_engine: Engine specified via CLI argument
        config_path: Path to configuration file

    Returns:
        Name of LaTeX engine to use (lowercase, validated)

    Raises:
        ValueError: If specified engine is not valid
    """
    engine = None

    # Priority 1: CLI argument (empty string treated as None)
    if cli_engine is not None and cli_engine.strip():
        engine = cli_engine.strip().lower()

    # Priority 2: Environment variable
    if engine is None:
        env_engine = os.environ.get("LATEX_ENGINE")
        if env_engine is not None and env_engine.strip():
            engine = env_engine.strip().lower()

    # Priority 3: Configuration file
    if engine is None:
        config = load_converter_config(config_path)
        if "latex_engine" in config:
            config_engine = config["latex_engine"]
            if config_engine is not None and str(config_engine).strip():
                engine = str(config_engine).strip().lower()

    # Priority 4: Default value
    if engine is None:
        engine = DEFAULT_LATEX_ENGINE

    # Validate engine
    if engine not in VALID_LATEX_ENGINES:
        raise ValueError(
            f"Invalid LaTeX engine '{engine}'. "
            f"Valid engines: {', '.join(VALID_LATEX_ENGINES)}"
        )

    return engine


def extract_mermaid_title(mermaid_code: str) -> tuple[str | None, str]:
    """Extract the title from a Mermaid diagram if present.

    Also applies the CoSAI theme to diagrams that don't have a config section.

    Args:
        mermaid_code: Raw Mermaid diagram code, potentially with YAML frontmatter.

    Returns:
        A tuple of (title, code_without_title) where title is None if not found.

    Raises:
        ConversionError: If the YAML frontmatter in the Mermaid block is malformed.
    """
    try:
        doc = frontmatter.loads(mermaid_code)
    except Exception as exc:
        # Show the first few lines of the block so the user can locate it
        preview = "\n".join(mermaid_code.splitlines()[:6])
        raise ConversionError(
            user_message=(
                f"Invalid YAML frontmatter in mermaid block:\n"
                f"  {exc}\n\n"
                f"  Block starts with:\n"
                f"  ```mermaid\n{preview}\n  ```\n\n"
                f"  Hint: Check indentation, quoting, and use ':' not '=' for YAML keys."
            ),
            detail=str(exc),
        ) from exc
    title = None
    if "title" in doc.metadata:
        title = str(doc.metadata["title"])
        del doc.metadata["title"]
    # define a unified CoSAI mermaid style
    if "config" not in doc.metadata:
        doc.metadata["config"] = {
            "look": "handDrawn",
            "theme": "base",
            "themeVariables": {
                "primaryColor": "#A8D9A4",
                "primaryTextColor": "#3a5837ff",
                "primaryBorderColor": "#60B358",
                "lineColor": "#475467",
                "secondaryColor": "#f2f4f7",
                "tertiaryColor": "#ffffff",
                "edgeLabelBackground": "#EBF6E8",
                "clusterBkg": "#E6EFFF",  # <- subgraph color
                "clusterBorder": "#4D8BFF",
                "titleColor": "#0059ff",
                "fontFamily": '"IBM Plex Sans", sans-serif',
            },
        }
    return title, str(frontmatter.dumps(doc))


def convert_mermaid_to_svg(
    mermaid_code: str, index: int, temp_dir: str | None = None
) -> tuple[str | None, str | None]:
    """Convert a Mermaid code block to an SVG file using mermaid-cli.

    SVG output provides better accessibility:
    - Text remains selectable and searchable in final PDF
    - No tagged PDF warnings
    - Alt text carries through to PDF structure

    Pandoc automatically converts SVG to PDF using rsvg-convert.

    Args:
        mermaid_code: Mermaid diagram code.
        index: Index for unique filename generation.
        temp_dir: Directory to create temp files in. If None, uses cwd.

    Returns:
        A tuple of (svg_filename, title) where both may be None on failure.

    Raises:
        ConversionError: If the Mermaid block contains malformed YAML frontmatter.
            This propagates from extract_mermaid_title() and is intentional — malformed
            YAML is an authoring error that should abort the entire conversion rather
            than silently skip the diagram.
    """
    # Extract title before conversion
    title, code_without_title = extract_mermaid_title(mermaid_code)

    # Create files in temp_dir if provided, otherwise use cwd (backward compat)
    if temp_dir:
        tmp_mmd = os.path.join(temp_dir, f"diagram_{index}.mmd")
        tmp_svg = os.path.join(temp_dir, f"diagram_{index}.svg")
    else:
        tmp_mmd = f"diagram_{index}.mmd"
        tmp_svg = f"diagram_{index}.svg"

    with open(tmp_mmd, "w") as f:
        f.write(code_without_title)

    # Use npx to run mmdc (Mermaid CLI)
    cmd = [
        "npx",
        "-y",
        "@mermaid-js/mermaid-cli",
        "-i",
        tmp_mmd,
        "-o",
        tmp_svg,
        "-c",
        get_asset_path("config.json"),
        "-p",
        get_asset_path("puppeteerConfig.json"),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        stderr_text = e.stderr.decode() if e.stderr else ""
        print(format_mermaid_error(stderr_text, index, mermaid_code), file=sys.stderr)
        return None, None
    finally:
        if os.path.exists(tmp_mmd):
            os.remove(tmp_mmd)

    # Return just filename since pandoc runs from temp_dir
    if temp_dir:
        return os.path.basename(tmp_svg), title
    return tmp_svg, title


def download_image(url: str, index: int, temp_dir: str | None = None) -> str | None:
    """Download an image from a URL to a local temporary file.

    Convert GitHub blob URLs to raw URLs for direct access.

    Args:
        url: URL to download the image from.
        index: Index for unique filename generation.
        temp_dir: Directory to download files to. If None, uses cwd.

    Returns:
        Path to downloaded file, or None on error.
    """
    # Convert GitHub blob URLs to raw URLs
    if "github.com" in url and "/blob/" in url:
        url = url.replace("/blob/", "/raw/")

    try:
        # Determine extension from URL or default to .png
        ext = os.path.splitext(url)[1]
        if not ext or len(ext) > 5:  # Basic check for valid extension
            ext = ".png"

        # Create file in temp_dir if provided, otherwise use cwd (backward compat)
        if temp_dir:
            tmp_img = os.path.join(temp_dir, f"downloaded_image_{index}{ext}")
        else:
            tmp_img = f"downloaded_image_{index}{ext}"

        if not os.path.exists(tmp_img):
            urllib.request.urlretrieve(url, tmp_img)
        # Return just filename since pandoc runs from temp_dir
        if temp_dir:
            return os.path.basename(tmp_img)
        return tmp_img
    except Exception as exc:
        print(f"❌ Failed to download image: {url}: {exc}", file=sys.stderr)
        return None


def strip_blockquote_prefix(text: str) -> str:
    """Strip Markdown blockquote `> ` prefixes from Mermaid block content.

    Applies an all-or-nothing rule: prefixes are only stripped when every
    non-empty line starts with `>`. This prevents accidentally corrupting
    content that is not fully blockquoted.

    Each line is processed as follows:
    - `> content` becomes `content`  (strips `> ` with trailing space)
    - `>content`  becomes `content`  (strips bare `>`)
    - `>`         becomes ``         (empty string)
    - empty line  stays empty

    Args:
        text: Mermaid block content extracted by regex, possibly with `> ` prefixes.

    Returns:
        Text with blockquote prefixes removed, or the original text if not all
        non-empty lines carry a `>` prefix.
    """
    if not text:
        return text

    lines = text.split("\n")
    non_empty_lines = [line for line in lines if line]

    # Safety rule: only strip when every non-empty line starts with `>`
    if not non_empty_lines or not all(line.startswith(">") for line in non_empty_lines):
        return text

    stripped_lines = []
    for line in lines:
        if line.startswith("> "):
            stripped_lines.append(line[2:])
        elif line.startswith(">"):
            stripped_lines.append(line[1:])
        else:
            stripped_lines.append(line)
    return "\n".join(stripped_lines)


def strip_trailing_whitespace(text: str) -> str:
    """Return a copy of text with trailing whitespace removed from every line.

    Markdown hard line breaks (2+ trailing spaces) are preserved as exactly
    two trailing spaces so Pandoc can emit the correct ``\\newline``.

    Args:
        text: The multiline string to process.

    Returns:
        A new string with trailing whitespace removed from each line,
        except lines that use Markdown hard breaks (2+ trailing spaces).
    """
    lines: Iterable[str] = text.splitlines(keepends=True)

    processed_lines = []
    for line in lines:
        content = line.rstrip("\n\r")
        stripped = content.rstrip()
        # 2+ trailing spaces → Markdown hard line break; preserve exactly 2
        # (but only when there is actual text content, not whitespace-only lines)
        if stripped and len(content) - len(stripped) >= 2 and content.endswith("  "):
            processed_lines.append(stripped + "  ")
        else:
            processed_lines.append(stripped)
    return "\n".join(processed_lines)


def build_figure_registry(content: str) -> dict[str, int]:
    """Scan document for {#fig-*} Pandoc anchor attributes and assign numbers.

    Processes anchors in document order. Duplicate IDs keep only the first
    occurrence. Non-fig anchors (e.g. {#tbl-data}, {#sec-intro}) are ignored.

    Args:
        content: Markdown content to scan (after strip_html_comment_attributes
                 has already unwrapped any <!--{#fig-*}--> comments).

    Returns:
        Mapping of anchor ID to sequential figure number, e.g.
        {"fig-arch": 1, "fig-flow": 2}.
    """
    pattern = re.compile(r"\{#(fig-[a-zA-Z0-9._-]+)[^}]*\}")
    registry: dict[str, int] = {}
    counter = 0
    for match in pattern.finditer(content):
        anchor_id = match.group(1)
        if anchor_id not in registry:
            counter += 1
            registry[anchor_id] = counter
    return registry


def validate_figure_refs(content: str, registry: dict[str, int]) -> list[str]:
    """Find all (#fig-*) reference targets not declared in the registry.

    Deduplicates: the same broken anchor appearing multiple times is reported
    once. Order of first appearance is preserved.

    Args:
        content: Markdown content to check.
        registry: Figure registry built by build_figure_registry().

    Returns:
        List of anchor IDs referenced but not found in registry, in order of
        first appearance. Empty list if all references are satisfied.
    """
    pattern = re.compile(r"(?<!!)\[[^\]]*\]\(#(fig-[a-zA-Z0-9._-]+)\)")
    seen: set[str] = set()
    broken: list[str] = []
    for match in pattern.finditer(content):
        anchor_id = match.group(1)
        if anchor_id not in registry and anchor_id not in seen:
            seen.add(anchor_id)
            broken.append(anchor_id)
    return broken


def rewrite_figure_refs(
    content: str, registry: dict[str, int], label: str = "Figure"
) -> str:
    """Replace figure link text with the canonical label and number.

    Transforms ``[any text](#fig-anchor)`` to ``[Figure N](#fig-anchor)``
    where N comes from the registry. Links to non-fig anchors are left
    unchanged. Image syntax ``![alt](path)`` is never modified.

    Args:
        content: Markdown content to rewrite.
        registry: Figure registry built by build_figure_registry().
        label: Prefix to use before the figure number (default: "Figure").

    Returns:
        Content with all registered figure links rewritten.
    """
    # Match [text](#fig-anchor) but NOT ![text](#fig-anchor) (image syntax)
    pattern = re.compile(r"(?<!!)\[([^\]]*)\]\(#(fig-[a-zA-Z0-9._-]+)\)")

    def replacer(match: re.Match) -> str:
        anchor_id = match.group(2)
        if anchor_id in registry:
            number = registry[anchor_id]
            return f"[{label} {number}](#{anchor_id})"
        return match.group(0)

    return pattern.sub(replacer, content)


def reattach_orphaned_image_attributes(content: str) -> str:
    """Promote standalone Pandoc attribute blocks onto the following image line.

    Pandoc only recognises image attributes when they appear inline, immediately
    after the closing parenthesis of an image link::

        ![alt](url){attrs}      ← Pandoc sees this as an image with attrs

    A bare ``{attrs}`` block on its own line is treated as a Div by Pandoc and
    silently discarded.  This function repairs that by rewriting::

        {attrs}                 ← orphaned attribute block
        ![alt](url)             ← image on next line

    to the inline form::

        ![alt](url){attrs}

    This typically arises after Mermaid conversion, where the author wrote
    ``<!--{#fig-id}-->`` before a code fence that became an image after rendering.

    Only the attribute block immediately preceding the image is attached
    (single-pass).  Authors who need multiple attributes should combine them
    into one block, e.g. ``{#fig-id width=80%}``.

    Args:
        content: Markdown source string.

    Returns:
        Content with orphaned attribute blocks reattached inline to following
        images.
    """
    return re.sub(
        r"^(\{[^}]+\})\n(!\[[^\]]*\]\([^)]+\))$",
        r"\2\1",
        content,
        flags=re.MULTILINE,
    )


def strip_html_comment_attributes(content: str) -> str:
    """Strip HTML comment wrappers from Pandoc/LaTeX directives.

    Converts ``<!--{width=55%}-->`` to ``{width=55%}`` and
    ``<!--\\newpage-->`` to ``\\newpage`` so that directives hidden from
    GitHub rendering are still picked up by Pandoc.
    """
    # Pandoc attribute blocks: <!--{width=55%}--> → {width=55%}
    content = re.sub(r"<!--(\{[^}]+\})-->", r"\1", content)
    # Raw LaTeX commands: <!--\newpage--> → \newpage
    content = re.sub(r"<!--(\\[a-zA-Z]+)-->", r"\1", content)
    return content


def process_markdown(
    input_file: str,
    engine: str | None = None,
    temp_dir: str | None = None,
    figure_refs: bool = False,
    figure_label: str = "Figure",
) -> str:
    """Read a Markdown file and preprocess it for LaTeX conversion.

    Performs these transformations:
    1. Strip trailing whitespace
    2. Normalize Unicode characters (for pdflatex)
    3. Remove manual Table of Contents sections
    4. Convert HTML anchor tags to Pandoc format
    5. Strip HTML comment wrappers from Pandoc attributes
    5a. (optional) Build figure registry, validate refs, rewrite figure links
    6. Convert Mermaid diagrams to SVG images
    6b. Reattach orphaned Pandoc attribute blocks to following image lines
    7. Download remote images to local files
    8. Convert HTML break tags to LaTeX newlines

    Args:
        input_file: Path to the input Markdown file.
        engine: LaTeX engine name for Unicode normalization. Should be one of
            VALID_LATEX_ENGINES (tectonic, pdflatex, xelatex, lualatex).
            Pass None to preserve all Unicode characters.
        temp_dir: Directory to create temp files in. If None, uses cwd.
        figure_refs: When True, scan for {#fig-*} anchors, validate that all
            (#fig-*) link targets are declared, and rewrite link text to
            "{figure_label} N". Raises ConversionError on broken refs.
        figure_label: Label prefix used when rewriting figure links (e.g.
            "Figure" produces "Figure 1"). Only used when figure_refs=True.

    Returns:
        Processed Markdown content ready for Pandoc conversion.

    Raises:
        ConversionError: If figure_refs=True and the document contains links
            to undeclared {#fig-*} anchors.
    """
    with open(input_file, "r") as f:
        content = f.read()

    # 1. Strip trailing whitespace
    content = strip_trailing_whitespace(content)

    # 2. Normalize Unicode characters for LaTeX engine compatibility
    content = normalize_unicode_for_latex(content, engine)

    # 3. Remove "Table of Contents" section
    # Matches H1-H4 headings (# through ####) or bold (**) "Table of Contents"
    # at line start, consuming everything until the next heading or end of string
    toc_pattern = re.compile(
        r"^(?:#{1,4}\s+|\*\*)Table of [Cc]ontents\*{0,2}.*?(?=^#|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    content = toc_pattern.sub("", content)

    # 4. Convert HTML anchor tags to Markdown anchors
    # Replace <a id="anchor-name"></a> with []{#anchor-name}
    anchor_pattern = re.compile(r'<a id="([^"]+)"></a>')
    content = anchor_pattern.sub(r"[]{#\1}", content)

    # 5. Strip HTML comment wrappers from Pandoc attributes
    # Converts <!--{width=55%}--> to {width=55%} so attributes hidden from
    # GitHub rendering are still picked up by Pandoc
    content = strip_html_comment_attributes(content)

    # 5a. Figure reference processing (optional, runs after comment unwrapping)
    if figure_refs:
        registry = build_figure_registry(content)
        broken = validate_figure_refs(content, registry)
        if broken:
            broken_list = ", ".join(broken)
            raise ConversionError(
                f"Broken figure reference(s): {broken_list}. "
                f"Declare each anchor with {{#fig-id}} in the document."
            )
        content = rewrite_figure_refs(content, registry, label=figure_label)

    # 6. Handle Mermaid blocks
    # Regex to find mermaid code blocks: ```mermaid ... ```
    mermaid_pattern = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)

    diagram_count = 0

    def mermaid_replacer(match):
        nonlocal diagram_count
        mermaid_code = match.group(1)
        mermaid_code = strip_blockquote_prefix(mermaid_code)
        svg_filename, title = convert_mermaid_to_svg(
            mermaid_code, diagram_count, temp_dir=temp_dir
        )

        if svg_filename:
            diagram_count += 1
            # Use extracted title as caption, or default to empty
            caption = title if title else ""
            return f"![{caption}]({svg_filename})"
        else:
            return match.group(0)  # distinct failure, keep original

    content = mermaid_pattern.sub(mermaid_replacer, content)

    # 6b. Reattach orphaned Pandoc attribute blocks to following image lines
    content = reattach_orphaned_image_attributes(content)

    # 7. Handle Remote Images
    # Regex to find image links: ![alt](url)
    # We are looking for http/https urls
    image_pattern = re.compile(r"!\[(.*?)\]\((http[s]?://.*?)\)")

    image_count = 0

    def image_replacer(match):
        nonlocal image_count
        alt_text = match.group(1)
        url = match.group(2)

        local_filename = download_image(url, image_count, temp_dir=temp_dir)

        if local_filename:
            image_count += 1
            return f"![{alt_text}]({local_filename})"
        else:
            return match.group(0)  # distinct failure, keep original

    content = image_pattern.sub(image_replacer, content)

    # 8. Replace HTML <br /> tags with LaTeX line breaks
    content = content.replace("<br />", " \\newline ")
    content = content.replace("<br/>", " \\newline ")
    content = content.replace("<br>", " \\newline ")
    content = content.replace("</br>", " \\newline ")

    return content


def main() -> None:
    """Parse arguments and execute the Markdown to PDF conversion pipeline."""
    parser = argparse.ArgumentParser(
        description="Convert Markdown to PDF with Mermaid support."
    )
    parser.add_argument("input_file", help="Path to input Markdown file")
    parser.add_argument("output_file", help="Path to output PDF file")
    # Override the Markdown header
    parser.add_argument("--title", help="Document title", default="")
    parser.add_argument("--author", help="Document author(s)", default="")
    parser.add_argument("--date", help="Document date", default="")
    parser.add_argument("--version", help="Version of the paper", default="1.0")
    parser.add_argument(
        "--engine",
        choices=VALID_LATEX_ENGINES,
        help=f"LaTeX engine to use (default: {DEFAULT_LATEX_ENGINE})",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Save intermediate files (processed.md, .tex) and show verbose output",
    )
    parser.add_argument(
        "--figure-refs",
        action="store_true",
        help="Auto-number figures and rewrite [text](#fig-*) links to 'Figure N'",
    )
    parser.add_argument(
        "--figure-label",
        default="Figure",
        help="Label prefix used when rewriting figure links (default: Figure)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"❌ Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Converting {args.input_file}...")

    # Determine which LaTeX engine to use (before processing markdown)
    dep_prefix = "latex-template" if os.path.exists("latex-template") else "."
    config_path = os.path.join(dep_prefix, CONFIG_FILE_NAME)
    engine = get_latex_engine(cli_engine=args.engine, config_path=config_path)

    # Use temporary directory for all conversion artifacts
    with tempfile.TemporaryDirectory(prefix="cosai_convert_") as temp_dir:
        # Process markdown with temp directory for diagrams and images
        try:
            processed_content = process_markdown(
                args.input_file,
                engine,
                temp_dir=temp_dir,
                figure_refs=args.figure_refs,
                figure_label=args.figure_label,
            )
        except ConversionError as exc:
            print(f"❌ {exc}", file=sys.stderr)
            sys.exit(1)

        # Create temporary file for processed markdown in temp directory
        tmp_md_path = os.path.join(temp_dir, "processed.md")
        with open(tmp_md_path, "w") as tmp_md:
            tmp_md.write(processed_content)

        # Copy LaTeX assets to temp directory so tectonic can find them
        # Tectonic looks in cwd for files, so we run pandoc from temp_dir
        latex_assets = [
            "cosai.sty",
            "cosai-logo.png",
            "background.pdf",
            "CoSAI(Light).pdf",
        ]
        for asset in latex_assets:
            src = get_asset_path(asset)
            if os.path.exists(src):
                shutil.copy(src, temp_dir)

        # Use absolute path for output file since we're changing cwd
        output_path = os.path.abspath(args.output_file)
        cmd = [
            "pandoc",
            "-f",
            "markdown+alerts",
            "processed.md",  # relative path since we run from temp_dir
            "-o",
            output_path,
            f"--template={get_asset_path('cosai-template.tex')}",
            f"--lua-filter={get_asset_path('callout.lua')}",
            f"--pdf-engine={engine}",
            "--syntax-highlighting=idiomatic",
            f"--resource-path={os.path.dirname(os.path.abspath(args.input_file)) or '.'}",
        ]

        if not args.debug:
            cmd.insert(1, "--quiet")

        # Add metadata variables if provided
        metadata_args = []
        if args.title:
            metadata_args.extend(["-V", f"title={args.title}"])
        if args.author:
            metadata_args.extend(["-V", f"author={args.author}"])
        if args.date:
            metadata_args.extend(["-V", f"date={args.date}"])
        metadata_args.extend(["-V", f"git={args.version}"])
        cmd.extend(metadata_args)

        try:
            # Run pandoc from temp_dir so tectonic finds assets in cwd
            if args.debug:
                result = subprocess.run(cmd, cwd=temp_dir, text=True)
            else:
                # Capture output to suppress tectonic warnings; show only on error
                result = subprocess.run(
                    cmd, cwd=temp_dir, capture_output=True, text=True
                )
            if result.returncode != 0:
                stderr_text = result.stderr or ""
                formatted = format_pandoc_error(
                    stderr_text,
                    input_file=os.path.basename(args.input_file),
                    engine=engine,
                    debug=args.debug,
                )
                print(f"❌ Conversion failed ({engine})", file=sys.stderr)
                if formatted:
                    print(formatted, file=sys.stderr)
                sys.exit(1)
            print(f"✅ {output_path}")
        except FileNotFoundError:
            print(
                "❌ pandoc not found. Install it from https://pandoc.org/installing.html",
                file=sys.stderr,
            )
            sys.exit(1)

        # Save debug artifacts alongside the output PDF
        if args.debug:
            output_dir = os.path.dirname(output_path) or "."
            stem = os.path.splitext(os.path.basename(output_path))[0]

            # Save preprocessed markdown
            debug_md_path = os.path.join(output_dir, f"{stem}_debug.md")
            with open(debug_md_path, "w") as f:
                f.write(processed_content)
            print(f"  Debug: {debug_md_path}")

            # Generate intermediate LaTeX via second pandoc call
            debug_tex_path = os.path.join(output_dir, f"{stem}_debug.tex")
            tex_cmd = [
                "pandoc",
                "-f",
                "markdown+alerts",
                "processed.md",
                "-s",
                "-t",
                "latex",
                "-o",
                debug_tex_path,
                f"--template={get_asset_path('cosai-template.tex')}",
                f"--lua-filter={get_asset_path('callout.lua')}",
                f"--pdf-engine={engine}",
            ]
            tex_cmd.extend(metadata_args)

            try:
                tex_result = subprocess.run(
                    tex_cmd, cwd=temp_dir, capture_output=True, text=True
                )
                if tex_result.returncode == 0:
                    print(f"  Debug: {debug_tex_path}")
                else:
                    print(
                        f"  Warning: .tex generation failed: {tex_result.stderr}",
                        file=sys.stderr,
                    )
            except FileNotFoundError:
                print(
                    "  Warning: could not generate .tex (pandoc not found)",
                    file=sys.stderr,
                )

    # Temp directory and all contents auto-cleaned by context manager


if __name__ == "__main__":
    main()
