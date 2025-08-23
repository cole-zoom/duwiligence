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
    "title": "Powell Signals Rate Cut Amid AI and Tech Sector Volatility",
    "body": "VGT VOOG\nAccording to WSJ Markets P.M., Jerome Powell's speech in Jackson Hole raised hopes for interest rate cuts and drove stocks higher on Friday. The rally reversed what had been a rough week for markets, and particularly tech stocks. According to FT Briefing, the sell-off provides a reminder of the risks of the tech sector’s dominance in public and private markets. According to Bloomberg, Fed Chair Jerome Powell was in Jackson Hole explaining why rising unemployment means a policy adjustment may be in the cards, a comment that instantly turbocharged markets.\n\nNVDA\nAccording to Bloomberg, Nvidia told its suppliers Samsung and Amkor to stop production related to its H20 AI chip after Beijing urged local firms to avoid using it. In other news, Bloomberg also reported that the market cap of Nvidia alone -- $4.3 trillion -- is larger than the GDP of the UK, France, or Italy. Looking ahead, WSJ Markets P.M. notes that Nvidia is set to post its fiscal second-quarter report on Wednesday afternoon.\n\nMETA GOOG\nAccording to Bloomberg, Meta agreed to a deal worth at least $10 billion with Google for cloud computing services, according to people familiar.\n\nMETA\nAccording to FT Briefing, Meta is set to license AI technology from start-up Midjourney as its in-house models lag rivals, a partnership that marks a shift away from internal product development.\n\nGOOG\nAccording to Bloomberg, Apple is exploring using Google Gemini AI to power a revamped Siri. Separately, according to WSJ The Future of Everything, Google’s new Pixel 10 is chock-full of useful AI tools.\n\nAMZN\nAccording to WSJ Politics & Policy, major retailers are thriving in the tariff economy. Walmart, Amazon and the owner of T.J. Maxx are scooping up market share from rivals by offering shoppers good deals and convenience. Additionally, WSJ The Future of Everything reports that cybercriminals are using AI to create high-quality fake websites, imitating well-known retailers such as Amazon.\n\nRY TD\nAccording to Bloomberg, the outlook for Canadian banks isn’t all that bad as the country’s big lenders head into reporting season. The Big Six — Royal Bank of Canada, Toronto-Dominion Bank, Bank of Nova Scotia, Bank of Montreal, Canadian Imperial Bank of Commerce and National Bank of Canada — have seen a run-up in their share prices since they last reported in the spring. The S&P/TSX banks index is now up more than 14% this year. The biggest member, RBC, hit another record on Thursday. Earnings reports are expected next week, with RBC reporting on Wednesday and Toronto-Dominion on Thursday.\n\nBTC\nAccording to FT Briefing, the EU is speeding up plans for a digital euro after a US stablecoin law. The news raises the possibility of a digital currency using a public rather than private blockchain. On a related note, an FT Briefing opinion piece titled \"Gold diggers follow the money\" notes that the danger with gold rushes is turning up too late, and previous bouts of outperformance have typically been reversed, a sentiment that could be applied to other alternative assets."
    }
    generate_pdf(data)
