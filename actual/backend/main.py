import base64
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import List
import uvicorn

# Import your custom modules
from yolo_detector import SkinDetector
from severity_score import SeverityAnalyzer
from rag_engine import SkinRAG

app = FastAPI(title="Skin AI Diagnosis & RAG API")

# Ensure these paths point to the specific  model 
detector = SkinDetector(model_path="F:/Desktop/dsml_ainn/actual/models/skin_trained.pt")

# Pointing to the specific pkl 
analyzer = SeverityAnalyzer(model_path="F:/Desktop/dsml_ainn/actual/models/severity_model_v1.pkl")

rag_system = SkinRAG(persist_dir="chroma_db", pdf_dir="skin_docs")



@app.get("/")
async def root():
    return {"status": "Skin AI API is running"}

@app.post("/analyze")
async def analyze_skin(
    file: UploadFile = File(...),
    user_query: str = Form("How can I treat this skin condition?")
):
    try:
        # Read uploaded image bytes
        image_bytes = await file.read()

        # YOLO Detection 
        # This should return a dict containing {"raw_result": result_object, "annotated_image_bytes": bytes}
        detection_data = detector.predict(image_bytes)
        
        # Severity Analysis 
        analysis = analyzer.calculate_score(detection_data["raw_result"])
        
        #  RAG Recommendation
        recommendation = rag_system.get_response(
            question=user_query, 
            conditions=analysis["conditions"], 
            severity=analysis["score"]
        )

        #  Prepare Image for Frontend (Base64)
        img_base64 = base64.b64encode(detection_data["annotated_image_bytes"]).decode('utf-8')

        return {
            "status": "success",
            "detected_conditions": analysis["conditions"],
            "severity_score": analysis["score"], 
            "recommendation": recommendation,
            "annotated_image": img_base64
        }

    except Exception as e:
        import logging
        logging.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error during Skin Analysis")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)