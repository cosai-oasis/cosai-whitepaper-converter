"""
Tests for the --figure-refs feature in the whitepaper converter.

This module tests the automatic figure numbering and cross-reference rewriting
pipeline, which consists of three cooperating functions:

- build_figure_registry()  — scans {#fig-*} Pandoc anchors and assigns numbers
- validate_figure_refs()   — checks all (#fig-*) link targets are declared
- rewrite_figure_refs()    — replaces link text with "Figure N" (or custom label)

The feature is activated in process_markdown() via figure_refs=True and wired
to the --figure-refs CLI flag in main().  Processing occurs after
strip_html_comment_attributes() so <!--{#fig-x}--> anchors are already
unwrapped before the registry is built.

NOTE: This is the RED phase of TDD.  All tests are expected to FAIL because
the implementation functions do not yet exist in convert.py.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import convert

# Soft imports: these functions do not exist yet (RED phase).  Each test that
# calls them will raise AttributeError at call time rather than at collection
# time, so all 30 tests are collected and individually marked as failures.
build_figure_registry = getattr(convert, "build_figure_registry", None)
rewrite_figure_refs = getattr(convert, "rewrite_figure_refs", None)
validate_figure_refs = getattr(convert, "validate_figure_refs", None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(
    tmp_path: Path,
    content: str,
    figure_refs: bool = False,
    figure_label: str = "Figure",
) -> str:
    """Write *content* to a temp file and return process_markdown output.

    Mermaid conversion and image downloading are patched out so the tests
    stay fast and self-contained.  Passes figure_refs and figure_label
    through to process_markdown().
    """
    md_file = tmp_path / "input.md"
    md_file.write_text(content)

    with (
        patch.object(
            convert,
            "convert_mermaid_to_svg",
            return_value=(None, None),
        ),
        patch.object(
            convert,
            "download_image",
            side_effect=lambda url, idx, temp_dir=None: url,
        ),
    ):
        return convert.process_markdown(
            str(md_file),
            engine="tectonic",
            temp_dir=str(tmp_path),
            figure_refs=figure_refs,
            figure_label=figure_label,
        )


# ---------------------------------------------------------------------------
# Group A: TestBuildFigureRegistry
# ---------------------------------------------------------------------------


class TestBuildFigureRegistry:
    """Tests for build_figure_registry() — scanning {#fig-*} anchors."""

    def test_single_image_anchor(self):
        """
        Test that a single image with a fig anchor is registered as Figure 1.

        Given: Markdown with one image using {#fig-arch} Pandoc attribute
        When: build_figure_registry() is called
        Then: Returns {"fig-arch": 1}
        """
        content = "![Architecture diagram](arch.png){#fig-arch}\n"

        result = build_figure_registry(content)

        assert result == {"fig-arch": 1}

    def test_multiple_image_anchors_sequential_numbering(self):
        """
        Test that multiple fig anchors are numbered in document order.

        Given: Markdown with two images each having a distinct fig anchor
        When: build_figure_registry() is called
        Then: Returns {"fig-a": 1, "fig-b": 2} in document order
        """
        content = (
            "![First](a.png){#fig-a}\n\n"
            "Some text in between.\n\n"
            "![Second](b.png){#fig-b}\n"
        )

        result = build_figure_registry(content)

        assert result == {"fig-a": 1, "fig-b": 2}

    def test_mermaid_anchor_before_fence(self):
        """
        Test that {#fig-flow} on the line before a mermaid fence is registered.

        Given: Markdown with a bare {#fig-flow} attribute on the line
               preceding a ```mermaid code fence.  This is the form seen by
               build_figure_registry() AFTER strip_html_comment_attributes()
               has already unwrapped <!--{#fig-flow}--> to {#fig-flow}.
               The registry function only ever sees the unwrapped form.
        When: build_figure_registry() is called
        Then: Returns {"fig-flow": 1}
        """
        content = "{#fig-flow}\n```mermaid\ngraph TD\n    A --> B\n```\n"

        result = build_figure_registry(content)

        assert result == {"fig-flow": 1}

    def test_mixed_image_and_mermaid_anchors(self):
        """
        Test that image anchors and mermaid anchors are both registered.

        Given: Markdown with an image anchor followed by a mermaid anchor
        When: build_figure_registry() is called
        Then: Returns {"fig-arch": 1, "fig-flow": 2} preserving document order
        """
        content = (
            "![Architecture](arch.png){#fig-arch}\n\n"
            "{#fig-flow}\n"
            "```mermaid\n"
            "graph TD\n"
            "    A --> B\n"
            "```\n"
        )

        result = build_figure_registry(content)

        assert result == {"fig-arch": 1, "fig-flow": 2}

    def test_no_figure_anchors_returns_empty(self):
        """
        Test that plain markdown without any fig anchors returns empty dict.

        Given: Markdown with regular headings, paragraphs, and links but no
               {#fig-*} anchors
        When: build_figure_registry() is called
        Then: Returns {}
        """
        content = (
            "# Introduction\n\n"
            "Some plain text.\n\n"
            "See [section two](#section-two) for details.\n\n"
            "## Section Two\n\n"
            "More text.\n"
        )

        result = build_figure_registry(content)

        assert result == {}

    def test_non_fig_anchors_ignored(self):
        """
        Test that anchors with prefixes other than fig- are not registered.

        Given: Markdown containing {#tbl-data} and {#sec-intro} anchors
        When: build_figure_registry() is called
        Then: Returns {} — only fig- prefixed anchors count
        """
        content = (
            "| Col A | Col B |\n"
            "|-------|-------|\n"
            "| 1     | 2     |\n"
            "{#tbl-data}\n\n"
            "## Introduction {#sec-intro}\n\n"
            "Text here.\n"
        )

        result = build_figure_registry(content)

        assert result == {}

    def test_anchor_with_other_attributes(self):
        """
        Test that a fig anchor combined with other attributes is still registered.

        Given: Markdown image with {#fig-arch width=80%} — anchor plus width
        When: build_figure_registry() is called
        Then: Returns {"fig-arch": 1} (extra attributes do not prevent matching)
        """
        content = "![Architecture](arch.png){#fig-arch width=80%}\n"

        result = build_figure_registry(content)

        assert result == {"fig-arch": 1}

    def test_duplicate_anchor_id_uses_first_occurrence(self):
        """
        Test that a duplicate anchor ID is counted only once, at first occurrence.

        Given: Markdown with two separate {#fig-same} anchors
        When: build_figure_registry() is called
        Then: Returns {"fig-same": 1} — only one entry, first wins
        """
        content = (
            "![First](a.png){#fig-same}\n\nSome text.\n\n![Second](b.png){#fig-same}\n"
        )

        result = build_figure_registry(content)

        assert result == {"fig-same": 1}
        assert len(result) == 1

    def test_standalone_anchor_not_before_fence_still_counted(self):
        """
        Test that a {#fig-*} anchor on a standalone line counts as a figure.

        Given: Content with {#fig-orphan} on its own line, not before a code fence
        When: build_figure_registry() is called
        Then: The anchor is included in the registry
        """
        content = "Some text.\n\n{#fig-orphan}\n\nMore text.\n"

        result = build_figure_registry(content)

        assert result == {"fig-orphan": 1}

    def test_anchor_with_dot_in_id(self):
        """
        Test that anchor IDs containing dots are fully captured.

        Given: Content with {#fig-arch.v2} anchor
        When: build_figure_registry() is called
        Then: Returns {"fig-arch.v2": 1} — dot is part of the ID
        """
        content = "![Overview](arch.png){#fig-arch.v2}\n"

        result = build_figure_registry(content)

        assert result == {"fig-arch.v2": 1}


# ---------------------------------------------------------------------------
# Group B: TestRewriteFigureRefs
# ---------------------------------------------------------------------------


class TestRewriteFigureRefs:
    """Tests for rewrite_figure_refs() — replacing link text with Figure N."""

    def test_basic_rewrite(self):
        """
        Test that a basic figure link is rewritten with the registry number.

        Given: Content with [Architecture Overview](#fig-arch), registry
               {"fig-arch": 1}
        When: rewrite_figure_refs() is called
        Then: Returns content with [Figure 1](#fig-arch)
        """
        content = "See [Architecture Overview](#fig-arch) for details.\n"
        registry = {"fig-arch": 1}

        result = rewrite_figure_refs(content, registry)

        assert "[Figure 1](#fig-arch)" in result
        assert "Architecture Overview" not in result

    def test_multiple_refs_different_figures(self):
        """
        Test that multiple links to different figures are all rewritten correctly.

        Given: Content with links to fig-arch (1) and fig-flow (2)
        When: rewrite_figure_refs() is called
        Then: Each link gets the correct number from the registry
        """
        content = (
            "See [System Architecture](#fig-arch) and "
            "[Data Flow](#fig-flow) for context.\n"
        )
        registry = {"fig-arch": 1, "fig-flow": 2}

        result = rewrite_figure_refs(content, registry)

        assert "[Figure 1](#fig-arch)" in result
        assert "[Figure 2](#fig-flow)" in result
        assert "System Architecture" not in result
        assert "Data Flow" not in result

    def test_same_figure_referenced_twice(self):
        """
        Test that two links to the same figure both receive the same number.

        Given: Content with two links both pointing to #fig-arch
        When: rewrite_figure_refs() is called
        Then: Both become [Figure 1](#fig-arch)
        """
        content = (
            "[Architecture diagram](#fig-arch) shows the system. "
            "Refer back to [this diagram](#fig-arch) later.\n"
        )
        registry = {"fig-arch": 1}

        result = rewrite_figure_refs(content, registry)

        assert result.count("[Figure 1](#fig-arch)") == 2
        assert "Architecture diagram" not in result
        assert "this diagram" not in result

    def test_custom_label(self):
        """
        Test that a custom label replaces the default "Figure" prefix.

        Given: Content with [Flow diagram](#fig-x), registry {"fig-x": 3},
               label="Diagram"
        When: rewrite_figure_refs() is called with label="Diagram"
        Then: Returns content with [Diagram 3](#fig-x)
        """
        content = "Refer to [Flow diagram](#fig-x).\n"
        registry = {"fig-x": 3}

        result = rewrite_figure_refs(content, registry, label="Diagram")

        assert "[Diagram 3](#fig-x)" in result
        assert "Flow diagram" not in result

    def test_non_fig_links_unchanged(self):
        """
        Test that links to non-fig anchors are left exactly as-is.

        Given: Content with [intro](#introduction) — no fig- prefix
        When: rewrite_figure_refs() is called
        Then: The link is unchanged
        """
        content = "See the [intro](#introduction) section.\n"
        registry = {"fig-arch": 1}

        result = rewrite_figure_refs(content, registry)

        assert "[intro](#introduction)" in result

    def test_empty_link_text_rewritten(self):
        """
        Test that a link with empty text is still rewritten to Figure N.

        Given: Content with [](#fig-arch) — empty link text
        When: rewrite_figure_refs() is called
        Then: Returns [Figure 1](#fig-arch)
        """
        content = "See [](#fig-arch) above.\n"
        registry = {"fig-arch": 1}

        result = rewrite_figure_refs(content, registry)

        assert "[Figure 1](#fig-arch)" in result

    def test_link_already_correct_still_rewritten(self):
        """
        Test that a link already in the correct form is processed idempotently.

        Given: Content already containing [Figure 1](#fig-arch)
        When: rewrite_figure_refs() is called
        Then: Returns [Figure 1](#fig-arch) — no corruption on second pass
        """
        content = "See [Figure 1](#fig-arch) above.\n"
        registry = {"fig-arch": 1}

        result = rewrite_figure_refs(content, registry)

        assert "[Figure 1](#fig-arch)" in result
        # Ensure no double-wrapping like [Figure 1 Figure 1]
        assert "Figure 1 Figure 1" not in result

    def test_image_caption_with_figure_prefix_unchanged(self):
        """
        Test that image captions containing 'Figure N:' are not modified.

        Given: An image with alt text '![Figure 1: System Overview](arch.png){#fig-arch}'
               and a reference link '[System Overview](#fig-arch)'
        When: rewrite_figure_refs() is called
        Then: The image alt text is unchanged, only the reference link is rewritten
        """
        content = (
            "See [System Overview](#fig-arch) for details.\n\n"
            "![Figure 1: System Overview](arch.png){#fig-arch}\n"
        )
        registry = {"fig-arch": 1}

        result = rewrite_figure_refs(content, registry)

        assert "![Figure 1: System Overview](arch.png){#fig-arch}" in result
        assert "[Figure 1](#fig-arch)" in result

    def test_rewrite_with_dot_in_anchor_id(self):
        """
        Test that figure links with dots in anchor IDs are rewritten correctly.

        Given: A link [text](#fig-arch.v2) and registry with fig-arch.v2
        When: rewrite_figure_refs() is called
        Then: Link becomes [Figure 1](#fig-arch.v2)
        """
        content = "See [the overview](#fig-arch.v2) for details.\n"
        registry = {"fig-arch.v2": 1}

        result = rewrite_figure_refs(content, registry)

        assert "[Figure 1](#fig-arch.v2)" in result


# ---------------------------------------------------------------------------
# Group C: TestValidateFigureRefs
# ---------------------------------------------------------------------------


class TestValidateFigureRefs:
    """Tests for validate_figure_refs() — detecting broken figure references."""

    def test_all_refs_valid_returns_empty(self):
        """
        Test that all declared fig refs produce an empty list (no errors).

        Given: Content with [x](#fig-arch) and registry containing fig-arch
        When: validate_figure_refs() is called
        Then: Returns [] — all references are satisfied
        """
        content = "See [Architecture](#fig-arch) for details.\n"
        registry = {"fig-arch": 1}

        result = validate_figure_refs(content, registry)

        assert result == []

    def test_broken_ref_returns_missing_anchor(self):
        """
        Test that a reference with no matching declaration is returned.

        Given: Content with [x](#fig-missing), registry does not contain
               fig-missing
        When: validate_figure_refs() is called
        Then: Returns ["fig-missing"]
        """
        content = "See [the missing figure](#fig-missing).\n"
        registry = {"fig-arch": 1}

        result = validate_figure_refs(content, registry)

        assert result == ["fig-missing"]

    def test_multiple_broken_refs(self):
        """
        Test that multiple broken references are all returned.

        Given: Content referencing fig-x and fig-y, neither in registry
        When: validate_figure_refs() is called
        Then: Returns a list containing both "fig-x" and "fig-y"
        """
        content = "See [figure x](#fig-x) and [figure y](#fig-y).\n"
        registry = {}

        result = validate_figure_refs(content, registry)

        assert "fig-x" in result
        assert "fig-y" in result
        assert len(result) == 2

    def test_mixed_valid_and_broken(self):
        """
        Test that only the broken reference is returned when one is valid.

        Given: Content referencing fig-arch (in registry) and fig-missing (not
               in registry)
        When: validate_figure_refs() is called
        Then: Returns ["fig-missing"] only
        """
        content = "[Architecture](#fig-arch) and [missing](#fig-missing).\n"
        registry = {"fig-arch": 1}

        result = validate_figure_refs(content, registry)

        assert result == ["fig-missing"]
        assert "fig-arch" not in result

    def test_no_fig_refs_returns_empty(self):
        """
        Test that a document with no fig-prefixed link targets returns empty.

        Given: Content with only [text](#section) — no (#fig-*) links
        When: validate_figure_refs() is called
        Then: Returns [] — nothing to validate
        """
        content = (
            "See the [introduction](#introduction) and [conclusion](#conclusion).\n"
        )
        registry = {}

        result = validate_figure_refs(content, registry)

        assert result == []

    def test_broken_ref_same_anchor_twice_deduplicated(self):
        """
        Test that the same broken anchor appearing twice is reported once.

        Given: Content referencing #fig-missing twice, neither in registry
        When: validate_figure_refs() is called
        Then: Returns ["fig-missing"] — one entry, not two
        """
        content = "[first](#fig-missing) and [second](#fig-missing).\n"
        registry = {}

        result = validate_figure_refs(content, registry)

        assert result == ["fig-missing"]
        assert len(result) == 1

    def test_image_syntax_not_treated_as_broken_ref(self):
        """
        Test that image syntax ![alt](#fig-*) is not flagged as a broken ref.

        Given: Content with image syntax ![alt](#fig-arch) and no registry entry
        When: validate_figure_refs() is called
        Then: Returns empty list — image syntax is not a figure reference
        """
        content = "![Architecture](#fig-arch)\n"
        registry = {}

        result = validate_figure_refs(content, registry)

        assert result == []


# ---------------------------------------------------------------------------
# Group D: TestFigureRefsPipeline
# ---------------------------------------------------------------------------


class TestFigureRefsPipeline:
    """Pipeline integration tests — figure-refs through process_markdown()."""

    def test_figure_refs_disabled_by_default(self, tmp_path):
        """
        Test that figure link text is left unchanged when figure_refs=False.

        Given: Markdown with [Architecture Overview](#fig-arch) link and a
               {#fig-arch} anchor, but figure_refs not enabled
        When: process_markdown() is called without figure_refs=True
        Then: The original link text is preserved in the output
        """
        content = (
            "![Arch](arch.png){#fig-arch}\n\n"
            "See [Architecture Overview](#fig-arch) for details.\n"
        )

        result = _run(tmp_path, content, figure_refs=False)

        assert "Architecture Overview" in result

    def test_figure_refs_enabled_rewrites_links(self, tmp_path):
        """
        Test that enabling figure_refs causes links to be rewritten.

        Given: Markdown with ![arch](arch.png){#fig-arch} and a link
               [see arch](#fig-arch)
        When: process_markdown() is called with figure_refs=True
        Then: The link becomes [Figure 1](#fig-arch)
        """
        content = (
            "![Architecture diagram](arch.png){#fig-arch}\n\n"
            "See [see arch](#fig-arch) for the full picture.\n"
        )

        result = _run(tmp_path, content, figure_refs=True)

        assert "[Figure 1](#fig-arch)" in result
        assert "see arch" not in result

    def test_figure_refs_with_mermaid_anchor(self, tmp_path):
        """
        Test that a mermaid anchor declared via HTML comment is rewritten.

        Given: Markdown with <!--{#fig-flow}--> before a mermaid fence and
               a [see flow](#fig-flow) link
        When: process_markdown() is called with figure_refs=True
        Then: strip_html_comment_attributes() unwraps the comment first,
              then the registry finds {#fig-flow} and rewrites the link
        """
        content = (
            "<!--{#fig-flow}-->\n"
            "```mermaid\n"
            "graph TD\n"
            "    A --> B\n"
            "```\n\n"
            "See [see flow](#fig-flow) above.\n"
        )

        result = _run(tmp_path, content, figure_refs=True)

        assert "[Figure 1](#fig-flow)" in result
        assert "see flow" not in result

    def test_figure_refs_broken_ref_raises_error(self, tmp_path):
        """
        Test that a broken figure reference causes an error to be raised.

        Given: Markdown with a [text](#fig-missing) link but no {#fig-missing}
               anchor declared anywhere in the document
        When: process_markdown() is called with figure_refs=True
        Then: convert.ConversionError is raised and the error message contains
              "fig-missing"
        """
        content = (
            "# Introduction\n\nSee [the missing figure](#fig-missing) for context.\n"
        )

        with pytest.raises(convert.ConversionError) as exc_info:
            _run(tmp_path, content, figure_refs=True)
        assert "fig-missing" in str(exc_info.value)

    def test_figure_refs_ordering_after_comment_stripping(self, tmp_path):
        """
        Test that comment-wrapped anchors are numbered correctly after unwrapping.

        Given: Markdown with two figures — first via <!--{#fig-x}--> (mermaid)
               and second via {#fig-y} (image), with links to both
        When: process_markdown() is called with figure_refs=True
        Then: fig-x gets number 1 (appears first), fig-y gets number 2, and
              both links are rewritten correctly
        """
        content = (
            "<!--{#fig-x}-->\n"
            "```mermaid\n"
            "graph TD\n"
            "    A --> B\n"
            "```\n\n"
            "![Second diagram](second.png){#fig-y}\n\n"
            "See [first figure](#fig-x) and [second figure](#fig-y).\n"
        )

        result = _run(tmp_path, content, figure_refs=True)

        assert "[Figure 1](#fig-x)" in result
        assert "[Figure 2](#fig-y)" in result
        assert "first figure" not in result
        assert "second figure" not in result

    def test_figure_refs_custom_label_in_pipeline(self, tmp_path):
        """
        Test that figure_label is honoured throughout the full pipeline.

        Given: Markdown with ![arch](arch.png){#fig-arch} and [see arch](#fig-arch),
               figure_label="Diagram"
        When: process_markdown() is called with figure_refs=True and
              figure_label="Diagram"
        Then: The link becomes [Diagram 1](#fig-arch)
        """
        content = (
            "![Architecture diagram](arch.png){#fig-arch}\n\n"
            "See [see arch](#fig-arch) for the full picture.\n"
        )

        result = _run(tmp_path, content, figure_refs=True, figure_label="Diagram")

        assert "[Diagram 1](#fig-arch)" in result
        assert "see arch" not in result


# ---------------------------------------------------------------------------
# Group E: TestFigureRefsCLI
# ---------------------------------------------------------------------------


class TestFigureRefsCLI:
    """Tests for --figure-refs and --figure-label argparse flags in main()."""

    def test_figure_refs_flag_parsed(self, tmp_path):
        """
        Test that --figure-refs sets args.figure_refs to True.

        Given: sys.argv contains --figure-refs
        When: argparse in main() parses the arguments
        Then: The conversion runs without argparse error (flag is recognised)
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = [
            "convert.py",
            "input.md",
            str(output_pdf),
            "--figure-refs",
        ]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content") as mock_pm:
                with patch(
                    "convert.subprocess.run",
                    return_value=MagicMock(returncode=0),
                ):
                    with patch("convert.os.path.exists", return_value=True):
                        convert.main()

        # process_markdown should have been called with figure_refs=True
        call_kwargs = mock_pm.call_args
        assert call_kwargs is not None
        assert call_kwargs.kwargs.get("figure_refs") is True

    def test_figure_refs_flag_default_false(self, tmp_path):
        """
        Test that omitting --figure-refs results in figure_refs=False.

        Given: sys.argv does not contain --figure-refs
        When: argparse in main() parses the arguments
        Then: process_markdown is called with the keyword argument
              figure_refs=False (the kwarg must be explicitly forwarded)
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf)]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content") as mock_pm:
                with patch(
                    "convert.subprocess.run",
                    return_value=MagicMock(returncode=0),
                ):
                    with patch("convert.os.path.exists", return_value=True):
                        convert.main()

        call_kwargs = mock_pm.call_args
        assert call_kwargs is not None
        # The implementation must explicitly forward figure_refs as a kwarg;
        # assert it is present in the call (not just absent with a default).
        assert "figure_refs" in call_kwargs.kwargs, (
            "process_markdown was not called with figure_refs keyword argument"
        )
        assert call_kwargs.kwargs["figure_refs"] is False

    def test_figure_label_flag_parsed(self, tmp_path):
        """
        Test that --figure-label Diagram sets figure_label to "Diagram".

        Given: sys.argv contains --figure-label Diagram
        When: argparse in main() parses the arguments
        Then: process_markdown is called with figure_label="Diagram"
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = [
            "convert.py",
            "input.md",
            str(output_pdf),
            "--figure-refs",
            "--figure-label",
            "Diagram",
        ]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content") as mock_pm:
                with patch(
                    "convert.subprocess.run",
                    return_value=MagicMock(returncode=0),
                ):
                    with patch("convert.os.path.exists", return_value=True):
                        convert.main()

        call_kwargs = mock_pm.call_args
        assert call_kwargs is not None
        assert call_kwargs.kwargs.get("figure_label") == "Diagram"

    def test_figure_label_default(self, tmp_path):
        """
        Test that omitting --figure-label results in the default "Figure" label.

        Given: sys.argv contains --figure-refs but no --figure-label
        When: argparse in main() parses the arguments
        Then: process_markdown is called with figure_label="Figure"
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = [
            "convert.py",
            "input.md",
            str(output_pdf),
            "--figure-refs",
        ]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content") as mock_pm:
                with patch(
                    "convert.subprocess.run",
                    return_value=MagicMock(returncode=0),
                ):
                    with patch("convert.os.path.exists", return_value=True):
                        convert.main()

        call_kwargs = mock_pm.call_args
        assert call_kwargs is not None
        assert "figure_label" in call_kwargs.kwargs, (
            "process_markdown was not called with figure_label keyword argument"
        )
        assert call_kwargs.kwargs["figure_label"] == "Figure"


"""
Test Summary
============
Total Tests: 36
- Group A — TestBuildFigureRegistry:   10 tests
- Group B — TestRewriteFigureRefs:     9 tests
- Group C — TestValidateFigureRefs:    7 tests
- Group D — TestFigureRefsPipeline:    6 tests
- Group E — TestFigureRefsCLI:         4 tests

Coverage Areas:
- build_figure_registry: single anchor, multiple anchors, mermaid anchors,
  mixed types, no anchors, non-fig anchors, extra attributes, duplicate IDs,
  standalone orphan anchor not before a code fence, anchor ID containing a dot
- rewrite_figure_refs: basic rewrite, multiple figs, repeated refs, custom
  label, non-fig links untouched, empty link text, idempotency,
  image caption with Figure N: prefix left unchanged, dotted anchor ID
- validate_figure_refs: all valid, single broken, multiple broken, mixed,
  no fig refs at all, same broken anchor deduplicated,
  image syntax ![alt](#fig-*) not treated as a broken reference
- Pipeline integration: feature disabled by default, links rewritten end-to-end,
  mermaid comment-wrapped anchor, broken ref raises ConversionError with
  diagnostic, ordering after comment stripping, custom label propagated
- CLI argparse: --figure-refs recognised and forwarded, default False,
  --figure-label forwarded, default "Figure"

TDD Phase:
  RED — all tests are expected to FAIL until the implementation is added to
  convert.py (build_figure_registry, validate_figure_refs, rewrite_figure_refs,
  updated process_markdown signature, and new argparse flags in main()).
"""
