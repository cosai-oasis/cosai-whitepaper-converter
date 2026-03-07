# Installation Guide

This guide covers installing the CoSAI Whitepaper Converter and its dependencies.

## Prerequisites

| Dependency | Minimum Version | Purpose |
|------------|-----------------|---------|
| Python | 3.12+ | Core script runtime |
| Pandoc | 3.9+ | Markdown to LaTeX conversion |
| Node.js | 18+ | Mermaid diagram rendering |
| LaTeX engine | Any recent | PDF generation |

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Ubuntu/Debian | ✓ Supported | Primary development platform |
| Alpine Linux | ✓ Supported | Minimal container images |
| macOS | ✓ Supported | Requires Homebrew |
| RHEL/Fedora | ✓ Supported | Uses dnf package manager |
| Windows | ✗ Unsupported | Use WSL2 or Linux VM (see below) |

### Windows Users

Windows is not directly supported due to LaTeX engine and shell script compatibility issues. We recommend using **Windows Subsystem for Linux 2 (WSL2)**:

1. [Install WSL2](https://docs.microsoft.com/en-us/windows/wsl/install) with Ubuntu
2. Follow the Ubuntu installation instructions within WSL2
3. Access files via `\\wsl$\Ubuntu\home\<username>\`

Alternatively, use the devcontainer in VS Code which works on all platforms including Windows.

## Installation Methods

### Option 1: Devcontainer Feature (Recommended for External Projects)

If your project already uses VS Code devcontainers, add this feature to your `.devcontainer/devcontainer.json`:

```json
{
  "image": "mcr.microsoft.com/devcontainers/base:debian",
  "features": {
    "ghcr.io/cosai-oasis/cosai-whitepaper-converter/whitepaper-converter:1": {
      "latexEngine": "tectonic"
    }
  }
}
```

This automatically installs all dependencies when the container is built.

**Available Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `latexEngine` | string | `tectonic` | LaTeX engine: tectonic, pdflatex, xelatex, lualatex |
| `skipChromium` | boolean | `false` | Skip Chromium (if you don't need Mermaid diagrams) |
| `skipPython` | boolean | `false` | Skip Python (if already installed by another feature) |
| `skipNode` | boolean | `false` | Skip Node.js (if already installed by another feature) |

**Supported Base Images:** Debian, Ubuntu, Alpine

**Version Tags:**
- `:1` - Latest 1.x version (recommended)
- `:1.0.0` - Specific version (pinned)

See the full [Feature Documentation](../src/whitepaper-converter/README.md) for more details.

### Option 2: Use This Repository's Devcontainer

For developing the converter itself or trying it out:

1. Clone this repository
2. Open in VS Code
3. Install the "Dev Containers" extension
4. Click "Reopen in Container" when prompted
5. All dependencies are ready to use

### Option 3: Install Script (CI/CD)

For CI/CD pipelines or manual installation on Linux/macOS:

```bash
# Clone and install
git clone https://github.com/cosai-oasis/cosai-whitepaper-converter.git
cd cosai-whitepaper-converter
./scripts/install-deps.sh

# With specific LaTeX engine
LATEX_ENGINE=pdflatex ./scripts/install-deps.sh

# Skip optional components
SKIP_CHROMIUM=true ./scripts/install-deps.sh
```

**Note**: You may need to make the script executable first:
```bash
chmod +x scripts/install-deps.sh
```

**Environment Variables:**
- `LATEX_ENGINE` - tectonic (default), pdflatex, xelatex, lualatex
- `SKIP_CHROMIUM` - Skip Chromium configuration (default: false)
- `SKIP_PYTHON` - Skip Python installation (default: false)
- `SKIP_NODE` - Skip Node.js installation (default: false)

**Exit Codes:**
- 0: Success
- 1: General error
- 2: Unsupported platform (Windows)
- 3: Missing sudo privileges
- 4: Network error
- 5: Verification failed

### Option 4: Manual Installation

#### macOS

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.12 pandoc node tectonic

# Install Python dependencies
pip install python-frontmatter
```

#### Ubuntu/Debian

```bash
# System packages
sudo apt update
sudo apt install -y python3 python3-pip pandoc nodejs npm

# LaTeX (choose one)
sudo apt install -y texlive-latex-extra texlive-fonts-extra  # pdflatex
# OR
cargo install tectonic  # tectonic (requires Rust)

# Python dependencies
pip install python-frontmatter
```

## Verifying Installation

Run the verification script to check all dependencies:

```bash
./scripts/verify-deps.sh
```

Expected output when all dependencies are installed:
```
[✓] Python 3.12.3 (requires 3.12+)
[✓] Node.js 22.14.0 (requires 18+)
[✓] Pandoc 3.9 (requires 3.9+)
[✓] tectonic 0.15.0
[✓] Chromium configured
[✓] python-frontmatter 1.1.0
[✓] rsvg-convert 2.52.5
[✓] mermaid-cli 11.12.0
```

**Manual verification** (if script is not available):

```bash
# Python
python --version  # Should show 3.12+

# Pandoc
pandoc --version  # Should show 3.9+

# Node.js
node --version    # Should show 18+
npx --version     # Should be available

# LaTeX engine (check the one you installed)
tectonic --version   # OR
pdflatex --version   # OR
xelatex --version    # OR
lualatex --version
```

## Chromium Configuration

Mermaid diagram rendering requires Chrome or Chromium. If you used the install script,
Chromium is already configured. For manual installations or if you encounter issues:

Run the configuration script:
```bash
./scripts/configure-chromium.sh
```

The script will:
1. Detect your platform
2. For ARM64 Linux: prompt to use Playwright Chromium, system Chromium, or custom path
3. Generate `assets/puppeteerConfig.json` with the correct executable path

**Note**: The devcontainer handles this automatically.

## First Conversion

Create a simple test file:

```bash
cat > test.md << 'EOF'
---
title: Test Document
author: Your Name
date: 2025-01-01
---

# Hello World

This is a test document.
EOF
```

Convert it to PDF:

```bash
python convert.py test.md test.pdf
```

If successful, you'll see:
```
Converting test.md...
✅ /path/to/test.pdf
```

## Using as a Git Submodule

The converter is designed to be embedded in other repositories as a git submodule. This allows whitepaper source files to live alongside code while sharing a common, versioned conversion toolchain.

### Why Use a Submodule?

- **Version control**: Pin to a specific converter version; update deliberately
- **Shared tooling**: Multiple documents use the same converter configuration
- **Self-contained repos**: Document repositories include everything needed to build
- **CI/CD friendly**: Build pipelines can initialize submodules and run conversions

### Adding the Submodule

```bash
# Navigate to your document repository
cd my-whitepaper-repo

# Add the converter as a submodule (latex-template/ is the conventional name)
git submodule add https://github.com/cosai-oasis/cosai-whitepaper-converter.git latex-template

# Commit the submodule reference
git add .gitmodules latex-template
git commit -m "Add whitepaper converter as submodule"
```

### Repository Structure

After adding the submodule, your repository might look like:

```
my-whitepaper-repo/
├── .gitmodules              # Submodule configuration
├── latex-template/          # The converter (submodule)
│   ├── convert.py
│   ├── assets/
│   └── ...
├── whitepaper.md            # Your document
├── images/                  # Local images
│   └── diagram.png
└── Makefile                 # Build automation
```

### Running Conversions

From your repository root, reference the converter in the submodule:

```bash
# Direct invocation
python latex-template/convert.py whitepaper.md whitepaper.pdf

# With options
python latex-template/convert.py whitepaper.md whitepaper.pdf \
    --version $(git rev-parse --short HEAD)
```

### Example Makefile

Automate builds with a Makefile:

```Makefile
# List your markdown files
MDs := whitepaper.md \
       appendix.md
PDFs := $(MDs:.md=.pdf)

# Default target: build all PDFs
all: $(PDFs)

# Pattern rule: convert .md to .pdf
%.pdf: %.md
	@echo "Converting $< → $@"
	python latex-template/convert.py $< $@ --version=$$(git log -1 --format=%h $<)

# Clean generated files
.PHONY: clean
clean:
	rm -f $(PDFs)

# Update the converter submodule
.PHONY: update-converter
update-converter:
	git submodule update --remote latex-template
```

Usage:
```bash
make              # Build all PDFs
make clean        # Remove generated PDFs
make update-converter  # Update to latest converter
```

### Cloning a Repository with Submodules

When cloning a repository that contains the converter as a submodule:

```bash
# Option 1: Clone and initialize in one command
git clone --recurse-submodules https://github.com/org/my-whitepaper-repo.git

# Option 2: Initialize after cloning
git clone https://github.com/org/my-whitepaper-repo.git
cd my-whitepaper-repo
git submodule update --init --recursive
```

### Updating the Converter

To update to a newer version of the converter:

```bash
# Fetch and checkout the latest version
cd latex-template
git fetch origin
git checkout main
git pull
cd ..

# Commit the updated submodule reference
git add latex-template
git commit -m "Update whitepaper converter to latest version"
```

Or use the Makefile target if defined:
```bash
make update-converter
git add latex-template
git commit -m "Update whitepaper converter"
```

### Pinning to a Specific Version

To pin the converter to a specific commit or tag:

```bash
cd latex-template
git checkout v1.2.0  # Or a specific commit hash
cd ..
git add latex-template
git commit -m "Pin converter to v1.2.0"
```

### CI/CD Integration

#### Option 1: Using Install Script (Recommended)

```yaml
name: Build PDFs

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive  # Initialize submodules

      - name: Install dependencies
        run: |
          cd latex-template
          ./scripts/install-deps.sh || exit $?
          cd ..

      - name: Build PDFs
        run: make

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: pdfs
          path: "*.pdf"
```

#### Option 2: Manual Installation

```yaml
name: Build PDFs

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive  # Initialize submodules

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y pandoc nodejs npm
          pip install python-frontmatter
          # Install tectonic
          curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Build PDFs
        run: make

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: pdfs
          path: "*.pdf"
```

### How the Converter Detects Submodule Usage

The converter automatically detects when it's running from a `latex-template/` subdirectory:

```python
# In convert.py
dep_prefix = "latex-template" if os.path.exists("latex-template") else "."
config_path = os.path.join(dep_prefix, CONFIG_FILE_NAME)
```

This allows `converter_config.json` to be placed either:
- In the converter directory (`latex-template/converter_config.json`)
- In the parent repository root (`converter_config.json`)

Assets (templates, styles, images) are always loaded relative to the converter's location.

## Next Steps

- [Devcontainer Feature Documentation](../src/whitepaper-converter/README.md) - Full feature options and examples
- [Configuration Guide](configuration.md) - Customize converter settings
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Customization](customization.md) - Modify styling and templates
