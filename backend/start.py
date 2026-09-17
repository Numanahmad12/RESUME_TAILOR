import sys
import os

# Add common module to path
sys.path.insert(0, r'C:\Users\numan\Desktop\RESUME_BUILDER\common')

# Now run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000)