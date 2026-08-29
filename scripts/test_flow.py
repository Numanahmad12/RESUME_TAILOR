import urllib.request
import json
import fitz

# Create a sample PDF resume
doc = fitz.open()
page = doc.new_page(width=612, height=792)
text = """John Doe
john.doe@example.com | (555) 123-4567 | linkedin.com/in/johndoe

SUMMARY
Experienced Senior Software Engineer with 6+ years in Python, FastAPI, React, and AWS cloud infrastructure.

SKILLS
Python, JavaScript, TypeScript, React, Next.js, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Redis, CI/CD

EXPERIENCE
Acme Corporation — Senior Backend Engineer
Jan 2021 – Present
• Architected scalable microservices using FastAPI and AWS ECS handling 10M requests daily.
• Optimized PostgreSQL databases and implemented Redis caching, reducing query latency by 45%.
• Mentored engineers and spearheaded containerization using Docker and Kubernetes.

Beta Innovations — Software Developer
Jun 2018 – Dec 2020
• Developed REST APIs with Python and Flask.
• Implemented continuous integration and deployment with GitHub Actions.

EDUCATION
State University — Bachelor of Science in Computer Science (2018)
"""
page.insert_text((50, 60), text, fontsize=11)
pdf_bytes = doc.tobytes()

boundary = "WebKitFormBoundaryTest123"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="john_doe_resume.pdf"\r\n'
    f"Content-Type: application/pdf\r\n\r\n"
).encode("utf-8") + pdf_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

print("--- 1. Testing Resume Upload ---")
req = urllib.request.Request(
    "http://localhost:3000/api/upload/resume",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
with urllib.request.urlopen(req) as res:
    resume_resp = json.loads(res.read().decode())
    print("Resume Upload Response:", resume_resp.get("resume_id"))
    resume_id = resume_resp["resume_id"]

print("\n--- 2. Testing JD Upload ---")
jd_text = """Job Title: Senior Backend Engineer (Python & AWS)
We are seeking a Senior Backend Engineer with 5+ years experience.

Responsibilities:
• Design and build distributed microservices in Python.
• Work with AWS infrastructure, Docker, Kubernetes, and PostgreSQL.
• Implement scalable APIs with FastAPI.

Required Skills:
Python, FastAPI, AWS, Docker, Kubernetes, PostgreSQL
"""
body_jd = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="text"\r\n\r\n'
    f"{jd_text}\r\n"
    f"--{boundary}--\r\n"
).encode("utf-8")

req_jd = urllib.request.Request(
    "http://localhost:3000/api/upload/jd",
    data=body_jd,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
with urllib.request.urlopen(req_jd) as res:
    jd_resp = json.loads(res.read().decode())
    print("JD Upload Response:", jd_resp.get("jd_id"))
    jd_id = jd_resp["jd_id"]

print("\n--- 3. Testing Analyze ---")
req_an = urllib.request.Request(
    "http://localhost:3000/api/analyze",
    data=json.dumps({"resume_id": resume_id, "jd_id": jd_id}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req_an) as res:
    an_resp = json.loads(res.read().decode())
    print("Analyze Score:", an_resp["match"]["overall_score"])
    match_report = an_resp["match"]

print("\n--- 4. Testing Generate Patches ---")
req_gen = urllib.request.Request(
    "http://localhost:3000/api/generate",
    data=json.dumps({"resume_id": resume_id, "jd_id": jd_id, "match_report": match_report}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req_gen) as res:
    gen_resp = json.loads(res.read().decode())
    print("Generated Patches Count:", len(gen_resp["patches"]))
    generation_id = gen_resp["generation_id"]

print("\n--- 5. Testing Apply Patches ---")
req_app = urllib.request.Request(
    "http://localhost:3000/api/apply",
    data=json.dumps({"resume_id": resume_id, "generation_id": generation_id}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req_app) as res:
    app_resp = json.loads(res.read().decode())
    print("Final ID:", app_resp.get("final_id"))
    final_id = app_resp["final_id"]

print("\n--- 6. Testing Render PDF ---")
body_ren = f"final_id={final_id}".encode("utf-8")
req_ren = urllib.request.Request(
    "http://localhost:3000/api/render/pdf",
    data=body_ren,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
with urllib.request.urlopen(req_ren) as res:
    pdf_out = res.read()
    print("Render PDF length:", len(pdf_out), "Content-Type:", res.headers.get("content-type"))
    print("First 20 bytes:", pdf_out[:20])

print("\nALL API PIPELINE ENDPOINTS TESTED SUCCESSFULLY!")
