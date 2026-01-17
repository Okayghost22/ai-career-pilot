import os
import requests
from pypdf import PdfReader
from groq import Groq
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# Initialize Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# STEP 4: Resume Text Extraction
def get_resume_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

# STEP 5: AI Analysis (Using Groq)
def get_ai_analysis(resume_text, job_description):
    prompt = f"""
    You are an expert ATS (Applicant Tracking System). Analyze the Resume against the JD.
    Return a JSON object with:
    1. "match_score": (0-100)
    2. "missing_keywords": (List of top 5 technical skills/tools in the JD but NOT in the Resume)
    3. "feedback": (2 sentences on how to improve the match)
    
    Resume: {resume_text}
    JD: {job_description}
    """
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"} # Ensures we get clean JSON back
    )
    return completion.choices[0].message.content

# STEP 6: Save to Supabase
def push_to_supabase(company, role, ai_result_json):
    import json
    res = json.loads(ai_result_json)
    
    url = f"{os.getenv('SUPABASE_URL')}/rest/v1/applications"
    headers = {
        "apikey": os.getenv("SUPABASE_KEY"),
        "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    data = {
        "company_name": company,
        "job_role": role,
        "match_score": res["match_score"],
        "ai_feedback": res["feedback"]
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        print(f"✅ Success! Data for {company} saved to Supabase.")
    else:
        print(f"❌ Error saving to Supabase: {response.text}")

# --- EXECUTION ---
if __name__ == "__main__":
    # Change these to your actual file and job details
    RESUME_FILE = "my_resume.pdf" 
    COMPANY = "Tech Corp"
    ROLE = "Software Engineer"
    JOB_DESC = "Looking for a developer skilled in Python, SQL, and Power BI."

    print("Reading Resume...")
    resume_content = get_resume_text(RESUME_FILE)

    if resume_content:
        print("Analyzing with Groq AI...")
        analysis = get_ai_analysis(resume_content, JOB_DESC)
        
        print("Pushing to Cloud...")
        push_to_supabase(COMPANY, ROLE, analysis)