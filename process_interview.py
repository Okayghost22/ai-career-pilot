import os
import json
from groq import Groq
from supabase import create_client
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 2. Initialize Clients
client = Groq(api_key=GROQ_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def transcribe_and_grade(audio_path):
    # --- STEP A: Transcribe ---
    print(f"Opening {audio_path}...")
    with open(audio_path, "rb") as file:
        transcript = client.audio.transcriptions.create(
            file=(audio_path, file.read()),
            model="whisper-large-v3",
            response_format="text",
        )
    print(f"\nTranscript generated successfully.")

    # --- STEP B: Grade ---
    print("AI is grading your performance...")
    prompt = f"""
    Analyze this interview answer. 
    Score it 0-10 on 'tech_score' and 'clarity_score'.
    Provide 2 sentences of 'feedback'.
    Return ONLY a JSON object.
    
    Answer: {transcript}
    """
    
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    analysis = json.loads(completion.choices[0].message.content)

    # --- STEP C: Push to Supabase ---
    print("Linking scores to your latest job application...")
    
    # Get the ID of the most recent application row
    latest_job = supabase.table("applications").select("id").order("created_at", desc=True).limit(1).execute()

    if latest_job.data:
        row_id = latest_job.data[0]['id']
        
        # Update that row with the new interview data
        supabase.table("applications").update({
            "tech_score": analysis.get('tech_score'),
            "clarity_score": analysis.get('clarity_score'),
            "ai_feedback": f"MATCH FEEDBACK: {analysis.get('feedback')}", # Keeping match feedback
            "interview_transcript": transcript
        }).eq("id", row_id).execute()
        
        print(f"✅ SUCCESS: Row ID {row_id} updated with Interview Scores!")
    else:
        print("❌ Error: No job application found in database to update.")

    return analysis

if __name__ == "__main__":
    # Ensure this filename matches your recording exactly!
    # If it is an MP4, keep it "interview.mp4"
    result = transcribe_and_grade("interview.mp4")
    print("\n--- Final Results ---")
    print(json.dumps(result, indent=2))