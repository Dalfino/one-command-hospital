#!/usr/bin/env python3
"""Willow Health AI Suite whitepaper - ReportLab body generator (Report route).
Body PDF only: TOC + 11 chapters + references. Cover is merged later via pypdf."""
import os, sys, hashlib

PDF_SKILL_DIR = "/home/z/my-project/skills/pdf"
sys.path.insert(0, os.path.join(PDF_SKILL_DIR, "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                Table, TableStyle, Image, KeepTogether, CondPageBreak,
                                HRFlowable)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from PIL import Image as PILImage

# ---------- Fonts ----------
FONT_DIR = '/usr/share/fonts'
pdfmetrics.registerFont(TTFont('NotoSerifSC', f'{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerifSC-Bold', f'{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Bold.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif', f'{FONT_DIR}/truetype/freefont/FreeSerif.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-Bold', f'{FONT_DIR}/truetype/freefont/FreeSerifBold.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-Italic', f'{FONT_DIR}/truetype/freefont/FreeSerifItalic.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-BoldItalic', f'{FONT_DIR}/truetype/freefont/FreeSerifBoldItalic.ttf'))
registerFontFamily('NotoSerifSC', normal='NotoSerifSC', bold='NotoSerifSC-Bold')
registerFontFamily('FreeSerif', normal='FreeSerif', bold='FreeSerif-Bold',
                   italic='FreeSerif-Italic', boldItalic='FreeSerif-BoldItalic')

from pdf import install_font_fallback
install_font_fallback()

# ---------- Cascade palette (design_engine.py palette-cascade, intent=nature, seed=7) ----------
PAGE_BG       = colors.HexColor('#f5f6f5')
SECTION_BG    = colors.HexColor('#edeeed')
CARD_BG       = colors.HexColor('#e4eae7')
TABLE_STRIPE  = colors.HexColor('#edefee')
HEADER_FILL   = colors.HexColor('#456454')
COVER_BLOCK   = colors.HexColor('#556e62')
BORDER        = colors.HexColor('#b7d3c5')
ICON          = colors.HexColor('#3a7d5b')
ACCENT        = colors.HexColor('#298959')
ACCENT_2      = colors.HexColor('#4fbb85')
TEXT_PRIMARY  = colors.HexColor('#232725')
TEXT_MUTED    = colors.HexColor('#77817c')

# ---------- Geometry ----------
PAGE_W, PAGE_H = A4
MARGIN = 1.0 * inch
TOP_MARGIN, BOTTOM_MARGIN = 86, 76
AVAIL_W = PAGE_W - 2 * MARGIN            # ~451pt
AVAIL_H = PAGE_H - TOP_MARGIN - BOTTOM_MARGIN
H1_THRESHOLD = AVAIL_H * 0.25
MAX_KEEP_HEIGHT = PAGE_H * 0.4

DOC_TITLE = 'Willow Health AI Suite - A Hospital-Ready Open Clinical AI Platform'
DOC_AUTHOR = 'Willow Health AI - Clinical Operations Briefing'

OUT = '/home/z/my-project/scripts/body.pdf'
ASSETS = '/home/z/my-project/scripts/assets'

# ---------- Styles ----------
S = {}
S['body'] = ParagraphStyle('Body', fontName='FreeSerif', fontSize=10.5, leading=17,
                           alignment=TA_JUSTIFY, textColor=TEXT_PRIMARY, spaceBefore=0, spaceAfter=10)
S['h1'] = ParagraphStyle('H1', fontName='FreeSerif', fontSize=22, leading=27,
                         textColor=HEADER_FILL, spaceBefore=22, spaceAfter=4)
S['h2'] = ParagraphStyle('H2', fontName='FreeSerif', fontSize=15, leading=20,
                         textColor=HEADER_FILL, spaceBefore=16, spaceAfter=7)
S['h3'] = ParagraphStyle('H3', fontName='FreeSerif', fontSize=11.5, leading=16,
                         textColor=TEXT_PRIMARY, spaceBefore=12, spaceAfter=6)
S['bullet'] = ParagraphStyle('Bullet', fontName='FreeSerif', fontSize=10.5, leading=16,
                             alignment=TA_LEFT, textColor=TEXT_PRIMARY,
                             leftIndent=16, bulletIndent=4, spaceAfter=5)
S['caption'] = ParagraphStyle('Caption', fontName='FreeSerif', fontSize=8.5, leading=12,
                              alignment=TA_CENTER, textColor=TEXT_MUTED, spaceBefore=3, spaceAfter=6)
S['callout_stat'] = ParagraphStyle('CalloutStat', fontName='FreeSerif', fontSize=21, leading=25,
                                   textColor=ACCENT, alignment=TA_CENTER)
S['callout_label'] = ParagraphStyle('CalloutLabel', fontName='FreeSerif', fontSize=9, leading=12.5,
                                    textColor=TEXT_MUTED, alignment=TA_CENTER)
S['th'] = ParagraphStyle('TH', fontName='FreeSerif', fontSize=9, leading=12,
                         textColor=colors.white, alignment=TA_LEFT)
S['ref'] = ParagraphStyle('Ref', fontName='FreeSerif', fontSize=9.5, leading=14,
                          textColor=TEXT_PRIMARY, leftIndent=24, firstLineIndent=-24, spaceAfter=6)
S['toc_title'] = ParagraphStyle('TocTitle', fontName='FreeSerif', fontSize=20, leading=25,
                                textColor=HEADER_FILL, spaceAfter=14)
S['box_item'] = ParagraphStyle('BoxItem', fontName='FreeSerif', fontSize=9.5, leading=13.5,
                               textColor=TEXT_PRIMARY, alignment=TA_LEFT)

TOC_L0 = ParagraphStyle('TOC0', fontName='FreeSerif', fontSize=11.5, leading=18, leftIndent=6, textColor=TEXT_PRIMARY)
TOC_L1 = ParagraphStyle('TOC1', fontName='FreeSerif', fontSize=10, leading=15, leftIndent=26, textColor=TEXT_MUTED)


# ---------- Doc template ----------
class TocDocTemplate(SimpleDocTemplate):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.body_start_page = None

    def afterFlowable(self, flowable):
        # Always re-assign: multiBuild converges the value across passes.
        if getattr(flowable, 'is_body_start', False):
            self.body_start_page = self.page
        if hasattr(flowable, 'bookmark_name'):
            level = getattr(flowable, 'bookmark_level', 0)
            text = getattr(flowable, 'bookmark_text', '')
            key = getattr(flowable, 'bookmark_key', '')
            self.notify('TOCEntry', (level, text, self.page, key))


ROMAN = {1: 'i', 2: 'ii', 3: 'iii', 4: 'iv', 5: 'v', 6: 'vi', 7: 'vii', 8: 'viii'}


def on_page(canvas, doc):
    canvas.saveState()
    # Header: title left + accent rule
    canvas.setFont('FreeSerif', 7.5)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(MARGIN, PAGE_H - 52, DOC_TITLE)
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.5)
    canvas.line(MARGIN, PAGE_H - 60, PAGE_W - MARGIN, PAGE_H - 60)
    # Footer: light rule + author left + page number right (bare number only)
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 56, PAGE_W - MARGIN, 56)
    canvas.setFont('FreeSerif', 7.5)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(MARGIN, 44, DOC_AUTHOR)
    bsp = getattr(doc, 'body_start_page', None)
    if bsp is None or doc.page < bsp:
        label = ROMAN.get(doc.page, str(doc.page))
    else:
        label = str(doc.page - bsp + 1)
    canvas.drawRightString(PAGE_W - MARGIN, 44, label)
    canvas.restoreState()


# ---------- Helpers ----------
def safe_keep_together(elements):
    total_h = 0
    for el in elements:
        w, h = el.wrap(AVAIL_W, PAGE_H)
        total_h += h
    if total_h <= MAX_KEEP_HEIGHT:
        return [KeepTogether(elements)]
    elif len(elements) >= 2:
        return [KeepTogether(elements[:2])] + list(elements[2:])
    return list(elements)


def add_heading(text, style, level=0, body_start=False):
    key = 'h_%s' % hashlib.md5(text.encode()).hexdigest()[:8]
    p = Paragraph('<a name="%s"/><b>%s</b>' % (key, text), style)
    p.bookmark_name = key
    p.bookmark_level = level
    p.bookmark_text = text
    p.bookmark_key = key
    if body_start:
        p.is_body_start = True
    return p


def make_table(spec):
    ratios = spec['ratios']
    assert abs(sum(ratios) - 1.0) < 0.01, 'ratios must sum to 1'
    col_widths = [r * AVAIL_W for r in ratios]
    assert sum(col_widths) <= AVAIL_W + 0.5, 'table exceeds available width'
    fs = spec.get('font', 8.5)
    cell = ParagraphStyle('TD%s' % fs, fontName='FreeSerif', fontSize=fs, leading=fs + 3.5,
                          textColor=TEXT_PRIMARY, alignment=TA_LEFT)
    data = [[Paragraph('<b>%s</b>' % h, S['th']) for h in spec['header']]]
    for row in spec['rows']:
        data.append([Paragraph(str(c), cell) for c in row])
    t = Table(data, colWidths=col_widths, hAlign='CENTER', repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_FILL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 5.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5.5),
    ]
    for i in range(1, len(data)):
        style.append(('BACKGROUND', (0, i), (-1, i), colors.white if i % 2 == 1 else TABLE_STRIPE))
    t.setStyle(TableStyle(style))
    return t


def make_box(items):
    rows = [[Paragraph(it, S['box_item'])] for it in items]
    t = Table(rows, colWidths=[AVAIL_W * 0.94], hAlign='CENTER')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('LINEBEFORE', (0, 0), (0, -1), 3, ACCENT),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


def make_callout(stat, label):
    t = Table([[Paragraph('<b>%s</b>' % stat, S['callout_stat'])],
               [Paragraph(label, S['callout_label'])]],
              colWidths=[300], hAlign='CENTER')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, ACCENT),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
        ('TOPPADDING', (0, -1), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return t


def embed_image(path, max_width=None, max_height=None):
    if max_width is None:
        max_width = AVAIL_W
    if max_height is None:
        max_height = A4[1] * 0.35
    pil = PILImage.open(path)
    ow, oh = pil.size
    ratio = min(max_width / ow if ow > max_width else 1.0,
                max_height / oh if oh > max_height else 1.0)
    return Image(path, width=ow * ratio, height=oh * ratio)


# ---------- Build story ----------
from wp_content_a import A
from wp_content_b import B

story = []

# TOC (front matter, roman numbering)
story.append(Paragraph('<b>Table of Contents</b>', S['toc_title']))
story.append(HRFlowable(width='100%', color=ACCENT, thickness=1.2, spaceAfter=10))
toc = TableOfContents()
toc.levelStyles = [TOC_L0, TOC_L1]
story.append(toc)
story.append(PageBreak())

pending = None          # heading awaiting first body block (for KeepTogether)
seen_body_start = False

def flush(block):
    """Append block, binding any pending heading group to it via KeepTogether."""
    global pending
    if pending is not None:
        group = pending
        pending = None
        story.extend(safe_keep_together([*group, block]))
    else:
        story.append(block)

i = 0
blocks = A + B
while i < len(blocks):
    kind, payload = blocks[i][0], blocks[i][1]
    nxt = blocks[i + 1] if i + 1 < len(blocks) else None

    if kind in ('h1', 'h1_plain'):
        story.append(CondPageBreak(H1_THRESHOLD))
        h = add_heading(payload, S['h1'], level=0, body_start=(not seen_body_start and kind == 'h1_plain'))
        if not seen_body_start and kind == 'h1_plain':
            seen_body_start = True
        rule = HRFlowable(width='100%', color=ACCENT, thickness=1.2, spaceBefore=0, spaceAfter=12)
        pending = [h, rule]

    elif kind == 'h2':
        story.append(CondPageBreak(H1_THRESHOLD * 0.55))
        pending = [add_heading(payload, S['h2'], level=1)]

    elif kind == 'h3':
        pending = [Paragraph('<b>%s</b>' % payload, S['h3'])]

    elif kind == 'body':
        flush(Paragraph(payload, S['body']))

    elif kind == 'bullet':
        flush(Paragraph(payload, S['bullet'], bulletText='\u2022'))

    elif kind == 'callout':
        story.append(Spacer(1, 8))
        story.append(make_callout(blocks[i][1], blocks[i][2]))
        story.append(Spacer(1, 14))

    elif kind == 'table':
        story.append(Spacer(1, 12))
        t = make_table(payload)
        cap = Paragraph(payload['caption'], S['caption'])
        if len(payload['rows']) <= 15:
            story.extend(safe_keep_together([t, Spacer(1, 5), cap]))
        else:
            story.append(t); story.append(Spacer(1, 5)); story.append(cap)
        story.append(Spacer(1, 12))

    elif kind == 'box':
        story.append(Spacer(1, 4))
        story.append(make_box(payload))
        story.append(Spacer(1, 12))

    elif kind == 'image':
        img = embed_image(os.path.join(ASSETS, payload))
        cap_text = blocks[i][2] if len(blocks[i]) > 2 else None
        cap = Paragraph(cap_text, S['caption']) if cap_text else None
        story.append(Spacer(1, 14))
        group = [img] + ([Spacer(1, 6), cap] if cap else [])
        story.extend(safe_keep_together(group))
        story.append(Spacer(1, 14))

    elif kind == 'caption':
        pass  # reserved

    elif kind == 'refs':
        for ref in payload:
            story.append(Paragraph(ref, S['ref']))

    i += 1

if pending is not None:
    story.extend(pending)

# ---------- Build ----------
doc = TocDocTemplate(OUT, pagesize=A4,
                     leftMargin=MARGIN, rightMargin=MARGIN,
                     topMargin=TOP_MARGIN, bottomMargin=BOTTOM_MARGIN,
                     title=DOC_TITLE, author='Z.ai', creator='Z.ai',
                     subject='Hospital productization blueprint for an open clinical AI platform')
doc.multiBuild(story, onFirstPage=on_page, onLaterPages=on_page)
print('OK body.pdf, body_start_page =', doc.body_start_page)
