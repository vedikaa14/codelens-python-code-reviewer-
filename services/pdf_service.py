from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os

REPORT_FOLDER = "reports"

os.makedirs(REPORT_FOLDER, exist_ok=True)

def generate_pdf(review, python_filename,user_id):

    # Remove .py extension
    name = os.path.splitext(python_filename)[0]

    # Unique timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # PDF filename
    filename = os.path.join(
    REPORT_FOLDER,
    f"{name}_review_{timestamp}.pdf"
)
    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    story = []

    # -------------------------
    # Title
    # -------------------------
    story.append(
        Paragraph(
            "<b>CodeLens AI - Code Review Report</b>",
            styles["Title"]
        )
    )

    story.append(Spacer(1, 20))

    # -------------------------
    # Overall Rating
    # -------------------------
    story.append(
        Paragraph(
            "<b>Overall Rating</b>",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            review.get("overall_rating", "N/A"),
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 12))

    # -------------------------
    # Summary
    # -------------------------
    story.append(
        Paragraph(
            "<b>Summary</b>",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            review.get("summary", "No summary available."),
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 12))

    # -------------------------
    # Helper Function
    # -------------------------
    def add_section(title, items):

        story.append(
            Paragraph(
                f"<b>{title}</b>",
                styles["Heading2"]
            )
        )

        if items:

            for item in items:

                story.append(
                    Paragraph(
                        f"• {item}",
                        styles["BodyText"]
                    )
                )

        else:

            story.append(
                Paragraph(
                    "No issues found.",
                    styles["BodyText"]
                )
            )

        story.append(Spacer(1, 12))

    # -------------------------
    # All Sections
    # -------------------------
    add_section("Bugs Found", review.get("bugs", []))

    add_section("Code Quality", review.get("code_quality", []))

    add_section("Performance", review.get("performance", []))

    add_section("Security", review.get("security", []))

    add_section("Best Practices", review.get("best_practices", []))

    add_section("Readability", review.get("readability", []))

    # -------------------------
    # Optimized Code
    # -------------------------
    story.append(
        Paragraph(
            "<b>Optimized Code</b>",
            styles["Heading2"]
        )
    )

    optimized = review.get("optimized_code", "")

    optimized = optimized.replace("\n", "<br/>")

    story.append(
        Paragraph(
            f"<font face='Courier'>{optimized}</font>",
            styles["Code"] if "Code" in styles else styles["BodyText"]
        )
    )

    doc.build(story)

    return filename