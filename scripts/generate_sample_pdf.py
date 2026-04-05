from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics import renderPDF

out_path = Path('sample_documents/supplier_launch_control_reference.pdf')
out_path.parent.mkdir(parents=True, exist_ok=True)

doc = SimpleDocTemplate(
    str(out_path),
    pagesize=A4,
    rightMargin=1.7 * cm,
    leftMargin=1.7 * cm,
    topMargin=1.6 * cm,
    bottomMargin=1.6 * cm,
)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Title2', parent=styles['Title'], fontSize=20, leading=24, textColor=colors.HexColor('#1f3a5f')))
styles.add(ParagraphStyle(name='Body2', parent=styles['BodyText'], fontSize=10.2, leading=15))
styles.add(ParagraphStyle(name='Sub2', parent=styles['Heading2'], fontSize=13, leading=16, textColor=colors.HexColor('#214e7a')))
styles.add(ParagraphStyle(name='Small2', parent=styles['BodyText'], fontSize=8.8, leading=12, textColor=colors.HexColor('#4d5b6a')) )
styles.add(ParagraphStyle(name='TableHeader', parent=styles['BodyText'], fontSize=9, leading=11, textColor=colors.white, fontName='Helvetica-Bold'))

story = []
story.append(Paragraph('Supplier Launch Control Reference Guide', styles['Title2']))
story.append(Paragraph('Synthetic multimodal PDF for parser and retrieval testing', styles['Small2']))
story.append(Spacer(1, 0.35 * cm))

intro = (
    'Automotive launch teams rely on APQP and PPAP documentation to confirm that a supplier has understood product requirements, '
    'stabilised the manufacturing process, and generated sufficient evidence for approval. In practice, the information is distributed '
    'across narrative procedure sections, phased checklists, capacity evidence, control plan references, PFMEA outputs, and launch review diagrams. '
    'This sample document is intentionally designed to contain text, tables, and a process diagram so that a multimodal RAG system can retrieve '
    'the right evidence for engineers, procurement stakeholders, and supplier quality teams.'
)
story.append(Paragraph(intro, styles['Body2']))
story.append(Spacer(1, 0.3 * cm))

p1 = (
    'Phase 1 Product PPAP focuses on design intent and early product evidence. Typical deliverables include the design record, approved engineering '
    'change documents, process flow chart, PFMEA, preliminary control plan, dimensional results for available characteristics, and material or '
    'performance test results. The objective of this phase is to demonstrate that the supplier understands the product and has begun translating customer '
    'requirements into a controlled manufacturing approach.'
)
p2 = (
    'Phase 2 Process PPAP deepens the assessment by validating the production process, measurement readiness, operator instructions, error-proofing, '
    'reaction plans, and traceability logic. Teams usually review control plan maturity, measurement system readiness, process audit findings, packaging, '
    'and trial build evidence. This phase is commonly used to confirm that the process is not only documented on paper but is also executable on the shop floor.'
)
p3 = (
    'Phase 3 Capacity PPAP confirms whether the supplier can sustain the required customer volume with acceptable quality. Evidence often includes run-at-rate '
    'results, bottleneck confirmation, scrap monitoring, final process capability status, and documented closure plans for any open issues. Capacity approval '
    'should not be interpreted as a design change approval; instead, it demonstrates readiness to meet production demand under stable operating conditions.'
)
for paragraph in (p1, p2, p3):
    story.append(Paragraph(paragraph, styles['Body2']))
    story.append(Spacer(1, 0.18 * cm))

story.append(Spacer(1, 0.15 * cm))
story.append(Paragraph('Key deliverables by PPAP phase', styles['Sub2']))
story.append(Spacer(1, 0.2 * cm))

table_data = [
    [Paragraph('Phase', styles['TableHeader']), Paragraph('Primary purpose', styles['TableHeader']), Paragraph('Typical evidence', styles['TableHeader'])],
    [Paragraph('Phase 1 Product PPAP', styles['Body2']), Paragraph('Confirm product understanding and early design alignment', styles['Body2']), Paragraph('Design record, engineering changes, process flow chart, PFMEA, preliminary control plan, dimensional and material test evidence', styles['Body2'])],
    [Paragraph('Phase 2 Process PPAP', styles['Body2']), Paragraph('Validate process execution and quality controls', styles['Body2']), Paragraph('Operator instructions, control plan updates, MSA readiness, process audit observations, traceability checks, packaging review', styles['Body2'])],
    [Paragraph('Phase 3 Capacity PPAP', styles['Body2']), Paragraph('Demonstrate production volume readiness', styles['Body2']), Paragraph('Run-at-rate evidence, bottleneck review, capability summary, scrap monitoring, open issue closure plan', styles['Body2'])],
]

ppap_table = Table(table_data, colWidths=[3.6 * cm, 4.8 * cm, 7.8 * cm], repeatRows=1)
ppap_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#24476b')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('LEADING', (0, 0), (-1, -1), 12),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f4f7fb'), colors.white]),
    ('GRID', (0, 0), (-1, -1), 0.45, colors.HexColor('#9bb0c7')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
story.append(ppap_table)
story.append(Spacer(1, 0.35 * cm))

story.append(Paragraph(
    'Supplier change requests should include enough context to allow the customer to evaluate whether the change affects part fit, form, function, safety, regulatory compliance, or process capability. '
    'Typical supporting documents include revised drawings, risk analysis, process flow updates, PFMEA impacts, control plan changes, trial part evidence, and the requested implementation timeline.',
    styles['Body2']
))

story.append(PageBreak())
story.append(Paragraph('Launch readiness timeline illustration', styles['Sub2']))
story.append(Spacer(1, 0.25 * cm))

d = Drawing(520, 240)
d.add(Rect(20, 150, 150, 48, fillColor=colors.HexColor('#d9e9f7'), strokeColor=colors.HexColor('#335f8a'), strokeWidth=1.1))
d.add(Rect(190, 150, 150, 48, fillColor=colors.HexColor('#dff0d8'), strokeColor=colors.HexColor('#497b39'), strokeWidth=1.1))
d.add(Rect(360, 150, 140, 48, fillColor=colors.HexColor('#fce5cd'), strokeColor=colors.HexColor('#b36b00'), strokeWidth=1.1))
for x1, x2 in [(170, 190), (340, 360)]:
    d.add(Line(x1, 174, x2, 174, strokeColor=colors.HexColor('#5b6b7a'), strokeWidth=2.2))
    d.add(Polygon(points=[x2 - 8, 180, x2, 174, x2 - 8, 168], fillColor=colors.HexColor('#5b6b7a'), strokeColor=colors.HexColor('#5b6b7a')))
d.add(String(42, 178, 'Phase 1 Product PPAP', fontName='Helvetica-Bold', fontSize=11, fillColor=colors.HexColor('#23405e')))
d.add(String(41, 162, 'Design record, process flow, PFMEA,', fontName='Helvetica', fontSize=9.5, fillColor=colors.black))
d.add(String(41, 149, 'preliminary control plan, early tests', fontName='Helvetica', fontSize=9.5, fillColor=colors.black))
d.add(String(211, 178, 'Phase 2 Process PPAP', fontName='Helvetica-Bold', fontSize=11, fillColor=colors.HexColor('#325d24')))
d.add(String(210, 162, 'MSA readiness, process audit,', fontName='Helvetica', fontSize=9.5, fillColor=colors.black))
d.add(String(210, 149, 'traceability, operator instructions', fontName='Helvetica', fontSize=9.5, fillColor=colors.black))
d.add(String(384, 178, 'Phase 3 Capacity PPAP', fontName='Helvetica-Bold', fontSize=11, fillColor=colors.HexColor('#8c4c00')))
d.add(String(378, 162, 'Run-at-rate, capability,', fontName='Helvetica', fontSize=9.5, fillColor=colors.black))
d.add(String(378, 149, 'bottleneck and closure plan', fontName='Helvetica', fontSize=9.5, fillColor=colors.black))
d.add(String(26, 110, 'Launch principle:', fontName='Helvetica-Bold', fontSize=10.5, fillColor=colors.HexColor('#1f3a5f')))
d.add(String(26, 96, 'evidence grows from product understanding to process confirmation', fontName='Helvetica', fontSize=9.6, fillColor=colors.black))
d.add(String(26, 84, 'and finally to volume readiness.', fontName='Helvetica', fontSize=9.6, fillColor=colors.black))

story.append(d)
story.append(Spacer(1, 0.3 * cm))

story.append(Paragraph(
    'The timeline shows that approval confidence should increase in a staged manner. Product PPAP establishes design understanding, Process PPAP checks whether the planned controls can operate in the manufacturing environment, and Capacity PPAP validates sustained output. '
    'A retrieval system should be able to explain the meaning of the diagram even when the answer depends on visual labels rather than only paragraph text.',
    styles['Body2']
))
story.append(Spacer(1, 0.25 * cm))

story.append(Paragraph('Sample retrieval questions', styles['Sub2']))
question_rows = [
    [Paragraph('Question type', styles['TableHeader']), Paragraph('Example query', styles['TableHeader'])],
    [Paragraph('Text-focused', styles['Body2']), Paragraph('Why is thorough documentation necessary during APQP, process audits, or PPAP activities?', styles['Body2'])],
    [Paragraph('Table-focused', styles['Body2']), Paragraph('List the documents required for Phase 1 Product PPAP.', styles['Body2'])],
    [Paragraph('Image-focused', styles['Body2']), Paragraph('Explain the launch-readiness timeline shown in the document.', styles['Body2'])],
    [Paragraph('Cross-modal', styles['Body2']), Paragraph('How do the three launch-readiness stages differ, and where do they appear in the timeline?', styles['Body2'])],
]
question_table = Table(question_rows, colWidths=[4.0 * cm, 12.3 * cm], repeatRows=1)
question_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#24476b')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('LEADING', (0, 0), (-1, -1), 12),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f6f9fc')]),
    ('GRID', (0, 0), (-1, -1), 0.45, colors.HexColor('#a9b8c8')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
story.append(question_table)

def add_page_number(canvas, doc):
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.HexColor('#5b6b7a'))
    canvas.drawRightString(19.5 * cm, 1.0 * cm, f'Page {doc.page}')


doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
print(f'Created {out_path}')
