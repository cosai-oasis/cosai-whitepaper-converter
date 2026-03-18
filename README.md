# CoSAI Markdown to PDF Converter

Simple script to automatically convert Markdown files, specifically CoSAI's white papers, into nicely formatted PDFs. The process makes use of a few dependencies. The heavy lifting is performed by pandoc, plus a simple Python script to handle various nuances and corner cases that popped up. To run the tool

```bash
python convert.py whitepaper.md whitepaper.pdf
```

The `convert.py` script takes a few optional parameters, though we try to minimize the need to use them.

```
usage: convert.py [-h] [--title TITLE] [--author AUTHOR] [--date DATE] [--version VERSION]
                  [--engine {tectonic,pdflatex,xelatex,lualatex}] [--debug]
                  input_file output_file

Convert Markdown to PDF with Mermaid support.

positional arguments:
  input_file         Path to input Markdown file
  output_file        Path to output PDF file

options:
  -h, --help         show this help message and exit
  --title TITLE      Document title
  --author AUTHOR    Document author(s)
  --date DATE        Document date
  --version VERSION  Version of the paper
  --engine {tectonic,pdflatex,xelatex,lualatex}
                     LaTeX engine to use (default: tectonic)
  --debug            Save intermediate files (processed.md, .tex) and show verbose output
```

## System Requirements

- **Python**: 3.12 or higher
- **Pandoc**: 3.9 or higher
- **Node.js**: 20 or higher (for Mermaid CLI)
- **LaTeX engine**: One of: tectonic (default), pdflatex, xelatex, or lualatex

## Installation Options

### Option 1: Devcontainer Feature (Recommended for External Projects)

If your project uses VS Code devcontainers, add this feature to your `.devcontainer/devcontainer.json`:

```json
{
  "image": "mcr.microsoft.com/devcontainers/base:debian",
  "features": {
    "ghcr.io/cosai-oasis/cosai-whitepaper-converter/whitepaper-converter:1": {}
  }
}
```

This installs all dependencies automatically. See the [Feature Documentation](src/whitepaper-converter/README.md) for configuration options (LaTeX engine selection, skip components, etc.).

### Option 2: Use This Repository's Devcontainer

Clone this repository and open in VS Code with the Dev Containers extension. All dependencies are pre-configured.

### Option 3: Install Script or Manual

For CI/CD pipelines or manual installation, see [docs/installation.md](docs/installation.md).

## LaTeX Engine Configuration

The converter supports multiple LaTeX engines. The engine is determined by priority:

1. **CLI flag**: `--engine pdflatex`
2. **Environment variable**: `LATEX_ENGINE=xelatex`
3. **Config file**: `converter_config.json` with `{"latex_engine": "lualatex"}`
4. **Default**: `tectonic`

| Engine | Unicode Support | Speed | Notes |
|--------|-----------------|-------|-------|
| tectonic | Full | Fast | Default, auto-downloads packages |
| xelatex | Full | Medium | Good for complex fonts |
| lualatex | Full | Slow | Most flexible |
| pdflatex | Limited | Fast | Requires Unicode normalization |

There are a few conventions we can use to simplify things. First, YAML metadata headers for all Markdown files can be automatically processed by pandoc, e.g., 

```markdown
---
title: A Very Good White Paper
author: V. S. People
date: 1 January 2026
---

# Whitepaper Title
Lorem ipsum dolor sit amet consectetur adipiscing elit scelerisque semper felis gravida, pretium urna ornare facilisis est habitant tellus arcu euismod sodales egestas nibh, tincidunt cursus faucibus ultrices proin potenti facilisi magnis ligula blandit. Cursus penatibus per aptent placerat euismod mus lectus pharetra morbi, nascetur felis blandit sollicitudin bibendum etiam sed fames, nec facilisis ac tempus tempor sem venenatis vel. Est arcu at iaculis sed tellus nam nascetur primis nibh etiam odio penatibus, dis integer nostra euismod consequat interdum sociis parturient habitant ornare sagittis, morbi per dictumst enim purus justo fusce feugiat leo facilisis mauris.
```

## Using as a Git Submodule

The converter can be embedded in other repositories as a git submodule, allowing whitepapers to live alongside their source code while sharing a common conversion toolchain. This is the recommended approach for organizations managing multiple documents.

### Quick Setup

```bash
# Add the converter as a submodule (conventionally named latex-template/)
git submodule add https://github.com/cosai-oasis/cosai-whitepaper-converter.git latex-template

# Initialize and fetch the submodule
git submodule update --init --recursive
```

### Example Makefile

A Makefile can automate builds and pass dynamic values like git commit hashes as the document version:

```Makefile
MDs := whitepaper-1.md \
        whitepaper-2.md
PDFs := $(MDs:.md=.pdf)

all: $(PDFs)

%.pdf: %.md
        @echo "Converting $< → $@"
        python latex-template/convert.py $< $@ --version=$$(git log -1 --format=%H $<)

.PHONY: clean
clean:
        @rm -f $(PDFs)
```

The converter automatically detects when running from a `latex-template/` subdirectory and locates its assets accordingly.

For detailed submodule setup instructions, see [docs/installation.md](docs/installation.md#using-as-a-git-submodule).

## Other Useful Tools

- **rsvg-convert**: For converting SVG to PDF (used internally by Pandoc for Mermaid diagrams)

# Comments and Best Practices
Testing several markdown files has revealed a few best practices or things to note:
1. The `convert.py` file will omit a manually included table of contents in favor of the LaTeX generated TOC. As such, any references numbered section will break, e.g., `[Link](#123-Subsection-Link)`. A link to the section itself, `#Subsection-Link` will still work. A consistent section name should be used.
1. Anchor tags can be used to include links which pandoc will preserve <a id="anchor"></a>
1. White space at the end of lines, such as lists, causes Markdown to render as separate sections (includes extra vertical whitespace) and will mess up PDF formatting. The `convert.py` script will strip any line-ending whitespace globally. 
1. Mermaid files with a title will have that title extracted, and stripped, so that it can be used in the latex `\figure` caption. Mermaid is converted to PDF and will have a consistent CoSAI theme applied unless already present in the metadata header. (`config:` section)
1. Any break, `<br>`, and variants, are converted to `\newline`. Errant `<br>` will break the LaTeX compilation. If you get an error about `\newline`, try this.
1. Pandoc attributes like `{width=55%}` and raw LaTeX commands like `\newpage` can be wrapped in HTML comments (`<!--{width=55%}-->`, `<!--\newpage-->`) to hide them from GitHub rendering. The converter automatically strips the comment wrapper during PDF conversion so they take effect in LaTeX output.

## Known Issues
1. ~~**Bold text in tables not rendering**~~ Fixed by upgrading Pandoc to 3.9. Earlier versions occasionally failed to convert `**bold**` to `\textbf` inside Markdown tables.
2. ~~**"No counter '' defined"**~~ Fixed by upgrading Pandoc to 3.8.2.1. Pandoc 3.8.1 emitted `\def\LTcaptype{}` for uncaptioned tables, which broke with the `caption` package. If you see this error, upgrade Pandoc.

## Troubleshooting

### LaTeX compilation errors
- **Unicode characters**: If using pdflatex, Unicode characters are auto-converted. For full Unicode support, use `--engine tectonic` or `--engine xelatex`.
- **Missing packages**: tectonic auto-downloads packages; other engines may require manual installation via `tlmgr` or system package manager.
- **`\newline` errors**: Often caused by errant `<br>` tags in unexpected places. Check your Markdown source.

### Mermaid rendering issues
- Ensure Node.js 20+ is installed
- Check that `npx` is available in your PATH
- Mermaid CLI is run via `npx -y @mermaid-js/mermaid-cli`

### Debugging conversion issues
Use `--debug` to save intermediate files and see verbose engine output:
```bash
python convert.py input.md output.pdf --debug
```
This produces `output_debug.md` (preprocessed Markdown) and `output_debug.tex` (intermediate LaTeX) alongside the PDF.

### Pandoc not found
- Verify Pandoc is installed: `pandoc --version` (must be 3.9+)
- Ensure Pandoc is in your PATH
- The devcontainer includes Pandoc pre-installed

For more details, see [docs/troubleshooting.md](docs/troubleshooting.md).
