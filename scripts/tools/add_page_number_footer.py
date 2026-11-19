"""Add the template's page-number footer to a report docx that has none: no number on the cover (section 1), a centred page number from the
certificate onward, numbering restarting at 1 on the certificate (section 2). Usage: python -I scripts/tools/add_page_number_footer.py <report.docx>"""
import sys

import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

path = sys.argv[1]
d = docx.Document(path)
sec = d.sections[1]
sec.footer.is_linked_to_previous = False
ftr = sec.footer
for p in list(ftr.paragraphs):
    p._p.getparent().remove(p._p)
rpr = '<w:rPr><w:rFonts w:ascii="times new roman" w:hAnsi="times new roman" w:cs="times new roman"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>'
p = parse_xml(
    f'<w:p {nsdecls("w")}><w:pPr><w:jc w:val="center"/></w:pPr>'
    f'<w:r>{rpr}<w:fldChar w:fldCharType="begin"/></w:r><w:r>{rpr}<w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
    f'<w:r>{rpr}<w:fldChar w:fldCharType="separate"/></w:r><w:r>{rpr}<w:t>1</w:t></w:r><w:r>{rpr}<w:fldChar w:fldCharType="end"/></w:r></w:p>')
ftr._element.append(p)
sp = sec._sectPr
for old in sp.findall(qn("w:pgNumType")):
    sp.remove(old)
pg = parse_xml(f'<w:pgNumType {nsdecls("w")} w:start="1"/>')
cols = sp.find(qn("w:cols"))
cols.addprevious(pg)
d.save(path)
print("footer added; sections:", len(d.sections))
