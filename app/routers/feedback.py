from fastapi import APIRouter, UploadFile, HTTPException
from app.core.logger import get_logger
from app.utils.pdf_utils import extract_resume_text

logger = get_logger(__name__)
router = APIRouter()

MAX_FILE_SIZE_MB = 2
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024 

@router.post("/resume/extract")
async def extract_resume(resume: UploadFile):
    file_bytes = await resume.read()

    if not file_bytes:
        logger.warning("Uploaded file is empty")
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB."
        )

    extracted_text = extract_resume_text(file_bytes, resume.content_type, resume.filename)

    if not extracted_text:
        logger.error(f"Failed to extract text from: {resume.filename}")
        raise HTTPException(status_code=422, detail="Could not extract text from file.")

    logger.info(f"Successfully extracted resume: {resume.filename}")

    return {
        "success": True,
        "filename": resume.filename,
        "word_count": len(extracted_text.split()),
        "extracted_text_preview": extracted_text[:500]
    }
