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

To remove table of contents:
```latex
% Comment out or remove:
% \tableofcontents
% \newpage
```

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
def process_markdown(input_file, engine=None, temp_dir=None):
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
