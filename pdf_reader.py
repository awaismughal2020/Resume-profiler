import PyPDF2
import pdfplumber
from pathlib import Path
import sys


def read_pdf_with_pypdf2(pdf_path):
    """
    Read PDF using PyPDF2 - basic text extraction
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = ""

            print(f"Total pages: {len(pdf_reader.pages)}")

            for page_num, page in enumerate(pdf_reader.pages, 1):
                print(f"\n--- Page {page_num} ---")
                page_text = page.extract_text()
                text_content += f"\n--- Page {page_num} ---\n{page_text}\n"
                print(page_text)

        return text_content

    except Exception as e:
        print(f"Error reading PDF with PyPDF2: {e}")
        return None


def read_pdf_with_pdfplumber(pdf_path):
    """
    Read PDF using pdfplumber - better formatting and table extraction
    """
    try:
        text_content = ""

        with pdfplumber.open(pdf_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}")

            for page_num, page in enumerate(pdf.pages, 1):
                print(f"\n--- Page {page_num} ---")

                # Extract text
                page_text = page.extract_text()
                if page_text:
                    text_content += f"\n--- Page {page_num} ---\n{page_text}\n"
                    print(page_text)

                # Extract tables if any
                tables = page.extract_tables()
                if tables:
                    print(f"\nTables found on page {page_num}:")
                    for i, table in enumerate(tables, 1):
                        print(f"\nTable {i}:")
                        for row in table:
                            print("\t".join(str(cell) if cell else "" for cell in row))
                        text_content += f"\nTable {i} from page {page_num}:\n"
                        for row in table:
                            text_content += "\t".join(str(cell) if cell else "" for cell in row) + "\n"

        return text_content

    except Exception as e:
        print(f"Error reading PDF with pdfplumber: {e}")
        return None


def clean_and_format_text(text):
    """
    Clean and format the extracted text
    """
    if not text:
        return ""

    # Remove extra whitespace and normalize line breaks
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # Strip whitespace and skip empty lines
        cleaned_line = line.strip()
        if cleaned_line:
            cleaned_lines.append(cleaned_line)

    return '\n'.join(cleaned_lines)


def save_text_to_file(text, output_path):
    """
    Save extracted text to a file
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(text)
        print(f"\nText saved to: {output_path}")
    except Exception as e:
        print(f"Error saving text to file: {e}")


def main():
    # Set default PDF file path
    pdf_path = "resume/cv1.pdf"

    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"Error: File '{pdf_path}' not found!")
        print("Please make sure the file exists in the 'resume' folder.")
        return

    print(f"Reading PDF: {pdf_path}")
    print("=" * 50)

    # Method 1: Try pdfplumber first (better formatting)
    print("Using pdfplumber (recommended):")
    text_content = read_pdf_with_pdfplumber(pdf_path)

    if not text_content:
        print("\nFalling back to PyPDF2:")
        text_content = read_pdf_with_pypdf2(pdf_path)

    if text_content:
        # Clean and format the text
        cleaned_text = clean_and_format_text(text_content)

        # Save to file
        output_path = "resume/" + Path(pdf_path).stem + "_extracted.txt"
        save_text_to_file(cleaned_text, output_path)

        print(f"\n{'=' * 50}")
        print("EXTRACTION COMPLETE")
        print(f"{'=' * 50}")
        print(f"Characters extracted: {len(cleaned_text)}")
        lines_count = len(cleaned_text.split('\n'))
        print(f"Lines extracted: {lines_count}")

    else:
        print("Failed to extract text from PDF!")


if __name__ == "__main__":
    main()
