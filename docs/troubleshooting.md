# Troubleshooting Guide

This guide covers common issues and their solutions.

## LaTeX Compilation Errors

### Unicode Character Errors (pdflatex)

**Symptom**: Errors like "Package inputenc Error: Unicode character"

**Cause**: pdflatex has limited Unicode support.

**Solutions**:
1. Use a Unicode-capable engine:
   ```bash
   python convert.py input.md output.pdf --engine tectonic
   ```
2. The converter automatically converts common Unicode characters (smart quotes, em dashes, ellipses) for pdflatex.

### Missing Package Errors

**Symptom**: "! LaTeX Error: File `package.sty' not found"

**Solutions**:

For **tectonic** (default):
- Packages are downloaded automatically. Ensure internet access.

For **texlive** (pdflatex, xelatex, lualatex):
```bash
# Ubuntu/Debian
sudo apt install texlive-latex-extra texlive-fonts-extra

# macOS
brew install --cask mactex

# Manual package install
tlmgr install package-name
```

### `\newline` Errors

**Symptom**: "! LaTeX Error: There's no line here to end"

**Cause**: `<br>` tags in places where LaTeX doesn't expect line breaks (e.g., inside tables or at start of paragraphs).

**Solutions**:
1. Find and remove errant `<br>` tags in your Markdown
2. Use blank lines for paragraph breaks instead

### Font Errors

**Symptom**: "Font ... not found"

**Cause**: Montserrat font not installed (used by CoSAI template).

**Solutions**:
```bash
# Ubuntu/Debian
sudo apt install fonts-montserrat

# Or install texlive fonts
sudo apt install texlive-fonts-extra
```

## Mermaid Diagram Issues

### Mermaid CLI Not Found

**Symptom**: "Failed to render diagram"

**Solutions**:
1. Verify Node.js is installed:
   ```bash
   node --version  # Should be 20+
   ```
2. Verify npx is available:
   ```bash
   npx --version
   ```
3. Test Mermaid CLI directly:
   ```bash
   npx -y @mermaid-js/mermaid-cli --help
   ```

### Chrome/Chromium Not Found (ARM64 Linux)

**Symptom**: "Could not find Chrome" or "Failed to launch browser"

**Cause**: On ARM64 Linux, Chrome is not available from Google. Puppeteer cannot
auto-detect a browser.

**Solution**: Run the configuration script:
```bash
./scripts/configure-chromium.sh
```

This will detect Playwright Chromium or system Chromium and configure
`assets/puppeteerConfig.json` with the correct path.

### Diagram Rendering Timeout

**Symptom**: Mermaid conversion hangs or times out.

**Cause**: Complex diagrams or slow system.

**Solutions**:
1. Simplify the diagram
2. Ensure puppeteerConfig.json includes:
   ```json
   {"args": ["--no-sandbox", "--disable-setuid-sandbox"]}
   ```

### Diagram Not Displayed

**Symptom**: Diagram code appears as text in PDF.

**Cause**: Syntax error in Mermaid code.

**Solutions**:
1. Validate your Mermaid syntax at [mermaid.live](https://mermaid.live/)
2. Check for unclosed brackets or quotes
3. Ensure the code block is properly fenced:
   ````markdown
   ```mermaid
   graph TD
       A --> B
   ```
   ````

## Pandoc Issues

### Pandoc Not Found

**Symptom**: "pandoc not found"

**Solutions**:
1. Install Pandoc:
   ```bash
   # Ubuntu/Debian
   sudo apt install pandoc

   # macOS
   brew install pandoc
   ```
2. Verify installation:
   ```bash
   pandoc --version
   ```
3. Ensure Pandoc is in PATH

### Version Mismatch

**Symptom**: Template errors or unexpected output.

**Cause**: Pandoc version too old.

**Solution**: Upgrade to Pandoc 3.9+:
```bash
# Ubuntu (get latest from GitHub)
wget https://github.com/jgm/pandoc/releases/download/3.9/pandoc-3.9-1-amd64.deb
sudo dpkg -i pandoc-3.9-1-amd64.deb
```

### "No counter '' defined" Error

**Symptom**: `LaTeX Error: No counter '' defined` during PDF generation, typically when the Markdown contains uncaptioned tables.

**Cause**: Pandoc versions before 3.8.2.1 emitted `\def\LTcaptype{}` for uncaptioned tables, which broke the `caption` LaTeX package.

**Solution**: Upgrade Pandoc to 3.9+ (the current project minimum). This was fixed in [Pandoc #11201](https://github.com/jgm/pandoc/issues/11201) starting with version 3.8.2.1.

## Image Issues

### Remote Images Not Downloaded

**Symptom**: "Failed to download image: URL"

**Causes**:
- Network issues
- Invalid URL
- Protected/authenticated URL

**Solutions**:
1. Verify the URL is accessible in a browser
2. Download the image manually and use a local path
3. For GitHub images, the converter auto-converts blob URLs to raw URLs

### Image Not Found

**Symptom**: Image placeholder in PDF.

**Solutions**:
1. Use absolute paths or paths relative to the Markdown file
2. Verify the image file exists

## Engine-Specific Issues

### tectonic

| Issue | Solution |
|-------|----------|
| Slow first run | Normal - downloading packages |
| "Network error" | Check internet connection |
| Cache issues | Delete `~/.cache/Tectonic` |

### pdflatex

| Issue | Solution |
|-------|----------|
| Unicode errors | Use `--engine tectonic` instead |
| Missing fonts | `sudo apt install texlive-fonts-extra` |
| Package errors | `tlmgr install package-name` |

### xelatex / lualatex

| Issue | Solution |
|-------|----------|
| Slow compilation | Normal for these engines |
| Font errors | Install system fonts or use texlive fonts |

## Devcontainer Feature Issues

### Feature Not Found

**Symptom**: "Feature not found: ghcr.io/cosai-oasis/..."

**Causes**:
- Registry not accessible
- Version tag doesn't exist
- Network/proxy issues

**Solutions**:
1. Verify you're using a valid version tag (`:1`, `:1.0`, or `:1.0.0`)
2. Check that GitHub Container Registry is accessible from your network
3. Try rebuilding without cache: "Dev Containers: Rebuild Container Without Cache"
4. Verify the package is public at [GHCR](https://github.com/orgs/cosai-oasis/packages)

### Feature Installation Fails

**Symptom**: Container build fails during feature installation.

**Solutions**:
1. Check your base image is supported (Debian, Ubuntu, or Alpine)
2. Review container build logs for specific errors
3. Try with `--log-level debug`:
   ```bash
   devcontainer up --workspace-folder . --log-level debug
   ```

### Conflicts with Other Features

**Symptom**: Python or Node.js version conflicts with other devcontainer features.

**Cause**: Multiple features trying to install same dependency.

**Solution**: Use skip options to avoid reinstalling components already provided by other features:
```json
{
  "features": {
    "ghcr.io/devcontainers/features/python:1": {"version": "3.12"},
    "ghcr.io/devcontainers/features/node:1": {"version": "20"},
    "ghcr.io/cosai-oasis/cosai-whitepaper-converter/whitepaper-converter:1": {
      "skipPython": true,
      "skipNode": true
    }
  }
}
```

### ARM64/Apple Silicon Issues

**Symptom**: Feature installs but Mermaid diagrams fail on ARM64.

**Cause**: Chromium configuration differs on ARM64 (uses Playwright bundled Chromium).

**Solutions**:
1. Run the configuration script inside the container:
   ```bash
   ./scripts/configure-chromium.sh
   ```
2. Or skip Chromium if you don't need Mermaid diagrams:
   ```json
   {
     "features": {
       "ghcr.io/cosai-oasis/cosai-whitepaper-converter/whitepaper-converter:1": {
         "skipChromium": true
       }
     }
   }
   ```

## Debug Tips

### Using `--debug` Mode

The `--debug` flag saves intermediate files and shows verbose engine output:

```bash
python convert.py input.md output.pdf --debug
```

This produces:
- `output_debug.md` — preprocessed Markdown (after all transformations)
- `output_debug.tex` — intermediate LaTeX (before PDF compilation)
- Verbose pandoc/engine output on the terminal

### Check Intermediate Files

1. Look at the `_debug.md` file for preprocessed Markdown
2. Look at the `_debug.tex` file for the LaTeX pandoc generates
3. Check SVG files for Mermaid output
4. Run pandoc manually for more verbose errors:
   ```bash
   pandoc processed.md -o output.pdf --template=cosai-template.tex --pdf-engine=tectonic
   ```

## Getting Help

If you've tried these solutions and still have issues:

1. Check the [GitHub Issues](https://github.com/your-org/cosai-whitepaper-converter/issues)
2. Include in your report:
   - Operating system and version
   - Python, Pandoc, Node.js versions
   - LaTeX engine and version
   - Full error message
   - Minimal Markdown that reproduces the issue
