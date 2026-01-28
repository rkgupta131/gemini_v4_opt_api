#!/bin/bash
# Start the FastAPI server

# Activate virtual environment if it exists
if [ -d "gemini_v4_opt" ]; then
    source gemini_v4_opt/bin/activate
fi

# Start the API server
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

