import requests
import tempfile
import os

API_URL = "http://54.225.33.50:5000/api/resume/upload"

def generate_resume(resume_file):
    try:
        # Prepare the file for upload
        files = {'resume': ('resume.pdf', resume_file, 'application/pdf')}

        # Make the API request
        response = requests.post(API_URL, files=files)

        # Check if the request was successful
        if response.status_code == 200:
            # Save the improved resume
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(response.content)
                return temp_file.name
        else:
            return f"API request failed (status {response.status_code}): {response.text[:1000]}"

    except requests.RequestException as e:
        return f"API request error: {str(e)[:1000]}"

    except Exception as e:
        return f"Resume generation error: {str(e)[:1000]}"