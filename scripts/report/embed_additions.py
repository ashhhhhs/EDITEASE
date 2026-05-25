"""
Insert the template-required additions into the FYP report .docx:
  * 5 design figures (Use Case, Class, ERD, Wireframe, Activity) as embedded PNGs
  * a Declaration sheet (front matter, before the Abstract)
  * a testing-framework / package-manager paragraph (end of Chapter 4)

Operates at the OOXML level by mirroring the document's existing inline-image
structure (it already embeds 55 PNGs), so the result stays MS-Word compatible.
A timestamped backup is written next to the source first.
"""
import os, re, shutil, struct, zipfile, html, datetime

BASE = "/mnt/d/EDITEASE"
DOC = os.path.join(BASE, "2407774_AshreenDangol_EDITEASE_FYP_REPORT_FIXED.docx")
FIGDIR = os.path.join(BASE, "report_assets", "screenshots")
EMU_PER_IN = 914400

# (file, caption, target_width_inches)
FIGURES = [
    ("figure_5_2a_use_case.png",
     "Figure 5.2a – Use Case Diagram showing the Editor and Admin actors against the EditEase system boundary.",
     6.0, "FDD"),
    ("figure_5_2b_class_diagram.png",
     "Figure 5.2b – Class / Module Diagram of the classifier hierarchy, processing pipeline, service layer and the Scene document.",
     6.0, "FDD"),
    ("figure_5_5a_erd.png",
     "Figure 5.5a – Entity Relationship Diagram of the MongoDB collections (users, scenes, tasks, organized_videos).",
     6.0, "DBSCHEMA"),
    ("figure_5_6a_wireframe.png",
     "Figure 5.6a – Wireframe of the Dashboard clip-grid workspace, filter rail and Inspector panel (AppShell layout).",
     6.0, "UI"),
    ("figure_6_1a_activity.png",
     "Figure 6.1a – Activity Diagram of the process_video() pipeline, including the confidence-band agentic decision and the per-scene loop.",
     4.3, "PIPELINE"),
]

ANCHORS = {  # body occurrence located with rfind
    "FDD": "Functional Decomposition Diagram (FDD)",
    "DBSCHEMA": "Scene Metadata Database Schema",
    "UI": "Live User Interface Layout",
    "PIPELINE": "Pipeline of Video Processing",
}


def png_size(path):
    d = open(path, "rb").read(24)
    return struct.unpack(">II", d[16:24])


def esc(s):
    return html.escape(s, quote=False)


def drawing(rid, name, emu_w, emu_h, docpr_id):
    return (
        '<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{emu_w}" cy="{emu_h}"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{docpr_id}" name="{esc(name)}"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/>'
        '</wp:cNvGraphicFramePr>'
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:nvPicPr><pic:cNvPr id="{docpr_id}" name="{esc(name)}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{emu_w}" cy="{emu_h}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>'
    )


def fig_paragraphs(rid, name, caption, emu_w, emu_h, docpr_id):
    img = ('<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="60"/></w:pPr>'
           f'<w:r>{drawing(rid, name, emu_w, emu_h, docpr_id)}</w:r></w:p>')
    cap = ('<w:p><w:pPr><w:spacing w:after="240"/><w:jc w:val="center"/>'
           '<w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr></w:pPr>'
           '<w:r><w:rPr><w:rFonts w:cs="Times New Roman"/><w:i/><w:sz w:val="20"/></w:rPr>'
           f'<w:t xml:space="preserve">{esc(caption)}</w:t></w:r></w:p>')
    return img + cap


def body_para(text, after=240):
    return (f'<w:p><w:pPr><w:spacing w:after="{after}"/><w:jc w:val="both"/>'
            '<w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr></w:pPr>'
            '<w:r><w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')


def lead_para(lead, rest):
    return ('<w:p><w:pPr><w:spacing w:after="240"/><w:jc w:val="both"/>'
            '<w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr></w:pPr>'
            '<w:r><w:rPr><w:rFonts w:cs="Times New Roman"/><w:b/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(lead)}</w:t></w:r>'
            '<w:r><w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(rest)}</w:t></w:r></w:p>')


def declaration_block():
    pb = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
    head = ('<w:p><w:pPr><w:pStyle w:val="Heading2"/><w:jc w:val="both"/>'
            '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/></w:rPr></w:pPr>'
            '<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/></w:rPr>'
            '<w:t>Declaration</w:t></w:r></w:p>')
    body = body_para(
        "I, Ashreen Dangol (Student ID 2407774), declare that this report titled "
        "“EditEase: An AI-Assisted Video Organising Platform” and the artefact it describes are my own "
        "work, carried out under the supervision of Kaushal Kishor Mishra for the Project and Professionalism "
        "module at Herald College Kathmandu (University of Wolverhampton). All sources of information, datasets "
        "and third-party libraries used have been acknowledged in the text and in the list of references.")
    body2 = body_para(
        "This work has not been submitted, in whole or in part, for any other degree or qualification at this "
        "or any other institution. Where the work of others has been used, it has been clearly cited and "
        "referenced, and any assistance received has been duly acknowledged.")
    sig = ('<w:p><w:pPr><w:spacing w:before="360" w:after="120"/><w:jc w:val="both"/>'
           '<w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr></w:pPr>'
           '<w:r><w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr>'
           '<w:t xml:space="preserve">Signed: ______________________</w:t></w:r>'
           '<w:r><w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr>'
           '<w:t xml:space="preserve">          Date: __________________</w:t></w:r></w:p>')
    name = body_para("Name: Ashreen Dangol          Student ID: 2407774", after=0)
    return pb + head + body + body2 + sig + name


def tools_para():
    return lead_para(
        "Testing and Dependency Management. ",
        "Backend behaviour is verified with the pytest framework (configured in pyproject.toml, with the "
        "suite under tests/ and shared fixtures in tests/conftest.py); fixtures isolate the service layer and "
        "stub external calls to MongoDB and Cloudinary so tests run without live infrastructure. Python "
        "dependencies are resolved with the pip package manager against the project's pyproject.toml, while the "
        "React frontend uses the npm package manager (package.json with a committed package-lock.json) together "
        "with the Vite build toolchain. A Makefile wraps these managers behind single targets (make install, "
        "make run-api, make run-celery, make run-frontend) to give a reproducible setup and run path.")


def main():
    z = zipfile.ZipFile(DOC)
    xml = z.read("word/document.xml").decode("utf-8")
    rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    orig_xml = xml

    # next media + rId numbers
    media_nums = [int(m.group(1)) for m in re.finditer(r"media/image(\d+)\.png", rels)]
    next_media = max(media_nums) + 1
    next_rid = max(int(m.group(1)) for m in re.finditer(r'Id="rId(\d+)"', rels)) + 1
    docpr = 9001

    new_media = {}          # zip member -> bytes
    new_rel_entries = []     # rel xml fragments
    inserts = []             # (orig_index, text)

    # group figure blocks per anchor
    per_anchor = {}
    for fname, caption, win, anchor in FIGURES:
        path = os.path.join(FIGDIR, fname)
        w, h = png_size(path)
        emu_w = int(win * EMU_PER_IN)
        emu_h = int(emu_w * h / w)
        member = f"word/media/image{next_media}.png"
        rid = f"rId{next_rid}"
        new_media[member] = open(path, "rb").read()
        new_rel_entries.append(
            f'<Relationship Id="{rid}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
            f'Target="media/image{next_media}.png"/>')
        block = fig_paragraphs(rid, fname, caption, emu_w, emu_h, docpr)
        per_anchor.setdefault(anchor, []).append(block)
        print(f"  prepared {fname}  {w}x{h}px -> {emu_w}x{emu_h}EMU  {rid}  {member}")
        next_media += 1; next_rid += 1; docpr += 1

    # figure insertion points: after </w:p> of the body caption (rfind anchor)
    for anchor, blocks in per_anchor.items():
        needle = ANCHORS[anchor]
        pos = xml.rfind(needle)
        assert pos != -1, f"anchor not found: {needle}"
        end = xml.find("</w:p>", pos) + len("</w:p>")
        inserts.append((end, "".join(blocks)))

    # declaration: before the Heading2 'Abstract' body paragraph
    abs = None
    for m in re.finditer(r"<w:p\b[^>]*>(?:(?!</w:p>).)*?Heading2(?:(?!</w:p>).)*?<w:t[^>]*>Abstract</w:t>", xml, re.S):
        abs = m.start()
    assert abs is not None, "Abstract Heading2 not found"
    inserts.append((abs, declaration_block()))

    # tools paragraph: before the Heading3 '5.1 Introduction to the Design of the Artefact'
    t_pos = xml.rfind("Introduction to the Design of the Artefact")
    p_start = max(xml.rfind("<w:p ", 0, t_pos), xml.rfind("<w:p>", 0, t_pos))
    assert p_start != -1
    inserts.append((p_start, tools_para()))

    # apply inserts descending so offsets stay valid
    for idx, text in sorted(inserts, key=lambda t: -t[0]):
        xml = xml[:idx] + text + xml[idx:]
    assert xml != orig_xml

    # splice new relationships before </Relationships>
    rels = rels.replace("</Relationships>", "".join(new_rel_entries) + "</Relationships>")

    # backup + write
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy(DOC, DOC.replace(".docx", f".pre_figs_{stamp}.docx"))

    tmp = DOC + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in z.infolist():
            if item.filename == "word/document.xml":
                zout.writestr(item, xml.encode("utf-8"))
            elif item.filename == "word/_rels/document.xml.rels":
                zout.writestr(item, rels.encode("utf-8"))
            else:
                zout.writestr(item, z.read(item.filename))
        for member, data in new_media.items():
            zout.writestr(member, data)
    z.close()
    os.replace(tmp, DOC)
    print("wrote", DOC)


if __name__ == "__main__":
    main()
