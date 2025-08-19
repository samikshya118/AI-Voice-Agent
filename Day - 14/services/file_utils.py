import os
import shutil

def save_uploaded_file(file, session_id: str) -> str:
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{session_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path
