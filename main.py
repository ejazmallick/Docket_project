from pathlib import Path
from datetime import datetime
import logging
from io import BytesIO
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


from openpyxl import Workbook

from utils import (
    STAMPS_DIR,
    OUTPUT_DIR,
    REPORTS_DIR,
    ensure_directories,
    setup_logging,
    validate_stamp,
    validate_pdf,
    get_input_pdfs,
)

STAMP_FILE = STAMPS_DIR / "StampTNH.png"


REPORT_FILE = REPORTS_DIR / "stamping_report.xlsx"


def process_pdf(pdf_path: Path):
    """
    Validate the PDF and apply the stamp image to the last page.

    The stamp is placed at the bottom-right corner of the last page.

    Returns:
        (True, "Success") on success
        (False, "Reason") on failure
    """
  
    is_valid, message = validate_pdf(pdf_path)
    if not is_valid:
        return False, message

    try:
  
        reader = PdfReader(str(pdf_path))
        writer = PdfWriter()

   
        for page in reader.pages:
            writer.add_page(page)

        last_page = writer.pages[-1]

   
        page_width = float(last_page.mediabox.width)
        page_height = float(last_page.mediabox.height)

     
        stamp_width = 120
        stamp_height = 60

       
        margin_x = 20
        margin_y = 20

        x = page_width - stamp_width - margin_x
        y = margin_y

    
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(page_width, page_height))

        c.drawImage(
            ImageReader(str(STAMP_FILE)),
            x,
            y,
            width=stamp_width,
            height=stamp_height,
            preserveAspectRatio=True,
            mask="auto"
        )

        c.save()
        packet.seek(0)

      
        overlay_reader = PdfReader(packet)
        overlay_page = overlay_reader.pages[0]


        last_page.merge_page(overlay_page)

 
        output_file = OUTPUT_DIR / f"{pdf_path.stem}_stamped.pdf"

        with open(output_file, "wb") as output_stream:
            writer.write(output_stream)

        logging.info(f"Stamped successfully: {output_file}")

        return True, "Success"

    except PermissionError:
        return False, "Permission denied"
    except Exception as exc:
        logging.exception(f"Unexpected error while processing {pdf_path.name}")
        return False, f"Unexpected runtime error: {exc}"



def generate_excel_report(records):
    """
    Create stamping_report.xlsx with columns:
    File Name | Stamped | Timestamp | Remarks
    """
    try:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Stamping Report"

        # Header row
        sheet.append(["File Name", "Stamped", "Timestamp", "Remarks"])

        # Data rows
        for record in records:
            sheet.append([
                record["File Name"],
                record["Stamped"],
                record["Timestamp"],
                record["Remarks"],
            ])

        workbook.save(REPORT_FILE)
        logging.info(f"Excel report generated: {REPORT_FILE}")

    except Exception:
        logging.exception("Failed to generate Excel report")




def main():

    ensure_directories()


    setup_logging()

    logging.info("=" * 60)
    logging.info("Starting Docket PDF Stamping Utility")
    logging.info("=" * 60)

    is_valid_stamp, stamp_message = validate_stamp(STAMP_FILE)
    if not is_valid_stamp:
        logging.error(f"Stamp validation failed: {stamp_message}")
        logging.info("Execution terminated.")
        return

    logging.info(f"Stamp validated successfully: {STAMP_FILE.name}")

 
    pdf_files = get_input_pdfs()
    total_files = len(pdf_files)

    if total_files == 0:
        logging.warning("No PDF files found in input_pdfs folder.")
        logging.info("Execution completed.")
        return

    logging.info(f"Total PDF files found: {total_files}")

    records = []
    success_count = 0
    failure_count = 0

    for pdf_file in pdf_files:
        logging.info(f"Processing: {pdf_file.name}")

        stamped, remarks = process_pdf(pdf_file)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        records.append({
            "File Name": pdf_file.name,
            "Stamped": stamped,
            "Timestamp": timestamp,
            "Remarks": remarks,
        })

        if stamped:
            success_count += 1
            logging.info(f"SUCCESS: {pdf_file.name}")
        else:
            failure_count += 1
            logging.error(f"FAILED: {pdf_file.name} | Reason: {remarks}")

  
    generate_excel_report(records)


    logging.info("=" * 60)
    logging.info("Execution Summary")
    logging.info("=" * 60)
    logging.info(f"Total files found        : {total_files}")
    logging.info(f"Successfully stamped     : {success_count}")
    logging.info(f"Failed files             : {failure_count}")
    logging.info(f"Output folder            : {OUTPUT_DIR}")
    logging.info(f"Excel report             : {REPORT_FILE}")
    logging.info("Processing completed successfully.")
    logging.info("=" * 60)
    
if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")