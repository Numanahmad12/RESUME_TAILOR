@echo off
set PYTHONPATH=C:\Users\numan\Desktop\RESUME_BUILDER\common
cd C:\Users\numan\Desktop\RESUME_BUILDER\backend
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000