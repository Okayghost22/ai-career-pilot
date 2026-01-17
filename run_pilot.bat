@echo off
echo 🚀 Activating AI Pilot Environment...
:: This line connects to your specific project libraries
call venv\Scripts\activate

echo 📂 Analyzing Resume and Job Description...
python process_job.py

echo 🎙️ Transcribing and Grading Interview...
python process_interview.py

echo ✅ SUCCESS: All data pushed to Supabase!
echo Open Power BI and click 'Refresh' to see your new scores.
pause