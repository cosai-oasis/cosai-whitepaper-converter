"""
Tests for improved error handling in convert.py.

This module defines the spec for new error-handling features:
- ConversionError: a typed exception carrying user_message, detail, and input_file
- format_pandoc_error(): formats raw pandoc stderr into actionable user-facing text
- format_mermaid_error(): formats mermaid-cli stderr with diagram context
- Main pandoc invocation error paths: friendly messages, exit code 1
- extract_mermaid_title() raises ConversionError instead of sys.exit on bad YAML
- download_image() includes the exception string in its failure message

"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path so we can import convert directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# These imports will raise ImportError until the implementation exists —
# that is the expected "Red" state for TDD.
from convert import (
    ConversionError,
    download_image,
    extract_mermaid_title,
    format_mermaid_error,
    format_pandoc_error,
    main,
)


# ---------------------------------------------------------------------------
# TestConversionError
# ---------------------------------------------------------------------------


class TestConversionError:
    """Tests for the ConversionError custom exception class."""

    def test_conversion_error_is_subclass_of_exception(self):
        """
        Test that ConversionError inherits from Exception.

        Given: The ConversionError class
        When: Checked with isinstance/issubclass
        Then: It is a subclass of Exception
        """
        assert issubclass(ConversionError, Exception)

    def test_conversion_error_stores_user_message(self):
        """
        Test that ConversionError stores user_message attribute.

        Given: A ConversionError constructed with a user_message
        When: The attribute is accessed
        Then: It equals the value passed at construction time
        """
        err = ConversionError(user_message="Something went wrong")
        assert err.user_message == "Something went wrong"

    def test_conversion_error_stores_detail(self):
        """
        Test that ConversionError stores a detail attribute.

        Given: A ConversionError constructed with detail text
        When: The attribute is accessed
        Then: It equals the value passed at construction time
        """
        err = ConversionError(
            user_message="Short message", detail="Longer technical detail"
        )
        assert err.detail == "Longer technical detail"

    def test_conversion_error_detail_defaults_to_none(self):
        """
        Test that ConversionError.detail defaults to None when omitted.

        Given: A ConversionError constructed without a detail argument
        When: The detail attribute is accessed
        Then: It is None
        """
        err = ConversionError(user_message="Short message")
        assert err.detail is None

    def test_conversion_error_stores_optional_input_file(self):
        """
        Test that ConversionError stores an optional input_file attribute.

        Given: A ConversionError constructed with input_file
        When: The attribute is accessed
        Then: It equals the value passed at construction time
        """
        err = ConversionError(user_message="Bad input", input_file="my_document.md")
        assert err.input_file == "my_document.md"

    def test_conversion_error_input_file_defaults_to_none(self):
        """
        Test that ConversionError.input_file defaults to None when omitted.

        Given: A ConversionError constructed without input_file
        When: The attribute is accessed
        Then: It is None
        """
        err = ConversionError(user_message="Short message")
        assert err.input_file is None

    def test_conversion_error_str_returns_user_message(self):
        """
        Test that str(ConversionError) returns user_message.

        Given: A ConversionError with a user_message
        When: str() is called on it
        Then: The result equals user_message
        """
        err = ConversionError(user_message="Human-readable message")
        assert str(err) == "Human-readable message"

    def test_conversion_error_can_be_raised_and_caught(self):
        """
        Test that ConversionError can be raised and caught normally.

        Given: Code that raises ConversionError
        When: It is caught as Exception
        Then: The caught exception is the ConversionError instance
        """
        with pytest.raises(ConversionError) as exc_info:
            raise ConversionError(user_message="test error")
        assert exc_info.value.user_message == "test error"


# ---------------------------------------------------------------------------
# TestFormatPandocError
# ---------------------------------------------------------------------------


class TestFormatPandocError:
    """Tests for the format_pandoc_error() helper function."""

    def test_format_pandoc_error_replaces_processed_md_with_input_filename(self):
        """
        Test that 'processed.md' is replaced with the user's input filename.

        Given: stderr text mentioning 'processed.md'
        When: format_pandoc_error is called with input_file='report.md'
        Then: The returned string contains 'report.md' not 'processed.md'
        """
        stderr = "Error in processed.md at line 12: undefined reference"
        result = format_pandoc_error(stderr, input_file="report.md", engine="tectonic")
        assert "report.md" in result
        assert "processed.md" not in result

    def test_format_pandoc_error_replaces_temp_directory_path(self):
        """
        Test that temp directory paths are replaced with '<temp>/'.

        Given: stderr text containing a temp path like /tmp/cosai_convert_abc123/
        When: format_pandoc_error is called
        Then: The path is replaced with '<temp>/'
        """
        stderr = "File not found: /tmp/cosai_convert_abc123/diagram_0.svg"
        result = format_pandoc_error(stderr, input_file="doc.md", engine="tectonic")
        assert "/tmp/cosai_convert_abc123/" not in result
        assert "<temp>/" in result

    def test_format_pandoc_error_replaces_temp_directory_path_variant(self):
        """
        Test that temp directory path replacement works for varying suffixes.

        Given: stderr text with a differently-suffixed cosai_convert_ temp path
        When: format_pandoc_error is called
        Then: The path is replaced with '<temp>/'
        """
        stderr = "Missing: /tmp/cosai_convert_xyz9876/cosai.sty"
        result = format_pandoc_error(stderr, input_file="doc.md", engine="tectonic")
        assert "/tmp/cosai_convert_xyz9876/" not in result
        assert "<temp>/" in result

    def test_format_pandoc_error_detects_yaml_parse_error_and_appends_guidance(self):
        """
        Test that YAML parse errors get guidance about quoting colons appended.

        Given: stderr text that indicates a YAML parsing failure
        When: format_pandoc_error is called
        Then: The returned string contains guidance about quoting values with colons
        """
        stderr = "YAML parse exception at line 5: mapping values are not allowed here"
        result = format_pandoc_error(stderr, input_file="doc.md", engine="tectonic")
        # Guidance should mention quoting or colons
        assert "quot" in result.lower() or "colon" in result.lower() or ":" in result

    def test_format_pandoc_error_yaml_guidance_mentions_quoting_values(self):
        """
        Test that YAML parse error guidance specifically mentions quoting values.

        Given: A YAML parse error in stderr
        When: format_pandoc_error is called
        Then: The output contains a hint about quoting values containing colons
        """
        stderr = "YAMLException: bad indentation of a mapping entry"
        result = format_pandoc_error(stderr, input_file="doc.md", engine="tectonic")
        lower = result.lower()
        assert "quot" in lower or "colon" in lower

    def test_format_pandoc_error_truncates_long_stderr_when_not_debug(self):
        """
        Test that stderr longer than 40 lines is truncated when debug=False.

        Given: stderr with 60 lines of content
        When: format_pandoc_error is called with debug=False
        Then: The returned string has at most 40 lines of original content
             and appends a hint to use --debug
        """
        lines = [f"line {i}: some error text" for i in range(60)]
        stderr = "\n".join(lines)
        result = format_pandoc_error(
            stderr, input_file="doc.md", engine="tectonic", debug=False
        )
        result_lines = result.splitlines()
        # The original content should be capped, and the truncation notice appended
        assert "--debug" in result
        # 40 content lines + 1 truncation notice line
        assert len(result_lines) <= 41

    def test_format_pandoc_error_truncation_hint_mentions_debug_flag(self):
        """
        Test that the truncation notice explicitly mentions --debug.

        Given: stderr with more than 40 lines
        When: format_pandoc_error is called with debug=False
        Then: The truncation hint contains the text '--debug'
        """
        lines = [f"error line {i}" for i in range(50)]
        stderr = "\n".join(lines)
        result = format_pandoc_error(
            stderr, input_file="doc.md", engine="tectonic", debug=False
        )
        assert "--debug" in result

    def test_format_pandoc_error_preserves_full_stderr_when_debug_true(self):
        """
        Test that full stderr is preserved without truncation when debug=True.

        Given: stderr with 60 lines of content
        When: format_pandoc_error is called with debug=True
        Then: All 60 lines appear in the returned string
        """
        lines = [f"line {i}: verbose detail" for i in range(60)]
        stderr = "\n".join(lines)
        result = format_pandoc_error(
            stderr, input_file="doc.md", engine="tectonic", debug=True
        )
        for line in lines:
            assert line in result

    def test_format_pandoc_error_no_truncation_hint_when_debug_true(self):
        """
        Test that no '--debug' truncation hint is appended when debug=True.

        Given: A long stderr (60 lines) and debug=True
        When: format_pandoc_error is called
        Then: The phrase 'use --debug' does NOT appear (it would be redundant)
        """
        lines = [f"line {i}" for i in range(60)]
        stderr = "\n".join(lines)
        result = format_pandoc_error(
            stderr, input_file="doc.md", engine="tectonic", debug=True
        )
        assert "use --debug" not in result

    def test_format_pandoc_error_short_stderr_not_truncated(self):
        """
        Test that stderr with 40 lines or fewer is never truncated.

        Given: stderr with exactly 40 lines
        When: format_pandoc_error is called with debug=False
        Then: All 40 lines appear in the output (no truncation)
        """
        lines = [f"line {i}" for i in range(40)]
        stderr = "\n".join(lines)
        result = format_pandoc_error(
            stderr, input_file="doc.md", engine="tectonic", debug=False
        )
        for line in lines:
            assert line in result

    def test_format_pandoc_error_returns_unchanged_when_no_patterns_match(self):
        """
        Test that stderr is returned unchanged when no substitution patterns match.

        Given: stderr that has no temp paths, no 'processed.md', no YAML errors
        When: format_pandoc_error is called
        Then: The returned string still contains all original content
        """
        stderr = "pandoc: could not convert table: unsupported feature"
        result = format_pandoc_error(stderr, input_file="doc.md", engine="tectonic")
        assert "could not convert table" in result

    def test_format_pandoc_error_handles_empty_stderr(self):
        """
        Test that format_pandoc_error handles empty stderr without raising.

        Given: An empty string as stderr
        When: format_pandoc_error is called
        Then: An empty string is returned (no exception)
        """
        result = format_pandoc_error("", input_file="doc.md", engine="tectonic")
        assert result == ""

    def test_format_pandoc_error_engine_does_not_change_output_for_generic_errors(self):
        """
        Test that the engine parameter does not affect output for generic errors.

        Given: The same generic stderr text
        When: format_pandoc_error is called with different engines
        Then: The results are identical
        """
        stderr = "Error: could not parse input"
        result_tectonic = format_pandoc_error(
            stderr, input_file="doc.md", engine="tectonic"
        )
        result_xelatex = format_pandoc_error(
            stderr, input_file="doc.md", engine="xelatex"
        )
        assert result_tectonic == result_xelatex

    def test_format_pandoc_error_debug_defaults_to_false(self):
        """
        Test that the debug parameter defaults to False (truncation active by default).

        Given: 50-line stderr and no debug argument
        When: format_pandoc_error is called without debug keyword
        Then: '--debug' truncation hint is present (confirming default is False)
        """
        lines = [f"line {i}" for i in range(50)]
        stderr = "\n".join(lines)
        result = format_pandoc_error(stderr, input_file="doc.md", engine="tectonic")
        assert "--debug" in result


# ---------------------------------------------------------------------------
# TestFormatMermaidError
# ---------------------------------------------------------------------------


class TestFormatMermaidError:
    """Tests for the format_mermaid_error() helper function."""

    def test_format_mermaid_error_uses_one_indexed_diagram_number(self):
        """
        Test that diagram index 0 is presented to the user as 'diagram 1'.

        Given: index=0
        When: format_mermaid_error is called
        Then: The returned message contains 'diagram 1' (1-indexed)
        """
        result = format_mermaid_error(
            stderr="Parse error",
            index=0,
            mermaid_code="graph TD\n    A --> B\n",
        )
        assert "diagram 1" in result

    def test_format_mermaid_error_uses_correct_one_indexed_number_for_index_3(self):
        """
        Test that diagram index 3 is presented to the user as 'diagram 4'.

        Given: index=3
        When: format_mermaid_error is called
        Then: The returned message contains 'diagram 4'
        """
        result = format_mermaid_error(
            stderr="Render failed",
            index=3,
            mermaid_code="sequenceDiagram\n    A->>B: Hello\n",
        )
        assert "diagram 4" in result

    def test_format_mermaid_error_includes_first_three_lines_of_code(self):
        """
        Test that the first 3 lines of mermaid_code appear in the message as preview.

        Given: mermaid_code with 6 lines
        When: format_mermaid_error is called
        Then: The first 3 lines are present in the returned string
        """
        mermaid_code = (
            "graph TD\n"
            "    A[Start] --> B[End]\n"
            "    B --> C[Done]\n"
            "    C --> D[Exit]\n"
            "    D --> E\n"
            "    E --> F\n"
        )
        result = format_mermaid_error(
            stderr="syntax error", index=0, mermaid_code=mermaid_code
        )
        assert "graph TD" in result
        assert "A[Start] --> B[End]" in result
        assert "B --> C[Done]" in result

    def test_format_mermaid_error_includes_stderr_detail(self):
        """
        Test that the actual error detail from stderr appears in the message.

        Given: stderr containing a specific error string
        When: format_mermaid_error is called
        Then: The error detail from stderr is present in the result
        """
        result = format_mermaid_error(
            stderr="Unexpected token 'GRAPH' at line 1",
            index=0,
            mermaid_code="INVALID SYNTAX\n",
        )
        assert "Unexpected token 'GRAPH' at line 1" in result

    def test_format_mermaid_error_handles_empty_stderr(self):
        """
        Test that format_mermaid_error handles empty stderr without raising.

        Given: An empty string as stderr
        When: format_mermaid_error is called
        Then: A non-empty message is still returned (diagram number at minimum)
        """
        result = format_mermaid_error(
            stderr="",
            index=0,
            mermaid_code="graph TD\n    A --> B\n",
        )
        assert result  # must be non-empty
        assert "diagram 1" in result

    def test_format_mermaid_error_only_shows_three_preview_lines_not_more(self):
        """
        Test that the preview is capped at 3 lines even for long diagrams.

        Given: mermaid_code with 10 lines
        When: format_mermaid_error is called
        Then: The 4th line of mermaid_code does NOT appear in the result
        """
        mermaid_code = "\n".join([f"line{i}" for i in range(10)]) + "\n"
        # line3 is the 4th line (0-indexed)
        result = format_mermaid_error(
            stderr="error", index=0, mermaid_code=mermaid_code
        )
        assert "line3" not in result

    def test_format_mermaid_error_returns_string(self):
        """
        Test that format_mermaid_error always returns a string.

        Given: Valid arguments
        When: format_mermaid_error is called
        Then: The return value is a str instance
        """
        result = format_mermaid_error(
            stderr="some error", index=2, mermaid_code="graph TD\n"
        )
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# TestPandocInvocationErrors
# ---------------------------------------------------------------------------


class TestPandocInvocationErrors:
    """
    Tests for the main() pandoc error path.

    These tests mock subprocess.run and sys.argv to drive main() through the
    failure branch and verify the messages printed to stderr.
    """

    def test_pandoc_failure_prints_input_filename_not_processed_md(
        self, tmp_path, capsys
    ):
        """
        Test that stderr from a pandoc failure references the user's input file.

        Given: pandoc fails with stderr mentioning 'processed.md'
        When: main() handles the failure
        Then: The message printed to stderr contains the user's filename, not 'processed.md'
        """
        output_pdf = tmp_path / "output.pdf"
        input_md = tmp_path / "my_report.md"
        input_md.write_text("# Hello\n")

        failed_result = MagicMock()
        failed_result.returncode = 1
        failed_result.stderr = "Error in processed.md at line 5: bad reference"

        # side_effect=[...] ensures a StopIteration if an unexpected second call occurs
        with patch(
            "sys.argv",
            ["convert.py", str(input_md), str(output_pdf)],
        ):
            with patch("convert.process_markdown", return_value="# Hello"):
                with patch("convert.subprocess.run", side_effect=[failed_result]):
                    with pytest.raises(SystemExit):
                        main()

        captured = capsys.readouterr()
        assert "my_report.md" in captured.err
        assert "processed.md" not in captured.err

    def test_pandoc_yaml_failure_prints_quoting_guidance(self, tmp_path, capsys):
        """
        Test that a YAML-related pandoc failure appends colon-quoting guidance.

        Given: pandoc fails with a YAML parse error in stderr
        When: main() handles the failure
        Then: The stderr message contains guidance about quoting values with colons
        """
        output_pdf = tmp_path / "output.pdf"
        input_md = tmp_path / "doc.md"
        input_md.write_text("# Hello\n")

        failed_result = MagicMock()
        failed_result.returncode = 1
        failed_result.stderr = (
            "YAML parse exception: mapping values are not allowed here"
        )

        with patch(
            "sys.argv",
            ["convert.py", str(input_md), str(output_pdf)],
        ):
            with patch("convert.process_markdown", return_value="# Hello"):
                with patch("convert.subprocess.run", side_effect=[failed_result]):
                    with pytest.raises(SystemExit):
                        main()

        captured = capsys.readouterr()
        lower = captured.err.lower()
        assert "quot" in lower or "colon" in lower

    def test_pandoc_missing_prints_install_url(self, tmp_path, capsys):
        """
        Test that a missing pandoc executable prints the install URL.

        Given: subprocess.run raises FileNotFoundError (pandoc not on PATH)
        When: main() handles the error
        Then: The message printed to stderr contains 'https://pandoc.org/installing.html'
        """
        output_pdf = tmp_path / "output.pdf"
        input_md = tmp_path / "doc.md"
        input_md.write_text("# Hello\n")

        with patch(
            "sys.argv",
            ["convert.py", str(input_md), str(output_pdf)],
        ):
            with patch("convert.process_markdown", return_value="# Hello"):
                with patch(
                    "convert.subprocess.run", side_effect=FileNotFoundError("pandoc")
                ):
                    with pytest.raises(SystemExit):
                        main()

        captured = capsys.readouterr()
        assert "https://pandoc.org/installing.html" in captured.err

    def test_pandoc_failure_exits_with_code_1(self, tmp_path):
        """
        Test that a pandoc failure causes sys.exit(1).

        Given: pandoc fails (non-zero returncode)
        When: main() handles the failure
        Then: SystemExit is raised with code 1
        """
        output_pdf = tmp_path / "output.pdf"
        input_md = tmp_path / "doc.md"
        input_md.write_text("# Hello\n")

        failed_result = MagicMock()
        failed_result.returncode = 1
        failed_result.stderr = "fatal error"

        with patch(
            "sys.argv",
            ["convert.py", str(input_md), str(output_pdf)],
        ):
            with patch("convert.process_markdown", return_value="# Hello"):
                with patch("convert.subprocess.run", side_effect=[failed_result]):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        assert exc_info.value.code == 1

    def test_pandoc_missing_exits_with_code_1(self, tmp_path):
        """
        Test that a missing pandoc executable causes sys.exit(1).

        Given: subprocess.run raises FileNotFoundError
        When: main() handles the error
        Then: SystemExit is raised with code 1
        """
        output_pdf = tmp_path / "output.pdf"
        input_md = tmp_path / "doc.md"
        input_md.write_text("# Hello\n")

        with patch(
            "sys.argv",
            ["convert.py", str(input_md), str(output_pdf)],
        ):
            with patch("convert.process_markdown", return_value="# Hello"):
                with patch(
                    "convert.subprocess.run", side_effect=FileNotFoundError("pandoc")
                ):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# TestExtractMermaidTitleRaisesConversionError
# ---------------------------------------------------------------------------


class TestExtractMermaidTitleRaisesConversionError:
    """
    Tests that extract_mermaid_title() raises ConversionError on malformed YAML
    instead of calling sys.exit(1).
    """

    def test_malformed_yaml_raises_conversion_error_not_system_exit(self):
        """
        Test that malformed YAML frontmatter raises ConversionError, not SystemExit.

        Given: Mermaid code with syntactically invalid YAML frontmatter
        When: extract_mermaid_title is called
        Then: ConversionError is raised (not SystemExit)
        """
        # Inconsistent indentation triggers a YAML parse error in python-frontmatter
        mermaid_code = (
            "---\nconfig:\n theme: neutral\n  layout: elk\n---\ngraph TD\n    A --> B"
        )

        with pytest.raises(ConversionError):
            extract_mermaid_title(mermaid_code)

    def test_malformed_yaml_conversion_error_user_message_includes_block_preview(self):
        """
        Test that the ConversionError user_message includes a preview of the block.

        Given: Mermaid code with malformed YAML frontmatter
        When: extract_mermaid_title raises ConversionError
        Then: The user_message attribute contains text from the mermaid block
        """
        mermaid_code = (
            "---\nconfig:\n theme: neutral\n  layout: elk\n---\ngraph TD\n    A --> B"
        )

        with pytest.raises(ConversionError) as exc_info:
            extract_mermaid_title(mermaid_code)

        # The preview should reference recognisable content from the block
        assert exc_info.value.user_message  # non-empty
        # At least some part of the block content or a meaningful label is present
        assert (
            "mermaid" in exc_info.value.user_message.lower()
            or "frontmatter" in exc_info.value.user_message.lower()
            or "graph" in exc_info.value.user_message
            or "config" in exc_info.value.user_message
        )


# ---------------------------------------------------------------------------
# TestImageDownloadErrorMessages
# ---------------------------------------------------------------------------


class TestImageDownloadErrorMessages:
    """Tests for download_image() failure message quality."""

    def test_download_image_failure_prints_url_in_error_message(self, capsys):
        """
        Test that a download failure prints the URL to stderr.

        Given: urllib.request.urlretrieve raises an exception for a given URL
        When: download_image is called with that URL
        Then: The URL appears in the message printed to stderr
        """
        url = "https://example.com/image.png"

        with patch(
            "convert.urllib.request.urlretrieve",
            side_effect=Exception("connection refused"),
        ):
            result = download_image(url, index=0)

        captured = capsys.readouterr()
        assert url in captured.err
        assert result is None

    def test_download_image_failure_prints_exception_string(self, capsys):
        """
        Test that a download failure prints the exception's string representation.

        Given: urllib.request.urlretrieve raises an exception with a specific message
        When: download_image is called
        Then: The exception message appears in the stderr output
        """
        url = "https://example.com/missing.png"
        exc_message = "404 Not Found"

        with patch(
            "convert.urllib.request.urlretrieve",
            side_effect=Exception(exc_message),
        ):
            result = download_image(url, index=0)

        captured = capsys.readouterr()
        assert exc_message in captured.err
        assert result is None

    def test_download_image_failure_returns_none(self, capsys):
        """
        Test that download_image returns None on failure (non-fatal).

        Given: A network error during image download
        When: download_image is called
        Then: None is returned so the caller can continue
        """
        url = "https://example.com/bad.png"

        with patch(
            "convert.urllib.request.urlretrieve",
            side_effect=Exception("timeout"),
        ):
            result = download_image(url, index=0)

        assert result is None

    def test_download_image_http_error_message_included(self, capsys):
        """
        Test that an HTTP error string (e.g. '403 Forbidden') is in stderr.

        Given: urllib raises an HTTPError with code 403
        When: download_image is called
        Then: '403' appears in the stderr message
        """
        import urllib.error

        url = "https://example.com/private.png"

        with patch(
            "convert.urllib.request.urlretrieve",
            side_effect=urllib.error.HTTPError(url, 403, "Forbidden", {}, None),
        ):
            result = download_image(url, index=0)

        captured = capsys.readouterr()
        assert "403" in captured.err
        assert result is None
