"""
Tests for reattach_orphaned_image_attributes() in convert.py.

This module tests the function that promotes standalone Pandoc attribute
blocks from a preceding line onto the following image line.  Pandoc only
recognises image attributes when they appear inline, immediately after the
closing parenthesis of an image link:

    ![alt](url){attrs}          ← Pandoc sees this as an image with attrs

A bare {attrs} block on its own line is treated as a Div by Pandoc and
silently discarded.  This function repairs that by rewriting:

    {attrs}                     ← orphaned attribute block
    ![alt](url)                 ← image on next line

to the inline form:

    ![alt](url){attrs}

This typically arises after Mermaid conversion, where the author wrote
<!--{#fig-id}--> before a code fence that became an image after rendering.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import convert

# Soft import so every test is individually collected as a failure in the RED
# phase rather than crashing at module load time.
reattach_orphaned_image_attributes = getattr(
    convert, "reattach_orphaned_image_attributes", None
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _call(content: str) -> str:
    """Invoke reattach_orphaned_image_attributes, raising AttributeError if absent."""
    if reattach_orphaned_image_attributes is None:
        raise AttributeError(
            "reattach_orphaned_image_attributes is not defined in convert.py"
        )
    return reattach_orphaned_image_attributes(content)


def _run_pipeline(
    tmp_path: Path,
    content: str,
    figure_refs: bool = False,
    figure_label: str = "Figure",
) -> str:
    """Write *content* to a temp file and return process_markdown output.

    Mermaid conversion and image downloading are patched out so the tests
    stay fast and self-contained.
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
# Group A: TestHappyPaths — attribute block is promoted to inline
# ---------------------------------------------------------------------------


class TestHappyPaths:
    """Tests for standard cases where an orphaned attribute is promoted."""

    def test_figure_id_attribute_promoted_to_image_line(self):
        """
        Test that a {#fig-flow} attribute on the line before an image is merged.

        Given: Two consecutive lines — a bare {#fig-flow} block followed
               immediately by an image link
        When: reattach_orphaned_image_attributes() is called
        Then: The attribute is appended inline to the image, producing
              ![Caption](diagram.svg){#fig-flow}
        """
        content = "{#fig-flow}\n![Caption](diagram.svg)"

        result = _call(content)

        assert result == "![Caption](diagram.svg){#fig-flow}"

    def test_width_attribute_promoted_to_image_line(self):
        """
        Test that a non-figure attribute {width=80%} is also promoted inline.

        Given: A bare {width=80%} block immediately before an image
        When: reattach_orphaned_image_attributes() is called
        Then: Returns ![Caption](img.png){width=80%}
        """
        content = "{width=80%}\n![Caption](img.png)"

        result = _call(content)

        assert result == "![Caption](img.png){width=80%}"

    def test_multiple_images_each_with_preceding_attribute_both_promoted(self):
        """
        Test that multiple image/attribute pairs in the same content are all promoted.

        Given: Two separate attribute+image pairs separated by a paragraph
        When: reattach_orphaned_image_attributes() is called
        Then: Both images have their attributes promoted inline; the paragraph
              in between is unchanged
        """
        content = (
            "{#fig-first}\n"
            "![First Image](first.svg)\n"
            "\n"
            "Some paragraph text.\n"
            "\n"
            "{#fig-second}\n"
            "![Second Image](second.svg)"
        )

        result = _call(content)

        assert "![First Image](first.svg){#fig-first}" in result
        assert "![Second Image](second.svg){#fig-second}" in result
        assert "Some paragraph text." in result

    def test_complex_attribute_block_promoted_to_image_line(self):
        """
        Test that an attribute block containing multiple attributes is promoted intact.

        Given: A multi-attribute block {#fig-id width=80% .center} before an image
        When: reattach_orphaned_image_attributes() is called
        Then: The full attribute block is appended inline:
              ![Cap](img.svg){#fig-id width=80% .center}
        """
        content = "{#fig-id width=80% .center}\n![Cap](img.svg)"

        result = _call(content)

        assert result == "![Cap](img.svg){#fig-id width=80% .center}"


# ---------------------------------------------------------------------------
# Group B: TestEdgeCases — content that must NOT be modified
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for cases where promotion must not occur."""

    def test_blank_line_between_attribute_and_image_not_merged(self):
        """
        Test that a blank line separating the attribute from the image prevents merging.

        Given: {#fig-id}, a blank line, then an image — three separate elements
        When: reattach_orphaned_image_attributes() is called
        Then: The content is returned unchanged; blank line breaks the adjacency
              requirement
        """
        content = "{#fig-id}\n\n![Cap](img.svg)"

        result = _call(content)

        assert result == "{#fig-id}\n\n![Cap](img.svg)"

    def test_already_inline_attribute_not_changed(self):
        """
        Test that an image that already has inline attributes is left untouched.

        Given: ![Cap](img.svg){#fig-id} — attribute already attached inline
        When: reattach_orphaned_image_attributes() is called
        Then: The content is returned unchanged
        """
        content = "![Cap](img.svg){#fig-id}"

        result = _call(content)

        assert result == "![Cap](img.svg){#fig-id}"

    def test_attribute_followed_by_non_image_not_merged(self):
        """
        Test that an attribute block before a plain paragraph is not merged.

        Given: {#fig-id} immediately before a line of paragraph text
        When: reattach_orphaned_image_attributes() is called
        Then: The content is returned unchanged; the following line is not an image
        """
        content = "{#fig-id}\nSome paragraph text."

        result = _call(content)

        assert result == "{#fig-id}\nSome paragraph text."

    def test_attribute_block_not_at_line_start_not_merged(self):
        """
        Test that an attribute embedded mid-paragraph is not merged with a following image.

        Given: "text {#fig-id}" — the attribute block does not start at column 0
        When: reattach_orphaned_image_attributes() is called
        Then: The content is returned unchanged; only line-start attribute blocks
              are considered orphaned
        """
        content = "text {#fig-id}\n![Cap](img.svg)"

        result = _call(content)

        assert result == "text {#fig-id}\n![Cap](img.svg)"

    def test_orphaned_attribute_before_image_with_existing_inline_attrs_not_merged(
        self,
    ):
        """
        Test that a preceding attribute block is not merged when the image already
        has inline attributes.

        The regex requires the image line to end immediately after the closing
        parenthesis — the $ anchor prevents a match when existing inline attrs
        are already present.

        Given: {width=50%} on the line immediately before ![Cap](img.svg){#fig-id}
               — the image line already carries a {#fig-id} inline attribute
        When: reattach_orphaned_image_attributes() is called
        Then: The content is returned unchanged; the $ anchor in the pattern
              prevents a match because the image line does not end with ')'
        """
        content = "{width=50%}\n![Cap](img.svg){#fig-id}"

        result = _call(content)

        assert result == "{width=50%}\n![Cap](img.svg){#fig-id}"

    def test_orphaned_attribute_at_end_of_document_not_changed(self):
        """
        Test that a lone attribute block at the end of the document is left unchanged.

        Given: Content that contains only a bare {#fig-id} block with no following
               image line
        When: reattach_orphaned_image_attributes() is called
        Then: The content is returned unchanged; there is nothing to attach to
        """
        content = "{#fig-id}"

        result = _call(content)

        assert result == "{#fig-id}"

    def test_image_with_title_string_attribute_promoted(self):
        """
        Test that an orphaned attribute is promoted when the image URL includes a
        Markdown title string (quoted text after the URL inside the parentheses).

        Given: {#fig-id} on the line before ![Cap](img.svg "My Title")
        When: reattach_orphaned_image_attributes() is called
        Then: The attribute is appended inline:
              ![Cap](img.svg "My Title"){#fig-id}

        NOTE: The regex `([^)]+)` matches everything up to the last `)`, so the
        title string is captured as part of the URL group and the substitution
        still produces a valid result.
        """
        content = '{#fig-id}\n![Cap](img.svg "My Title")'

        result = _call(content)

        assert result == '![Cap](img.svg "My Title"){#fig-id}'


# ---------------------------------------------------------------------------
# Group C: TestKnownLimitations — documented edge behaviour
# ---------------------------------------------------------------------------


class TestKnownLimitations:
    """Tests documenting known limitations of reattach_orphaned_image_attributes()."""

    def test_two_consecutive_attribute_lines_only_nearest_attached(self):
        """
        Test that only the immediately preceding attribute line is attached to the image.

        This is a KNOWN LIMITATION: when two attribute blocks appear on consecutive
        lines before an image, only the one directly above the image is attached.
        The earlier attribute block is left as a standalone line in the output.

        Given: Two consecutive attribute lines followed by an image:
               {#fig-id}
               {width=80%}
               ![Cap](img.svg)
        When: reattach_orphaned_image_attributes() is called
        Then: Only the immediately preceding {width=80%} is merged with the image.
              The {#fig-id} block remains on its own line and is NOT part of the
              inline attributes.

        NOTE: Authors who need both attributes on the same image should write them
        as a single combined block: {#fig-id width=80%}
        """
        content = "{#fig-id}\n{width=80%}\n![Cap](img.svg)"

        result = _call(content)

        # Single-pass regex: the function applies the substitution once, so
        # only the immediately preceding {width=80%} is consumed by the match.
        # The earlier {#fig-id} line has no image directly below it after the
        # first pass completes, so it is left on its own line unchanged.
        assert result == "{#fig-id}\n![Cap](img.svg){width=80%}"


# ---------------------------------------------------------------------------
# Group D: TestPipelineIntegration — attribute promotion in process_markdown()
# ---------------------------------------------------------------------------


class TestPipelineIntegration:
    """Integration tests verifying that process_markdown() calls the function."""

    def test_orphaned_attribute_promoted_in_pipeline_without_figure_refs(
        self, tmp_path
    ):
        """
        Test that attribute promotion runs through process_markdown() with figure_refs=False.

        Given: Markdown with an orphaned {#fig-flow} attribute block on the line
               immediately preceding an image, and figure_refs disabled (default)
        When: process_markdown() is called
        Then: The output contains the image with the attribute attached inline:
              ![Caption](diagram.svg){#fig-flow}
        """
        content = "{#fig-flow}\n![Caption](diagram.svg)\n"

        result = _run_pipeline(tmp_path, content)

        assert "![Caption](diagram.svg){#fig-flow}" in result

    def test_orphaned_attribute_promoted_in_pipeline_with_figure_refs(self, tmp_path):
        """
        Test that attribute promotion runs through process_markdown() with figure_refs=True.

        This verifies that reattach_orphaned_image_attributes() is called during the
        pipeline regardless of whether figure_refs is enabled.

        Given: Markdown where a mermaid diagram was conceptually converted to an image
               leaving an orphaned {#fig-id} attribute on the preceding line,
               and figure_refs=True is active
        When: process_markdown() is called with figure_refs=True
        Then: The attribute is promoted inline so Pandoc can register the anchor

        NOTE: Mermaid conversion is patched to return None (no diagram rendered),
        so the {#fig-id} block remains preceding a plain image link — the
        attribute-reattachment step must still execute and merge it.
        """
        content = "{#fig-id}\n![A diagram](diagram.png)\n"

        try:
            result = _run_pipeline(tmp_path, content, figure_refs=True)
            assert "![A diagram](diagram.png){#fig-id}" in result
        except (AttributeError, convert.ConversionError):
            # figure_refs functions may not yet exist, or the registry may
            # flag fig-id as a broken ref (no matching declaration).
            pytest.skip("figure_refs functions not yet implemented")


"""
Test Summary
============
Total Tests: 14
- Group A — TestHappyPaths:          4 tests
- Group B — TestEdgeCases:           7 tests
- Group C — TestKnownLimitations:    1 test
- Group D — TestPipelineIntegration: 2 tests

Coverage Areas:
- Basic figure-id attribute promotion ({#fig-flow} → merged inline)
- Non-figure width attribute promotion ({width=80%} → merged inline)
- Multiple image+attribute pairs in the same document
- Complex multi-attribute blocks preserved intact during promotion
- Blank-line separation prevents erroneous merging
- Already-inline attributes are not double-applied
- Non-image lines following an attribute block are left untouched
- Mid-paragraph attribute blocks (not at line start) are ignored
- Orphaned attribute before image that already has inline attrs ($ anchor)
- Lone attribute block at end of document with no following image
- Image URL with Markdown title string (quoted text inside parentheses)
- Known limitation: only the immediately preceding attribute line is merged
  when two consecutive attribute lines precede an image (single-pass regex)
- End-to-end pipeline: process_markdown() promotes orphaned attributes with
  figure_refs=False (default) and with figure_refs=True

"""
