import requests
import logging
import json

logger = logging.getLogger(__name__)

API_URL = "http://54.163.59.72:5000/api/profile/update-profile"

def improve_linkedin_profile(profile_url: str, li_at: str) -> dict:
    """
    Send LinkedIn Profile URL and li_at cookie to improvement API
    Returns dict with success/error status and message
    """
    try:
        # Validate li_at cookie format
        if not li_at or len(li_at) < 50:
            return {
                "success": False,
                "message": "Invalid LinkedIn cookie. Please make sure you copied the entire 'li_at' cookie value."
            }
        
        payload = {
            "authCookie": li_at,
            "profileUrl": profile_url
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        
        logger.info(f"Sending request to {API_URL}")
        logger.info(f"Payload: {json.dumps(payload)}")
        
        response = requests.post(
            API_URL, 
            json=payload, 
            headers=headers, 
            timeout=300,
            verify=False  # Added to handle any SSL issues
        )
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON response")
            return {
                "success": False,
                "message": "Invalid response from server. Please try again."
            }
            
        if response.status_code in [200, 201]:
            return {
                "success": True,
                "message": response_data.get("message", "Profile improvement suggestions generated successfully!")
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "message": "Failed to access LinkedIn profile. Please verify your cookie is valid and try again."
            }
        elif response.status_code == 400:
            error_msg = response_data.get("message", "Unknown error occurred")
            return {
                "success": False,
                "message": f"API Error: {error_msg}\nPlease verify your LinkedIn cookie and profile URL are correct."
            }
        else:
            error_msg = response_data.get("message", "Unknown error occurred")
            return {
                "success": False,
                "message": f"Server error: {error_msg}. Please try again later."
            }
    
    except requests.Timeout:
        logger.error("Request timed out after 5 minutes")
        return {
            "success": False,
            "message": "The request is taking longer than expected. Please try again later."
        }
    except requests.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {
            "success": False,
            "message": "Connection error. Please check your internet connection and try again."
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "success": False,
            "message": "An unexpected error occurred. Please try again later."
        }