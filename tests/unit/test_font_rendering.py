"""
Unit tests for font rendering configuration in cosai.sty.

This module tests the LaTeX font configuration to ensure that:
- Bold text renders correctly with fontspec-based engines (tectonic/xelatex/lualatex)
- The boldFontWeight command uses the correct NFSS series code
- FontFace definitions use proper series codes
- pdflatex configuration remains unchanged and functional

Bug Context:
- Issue: Bold text renders correctly with pdflatex but not with tectonic
- Root Cause: fontspec configuration uses reserved 'm' series code for Medium weight
- Fix: Change to 'mb' series code (Medium Bold) for fontspec configuration
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestFontWeightConfiguration:
    """Test suite for font weight configuration in cosai.sty."""

    def test_boldFontWeight_uses_mb_series_code(self):
        """
        Test that boldFontWeight command uses 'mb' series code for Medium Bold.

        Given: The cosai.sty file with font configuration
        When: boldFontWeight command is examined
        Then: It should be defined as 'mb' (not 'm') for proper fontspec rendering

        This test will FAIL with current code (uses 'm') and PASS after fix (uses 'mb').
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Look for the boldFontWeight definition
        # Expected after fix: \newcommand{\boldFontWeight}{mb}
        # Current (buggy): \newcommand{\boldFontWeight}{m}

        # This assertion will FAIL until the fix is applied
        assert r"\newcommand{\boldFontWeight}{mb}" in content, (
            "boldFontWeight should use 'mb' series code for Medium Bold weight. "
            "Found 'm' which is reserved for Regular weight and doesn't work with fontspec. "
            "Change from \\newcommand{\\boldFontWeight}{m} to \\newcommand{\\boldFontWeight}{mb}"
        )

    def test_fontspec_defines_mb_series_for_medium(self):
        """
        Test that fontspec FontFace defines 'mb' series (not 'm') for Medium weight.

        Given: The cosai.sty file with fontspec configuration
        When: FontFace declarations are examined
        Then: Medium weight should use series code 'mb' (not 'm')

        This test will FAIL with current code and PASS after fix.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Look for FontFace definition for Medium weight
        # Expected after fix: FontFace = {mb}{n}{*-Medium}
        # Current (buggy): FontFace = {m}{n}{*-Medium}

        # This assertion will FAIL until the fix is applied
        assert "FontFace = {mb}{n}{*-Medium}" in content, (
            "FontFace should define 'mb' series for Medium weight font. "
            "Found FontFace = {m}{n}{*-Medium} but 'm' is reserved for Regular. "
            "Change to FontFace = {mb}{n}{*-Medium}"
        )

    def test_fontspec_boldFont_maps_to_medium(self):
        """
        Test that fontspec BoldFont is configured to use Medium weight.

        Given: The cosai.sty file with fontspec configuration
        When: BoldFont specification is examined
        Then: BoldFont should map to *-Medium (not *-Bold)

        Note: This test verifies the design decision to use Medium for bold text.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Extract the fontspec \setmainfont section
        # We expect BoldFont = *-Medium (design choice for CoSAI styling)
        # Current implementation should have BoldFont = *-Bold

        # After the fix, BoldFont should be changed to *-Medium
        # This test documents the expected final state
        assert "BoldFont = *-Medium" in content, (
            "BoldFont should be configured to use *-Medium for CoSAI's lighter bold style. "
            "Current configuration uses *-Bold. Change BoldFont = *-Bold to BoldFont = *-Medium"
        )

    def test_pdflatex_branch_uses_montserrat_package(self):
        """
        Test that pdflatex configuration uses the montserrat package (unchanged).

        Given: The cosai.sty file with engine-specific font configuration
        When: The pdflatex branch is examined
        Then: It should use the montserrat package (traditional 8-bit encoding)

        This verifies backward compatibility - pdflatex config should remain unchanged.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Verify pdflatex uses traditional font loading
        assert r"\ifPDFTeX" in content, "Should have pdflatex engine detection"
        assert r"\usepackage[defaultfam,tabular,lining]{montserrat}" in content, (
            "pdflatex should use montserrat package with traditional font loading"
        )
        assert r"\RequirePackage[utf8]{inputenc}" in content, (
            "pdflatex should use utf8 inputenc"
        )
        assert r"\RequirePackage[T1]{fontenc}" in content, (
            "pdflatex should use T1 font encoding"
        )

    def test_fontspec_engine_detection_exists(self):
        """
        Test that fontspec is loaded for Unicode engines (XeTeX/LuaTeX/Tectonic).

        Given: The cosai.sty file with engine detection
        When: The else branch (non-pdflatex) is examined
        Then: It should load fontspec for full Unicode support

        This verifies the engine detection logic is in place.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Verify fontspec branch exists
        assert r"\else" in content, "Should have else branch for non-pdflatex engines"
        assert r"\RequirePackage{fontspec}" in content, (
            "Non-pdflatex engines should load fontspec for Unicode support"
        )

    def test_bodyFontWeight_uses_extralight(self):
        """
        Test that bodyFontWeight is set to ExtraLight (design requirement).

        Given: The cosai.sty file with font weight configuration
        When: bodyFontWeight command is examined
        Then: It should be 'el' (ExtraLight) per CoSAI styling guide

        This test verifies that body text styling remains unchanged.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Verify body font weight is ExtraLight
        assert r"\newcommand{\bodyFontWeight}{el}" in content, (
            "Body text should use ExtraLight weight (el) per CoSAI styling"
        )

    def test_font_weight_options_documented(self):
        """
        Test that font weight options are documented in the style file.

        Given: The cosai.sty file with configuration comments
        When: Documentation section is examined
        Then: Font weight options should be clearly documented

        This ensures maintainability and clarity for future modifications.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Check for documentation of font weight options
        assert "el = ExtraLight" in content, "Should document ExtraLight option"
        assert "l  = Light" in content, "Should document Light option"
        assert "sb = SemiBold" in content, "Should document SemiBold option"
        assert "b  = Bold" in content, "Should document Bold option"

    def test_bfseries_redefinition_uses_boldFontWeight(self):
        """
        Test that \\bfseries command is redefined to use boldFontWeight.

        Given: The cosai.sty file with font command redefinitions
        When: \\bfseries redefinition is examined
        Then: It should use \\boldFontWeight variable for consistency

        This verifies that the bold weight is centrally configured.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Verify \bfseries uses the boldFontWeight variable
        assert (
            r"\renewcommand{\bfseries}{\fontseries{\boldFontWeight}\selectfont}"
            in content
        ), (
            "\\bfseries should be redefined to use \\boldFontWeight for centralized configuration"
        )

    def test_textbf_redefinition_uses_boldFontWeight(self):
        """
        Test that \\textbf command is redefined to use boldFontWeight.

        Given: The cosai.sty file with text command redefinitions
        When: \\textbf redefinition is examined
        Then: It should use \\boldFontWeight variable

        This ensures markdown bold (**text**) uses the configured weight.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Verify \textbf uses the boldFontWeight variable
        assert (
            r"\DeclareTextFontCommand{\textbf}{\fontseries{\boldFontWeight}\selectfont}"
            in content
        ), "\\textbf should be redefined to use \\boldFontWeight for markdown bold text"


class TestFontSpecConfiguration:
    """Test suite for detailed fontspec configuration requirements."""

    def test_setmainfont_uses_montserrat(self):
        """
        Test that setmainfont specifies Montserrat font family.

        Given: The cosai.sty file with fontspec configuration
        When: \\setmainfont command is examined
        Then: It should specify Montserrat as the main font

        This verifies the font family requirement.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Verify Montserrat is set as main font
        assert r"\setmainfont{Montserrat}" in content, (
            "Main font should be set to Montserrat"
        )

    def test_setmainfont_specifies_otf_extension(self):
        """
        Test that setmainfont uses .otf extension for font files.

        Given: The cosai.sty file with fontspec configuration
        When: Font extension specification is examined
        Then: It should specify Extension = .otf

        This ensures proper font file loading.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Verify .otf extension is specified
        assert "Extension = .otf" in content, (
            "Font extension should be specified as .otf"
        )

    def test_fontspec_defines_extralight_face(self):
        """
        Test that FontFace defines ExtraLight weight (el series).

        Given: The cosai.sty file with fontspec configuration
        When: FontFace declarations are examined
        Then: ExtraLight face should be defined

        This is required for body text styling.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Verify ExtraLight face is defined
        assert "FontFace = {el}{n}{*-ExtraLight}" in content, (
            "ExtraLight font face should be defined for body text"
        )

    def test_fontspec_defines_light_face(self):
        """
        Test that FontFace defines Light weight (l series).

        Given: The cosai.sty file with fontspec configuration
        When: FontFace declarations are examined
        Then: Light face should be defined

        This is required for section headings.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Verify Light face is defined
        assert "FontFace = {l}{n}{*-Light}" in content, (
            "Light font face should be defined for headings"
        )

    def test_fontspec_defines_semibold_face(self):
        """
        Test that FontFace defines SemiBold weight (sb series).

        Given: The cosai.sty file with fontspec configuration
        When: FontFace declarations are examined
        Then: SemiBold face should be defined

        This provides additional weight option for styling.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Verify SemiBold face is defined
        assert "FontFace = {sb}{n}{*-SemiBold}" in content, (
            "SemiBold font face should be defined"
        )

    def test_setsansfont_has_fontface_definitions(self):
        """
        Test that setsansfont has FontFace definitions for custom weights.

        Given: The cosai.sty file with fontspec configuration
        When: The setsansfont declaration is examined
        Then: It should have FontFace definitions for el, l, mb, sb

        CRITICAL Bug: The document uses \\familydefault{\\sfdefault} (line 131),
        meaning the SANS-SERIF font is used for body text, NOT the main font.
        If setsansfont lacks FontFace definitions, body weight (el) and bold (mb)
        switching won't work.

        This test will FAIL with original code and PASS after fix.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Verify document uses sans-serif as default
        assert r"\renewcommand{\familydefault}{\sfdefault}" in content, (
            "Document uses sans-serif as default font family"
        )

        # Find the setsansfont block
        sansfont_start = content.find(r"\setsansfont{Montserrat}")
        assert sansfont_start != -1, "setsansfont should be defined for Montserrat"

        # Get content after setsansfont (the configuration block)
        sansfont_section = content[sansfont_start:sansfont_start + 600]

        # setsansfont MUST have FontFace definitions since it's the default family
        assert "FontFace = {el}{n}{*-ExtraLight}" in sansfont_section, (
            "setsansfont MUST have FontFace = {el} for ExtraLight body text. "
            "The document uses \\sfdefault, so sans-serif needs all weight definitions."
        )
        assert "FontFace = {mb}{n}{*-Medium}" in sansfont_section, (
            "setsansfont MUST have FontFace = {mb} for Medium bold text. "
            "The document uses \\sfdefault, so sans-serif needs the mb series."
        )

    def test_setsansfont_boldFont_is_medium(self):
        """
        Test that setsansfont BoldFont is set to Medium weight.

        Given: The cosai.sty file with fontspec configuration
        When: The setsansfont BoldFont setting is examined
        Then: It should be *-Medium (not *-Bold)

        CRITICAL: Since the document uses \\sfdefault, the sans-serif bold
        setting determines what \\textbf{} produces in body text.
        """
        sty_path = Path(__file__).parent.parent.parent / "assets" / "cosai.sty"
        content = sty_path.read_text()

        # Find the setsansfont block
        sansfont_start = content.find(r"\setsansfont{Montserrat}")
        assert sansfont_start != -1, "setsansfont should be defined"

        sansfont_section = content[sansfont_start:sansfont_start + 400]

        # BoldFont in setsansfont must be *-Medium
        assert "BoldFont = *-Medium" in sansfont_section, (
            "setsansfont BoldFont must be *-Medium for proper bold rendering. "
            "Original bug had BoldFont = *-Bold in setsansfont but *-Medium in setmainfont."
        )


"""
Test Summary
============
Total Tests: 15
- Happy Path: 7
- Configuration Verification: 8

Coverage Areas:
- boldFontWeight command definition (mb series code)
- FontFace definition for Medium weight (mb series)
- BoldFont mapping to Medium weight file
- pdflatex branch backward compatibility
- fontspec engine detection
- bodyFontWeight configuration (ExtraLight)
- Font weight documentation
- \\bfseries redefinition
- \\textbf redefinition
- Montserrat font family
- .otf extension specification
- ExtraLight face definition
- Light face definition
- SemiBold face definition

Test Characteristics:
- All tests read actual cosai.sty file
- Tests verify exact string patterns in LaTeX code
- Tests include helpful error messages explaining the fix
- Tests document the root cause of the bug
- Tests ensure backward compatibility with pdflatex
- Tests verify centralized configuration approach

Expected Test Results (RED Phase):
- test_boldFontWeight_uses_mb_series_code: FAIL (currently uses 'm')
- test_fontspec_defines_mb_series_for_medium: FAIL (currently uses 'm')
- test_fontspec_boldFont_maps_to_medium: FAIL (currently uses '*-Bold')
- All other tests: PASS (verifying existing correct configuration)

After Fix (GREEN Phase):
- All tests should PASS

Running Tests:
- All unit tests: pytest tests/unit/test_font_rendering.py
- Single test: pytest tests/unit/test_font_rendering.py::test_boldFontWeight_uses_mb_series_code
- Verbose: pytest tests/unit/test_font_rendering.py -v
"""
