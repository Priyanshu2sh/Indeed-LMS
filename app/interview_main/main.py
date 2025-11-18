from pdf_utils import extract_text_from_pdf
from interview import run_interview

resume_path = "C:\\Users\\Chaitanya\\Desktop\\Resume\\Chaitanya_Thakre.pdf"  # change if docx
job_desc_path ="C:\\Users\\Chaitanya\\Desktop\\full_stack_developer_job_description.txt"

resume_text = extract_text_from_pdf(resume_path)
job_desc_text = extract_text_from_pdf(job_desc_path)

level = input("Select interview difficulty (easy/moderate/experienced): ").lower()
type= input ("Select Type of interview (HR/Technical): ").lower()

if input("Start the interview? (y/n): ").lower() == "y" or "yes" or "ye":
    results = run_interview(level, type,job_desc_text, resume_text)
    
else:
    print("Interview canceled.")
