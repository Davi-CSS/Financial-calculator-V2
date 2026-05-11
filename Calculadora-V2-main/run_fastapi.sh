bash
#!/usr/bin/env bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.fastapi_app:app --reload --port 8000