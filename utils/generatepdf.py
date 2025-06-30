from reportlab.lib.pagesizes import LETTER
from reportlab.lib.colors import black, white, HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame
from reportlab.pdfgen import canvas

def draw_header(c, width, height):
    # Draw black rectangle
    c.setFillColor(black)
    c.rect(0, height - 120, width, 120, fill=1, stroke=0)

    # Draw gold line
    gold = HexColor("#FAE100")
    c.setFillColor(gold)
    c.rect(0, height - 122, width, 2, fill=1, stroke=0)

    # Write title "dUW Diligence"
    c.setFont("Times-BoldItalic", 36)
    c.setFillColor(gold)
    c.drawString(72, height - 80, "dUW")

    c.setFont("Times-Roman", 36)
    c.setFillColor(white)
    c.drawString(150, height - 80, "Diligence")

def generate_pdf(data, filename="newsletter.pdf"):
    width, height = LETTER
    c = canvas.Canvas(filename, pagesize=LETTER)
    draw_header(c, width, height)

    # Create frame for body text
    margin = 72
    usable_height = height - 180
    frame = Frame(margin, margin, width - 2*margin, usable_height, showBoundary=0)

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

    story_flowables = [Paragraph("",body_style)]
    for item in data:
        ticker = item["ticker"]
        for story in item["stories"]:
            title = story["title"]
            body = story["body"]
            confidence = story["confidence"]
            explanation = story["explanation"]

            story_text = f"<b>{ticker}:</b> <u>{title}</u><br/><br/>{body}<br/><br/><i>Explanation:</i> {explanation}<br/><br/><i>Confidence:</i> {confidence}%"
            story_flowables.append(Paragraph(story_text, body_style))
            story_flowables.append(Spacer(1, 12))

    frame.addFromList(story_flowables, c)
    c.save()


if __name__ == '__main__':
    data = [
        {
            "stories": [
                {
                    "body": "Nvidia could become the first company worth $4 trillion: “Two years after Nvidia Corp. made history by becoming the first chipmaker to achieve a $1 trillion market capitalization, an even more remarkable milestone is within its grasp.” — Ryan Vlastelica, Bloomberg News",
                    "confidence": 90,
                    "explanation": "The story about Nvidia potentially becoming the first company worth $4 trillion is relevant to VGT, which is the ticker for the Vanguard Information Technology ETF. Nvidia is a major component of many technology-focused ETFs, including VGT, due to its significant role in the semiconductor industry and its substantial market capitalization. Therefore, developments in Nvidia's valuation could impact the performance of VGT.",
                    "title": "Nvidia could become the first company worth $4 trillion"
                }
            ],
            "ticker": "VGT"
        },
        {
            "stories": [
                {
                    "body": "Nvidia could become the first company worth $4 trillion: “Two years after Nvidia Corp. made history by becoming the first chipmaker to achieve a $1 trillion market capitalization, an even more remarkable milestone is within its grasp.” — Ryan Vlastelica, Bloomberg News",
                    "confidence": 100,
                    "explanation": "This story is directly related to Nvidia (NVDA) as it discusses the company's potential to reach a $4 trillion market capitalization, highlighting its significant growth and market impact.",
                    "title": "Nvidia could become the first company worth $4 trillion"
                }
            ],
            "ticker": "NVDA"
        }
    ]   
    generate_pdf(data)
