#!/usr/bin/env python3
"""Merge cover.pdf + body.pdf into the final whitepaper, normalized to A4."""
from pypdf import PdfReader, PdfWriter

A4_W, A4_H = 595.28, 841.89

def normalize_page_to_a4(page):
    box = page.mediabox
    w, h = float(box.width), float(box.height)
    if abs(w - A4_W) > 0.1 or abs(h - A4_H) > 0.1:
        page.scale_to(A4_W, A4_H)
    return page

def insert_cover(cover_pdf, body_pdf, output_pdf):
    writer = PdfWriter()
    cover_page = PdfReader(cover_pdf).pages[0]
    writer.add_page(normalize_page_to_a4(cover_page))
    for page in PdfReader(body_pdf).pages:
        writer.add_page(normalize_page_to_a4(page))
    writer.add_metadata({
        '/Title': 'Willow Health AI Suite - A Hospital-Ready Open Clinical AI Platform',
        '/Author': 'Z.ai', '/Creator': 'Z.ai',
        '/Subject': 'Hospital productization blueprint for an open clinical AI platform',
    })
    with open(output_pdf, 'wb') as f:
        writer.write(f)
    print('OK merged:', output_pdf, 'pages:', len(writer.pages))

if __name__ == '__main__':
    insert_cover('/home/z/my-project/scripts/cover.pdf',
                 '/home/z/my-project/scripts/body.pdf',
                 '/home/z/my-project/download/Willow_Health_AI_Suite_Whitepaper.pdf')
