import os
import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

# ─── Upload folder setup ───────────────────────────────────────────────────────
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "document": [".pdf", ".txt", ".csv", ".docx"],
    "data": [".csv", ".json", ".xlsx"],
}
ALL_ALLOWED = [ext for exts in ALLOWED_EXTENSIONS.values() for ext in exts]

MAX_FILE_SIZE_MB = 10  # 10 MB limit


class FileUploadService:
    """
    File upload, delete, aur list karne ka service.
    Files /uploads/ folder mein save hoti hain.
    """

    def save_file(self, file: UploadFile) -> dict:
        """
        File ko disk pe save karo.
        Unique filename generate karta hai — naam clash nahi hoga.
        """
        # Extension check
        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALL_ALLOWED:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{suffix}' allowed nahi hai. Allowed: {ALL_ALLOWED}"
            )

        # File size check (read into memory temporarily)
        contents = file.file.read()
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File bahut badi hai ({size_mb:.1f} MB). Max {MAX_FILE_SIZE_MB} MB allowed hai."
            )

        # Unique filename banao
        unique_name = f"{uuid.uuid4().hex}{suffix}"
        save_path = UPLOAD_DIR / unique_name

        # Save to disk
        with open(save_path, "wb") as f:
            f.write(contents)

        return {
            "original_name": file.filename,
            "saved_as": unique_name,
            "file_path": str(save_path),
            "size_mb": round(size_mb, 3),
            "file_type": suffix,
            "url": f"/files/{unique_name}"
        }

    def list_files(self) -> list:
        """Saari uploaded files ki list"""
        files = []
        for f in UPLOAD_DIR.iterdir():
            if f.is_file():
                size_mb = round(f.stat().st_size / (1024 * 1024), 3)
                files.append({
                    "filename": f.name,
                    "size_mb": size_mb,
                    "url": f"/files/{f.name}"
                })
        return files

    def delete_file(self, filename: str) -> dict:
        """Kisi file ko delete karo"""
        # Security: sirf filename allow karo, path traversal nahi
        if "/" in filename or "\\" in filename or ".." in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        file_path = UPLOAD_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File nahi mili")

        os.remove(file_path)
        return {"message": f"'{filename}' delete ho gayi"}

    def read_text_file(self, filename: str) -> str:
        """Text/CSV file ka content padhho (AI analysis ke liye)"""
        if "/" in filename or ".." in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        file_path = UPLOAD_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File nahi mili")

        suffix = file_path.suffix.lower()
        if suffix not in [".txt", ".csv", ".json"]:
            raise HTTPException(status_code=400, detail="Sirf .txt, .csv, .json files padhi ja sakti hain")

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(5000)  # First 5000 chars (Groq context limit ke liye)

        return content
