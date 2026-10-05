from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO


# ── Colours ──────────────────────────────────────────────────────────────────
DARK  = colors.HexColor('#1a1a2e')
MID   = colors.HexColor('#16213e')
LIGHT = colors.HexColor('#e8eaf6')
WHITE = colors.white
GREY  = colors.HexColor('#f5f5f5')

W, H  = A4          # 210 × 297 mm


def _style(name='Normal', **kw):
    base = getSampleStyleSheet()[name]
    return ParagraphStyle(name + str(id(kw)), parent=base, **kw)


def _p(text, **kw):
    return Paragraph(str(text) if text else '', _style(**kw))


def _label(text):
    return _p(text, fontSize=6, textColor=colors.grey, leading=8)


def _val(text, bold=False):
    return _p(
        str(text) if text else '—',
        fontSize=8,
        leading=10,
        fontName='Helvetica-Bold' if bold else 'Helvetica'
    )


def generate_bl_pdf(igm, commodity_name=None, forwarder_name=None, forwarder_address=None):
    """Generate a formal B/L PDF and return bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    story = []
    full_w = W - 24 * mm      # usable width

    # ── TITLE BLOCK ──────────────────────────────────────────────────────────
    title_data = [[
        _p('BILL OF LADING', fontSize=16, fontName='Helvetica-Bold',
           alignment=TA_CENTER, textColor=WHITE),
        _p('HOUSE B/L', fontSize=10, fontName='Helvetica-Bold',
           alignment=TA_RIGHT, textColor=colors.yellow)
    ]]
    title_tbl = Table(title_data, colWidths=[full_w * 0.75, full_w * 0.25])
    title_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
    ]))
    story.append(title_tbl)
    story.append(Spacer(1, 3 * mm))

    # ── FORWARDER BLOCK ───────────────────────────────────────────────────────
    fwd_data = [
        [_label('FORWARDER NAME'), _label('FORWARDER ADDRESS')],
        [_val(forwarder_name or '—', True), _val(forwarder_address or '—')],
    ]
    fwd_tbl = Table(fwd_data, colWidths=[full_w * 0.35, full_w * 0.65])
    fwd_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), LIGHT),
        ('BOX',           (0, 0), (-1, -1), 0.5, colors.grey),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
    ]))
    story.append(fwd_tbl)
    story.append(Spacer(1, 3 * mm))

    # ── BL REFERENCE ROW ─────────────────────────────────────────────────────
    bl_date = igm.bl_date.strftime('%d-%b-%Y') if igm.bl_date else '—'
    ref_data = [
        [_label('Master B/L No.'), _label('B/L No.'),
         _label('B/L Date'),       _label('POL'),
         _label('POD'),            _label('Manifest Type'),
         _label('Freight Type'),   _label('Freight Amount')],
        [_val(igm.m_bl_no, True),  _val(igm.bl_no, True),
         _val(bl_date),            _val(igm.pol),
         _val(igm.pod),            _val(igm.manifest_type),
         _val('Prepaid' if igm.frieght_type == 'P' else 'Collect' if igm.frieght_type == 'C' else '—'),
         _val(igm.fright_con)],
    ]
    col_w = full_w / 8
    ref_tbl = Table(ref_data, colWidths=[col_w] * 8)
    ref_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT),
        ('BOX',        (0, 0), (-1, -1), 0.5, colors.grey),
        ('INNERGRID',  (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
    ]))
    story.append(ref_tbl)
    story.append(Spacer(1, 3 * mm))

    # ── SHIPPER / CONSIGNEE / NOTIFY ─────────────────────────────────────────
    def addr_block(label, name, adr1, adr2, adr3, extra_label=None, extra_val=None):
        lines = [_label(label), _val(name, True)]
        for a in [adr1, adr2, adr3]:
            if a:
                lines.append(_val(a))
        if extra_label and extra_val:
            lines.append(_label(extra_label))
            lines.append(_val(extra_val))
        return lines

    shp_lines  = addr_block('SHIPPER',       igm.shp_name, igm.shp_adr1, igm.shp_adr2, igm.shp_adr3,
                             'COUNTRY', igm.shp_country)
    cne_lines  = addr_block('CONSIGNEE',     igm.cne_name, igm.cne_adr1, igm.cne_adr2, igm.cne_adr3,
                             'NTN', igm.cne_ntn)

    # Pad to same length
    max_len = max(len(shp_lines), len(cne_lines))
    for lst in [shp_lines, cne_lines]:
        while len(lst) < max_len:
            lst.append(_p(''))

    party_data = list(zip(shp_lines, cne_lines))
    col2 = full_w / 2
    party_tbl = Table(party_data, colWidths=[col2, col2])
    party_tbl.setStyle(TableStyle([
        ('BOX',       (0, 0), (-1, -1), 0.5, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('VALIGN',    (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT),
    ]))
    story.append(party_tbl)
    story.append(Spacer(1, 3 * mm))

    # ── GOODS ────────────────────────────────────────────────────────────────
    goods_data = [
        [_label('COMMODITY'), _label('HS CODE'),
         _label('DESCRIPTION OF GOODS'), _label('MARKS & NUMBERS')],
        [_val(commodity_name or igm.commodity), _val(igm.hs_code),
         _val(igm.dsc_of_goods), _val(igm.marks)],
    ]
    goods_tbl = Table(
        goods_data,
        colWidths=[full_w * 0.12, full_w * 0.12, full_w * 0.46, full_w * 0.30]
    )
    goods_tbl.setStyle(TableStyle([
        ('BOX',       (0, 0), (-1, -1), 0.5, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('VALIGN',    (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(goods_tbl)
    story.append(Spacer(1, 3 * mm))

    # ── CONTAINER TABLE ───────────────────────────────────────────────────────
    cnt_header = [
        _p('SR#',          fontSize=7, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_CENTER),
        _p('CONTAINER NO', fontSize=7, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_CENTER),
        _p('SEAL NO',      fontSize=7, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_CENTER),
        _p('SIZE',         fontSize=7, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_CENTER),
        _p('TYPE',         fontSize=7, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_CENTER),
        _p('TERM',         fontSize=7, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_CENTER),
        _p('PKG TYPE',     fontSize=7, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_CENTER),
        _p('NO. PKGS',     fontSize=7, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_CENTER),
        _p('NET WT',       fontSize=7, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_CENTER),
        _p('GROSS WT',     fontSize=7, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_CENTER),
    ]

    cnt_rows = [cnt_header]
    for c in igm.containers:
        cnt_rows.append([
            _p(str(int(c.sr_no)),   fontSize=7, alignment=TA_CENTER),
            _p(c.cnt_no or '—',     fontSize=7, fontName='Helvetica-Bold'),
            _p(c.seal_no or '—',    fontSize=7),
            _p(c.size or '—',       fontSize=7, alignment=TA_CENTER),
            _p(c.type or '—',       fontSize=7, alignment=TA_CENTER),
            _p(c.term or '—',       fontSize=7, alignment=TA_CENTER),
            _p(c.packages or '—',   fontSize=7, alignment=TA_CENTER),
            _p(str(int(c.no_of_pkgs)) if c.no_of_pkgs else '—', fontSize=7, alignment=TA_CENTER),
            _p(f'{float(c.net_weight):,.2f}' if c.net_weight else '—',   fontSize=7, alignment=TA_RIGHT),
            _p(f'{float(c.gross_weight):,.2f}' if c.gross_weight else '—', fontSize=7, alignment=TA_RIGHT),
        ])

    # Totals row
    total_pkgs  = sum(int(c.no_of_pkgs)    for c in igm.containers if c.no_of_pkgs)
    total_net   = sum(float(c.net_weight)   for c in igm.containers if c.net_weight)
    total_gross = sum(float(c.gross_weight) for c in igm.containers if c.gross_weight)
    cnt_rows.append([
        _p('TOTAL', fontSize=7, fontName='Helvetica-Bold', alignment=TA_RIGHT, colSpan=7),
        '', '', '', '', '', '',
        _p(str(total_pkgs),           fontSize=7, fontName='Helvetica-Bold', alignment=TA_CENTER),
        _p(f'{total_net:,.2f}',       fontSize=7, fontName='Helvetica-Bold', alignment=TA_RIGHT),
        _p(f'{total_gross:,.2f}',     fontSize=7, fontName='Helvetica-Bold', alignment=TA_RIGHT),
    ])

    cw = [
        full_w * 0.04, full_w * 0.14, full_w * 0.12,
        full_w * 0.06, full_w * 0.06, full_w * 0.10,
        full_w * 0.10, full_w * 0.09, full_w * 0.14, full_w * 0.15
    ]
    cnt_tbl = Table(cnt_rows, colWidths=cw, repeatRows=1)
    last = len(cnt_rows) - 1
    cnt_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),    MID),
        ('BACKGROUND',    (0, last), (-1, last), LIGHT),
        ('ROWBACKGROUNDS',(0, 1), (-1, last - 1), [WHITE, GREY]),
        ('BOX',           (0, 0), (-1, -1), 0.5, colors.grey),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 3),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN',          (0, last), (6, last)),
        ('FONTNAME',      (0, last), (-1, last), 'Helvetica-Bold'),
    ]))
    story.append(cnt_tbl)
    story.append(Spacer(1, 6 * mm))

    # ── SIGNATURE BLOCK ───────────────────────────────────────────────────────
    sig_data = [[
        _p('Shipped on board in apparent good order and condition.',
           fontSize=7, textColor=colors.grey),
        _p('As Agent for the Carrier', fontSize=7, alignment=TA_CENTER),
        _p('Authorised Signatory', fontSize=7, alignment=TA_CENTER),
    ]]
    sig_tbl = Table(sig_data, colWidths=[full_w * 0.5, full_w * 0.25, full_w * 0.25])
    sig_tbl.setStyle(TableStyle([
        ('BOX',       (0, 0), (-1, -1), 0.5, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('TOPPADDING',    (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('VALIGN',    (0, 0), (-1, -1), 'BOTTOM'),
    ]))
    story.append(sig_tbl)

    doc.build(story)
    buf.seek(0)
    return buf.read()