import sys
import os
import re
import subprocess
import shutil
import tempfile
import argparse
import urllib.request

def convert_mermaid_to_pdf(mermaid_code, index):
    """
    Converts a mermaid code block to a PDF file using mermaid-cli.
    """
    tmp_mmd = f"diagram_{index}.mmd"
    tmp_pdf = f"diagram_{index}.pdf"
    
    with open(tmp_mmd, "w") as f:
        f.write(mermaid_code)
    
    # Use npx to run mmdc (Mermaid CLI)
    cmd = ["npx", "-y", "@mermaid-js/mermaid-cli", "-i", tmp_mmd, "-o", tmp_pdf]
    
    print(f"Generating diagram {index}...")
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error converting mermaid diagram {index}:")
        print(e.stderr.decode())
        return None
    finally:
        if os.path.exists(tmp_mmd):
            os.remove(tmp_mmd)
            
    return tmp_pdf

def download_image(url, index):
    """
    Downloads an image from a URL to a local temporary file.
    Converts GitHub blob URLs to raw URLs.
    """
    # Convert GitHub blob URLs to raw URLs
    if "github.com" in url and "/blob/" in url:
        url = url.replace("/blob/", "/raw/")
    
    try:
        # Determine extension from URL or default to .png
        ext = os.path.splitext(url)[1]
        if not ext or len(ext) > 5: # Basic check for valid extension
             ext = ".png"
        
        tmp_img = f"downloaded_image_{index}{ext}"
        
        print(f"Downloading image {index} from {url}...")
        urllib.request.urlretrieve(url, tmp_img)
        return tmp_img
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None

def process_markdown(input_file):
    """
    Reads markdown file, finds mermaid blocks, converts them, and replaces 
    blocks with image links. Also downloads remote images.
    """
    with open(input_file, "r") as f:
        content = f.read()

    # 1. Handle Mermaid blocks
    # Regex to find mermaid code blocks: ```mermaid ... ```
    mermaid_pattern = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
    
    diagram_count = 0
    def mermaid_replacer(match):
        nonlocal diagram_count
        mermaid_code = match.group(1)
        pdf_filename = convert_mermaid_to_pdf(mermaid_code, diagram_count)
        
        if pdf_filename:
            diagram_count += 1
            return f"![Diagram {diagram_count-1}]({pdf_filename})"
        else:
            return match.group(0) # distinct failure, keep original

    content = mermaid_pattern.sub(mermaid_replacer, content)

    # 2. Handle Remote Images
    # Regex to find image links: ![alt](url)
    # We are looking for http/https urls
    image_pattern = re.compile(r'!\[(.*?)\]\((http[s]?://.*?)\)')
    
    image_count = 0
    def image_replacer(match):
        nonlocal image_count
        alt_text = match.group(1)
        url = match.group(2)
        
        local_filename = download_image(url, image_count)
        
        if local_filename:
            image_count += 1
            return f"![{alt_text}]({local_filename})"
        else:
            return match.group(0) # distinct failure, keep original

    content = image_pattern.sub(image_replacer, content)
    
    return content

def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to PDF with Mermaid support.")
    parser.add_argument("input_file", help="Path to input Markdown file")
    parser.add_argument("output_file", help="Path to output PDF file")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        sys.exit(1)

    # create a temporary file for the processed markdown
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp_md:
        processed_content = process_markdown(args.input_file)
        tmp_md.write(processed_content)
        tmp_md_path = tmp_md.name

    print("Markdown processed. Running Pandoc...")

    cmd = [
        "pandoc",
        tmp_md_path,
        "-o", args.output_file,
        "--template=cosai-template.tex",
        "--pdf-engine=pdflatex",
        "--syntax-highlighting=idiomatic" # Replaced deprecated --listings
    ]
    print(f'Running command: {cmd}')
    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully created {args.output_file}")
    except subprocess.CalledProcessError as e:
        print("Error running pandoc:")
        print("Make sure you have a latex engine installed (e.g. pdflatex).")
    except FileNotFoundError:
        print("Error: pandoc not found.")
        print("Make sure pandoc is installed and in your PATH.")
    finally:
        # Cleanup temp markdown
        if os.path.exists(tmp_md_path):
            os.remove(tmp_md_path)
            
    # Optional logic to cleanup generated PDFs/Images could go here
    # but based on previous behaviour we leave them for now.

if __name__ == "__main__":
    main()
