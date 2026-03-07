"""Tests for strip_html_comment_attributes() preprocessing."""

from convert import strip_html_comment_attributes


class TestStripHtmlCommentAttributes:
    """Tests for unwrapping Pandoc attributes from HTML comments."""

    def test_basic_width_attribute(self):
        assert strip_html_comment_attributes("<!--{width=55%}-->") == "{width=55%}"

    def test_multiple_attributes_in_block(self):
        assert (
            strip_html_comment_attributes("<!--{width=55% height=auto}-->")
            == "{width=55% height=auto}"
        )

    def test_multiple_occurrences(self):
        text = "![a](a.svg)<!--{width=55%}-->\n![b](b.svg)<!--{width=30%}-->"
        expected = "![a](a.svg){width=55%}\n![b](b.svg){width=30%}"
        assert strip_html_comment_attributes(text) == expected

    def test_inline_with_image(self):
        text = "![alt](img.svg)<!--{width=55%}-->"
        expected = "![alt](img.svg){width=55%}"
        assert strip_html_comment_attributes(text) == expected

    def test_regular_comment_unchanged(self):
        text = "<!-- this is a comment -->"
        assert strip_html_comment_attributes(text) == text

    def test_comment_with_mixed_content_unchanged(self):
        text = "<!--{width=55%} extra text-->"
        assert strip_html_comment_attributes(text) == text

    def test_empty_comment_unchanged(self):
        text = "<!---->"
        assert strip_html_comment_attributes(text) == text

    def test_no_braces_unchanged(self):
        text = "<!--width=55%-->"
        assert strip_html_comment_attributes(text) == text

    def test_class_syntax(self):
        assert strip_html_comment_attributes("<!--{.centered}-->") == "{.centered}"

    def test_no_changes_needed(self):
        text = "Just regular markdown text"
        assert strip_html_comment_attributes(text) == text

    def test_attribute_with_hash_id(self):
        assert strip_html_comment_attributes("<!--{#my-figure}-->") == "{#my-figure}"


class TestStripHtmlCommentLatexCommands:
    """Tests for unwrapping raw LaTeX commands from HTML comments."""

    def test_newpage(self):
        assert strip_html_comment_attributes("<!--\\newpage-->") == "\\newpage"

    def test_clearpage(self):
        assert strip_html_comment_attributes("<!--\\clearpage-->") == "\\clearpage"

    def test_latex_command_with_surrounding_text(self):
        text = "Some text\n<!--\\newpage-->\nMore text"
        expected = "Some text\n\\newpage\nMore text"
        assert strip_html_comment_attributes(text) == expected

    def test_latex_command_with_args_unchanged(self):
        """Commands with arguments like \\textbf{x} should NOT match."""
        text = "<!--\\textbf{hello}-->"
        assert strip_html_comment_attributes(text) == text

    def test_comment_with_latex_and_extra_text_unchanged(self):
        text = "<!--\\newpage some extra-->"
        assert strip_html_comment_attributes(text) == text

    def test_mixed_attributes_and_latex(self):
        text = "![img](a.svg)<!--{width=55%}-->\n<!--\\newpage-->"
        expected = "![img](a.svg){width=55%}\n\\newpage"
        assert strip_html_comment_attributes(text) == expected


class TestProcessMarkdownIntegration:
    """Verify strip_html_comment_attributes is wired into process_markdown."""

    def test_process_markdown_strips_comment_attributes(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("![alt](img.svg)<!--{width=55%}-->\n")

        from convert import process_markdown

        result = process_markdown(
            str(md_file), engine="tectonic", temp_dir=str(tmp_path)
        )
        assert "<!--" not in result
        assert "{width=55%}" in result
