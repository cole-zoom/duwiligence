from reportlab.lib.pagesizes import LETTER
from reportlab.lib.colors import black, white, HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate
from reportlab.pdfgen import canvas

def draw_header(canvas, doc, newsletter_title=""):
    width, height = LETTER
    # Draw black rectangle (extended to accommodate newsletter title)
    canvas.setFillColor(black)
    canvas.rect(0, height - 160, width, 160, fill=1, stroke=0)

    # Draw gold line
    gold = HexColor("#FAE100")
    canvas.setFillColor(gold)
    canvas.rect(0, height - 162, width, 2, fill=1, stroke=0)

    # Write title "dUW Diligence"
    canvas.setFont("Times-BoldItalic", 36)
    canvas.setFillColor(gold)
    canvas.drawString(72, height - 80, "dUW")

    canvas.setFont("Times-Roman", 36)
    canvas.setFillColor(white)
    canvas.drawString(150, height - 80, "Diligence")
    
    # Add newsletter title below "dUW Diligence" if provided
    if newsletter_title:
        canvas.setFont("Times-Roman", 18)
        canvas.setFillColor(white)
        # Center the newsletter title with more buffer from the gold line
        text_width = canvas.stringWidth(newsletter_title, "Times-Roman", 18)
        x_position = (width - text_width) / 2
        canvas.drawString(x_position, height - 130, newsletter_title)

def generate_pdf(data, filename="newsletter.pdf"):
    width, height = LETTER
    margin = 72
    usable_height = height - 240
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        'Story',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        leading=16,
        spaceAfter=12,
        textColor=black,
    )

    # Extract title and body from the new data format
    newsletter_title = data.get("title", "")
    newsletter_body = data.get("body", "")
    
    # Create the story flowables with just the body content
    story_flowables = []
    if newsletter_body:
        # Split body into paragraphs for better formatting
        paragraphs = newsletter_body.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():  # Only add non-empty paragraphs
                story_flowables.append(Paragraph(paragraph.strip(), body_style))
                story_flowables.append(Spacer(1, 12))
    else:
        # If no body content, add a placeholder
        story_flowables.append(Paragraph("No relevant stories found.", body_style))

    def on_page(canvas, doc):
        draw_header(canvas, doc, newsletter_title)

    frame = Frame(margin, margin, width - 2*margin, usable_height, showBoundary=0)
    template = PageTemplate(id='headered', frames=frame, onPage=on_page)
    doc = SimpleDocTemplate(filename, pagesize=LETTER, leftMargin=margin, rightMargin=margin, topMargin=margin, bottomMargin=margin)
    doc.addPageTemplates([template])
    doc.build(story_flowables)


if __name__ == '__main__':
    data = {
        "title": "Weekly Tech Market Update",
        "body": "NVDA\n\nNvidia could become the first company worth $4 trillion: \"Two years after Nvidia Corp. made history by becoming the first chipmaker to achieve a $1 trillion market capitalization, an even more remarkable milestone is within its grasp.\" — Ryan Vlastelica, Bloomberg News\n\nTSLA\n\nTesla shares surged following strong quarterly delivery numbers, beating analyst expectations by 15%. The electric vehicle manufacturer reported record deliveries of 466,140 vehicles in the quarter, demonstrating continued growth in the EV market.\n\nAAPL\n\nApple announced new AI features for iOS 18, including enhanced Siri capabilities and on-device machine learning improvements. The company's focus on privacy-first AI implementation has been well-received by both consumers and investors.",
    }
    generate_pdf(data)
