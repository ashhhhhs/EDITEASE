"""Embed a single PNG into the report .docx after a text anchor, with a caption.
Usage: python embed_one.py <png> <anchor substring> <caption> [width_in]"""
import os, re, sys, struct, zipfile, html, shutil, datetime

BASE = "/mnt/d/EDITEASE"
DOC = os.path.join(BASE, "2407774_AshreenDangol_EDITEASE_FYP_REPORT_FIXED.docx")


def main():
    png, anchor, caption = sys.argv[1], sys.argv[2], sys.argv[3]
    win = float(sys.argv[4]) if len(sys.argv) > 4 else 6.0
    w, h = struct.unpack(">II", open(png, "rb").read(24)[16:24])
    emu_w = int(win * 914400); emu_h = int(emu_w * h / w)
    name = os.path.basename(png)
    z = zipfile.ZipFile(DOC)
    xml = z.read("word/document.xml").decode("utf-8")
    rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    if name in xml:
        print("already embedded:", name); z.close(); return
    nmedia = max(int(m.group(1)) for m in re.finditer(r"media/image(\d+)\.png", rels)) + 1
    nrid = max(int(m.group(1)) for m in re.finditer(r'Id="rId(\d+)"', rels)) + 1
    rid = f"rId{nrid}"; member = f"word/media/image{nmedia}.png"
    draw = (
        '<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{emu_w}" cy="{emu_h}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="9060" name="{name}"/><wp:cNvGraphicFramePr>'
        '<a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/>'
        '</wp:cNvGraphicFramePr><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:nvPicPr><pic:cNvPr id="9060" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{emu_w}" cy="{emu_h}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
        '</wp:inline></w:drawing>')
    para = ('<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="60"/></w:pPr>'
            f'<w:r>{draw}</w:r></w:p>'
            '<w:p><w:pPr><w:spacing w:after="240"/><w:jc w:val="center"/>'
            '<w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr></w:pPr>'
            '<w:r><w:rPr><w:rFonts w:cs="Times New Roman"/><w:i/><w:sz w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">{html.escape(caption, quote=False)}</w:t></w:r></w:p>')
    pos = xml.rfind(anchor)
    if pos == -1:
        raise SystemExit("anchor not found: " + anchor)
    end = xml.find("</w:p>", pos) + len("</w:p>")
    xml = xml[:end] + para + xml[end:]
    rels = rels.replace("</Relationships>",
        f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
        f'Target="media/image{nmedia}.png"/></Relationships>')
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy(DOC, DOC.replace(".docx", f".pre_seq_{stamp}.docx"))
    tmp = DOC + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in z.infolist():
            if it.filename == "word/document.xml":
                zo.writestr(it, xml.encode("utf-8"))
            elif it.filename == "word/_rels/document.xml.rels":
                zo.writestr(it, rels.encode("utf-8"))
            else:
                zo.writestr(it, z.read(it.filename))
        zo.writestr(member, open(png, "rb").read())
    z.close(); os.replace(tmp, DOC)
    print(f"embedded {name} -> {rid}, {member}")


if __name__ == "__main__":
    main()
