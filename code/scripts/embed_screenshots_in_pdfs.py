#!/usr/bin/env python3
"""embed_screenshots_in_pdfs.py - Natively replaces placeholder screenshot boxes in A1 & A2 PDFs."""

import fitz
import shutil
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_A1 = os.path.join(ROOT_DIR, 'report', 'final_reports', 'STTAI_reports', 'report', 'report_A1.pdf')
BASE_A2 = os.path.join(ROOT_DIR, 'report', 'final_reports', 'STTAI_reports', 'report', 'report_A2.pdf')

def patch_a1():
    doc = fitz.open(BASE_A1)
    page = doc[5] # Page 6 (0-indexed 5)
    
    # 3 screenshot boxes in Column 2 (x: 317 to 559, width 242)
    boxes = [
        (fitz.Rect(317, 455, 559, 518), os.path.join(ROOT_DIR, 'report', 'shots', 'labelstudio_task.png')),
        (fitz.Rect(317, 528, 559, 591), os.path.join(ROOT_DIR, 'report', 'shots', 'dvc_status.png')),
        (fitz.Rect(317, 601, 559, 664), os.path.join(ROOT_DIR, 'report', 'shots', 'validation_run.png')),
    ]
    
    for rect, _ in boxes:
        page.add_redact_annot(rect, fill=(1, 1, 1))
    page.apply_redactions()
    
    for rect, img_path in boxes:
        page.insert_image(rect, filename=img_path, keep_proportion=False)
        
    out_a1 = os.path.join(ROOT_DIR, 'report', 'report_A1.pdf')
    doc.save(out_a1)
    shutil.copy2(out_a1, os.path.join(ROOT_DIR, 'report', 'report.pdf'))
    shutil.copy2(out_a1, BASE_A1)
    print("report_A1.pdf successfully updated with native embedded screenshots!")

def patch_a2():
    doc = fitz.open(BASE_A2)
    page = doc[7] # Page 8 (0-indexed 7)
    
    # 4 screenshot boxes in Column 1 (x: 53.5 to 295.5, width 242)
    boxes = [
        (fitz.Rect(53.5, 80.5, 295.5, 143.0), os.path.join(ROOT_DIR, 'report', 'shots', 'ui_prediction.png')),
        (fitz.Rect(53.5, 153.5, 295.5, 216.0), os.path.join(ROOT_DIR, 'report', 'shots', 'mlflow_runs.png')),
        (fitz.Rect(53.5, 227.0, 295.5, 289.5), os.path.join(ROOT_DIR, 'report', 'shots', 'docker_validate.png')),
        (fitz.Rect(53.5, 299.5, 295.5, 362.0), os.path.join(ROOT_DIR, 'report', 'shots', 'ci_green.png')),
    ]
    
    for rect, _ in boxes:
        page.add_redact_annot(rect, fill=(1, 1, 1))
    page.apply_redactions()
    
    for rect, img_path in boxes:
        page.insert_image(rect, filename=img_path, keep_proportion=False)
        
    out_a2 = os.path.join(ROOT_DIR, 'report', 'report_A2.pdf')
    doc.save(out_a2)
    shutil.copy2(out_a2, os.path.join(ROOT_DIR, 'report', 'report2.pdf'))
    shutil.copy2(out_a2, BASE_A2)
    print("report_A2.pdf successfully updated with native embedded screenshots!")

if __name__ == '__main__':
    patch_a1()
    patch_a2()

