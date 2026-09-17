import sys
sys.path.insert(0, r'C:\Users\numan\Desktop\RESUME_BUILDER')

import uvicorn
uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, log_level="info")