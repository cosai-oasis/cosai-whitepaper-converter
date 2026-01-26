# CoSAI Markdownt to PDF Converter

Simple script to automatically convert Markdown files, specificially CoSAI's white papers, into nicely formatted PDFs. The process makes use of a few dependencies. The heavy lifting is performed by pandoc, plus a simple Python script to handle various nuances and corner cases that popped up. To run the tool

```bash
python convert.py whitepaper.md whitepaper.pdf
```

The `convert.py` script takes a few optional parameters, though we try to minimize the need to use them.

```
usage: convert.py [-h] [--title TITLE] [--author AUTHOR] [--date DATE] [--version VERSION] input_file output_file

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
```

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

Next, a Makefile can be used to automatically build the paper and handle some options, such as passing in the git commit for the version (which cannot be included into the metadata header). 


```Makefile
MDs := whitepaper-1.md \
        whitepaper-2.md
PDFs := $(MDs:.md=.pdf)

all: $(PDFs)

%.pdf: %.md
        @echo "Converting $< → $@"
        export TEXINPUTS=`pwd`/latex-template/:
        python latex-template/convert.py $< $@ --version=$$(git log -1 --format=%H $<)

.PHONY: clean
clean:
        @rm -f $(PDFs)
```

Other tools that have proven helpful here:
- rsvg-convert: for converting SVG to PDF to include

# Comments and Best Practices
Testing several markdown files has revealed a few best practices or things to note:
1. The `convert.py` file will omit a manually included table of contents in favor of the LaTeX generated TOC. As such, any references numbered section will break, e.g., `[Link](#123-Subsection-Link)`. A link to the section itself, `#Subsection-Link` will still work. A consistent section name should be used.
1. Anchor tags can be used to include links which pandoc will preserve <a id="anchor"></a>
1. White space at the end of lines, such as lists, causes Markdown to render as separate sections (includes extra vertical whitespace) and will mess up PDF formatting. The `convert.py` script will strip any line-ending whitespace globally. 
1. Mermaid files with a title will have that title extracted, and stripped, so that it can be used in the latex `\figure` caption. Mermaid is converted to PDF and will have a consistent CoSAI theme applied unless already present in the metadata header. (`config:` section)
1. Any break, `<br>`, and variants, are converted to `\newline`. Errant `<br>` will break the LaTeX compilation. If you get an error about `\newline`, try this.

## Known Issues
1. Currently there is an issue where some formatted text, such as ``**I want this bold**` will not be converted to a `\textbf` and will not not be bold. So far, this has only been observed in Markdown Tables.
