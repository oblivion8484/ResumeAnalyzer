import os
import fitz
import json
import time
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, File, HTTPException

API_KEY = "AIzaSyDgrWPvAAf7wXxPpKRzCtiW_h0J5DX8ce0"
genai.configure(api_key=API_KEY)

app = FastAPI()

class ResumeAnalyzer:
    def __init__(self):
        self.max_tokens = 512
        self.system_prompt = (
            "(NEVER PRINT THE RESUME TEXT IN ANY WAY AND ALWAYS SCORE THE RESUME FROM 100.) "
            "You are an expert resume analyzer. Based on the resume text, provide:\n"
            "1) A score from 0 to 100 evaluating the resume quality on content relevance with respect to job, clarity, formatting, grammar, and impact.\n"
            "2) A list of 3-5 suggestions to improve the resume.\n\n"
            "{\n  \"score\": number,\n  \"suggestions\": [\"string\", \"string\", \"...\"]\n}"
        )
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        with fitz.open(pdf_path) as doc:
            text = "\n".join(page.get_text() for page in doc).strip()
        if not text:
            raise RuntimeError("No text could be extracted.")
        return text

    def chunk_text(self, text: str) -> list[str]:
        chunk_size = 1000
        words = text.split()
        chunks, current_chunk = [], []

        for word in words:
            current_chunk.append(word)
            if len(" ".join(current_chunk)) > chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def analyze_resume_text_chunk(self, resume_text_chunk: str) -> dict:
        full_prompt = f"{self.system_prompt}\n\nResume Text:\n{resume_text_chunk}"

        start = time.time()
        response = genai.generate_text(
            model="models/chat-bison-001",
            prompt=full_prompt,
            max_output_tokens=self.max_tokens,
            temperature=0.7,
        )
        end = time.time()
        print(f"🕒 Inference time: {round(end - start, 2)} seconds")

        text_response = response.text

        json_start = text_response.find('{')
        json_data = text_response[json_start:].strip()

        try:
            result = json.loads(json_data)
            if "score" not in result or "suggestions" not in result:
                raise ValueError("Response JSON missing keys.")
            return result
        except json.JSONDecodeError:
            raise RuntimeError(f"JSON decoding failed:\n{json_data}")

    def analyze_resume_text(self, resume_text: str) -> dict:
        chunks = self.chunk_text(resume_text)
        all_scores = []
        all_suggestions = []

        for idx, chunk in enumerate(chunks, 1):
            print(f"🔍 Analyzing chunk {idx}/{len(chunks)}...")
            result = self.analyze_resume_text_chunk(chunk)
            all_scores.append(result["score"])
            all_suggestions.extend(result["suggestions"])

        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        unique_suggestions = list(dict.fromkeys(all_suggestions))[:5]
        return {"score": round(avg_score, 2), "suggestions": unique_suggestions}

    def analyze_pdf_resume(self, pdf_path: str) -> dict:
        text = self.extract_text_from_pdf(pdf_path)
        return self.analyze_resume_text(text)

@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    contents = await file.read()
    with open("temp_resume.pdf", "wb") as f:
        f.write(contents)

    analyzer = ResumeAnalyzer()
    try:
        result = analyzer.analyze_pdf_resume("temp_resume.pdf")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
