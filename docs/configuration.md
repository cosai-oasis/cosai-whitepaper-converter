# Configuration Guide

This guide covers all configuration options for the CoSAI Whitepaper Converter.

## CLI Options

```bash
python convert.py [OPTIONS] input_file output_file
```

| Option | Description | Default |
|--------|-------------|---------|
| `--title TITLE` | Override document title | From YAML frontmatter |
| `--author AUTHOR` | Override document author | From YAML frontmatter |
| `--date DATE` | Override document date | From YAML frontmatter |
| `--version VERSION` | Document version (e.g., git commit) | `1.0` |
| `--engine ENGINE` | LaTeX engine to use | `tectonic` |
| `--debug` | Save intermediate files (processed.md, .tex) and show verbose output | Off |
| `--figure-refs` | Auto-number figures and rewrite `[text](#fig-*)` links to "Figure N" | Off |
| `--figure-label LABEL` | Label prefix for figure references (e.g., "Diagram") | `Figure` |

### Examples

```bash
# Basic conversion
python convert.py whitepaper.md whitepaper.pdf

# With metadata overrides
python convert.py input.md output.pdf --title "My Paper" --author "Jane Doe"

# With git commit as version
python convert.py input.md output.pdf --version $(git rev-parse --short HEAD)

# With specific LaTeX engine
python convert.py input.md output.pdf --engine xelatex

# Debug mode: save intermediate files and show verbose output
python convert.py input.md output.pdf --debug

# Auto-number figure references
python convert.py input.md output.pdf --figure-refs

# Custom figure label
python convert.py input.md output.pdf --figure-refs --figure-label "Diagram"
```

## LaTeX Engine Selection

The converter supports four LaTeX engines. Priority order:

1. CLI flag (`--engine`)
2. Environment variable (`LATEX_ENGINE`)
3. Config file (`converter_config.json`)
4. Default (`tectonic`)

### Via CLI

```bash
python convert.py input.md output.pdf --engine pdflatex
```

### Via Environment Variable

```bash
export LATEX_ENGINE=xelatex
python convert.py input.md output.pdf
```

Or inline:

```bash
LATEX_ENGINE=lualatex python convert.py input.md output.pdf
```

### Via Config File

Create `converter_config.json` in the project root:

```json
{
  "latex_engine": "pdflatex"
}
```

### Engine Comparison

| Engine | Unicode | Speed | Package Management |
|--------|---------|-------|-------------------|
| tectonic | Full | Fast | Auto-downloads |
| pdflatex | Limited* | Fast | Manual (texlive) |
| xelatex | Full | Medium | Manual (texlive) |
| lualatex | Full | Slow | Manual (texlive) |

*pdflatex: Unicode characters are automatically converted to LaTeX commands.

## Config File Schema

The `converter_config.json` file supports these options:

```json
{
  "latex_engine": "tectonic"
}
```

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `latex_engine` | string | `tectonic`, `pdflatex`, `xelatex`, `lualatex` | LaTeX engine to use |

## Mermaid Configuration

### config.json

Controls Mermaid diagram dimensions:

```json
{
  "width": 1600
}
```

### puppeteerConfig.json

Configures the headless browser for Mermaid rendering:

```json
{
  "args": ["--no-sandbox", "--disable-setuid-sandbox"]
}
```

These flags are required when running in containers or CI environments.

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LATEX_ENGINE` | LaTeX engine to use | `xelatex` |
| `TEXINPUTS` | Additional LaTeX input paths | `/path/to/templates/:` |

## YAML Frontmatter

Documents should include YAML frontmatter for metadata:

```yaml
---
title: Document Title
author: Author Name
date: January 2025
---
```

Frontmatter values can be overridden via CLI options.

## Next Steps

- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Customization](customization.md) - Modify styling and templates
