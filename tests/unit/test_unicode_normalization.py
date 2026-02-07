"""Unit tests for Unicode normalization in convert.py."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestNormalizeUnicodeForLatex:
    """Test suite for normalize_unicode_for_latex function."""

    def test_ellipsis_replaced_for_pdflatex(self):
        """
        Given: Content with ellipsis character (U+2026)
        When: Normalized for pdflatex engine
        Then: Ellipsis is replaced with LaTeX \\ldots{} command
        """
        from convert import normalize_unicode_for_latex

        content = "Wait… what happened?"
        result = normalize_unicode_for_latex(content, "pdflatex")
        assert result == r"Wait\ldots{} what happened?"

    def test_right_single_quote_replaced_for_pdflatex(self):
        """
        Given: Content with right single quote (U+2019)
        When: Normalized for pdflatex engine
        Then: Right single quote is replaced with ASCII apostrophe
        """
        from convert import normalize_unicode_for_latex

        content = "It’s working"
        result = normalize_unicode_for_latex(content, "pdflatex")
        assert result == "It's working"

    def test_left_single_quote_replaced_for_pdflatex(self):
        """
        Given: Content with left single quote (U+2018)
        When: Normalized for pdflatex engine
        Then: Left single quote is replaced with backtick
        """
        from convert import normalize_unicode_for_latex

        content = "‘quoted’"
        result = normalize_unicode_for_latex(content, "pdflatex")
        assert result == "`quoted'"

    def test_curly_double_quotes_replaced_for_pdflatex(self):
        """
        Given: Content with curly double quotes (U+201C and U+201D)
        When: Normalized for pdflatex engine
        Then: Curly quotes are replaced with LaTeX-style quotes
        """
        from convert import normalize_unicode_for_latex

        content = "“Hello,” she said."
        result = normalize_unicode_for_latex(content, "pdflatex")
        assert result == "``Hello,'' she said."

    def test_em_dash_replaced_for_pdflatex(self):
        """
        Given: Content with em dash (U+2014)
        When: Normalized for pdflatex engine
        Then: Em dash is replaced with triple hyphens
        """
        from convert import normalize_unicode_for_latex

        content = "word—another word"
        result = normalize_unicode_for_latex(content, "pdflatex")
        assert result == "word---another word"

    def test_en_dash_replaced_for_pdflatex(self):
        """
        Given: Content with en dash (U+2013)
        When: Normalized for pdflatex engine
        Then: En dash is replaced with double hyphens
        """
        from convert import normalize_unicode_for_latex

        content = "pages 1–10"
        result = normalize_unicode_for_latex(content, "pdflatex")
        assert result == "pages 1--10"

    def test_non_breaking_space_replaced_for_pdflatex(self):
        """
        Given: Content with non-breaking space (U+00A0)
        When: Normalized for pdflatex engine
        Then: Non-breaking space is replaced with tilde
        """
        from convert import normalize_unicode_for_latex

        content = "100\u00a0km"  # Non-breaking space
        result = normalize_unicode_for_latex(content, "pdflatex")
        assert result == "100~km"

    def test_unicode_preserved_for_tectonic(self):
        """
        Given: Content with various Unicode characters
        When: Normalized for tectonic engine
        Then: All Unicode characters are preserved unchanged
        """
        from convert import normalize_unicode_for_latex

        # Using explicit Unicode escapes to avoid quote issues in source
        content = "Wait\u2026 It\u2019s \u201cworking\u201d \u2014 pages 1\u201310"
        result = normalize_unicode_for_latex(content, "tectonic")
        assert result == content  # No changes

    def test_unicode_preserved_for_xelatex(self):
        """
        Given: Content with various Unicode characters
        When: Normalized for xelatex engine
        Then: All Unicode characters are preserved unchanged
        """
        from convert import normalize_unicode_for_latex

        # Using explicit Unicode escapes to avoid quote issues in source
        content = "Wait\u2026 It\u2019s \u201cworking\u201d \u2014 pages 1\u201310"
        result = normalize_unicode_for_latex(content, "xelatex")
        assert result == content  # No changes

    def test_unicode_preserved_for_lualatex(self):
        """
        Given: Content with various Unicode characters
        When: Normalized for lualatex engine
        Then: All Unicode characters are preserved unchanged
        """
        from convert import normalize_unicode_for_latex

        # Using explicit Unicode escapes to avoid quote issues in source
        content = "Wait\u2026 It\u2019s \u201cworking\u201d \u2014 pages 1\u201310"
        result = normalize_unicode_for_latex(content, "lualatex")
        assert result == content  # No changes

    def test_multiple_unicode_characters_in_same_string(self):
        """
        Given: Content with multiple different Unicode characters
        When: Normalized for pdflatex engine
        Then: All Unicode characters are replaced appropriately
        """
        from convert import normalize_unicode_for_latex

        # Using explicit Unicode escapes to avoid quote issues in source
        content = "\u201cHello\u2026\u201d she said\u2014it\u2019s \u201cdone\u201d!"
        result = normalize_unicode_for_latex(content, "pdflatex")
        assert result == "``Hello\\ldots{}'' she said---it's ``done''!"

    def test_empty_string_returns_empty(self):
        """
        Given: Empty string
        When: Normalized for any engine
        Then: Empty string is returned
        """
        from convert import normalize_unicode_for_latex

        assert normalize_unicode_for_latex("", "pdflatex") == ""
        assert normalize_unicode_for_latex("", "tectonic") == ""

    def test_ascii_only_unchanged(self):
        """
        Given: Content with only ASCII characters
        When: Normalized for pdflatex engine
        Then: Content is unchanged
        """
        from convert import normalize_unicode_for_latex

        content = "This is plain ASCII text with 'quotes' and -- dashes."
        result = normalize_unicode_for_latex(content, "pdflatex")
        assert result == content

    def test_unknown_engine_preserves_unicode(self):
        """
        Given: Content with Unicode characters and unknown engine name
        When: Normalized for unknown engine (e.g., "unknown_engine")
        Then: Unicode characters are preserved unchanged (safe default behavior)
        """
        from convert import normalize_unicode_for_latex

        content = "Wait\u2026 It\u2019s working"
        result = normalize_unicode_for_latex(content, "unknown_engine")
        assert result == content  # Safe default: preserve Unicode

    def test_none_engine_preserves_unicode(self):
        """
        Given: Content with Unicode characters and None engine
        When: Normalized with engine=None
        Then: Unicode characters are preserved (safe default)
        """
        from convert import normalize_unicode_for_latex

        content = "Wait\u2026 working"
        result = normalize_unicode_for_latex(content, None)
        assert result == content

    def test_empty_string_engine_preserves_unicode(self):
        """
        Given: Content with Unicode characters and empty string engine
        When: Normalized with engine=""
        Then: Unicode characters are preserved (safe default)
        """
        from convert import normalize_unicode_for_latex

        content = "Wait\u2026 working"
        result = normalize_unicode_for_latex(content, "")
        assert result == content

    def test_engine_name_case_insensitive(self):
        """
        Given: Content with Unicode and uppercase engine name
        When: Normalized with engine="PDFLATEX" or "PDFLaTeX"
        Then: Normalization occurs correctly (case-insensitive match)
        """
        from convert import normalize_unicode_for_latex

        content = "Wait\u2026"
        result_upper = normalize_unicode_for_latex(content, "PDFLATEX")
        result_mixed = normalize_unicode_for_latex(content, "PDFLaTeX")
        result_lower = normalize_unicode_for_latex(content, "pdflatex")
        expected = r"Wait\ldots{}"
        assert result_upper == expected
        assert result_mixed == expected
        assert result_lower == expected
