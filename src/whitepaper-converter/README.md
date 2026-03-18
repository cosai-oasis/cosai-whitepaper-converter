# CoSAI Whitepaper Converter

A devcontainer feature that installs dependencies for converting Markdown files to professionally formatted PDFs with CoSAI (Coalition for Secure AI) branding.

## Features

- Installs LaTeX engine (tectonic, pdflatex, xelatex, or lualatex)
- Configures Pandoc for document conversion
- Sets up Mermaid CLI for diagram rendering
- Installs Python dependencies
- Configures Chromium for headless diagram rendering

## Usage

Add this feature to your `.devcontainer/devcontainer.json`:

```json
{
  "features": {
    "ghcr.io/cosai-oasis/cosai-whitepaper-converter/whitepaper-converter:1": {
      "latexEngine": "tectonic",
      "installPath": "/usr/local/lib/cosai-converter",
      "skipChromium": false,
      "skipPython": false,
      "skipNode": false
    }
  }
}
```

### Version Tags

| Tag | Description | Updates |
|-----|-------------|---------|
| `:1` | Latest 1.x version | Auto-updates to 1.1, 1.2, etc. (recommended) |
| `:1.0` | Latest 1.0.x patch | Auto-updates to 1.0.1, 1.0.2, etc. |
| `:1.0.0` | Specific version | Pinned, no auto-updates |

We recommend using `:1` to automatically receive compatible updates.

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `latexEngine` | string | `"tectonic"` | LaTeX engine to install. Supported values: `tectonic`, `pdflatex`, `xelatex`, `lualatex` |
| `installPath` | string | `"/usr/local/lib/cosai-converter"` | Directory to install the converter tool (convert.py and assets) |
| `skipChromium` | boolean | `false` | Skip Chromium configuration for Mermaid rendering |
| `skipPython` | boolean | `false` | Skip Python installation and dependencies |
| `skipNode` | boolean | `false` | Skip Node.js installation and Mermaid CLI |

### LaTeX Engines

The feature supports multiple LaTeX engines:

- **tectonic** (default) - Modern, self-contained TeX distribution with automatic package management
- **pdflatex** - Traditional LaTeX engine, widely compatible
- **xelatex** - Extended LaTeX with native Unicode support
- **lualatex** - LaTeX with Lua scripting capabilities

Choose the engine that best fits your document requirements and system constraints.

## Examples

### Minimal Installation

Install with default settings (tectonic engine):

```json
{
  "features": {
    "ghcr.io/cosai-oasis/cosai-whitepaper-converter/whitepaper-converter:1": {}
  }
}
```

### Custom LaTeX Engine

Use pdflatex instead of tectonic:

```json
{
  "features": {
    "ghcr.io/cosai-oasis/cosai-whitepaper-converter/whitepaper-converter:1": {
      "latexEngine": "pdflatex"
    }
  }
}
```

### Skip Optional Components

If Python and Node.js are already installed by other features:

```json
{
  "features": {
    "ghcr.io/cosai-oasis/cosai-whitepaper-converter/whitepaper-converter:1": {
      "skipPython": true,
      "skipNode": true
    }
  }
}
```

## Supported Platforms

This feature supports:

- Debian-based Linux distributions (Debian, Ubuntu)
- Alpine Linux
- macOS (via Homebrew)

The installer automatically detects your platform and uses the appropriate package manager.

## Configuration

After installation, the feature sets the `COSAI_CONVERTER_INSTALLED` environment variable to `true`.

The LaTeX engine choice is configured via the `LATEX_ENGINE` environment variable during installation.

## Converter Usage

After installation, use the `cosai-convert` command to convert Markdown to PDF:

```bash
cosai-convert input.md output.pdf
```

With options:

```bash
# Metadata and engine
cosai-convert input.md output.pdf --title "My Document" --engine pdflatex

# Auto-number figure references (rewrites [text](#fig-*) links to "Figure N")
cosai-convert input.md output.pdf --figure-refs

# Custom figure label
cosai-convert input.md output.pdf --figure-refs --figure-label "Diagram"

# Debug mode (saves intermediate .md and .tex files)
cosai-convert input.md output.pdf --debug
```

The converter is installed to the path specified by `installPath` (default: `/usr/local/lib/cosai-converter`). The `COSAI_CONVERTER_PATH` environment variable points to the installation directory.

### Custom Install Path

```json
{
  "features": {
    "ghcr.io/cosai-oasis/cosai-whitepaper-converter/whitepaper-converter:1": {
      "installPath": "/opt/cosai"
    }
  }
}
```

## Requirements

This feature should be installed after Python and Node.js features if you're using multiple features:

```json
{
  "features": {
    "ghcr.io/devcontainers/features/python:1": {},
    "ghcr.io/devcontainers/features/node:1": {},
    "ghcr.io/cosai-oasis/cosai-whitepaper-converter/whitepaper-converter:1": {}
  }
}
```

## More Information

For more details on the CoSAI Whitepaper Converter, see the [main repository](https://github.com/cosai-oasis/cosai-whitepaper-converter).
