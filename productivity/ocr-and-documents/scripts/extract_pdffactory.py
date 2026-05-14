#!/usr/bin/env python3
"""
Reconstruct pdfFactory tiled PDF pages into full-page images.
Usage: python extract_pdffactory.py input.pdf [output_dir]

pdfFactory Pro splits each printed page into 46+ JPEG strips (tiles).
This script extracts tiles, reconstructs full pages, and saves as PNG.
"""
import sys, os, io
from PIL import Image
from pypdf import PdfReader

def reconstruct_pdf_pages(pdf_path, output_dir=None):
    reader = PdfReader(pdf_path)
    producer = reader.metadata.get('/Producer', '')
    is_pdffactory = 'pdfFactory' in producer
    
    if output_dir is None:
        output_dir = os.path.splitext(os.path.basename(pdf_path))[0] + "_pages"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"PDF: {os.path.basename(pdf_path)} ({len(reader.pages)} pages)")
    print(f"Producer: {producer}")
    print(f"pdfFactory detected: {is_pdffactory}")
    print(f"Output: {output_dir}/\n")
    
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        images = list(page.images)
        
        if not images:
            print(f"Page {page_num+1}: no embedded images, skipping")
            continue
        
        all_ims = [Image.open(io.BytesIO(img.data)) for img in images]
        tile_w = all_ims[0].width
        total_h = sum(im.height for im in all_ims)
        
        canvas = Image.new('RGB', (tile_w, total_h), (255, 255, 255))
        y = 0
        for im in all_ims:
            canvas.paste(im, (0, y))
            y += im.height
        
        out_path = os.path.join(output_dir, f"page_{page_num+1}.png")
        canvas.save(out_path, "PNG")
        print(f"Page {page_num+1}: {canvas.size[0]}x{canvas.size[1]} -> {out_path} ({os.path.getsize(out_path)//1024}KB)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_pdffactory.py input.pdf [output_dir]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else None
    reconstruct_pdf_pages(pdf_path, out_dir)
