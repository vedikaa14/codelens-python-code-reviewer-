from google import genai
from dotenv import load_dotenv
import os
import re
import time
import traceback
# -----------------------------------
# Load Environment Variables
# -----------------------------------
load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# -----------------------------------
# Extract Section Between Headings
# -----------------------------------
def get_section(text, start, end=None):

    if end:
        pattern = rf"{re.escape(start)}(.*?){re.escape(end)}"
    else:
        pattern = rf"{re.escape(start)}(.*)"

    match = re.search(
        pattern,
        text,
        re.DOTALL | re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return ""


# -----------------------------------
# Convert Bullet Points into List
# -----------------------------------
def get_list(section):

    items = []

    for line in section.splitlines():

        line = line.strip()

        if line.startswith("-"):
            items.append(line[1:].strip())

        elif line.startswith("*"):
            items.append(line[1:].strip())

    return items


# -----------------------------------
# Main AI Review Function
# -----------------------------------
def review_python_code(code):

    MAX_LINES = 300

    lines = code.splitlines()
    truncated = False

    if len(lines) > MAX_LINES:
        code = "\n".join(lines[:MAX_LINES])
        truncated = True

    prompt = f"""
You are an Expert Python Senior Software Engineer.

Analyze the following Python code carefully.

Return your answer EXACTLY in this format.

# Overall Rating
Give ONLY the rating out of 10.

# Summary
Write 4-5 concise lines summarizing the code.

# Bugs Found
Use bullet points beginning with "-".

# Code Quality
Use bullet points beginning with "-".

# Performance Improvements
Use bullet points beginning with "-".

# Security Issues
Use bullet points beginning with "-".

# Best Practices
Use bullet points beginning with "-".

# Readability
Use bullet points beginning with "-".

# Optimized Code
Return ONLY the improved Python code.

Do NOT use Markdown.
Do NOT use triple backticks.
Do NOT return JSON.
"""

    if truncated:
        prompt += """

NOTE:
The uploaded file exceeded 300 lines.
Review ONLY the visible portion.
Mention this limitation in the summary.

"""

    prompt += f"""

Python Code:

{code}
"""

    MAX_RETRIES = 3

    try:

        for attempt in range(MAX_RETRIES):

            try:

                print(f"\n========== GEMINI REQUEST ({attempt+1}/{MAX_RETRIES}) ==========")

                start = time.time()

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )

                elapsed = time.time() - start

                print(f"✅ Gemini Response Time: {elapsed:.2f} seconds")

                if not response or not response.text:
                    raise Exception("Gemini returned an empty response.")

                text = response.text

                print("\n========== RAW GEMINI RESPONSE ==========\n")
                print(text)
                print("\n=========================================\n")

                break

            except Exception as e:

                error = str(e).lower()

                print(f"Gemini Error: {e}")

                if (
                    (
                        "503" in error
                        or "unavailable" in error
                        or "overloaded" in error
                        or "high demand" in error
                    )
                    and attempt < MAX_RETRIES - 1
                ):

                    print(f"⚠️ Gemini busy. Retrying ({attempt+1}/{MAX_RETRIES})...")

                    time.sleep(2)

                    continue

                raise

        review = {

            "overall_rating": get_section(
                text,
                "# Overall Rating",
                "# Summary"
            ),

            "summary": get_section(
                text,
                "# Summary",
                "# Bugs Found"
            ),

            "bugs": get_list(
                get_section(
                    text,
                    "# Bugs Found",
                    "# Code Quality"
                )
            ),

            "code_quality": get_list(
                get_section(
                    text,
                    "# Code Quality",
                    "# Performance Improvements"
                )
            ),

            "performance": get_list(
                get_section(
                    text,
                    "# Performance Improvements",
                    "# Security Issues"
                )
            ),

            "security": get_list(
                get_section(
                    text,
                    "# Security Issues",
                    "# Best Practices"
                )
            ),

            "best_practices": get_list(
                get_section(
                    text,
                    "# Best Practices",
                    "# Readability"
                )
            ),

            "readability": get_list(
                get_section(
                    text,
                    "# Readability",
                    "# Optimized Code"
                )
            ),

            "optimized_code": get_section(
                text,
                "# Optimized Code"
            )

        }

        review["overall_rating"] = review["overall_rating"] or "N/A"
        review["summary"] = review["summary"] or "No summary generated."
        review["bugs"] = review["bugs"] or []
        review["code_quality"] = review["code_quality"] or []
        review["performance"] = review["performance"] or []
        review["security"] = review["security"] or []
        review["best_practices"] = review["best_practices"] or []
        review["readability"] = review["readability"] or []
        review["optimized_code"] = (
            review["optimized_code"] or
            "No optimized code generated."
        )

        return review

    except Exception as e:

        print("\n========== GEMINI ERROR ==========")
        traceback.print_exc()
        print("==================================\n")

        return {
            "overall_rating": "Error",
            "summary": f"AI Review Failed: {e}",
            "bugs": [],
            "code_quality": [],
            "performance": [],
            "security": [],
            "best_practices": [],
            "readability": [],
            "optimized_code": ""
        }