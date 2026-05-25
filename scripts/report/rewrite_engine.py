"""
Section-level rewrite engine for the FYP report .docx.

Operates on word/document.xml as an ordered list of top-level blocks
(<w:p>, <w:tbl>, other). It can:
  * strip the [CODEX-SCREENSHOT: ...] editorial notes from figure captions,
  * REPLACE a section's prose paragraphs with condensed ones while preserving
    the heading, any figures + their captions, and any tables,
  * INSERT new blocks (new chapters/sections/tables) before a given heading.

Headings, figures, captions, tables, front matter, references and appendices
are preserved verbatim unless explicitly targeted.
"""
import os, re, html, shutil, datetime, zipfile

BASE = "/mnt/d/EDITEASE"
DOC = os.path.join(BASE, "2407774_AshreenDangol_EDITEASE_FYP_REPORT_FIXED.docx")

RPR = '<w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr>'


# ---------- helpers to author content ----------
def esc(s):
    return html.escape(s, quote=False)


def para(text, after=160):
    return (f'<w:p><w:pPr><w:spacing w:after="{after}"/><w:jc w:val="both"/>{RPR}</w:pPr>'
            f'<w:r>{RPR}<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')


def lead_para(lead, rest, after=160):
    return (f'<w:p><w:pPr><w:spacing w:after="{after}"/><w:jc w:val="both"/>{RPR}</w:pPr>'
            f'<w:r><w:rPr><w:rFonts w:cs="Times New Roman"/><w:b/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(lead)}</w:t></w:r>'
            f'<w:r>{RPR}<w:t xml:space="preserve">{esc(rest)}</w:t></w:r></w:p>')


def bullet(text):
    return (f'<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
            f'<w:spacing w:after="60"/><w:jc w:val="both"/>{RPR}</w:pPr>'
            f'<w:r>{RPR}<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')


def heading(text, level=3):
    rf = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
    return (f'<w:p><w:pPr><w:pStyle w:val="Heading{level}"/><w:jc w:val="both"/>'
            f'<w:rPr>{rf}</w:rPr></w:pPr>'
            f'<w:r><w:rPr>{rf}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')


def table(headers, rows, widths=None):
    n = len(headers)
    widths = widths or [int(9180 / n)] * n
    grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths)

    def cell(txt, w, bold=False):
        b = '<w:b/>' if bold else ''
        shade = '<w:shd w:val="clear" w:fill="F0F0F0"/>' if bold else ''
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shade}</w:tcPr>'
                f'<w:p><w:pPr><w:spacing w:after="20"/><w:jc w:val="both"/>'
                f'<w:rPr><w:rFonts w:cs="Times New Roman"/><w:sz w:val="20"/>{b}</w:rPr></w:pPr>'
                f'<w:r><w:rPr><w:rFonts w:cs="Times New Roman"/><w:sz w:val="20"/>{b}</w:rPr>'
                f'<w:t xml:space="preserve">{esc(txt)}</w:t></w:r></w:p></w:tc>')
    trs = ['<w:tr>' + ''.join(cell(h, widths[i], True) for i, h in enumerate(headers)) + '</w:tr>']
    for row in rows:
        trs.append('<w:tr>' + ''.join(cell(str(c), widths[i]) for i, c in enumerate(row)) + '</w:tr>')
    return ('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/>'
            '<w:tblBorders>'
            '<w:top w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
            '<w:left w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
            '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
            '<w:right w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
            '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
            '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
            '</w:tblBorders><w:tblLook w:val="04A0"/></w:tblPr>'
            f'<w:tblGrid>{grid}</w:tblGrid>' + ''.join(trs) + '</w:tbl>'
            + '<w:p><w:pPr><w:spacing w:after="120"/></w:pPr></w:p>')


# ---------- block tokeniser ----------
def split_blocks(s):
    out = []; i = 0; n = len(s)
    while i < n:
        if s.startswith('<w:p', i) and s[i+4] in ' >':
            j = s.index('</w:p>', i) + 6; out.append(['p', s[i:j]]); i = j
        elif s.startswith('<w:tbl', i) and s[i+6] in ' >':
            j = s.index('</w:tbl>', i) + 8; out.append(['tbl', s[i:j]]); i = j
        else:
            np_ = s.find('<w:p', i); nt = s.find('<w:tbl', i)
            cands = [x for x in (np_, nt) if x != -1]
            j = min(cands) if cands else n
            if j <= i:
                j = i + 1
            out.append(['other', s[i:j]]); i = j
    return out


def block_text(b):
    return html.unescape(''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', b[1])))


def is_heading(b):
    return b[0] == 'p' and 'w:pStyle w:val="Heading' in b[1]


def heading_title(b):
    return block_text(b).strip()


def is_keepable(b):
    if b[0] == 'tbl':
        return True
    if b[0] == 'p' and '<w:drawing>' in b[1]:
        return True
    if b[0] == 'p' and block_text(b).strip().startswith('Figure '):
        return True
    return False


def body_word_count(body_xml):
    """Count body prose words: re-tokenise the body, count <w:p> blocks between
    the Introduction and References headings, excluding headings, figure
    captions ('Figure ...') and tables."""
    blocks = split_blocks(body_xml)
    total = 0
    seen_intro = False
    for b in blocks:
        if is_heading(b):
            t = heading_title(b)
            if t.startswith('1.1') or t == 'Introduction':
                seen_intro = True
            if t.startswith('References'):
                seen_intro = False
            continue
        if seen_intro and b[0] == 'p':
            tx = block_text(b)
            if not tx.strip().startswith('Figure'):
                total += len(tx.split())
    return total


def apply(replacements, inserts, rename=None, strip_codex=True, dry=False):
    """replacements: {heading_title: [xml_paragraph,...]}
       inserts: list of (before_heading_title, xml_block)
       rename: {old_title: new_title}
    """
    z = zipfile.ZipFile(DOC)
    xml = z.read('word/document.xml').decode('utf-8')
    if strip_codex:
        xml = re.sub(r'\s*\[CODEX-SCREENSHOT:.*?\]', '', xml, flags=re.S)

    pre, body, suf = re.match(r'(.*<w:body>)(.*)(</w:body>.*)', xml, re.S).groups()
    blocks = split_blocks(body)

    # locate heading indices
    head_idx = [i for i, b in enumerate(blocks) if is_heading(b)]
    titles = {heading_title(blocks[i]): i for i in head_idx}

    # report any missing targets
    missing = [t for t in list(replacements) + [t for t, _ in inserts] if t not in titles]
    if missing:
        raise SystemExit("targets not found:\n  " + "\n  ".join(missing))

    # build section end map (next heading index)
    end_of = {}
    for k, i in enumerate(head_idx):
        end_of[i] = head_idx[k+1] if k+1 < len(head_idx) else len(blocks)

    new_blocks = []
    i = 0
    insert_map = {}
    for t, blk in inserts:
        insert_map.setdefault(titles[t], []).append(blk)

    while i < len(blocks):
        b = blocks[i]
        # insertion before this heading
        if i in insert_map:
            for blk in insert_map[i]:
                new_blocks.append(['raw', blk])
        if is_heading(b) and heading_title(b) in replacements:
            title = heading_title(b)
            # optional rename
            hb = b
            if rename and title in rename:
                hb = ['p', b[1].replace(f'<w:t xml:space="preserve">{title}</w:t>',
                                       f'<w:t xml:space="preserve">{esc(rename[title])}</w:t>')
                      .replace(f'<w:t>{title}</w:t>', f'<w:t>{esc(rename[title])}</w:t>')]
            new_blocks.append(hb)
            # condensed paras
            for p in replacements[title]:
                new_blocks.append(['raw', p])
            # keep figures/captions/tables from original section, drop other text
            for j in range(i+1, end_of[i]):
                if is_keepable(blocks[j]):
                    new_blocks.append(blocks[j])
            i = end_of[i]
            continue
        new_blocks.append(b)
        i += 1

    new_body = ''.join(b[1] for b in new_blocks)
    new_xml = pre + new_body + suf

    wc = body_word_count(new_body)
    print("BODY word count after rewrite:", wc)
    if dry:
        z.close(); return wc, new_xml

    # validate well-formed
    import xml.dom.minidom as M
    M.parseString(new_xml.encode('utf-8'))

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy(DOC, DOC.replace(".docx", f".pre_rewrite_{stamp}.docx"))
    tmp = DOC + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in z.infolist():
            if it.filename == "word/document.xml":
                zo.writestr(it, new_xml.encode("utf-8"))
            else:
                zo.writestr(it, z.read(it.filename))
    z.close(); os.replace(tmp, DOC)
    print("wrote", DOC)
    return wc, new_xml
