import requests
import os
from django.shortcuts import render

# Read the API URL from the environment variable
HELIX_API_URL = os.getenv("HELIX_API_URL", "https://helix.local") 

def test_fastapi_connection(request):
    """
    Attempts to ping a FastAPI endpoint to verify cross-container communication.
    We assume the FastAPI app has a simple health check or root endpoint ('/').
    """
    api_endpoint = f"{HELIX_API_URL}/"
    context = {}
    
    try:
        # We use a short timeout since it's an internal network call
        response = requests.get(api_endpoint, timeout=3)
        
        # Check for successful response status codes (2xx)
        if response.ok:
            # Try to get data if the FastAPI endpoint returns JSON
            try:
                data = response.json()
                status = "SUCCESS: Received JSON response from FastAPI."
                detail = f"Status Code: {response.status_code}. Data: {data}"
            except requests.exceptions.JSONDecodeError:
                # If it's not JSON (e.g., just a simple "Hello World" text response)
                status = "SUCCESS: Received valid non-JSON response from FastAPI."
                detail = f"Status Code: {response.status_code}. Text Content: {response.text[:100]}..."

        else:
            status = f"FAILURE: FastAPI returned a non-200 status code."
            detail = f"Status Code: {response.status_code}. Response: {response.text[:100]}"
            
    except requests.exceptions.ConnectionError:
        status = "CRITICAL FAILURE: Django cannot connect to FastAPI."
        detail = f"Could not connect to {api_endpoint}. Check Docker network and the HELIX_API_URL setting."
    except requests.exceptions.RequestException as e:
        status = "FAILURE: An unknown request error occurred."
        detail = f"Error: {e}"

    context['api_url'] = HELIX_API_URL
    context['status'] = status
    context['detail'] = detail

    return render(request, 'connection_test.html', context)
