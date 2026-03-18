"""
Tests for extract_mermaid_title function.

This module tests the Mermaid diagram title extraction and CoSAI theme
application functionality.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from convert import extract_mermaid_title


class TestExtractMermaidTitle:
    """Test suite for extract_mermaid_title function."""

    def test_extract_mermaid_title_with_frontmatter_title(self):
        """
        Test title extraction from Mermaid code with YAML frontmatter.

        Given: Mermaid code with YAML frontmatter containing title
        When: extract_mermaid_title is called
        Then: Title is extracted and removed from code
        """
        mermaid_code = """---
title: "My Diagram"
---
graph TD
    A --> B
"""

        title, code = extract_mermaid_title(mermaid_code)

        assert title == "My Diagram"
        assert "title:" not in code
        assert "graph TD" in code
        assert "A --> B" in code

    def test_extract_mermaid_title_without_title(self):
        """
        Test Mermaid code without title.

        Given: Mermaid code without YAML frontmatter title
        When: extract_mermaid_title is called
        Then: None is returned for title, code preserved with config added
        """
        mermaid_code = """graph TD
    A --> B
"""

        title, code = extract_mermaid_title(mermaid_code)

        assert title is None
        assert "graph TD" in code
        assert "A --> B" in code

    def test_extract_mermaid_title_adds_cosai_theme(self):
        """
        Test that CoSAI theme configuration is added to code.

        Given: Mermaid code without config
        When: extract_mermaid_title is called
        Then: CoSAI theme config is added to frontmatter
        """
        mermaid_code = """graph TD
    A --> B
"""

        title, code = extract_mermaid_title(mermaid_code)

        # Check that config is present in returned code
        assert "config:" in code or "---" in code
        # The function should add frontmatter with config
        assert "look:" in code or "theme:" in code

    def test_extract_mermaid_title_preserves_existing_config(self):
        """
        Test that existing config in frontmatter is preserved.

        Given: Mermaid code with existing config in frontmatter
        When: extract_mermaid_title is called
        Then: Existing config is preserved (not overwritten)
        """
        mermaid_code = """---
config:
  look: classic
  theme: dark
---
graph TD
    A --> B
"""

        title, code = extract_mermaid_title(mermaid_code)

        # Should preserve the existing config
        assert "classic" in code
        assert "dark" in code

    def test_extract_mermaid_title_with_complex_diagram(self):
        """
        Test title extraction from complex diagram.

        Given: Complex Mermaid diagram with title
        When: extract_mermaid_title is called
        Then: Title extracted correctly, diagram structure preserved
        """
        mermaid_code = """---
title: "Complex Flow"
---
flowchart LR
    A[Start] --> B{Decision}
    B -->|Yes| C[Process 1]
    B -->|No| D[Process 2]
    C --> E[End]
    D --> E
"""

        title, code = extract_mermaid_title(mermaid_code)

        assert title == "Complex Flow"
        assert "flowchart LR" in code
        assert "Decision" in code
        assert "Process 1" in code

    def test_extract_mermaid_title_empty_title(self):
        """
        Test handling of empty title in frontmatter.

        Given: Mermaid code with empty title value
        When: extract_mermaid_title is called
        Then: Empty string title is extracted
        """
        mermaid_code = """---
title: ""
---
graph TD
    A --> B
"""

        title, code = extract_mermaid_title(mermaid_code)

        assert title == ""
        assert "graph TD" in code

    def test_extract_mermaid_title_returns_tuple(self):
        """
        Test that function returns correct tuple structure.

        Given: Any valid Mermaid code
        When: extract_mermaid_title is called
        Then: Returns tuple of (title, code)
        """
        mermaid_code = "graph TD\n    A --> B"

        result = extract_mermaid_title(mermaid_code)

        assert isinstance(result, tuple)
        assert len(result) == 2
        title, code = result
        assert title is None or isinstance(title, str)
        assert isinstance(code, str)

    def test_extract_mermaid_title_malformed_yaml_raises_conversion_error(self):
        """
        Given: Mermaid code with syntactically invalid YAML frontmatter
        When: extract_mermaid_title is called
        Then: Raises ConversionError with a diagnostic message
        """
        from convert import ConversionError

        mermaid_code = (
            "---\nconfig:\n theme: neutral\n  layout: elk\n---\ngraph TD\n    A --> B"
        )

        with pytest.raises(ConversionError) as exc_info:
            extract_mermaid_title(mermaid_code)

        assert exc_info.value.user_message  # non-empty
        assert (
            "mermaid" in exc_info.value.user_message.lower()
            or "frontmatter" in exc_info.value.user_message.lower()
            or "graph" in exc_info.value.user_message
        )
