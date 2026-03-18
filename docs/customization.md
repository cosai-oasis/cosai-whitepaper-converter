# Customization Guide

This guide covers how to customize the CoSAI Whitepaper Converter's styling and templates.

## File Overview

| File | Purpose | Modify for |
|------|---------|------------|
| `assets/cosai.sty` | LaTeX styling | Colors, fonts, headers/footers |
| `assets/cosai-template.tex` | Document structure | Cover page, layout |
| `assets/config.json` | Mermaid settings | Diagram width |
| `convert.py` | Conversion logic | Preprocessing rules |

## Modifying Colors

Colors are defined in `assets/cosai.sty`:

```latex
% CoSAI brand colors
\definecolor{darkblue}{RGB}{17, 38, 64}    % Headings, cover background
\definecolor{greenaccent}{RGB}{49, 97, 71}  % Accent, section underlines
```

### Changing the Primary Color

Edit the RGB values:
```latex
\definecolor{darkblue}{RGB}{25, 50, 100}  % New blue
```

### Adding New Colors

```latex
\definecolor{mycolor}{RGB}{255, 128, 0}  % Orange accent
```

Then use in formatting:
```latex
\titleformat{\section}
  {\Large\bfseries\color{mycolor}}  % Use new color for sections
  ...
```

## Font Customization

The template uses Montserrat font family:

```latex
% In cosai.sty
\setmainfont{Montserrat}[
  UprightFont = *-ExtraLight,
  BoldFont = *-Medium,
  ItalicFont = *-ExtraLightItalic,
]
```

### Using a Different Font

1. Ensure the font is installed on your system
2. Update the font specification:

```latex
\setmainfont{Open Sans}[
  UprightFont = *-Regular,
  BoldFont = *-Bold,
  ItalicFont = *-Italic,
]
```

### Font Weights

Available Montserrat weights:
- ExtraLight (default body)
- Light (headings)
- Regular
- Medium (bold text)
- SemiBold
- Bold

## Template Structure

The `cosai-template.tex` file controls document structure:

```latex
% Cover page
\begin{titlepage}
  % Background, logo, title, author, date
\end{titlepage}

% Front matter
\tableofcontents

% Main content
$body$
```

### Modifying the Cover Page

The cover page uses:
- `background.pdf` - Full-page background
- `CoSAI(Light).pdf` - Logo
- Variables: `$title$`, `$author$`, `$date$`, `$git$`

Example: Moving the title position:
```latex
\begin{textblock*}{\textwidth}(1in, 4in)  % Changed from 3in
  {\fontsize{28}{36}\selectfont\color{darkblue}\textbf{$title$}}
\end{textblock*}
```

### Adding/Removing TOC

The PDF automatically generates a native LaTeX table of contents. Any Markdown-based TOC in your source file is **automatically stripped** during preprocessing to avoid duplication.

**Supported Markdown TOC formats** (auto-stripped):
- Heading levels 1–4: `# Table of Contents` through `#### Table of Contents`
- Bold text: `**Table of Contents**`
- Case-insensitive on "Contents" vs "contents"

**Not auto-stripped** (will appear as duplicate text in the PDF):
- H5/H6 headings (`#####`, `######`)
- Plain unformatted text (e.g., `Table of Contents` without bold or heading markup)
- Variant labels like "Contents", "TOC", or "In This Document"

If your whitepaper uses a Markdown TOC, use one of the supported formats above to ensure it is stripped cleanly.

To remove the native PDF table of contents from the LaTeX template:
```latex
% Comment out or remove:
% \tableofcontents
% \newpage
```

### Figure References

The PDF auto-numbers figures via LaTeX (`Figure 1`, `Figure 2`, etc.). To cross-reference figures from your Markdown source — in a way that works on both GitHub and in the PDF — use the `--figure-refs` flag.

#### How it works

1. **Declare** a figure anchor using Pandoc attribute syntax `{#fig-*}`:

   ```markdown
   ![Architecture Overview](arch.png)<!--{#fig-architecture}-->
   ```

   For Mermaid diagrams, place the anchor comment before the code fence:

   ```markdown
   <!--{#fig-dataflow}-->
   ```mermaid
   graph LR
     A[Input] --> B[Process] --> C[Output]
   ```

2. **Reference** figures with standard Markdown links using descriptive text:

   ```markdown
   See [Architecture Overview](#fig-architecture) for details.

   The data flows as shown in [Data Flow](#fig-dataflow).
   ```

3. **Convert** with the flag:

   ```bash
   python convert.py input.md output.pdf --figure-refs
   ```

#### What happens

| Context | Renders as |
|---------|-----------|
| **GitHub** (no processing) | "See Architecture Overview" — clickable link to the image |
| **PDF** with `--figure-refs` | "See Figure 1" — numbered reference matching the LaTeX caption |
| **PDF** without flag | "See Architecture Overview" — link text unchanged |

The preprocessor scans for `{#fig-*}` anchors in document order, assigns sequential numbers, and rewrites each `[text](#fig-*)` link to `[Figure N](#fig-*)`.

#### Custom label

Use `--figure-label` to change the prefix (default: `Figure`):

```bash
python convert.py input.md output.pdf --figure-refs --figure-label "Diagram"
# Produces "See Diagram 1" instead of "See Figure 1"
```

#### Validation

If a link points to a `#fig-*` anchor that doesn't exist in the document, the converter will **error with diagnostics** listing all broken references. This catches typos and stale references before they reach the PDF.

#### Anchor ID conventions

- Anchor IDs **must** start with `fig-` (e.g., `{#fig-architecture}`, `{#fig-data.flow}`)
- Dots, hyphens, underscores, and alphanumeric characters are supported
- Non-`fig-` anchors (e.g., `{#tbl-data}`, `{#sec-intro}`) are ignored

## Section Formatting

Section styles are defined in `cosai.sty`:

```latex
\titleformat{\section}
  {\Large\bfseries\color{darkblue}}  % Format
  {\thesection}                       % Label
  {1em}                               % Sep
  {}                                  % Before-code
  [\color{greenaccent}\titlerule[1pt]] % After-code (underline)
```

### Removing Section Underlines

```latex
\titleformat{\section}
  {\Large\bfseries\color{darkblue}}
  {\thesection}
  {1em}
  {}
  []  % Empty after-code
```

### Changing Section Numbering

To use Roman numerals:
```latex
\renewcommand{\thesection}{\Roman{section}}
```

## Mermaid Theming

Mermaid diagrams use a custom CoSAI theme defined in `convert.py`:

```python
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
        "clusterBkg": "#E6EFFF",
        "clusterBorder": "#4D8BFF",
        "titleColor": "#0059ff",
        "fontFamily": '"IBM Plex Sans", sans-serif',
    },
}
```

### Changing Diagram Colors

Modify the `themeVariables` dictionary:
```python
"primaryColor": "#FF6B6B",      # Main node background
"primaryBorderColor": "#CC5555", # Node borders
```

### Using a Different Theme

Change the theme:
```python
doc.metadata["config"] = {
    "theme": "forest",  # Use built-in forest theme
}
```

Available themes: `default`, `forest`, `dark`, `neutral`, `base`

### Disabling Hand-Drawn Look

Remove the "look" setting:
```python
doc.metadata["config"] = {
    "theme": "base",
    "themeVariables": { ... }
    # No "look" key = clean lines
}
```

## Adding Preprocessing Steps

Add custom Markdown preprocessing in `convert.py`:

```python
def process_markdown(input_file, engine=None, temp_dir=None, figure_refs=False, figure_label="Figure"):
    with open(input_file, "r") as f:
        content = f.read()

    content = strip_trailing_whitespace(content)

    # Add your custom preprocessing here:
    content = content.replace("(c)", "\u00a9")  # Copyright symbol
    content = re.sub(r"\bTODO\b", "**TODO**", content)  # Highlight TODOs

    # ... rest of function
```

### Built-in: HTML Comment-Wrapped Pandoc Attributes

Pandoc attributes like `{width=55%}` control image sizing in PDF output, but GitHub renders them as visible text. To hide them on GitHub while preserving them for PDF conversion, wrap them in HTML comments:

```markdown
![Diagram](diagrams/example.svg)<!--{width=55%}-->
```

The converter automatically strips the `<!-- -->` wrapper, producing:

```markdown
![Diagram](diagrams/example.svg){width=55%}
```

This works for any Pandoc attribute block: `{width=...}`, `{.class}`, `{#id}`, or combinations thereof.

Raw LaTeX commands are also supported:

```markdown
<!--\newpage-->
```

becomes `\newpage` in the Pandoc input, forcing a page break in the PDF without showing anything on GitHub.

## Page Layout

Page dimensions in `cosai.sty`:

```latex
\geometry{
  letterpaper,
  left=1in,
  right=1in,
  top=1in,
  bottom=1in,
}
```

### Changing Margins

```latex
\geometry{
  letterpaper,
  left=0.75in,
  right=0.75in,
  top=0.5in,
  bottom=0.5in,
}
```

### Using A4 Paper

```latex
\geometry{
  a4paper,
  left=25mm,
  right=25mm,
  top=25mm,
  bottom=25mm,
}
```

## Headers and Footers

Defined in `cosai.sty` using `fancyhdr`:

```latex
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\leftmark}           % Section name
\fancyhead[R]{\thepage}            % Page number
\fancyfoot[C]{\footnotesize Draft} % Footer text
```

### Removing Headers

```latex
\fancyhead{}  % Clear headers
```

### Adding Document Title to Footer

```latex
\fancyfoot[L]{\footnotesize\@title}
\fancyfoot[R]{\footnotesize Page \thepage}
```

## Code Block Styling

Pandoc handles syntax highlighting. To customize:

1. Generate a highlighting style:
   ```bash
   pandoc --print-highlight-style=pygments > highlight.theme
   ```
2. Edit the JSON theme file
3. Use it in conversion:
   ```bash
   pandoc --highlight-style=highlight.theme ...
   ```
