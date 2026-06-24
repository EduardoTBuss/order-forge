"""
Generate sample PDF files for integration tests.

Run this script to regenerate the test PDFs:
    python -m tests.samples.generate_pdfs

The generated PDFs are committed to git so tests don't need reportlab at runtime.
"""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

SAMPLES_DIR = Path(__file__).parent


def create_pdf(filename: str, pages: list[list[str]]) -> None:
    """Create a PDF with the given pages of text content."""
    filepath = SAMPLES_DIR / filename
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=20,
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        spaceAfter=12,
    )

    story = []
    for i, page_content in enumerate(pages):
        if i > 0:
            story.append(PageBreak())

        for j, text in enumerate(page_content):
            if j == 0:
                story.append(Paragraph(text, title_style))
            else:
                story.append(Paragraph(text, body_style))
            story.append(Spacer(1, 6))

    doc.build(story)
    print(f"Created: {filepath}")


def generate_single_page_invoice() -> None:
    """Generate a simple single-page invoice PDF."""
    pages = [
        [
            "INVOICE #INV-2024-001",
            "Date: January 15, 2024",
            "Bill To: Acme Corporation, 123 Business Street, New York, NY 10001",
            "From: Tech Solutions Inc., 456 Innovation Drive, San Francisco, CA 94105",
            "",
            "Description: Software Development Services",
            "Quantity: 40 hours",
            "Rate: $150.00 per hour",
            "Subtotal: $6,000.00",
            "Tax (8%): $480.00",
            "Total Amount Due: $6,480.00",
            "",
            "Payment Terms: Net 30",
            "Due Date: February 14, 2024",
        ]
    ]
    create_pdf("single_page_invoice.pdf", pages)


def generate_multi_page_contract() -> None:
    """Generate a 3-page contract PDF with information distributed across pages."""
    pages = [
        [
            "SERVICE AGREEMENT",
            "Contract Number: SA-2024-0042",
            "",
            "This Service Agreement is entered into between:",
            "Provider: CloudTech Solutions Inc., a Delaware corporation",
            "Client: Global Enterprises LLC, a New York limited liability company",
            "",
            "Effective Date: March 1, 2024",
            "",
            "ARTICLE 1: SERVICES",
            "Provider agrees to deliver cloud infrastructure management services "
            "including server monitoring, security updates, and technical support.",
        ],
        [
            "ARTICLE 2: COMPENSATION",
            "Monthly Service Fee: $4,500.00",
            "Payment is due on the first business day of each month.",
            "",
            "ARTICLE 3: TERM",
            "Contract Duration: 24 months",
            "This agreement shall commence on the Effective Date and continue "
            "for a period of twenty-four (24) months unless terminated earlier.",
            "",
            "ARTICLE 4: SERVICE LEVELS",
            "System Uptime Guarantee: 99.9%",
            "Provider guarantees system availability of ninety-nine point nine percent.",
        ],
        [
            "ARTICLE 5: GOVERNING LAW",
            "This Agreement shall be governed by the laws of the State of California.",
            "",
            "ARTICLE 6: SIGNATURES",
            "IN WITNESS WHEREOF, the parties have executed this Agreement.",
            "",
            "Provider Representative: ___________________",
            "Client Representative: ___________________",
            "Date: ___________________",
        ],
    ]
    create_pdf("multi_page_contract.pdf", pages)


def generate_quarterly_report() -> None:
    """Generate a 2-page quarterly sales report PDF."""
    pages = [
        [
            "Q4 2024 SALES REPORT",
            "Report ID: QR-2024-Q4",
            "Prepared by: Analytics Department",
            "Date: January 5, 2025",
            "",
            "EXECUTIVE SUMMARY",
            "Total Revenue: $2,450,000",
            "Units Sold: 12,500",
            "Growth Rate: 15% year-over-year",
        ],
        [
            "REGIONAL BREAKDOWN",
            "Top Performing Region: West Coast",
            "West Coast Revenue: $890,000 (36%)",
            "East Coast Revenue: $720,000 (29%)",
            "Midwest Revenue: $480,000 (20%)",
            "South Revenue: $360,000 (15%)",
            "",
            "KEY INSIGHTS",
            "The West Coast region exceeded targets by 22%, driven by strong "
            "enterprise sales in the technology sector.",
        ],
    ]
    create_pdf("quarterly_report.pdf", pages)


def generate_employee_record() -> None:
    """Generate a 5-page employee record with info distributed across pages."""
    pages = [
        [
            "EMPLOYEE RECORD",
            "Employee ID: EMP-78432",
            "Full Name: Alexandra Marie Johnson",
            "Date of Birth: June 15, 1988",
            "Department: Engineering",
            "Position: Senior Software Engineer",
            "Hire Date: September 1, 2019",
        ],
        [
            "CONTACT INFORMATION",
            "Email: alexandra.johnson@company.com",
            "Phone: (555) 123-4567",
            "Address: 742 Maple Avenue, Seattle, WA 98101",
            "Emergency Contact: Michael Johnson (Spouse)",
            "Emergency Phone: (555) 987-6543",
        ],
        [
            "COMPENSATION",
            "Annual Salary: $145,000",
            "Bonus Target: 15%",
            "Stock Options: 5,000 shares vested",
            "Last Review Date: December 2023",
            "Performance Rating: Exceeds Expectations",
        ],
        [
            "EDUCATION AND CERTIFICATIONS",
            "Degree: Master of Science, Computer Science",
            "University: Stanford University",
            "Graduation Year: 2012",
            "Certifications: AWS Solutions Architect, Kubernetes Administrator",
        ],
        [
            "EMPLOYMENT HISTORY",
            "Previous Position: Software Engineer (2019-2022)",
            "Current Position: Senior Software Engineer (2022-Present)",
            "Total Years at Company: 5 years",
            "Skills: Python, Go, Kubernetes, AWS, System Design",
        ],
    ]
    create_pdf("employee_record.pdf", pages)


if __name__ == "__main__":
    print("Generating test PDF samples...")
    generate_single_page_invoice()
    generate_multi_page_contract()
    generate_quarterly_report()
    generate_employee_record()
    print("Done!")
