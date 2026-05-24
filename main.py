from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Any
import uvicorn
from pathlib import Path

from database import get_db, engine, Base, SQLService
from groq_service import GroqService
from file_service import FileUploadService
import models

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI + SQL App",
    description="General AI App with Groq LLM + MySQL Database",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
groq_service = GroqService()
sql_service = SQLService()
file_service = FileUploadService()

# Serve uploaded files as static URLs: /files/filename.jpg
Path("uploads").mkdir(exist_ok=True)
app.mount("/files", StaticFiles(directory="uploads"), name="files")


# ─── Request/Response Models ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    conversation_id: Optional[str]
    tokens_used: Optional[int]

class SQLQueryRequest(BaseModel):
    query: str

class NLToSQLRequest(BaseModel):
    natural_language: str
    table_schema: Optional[str] = None

class SaveChatRequest(BaseModel):
    conversation_id: str
    user_message: str
    ai_response: str

class UserCreate(BaseModel):
    name: str
    email: str

class ProductCreate(BaseModel):
    name: str
    price: float
    description: Optional[str] = None


# ─── Health Check ──────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "running", "message": "AI + SQL FastAPI App is live!"}

@app.get("/health")
def health_check():
    db_status = sql_service.test_connection()
    return {
        "api": "ok",
        "database": "connected" if db_status else "error",
        "llm": "groq"
    }


# ─── LLM / AI Routes ──────────────────────────────────────────────────────────

@app.post("/ai/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """
    Groq LLM se chat karo — general purpose AI endpoint
    """
    try:
        result = await groq_service.chat(
            message=request.message,
            system_prompt=request.system_prompt,
            conversation_id=request.conversation_id
        )
        return ChatResponse(
            reply=result["reply"],
            conversation_id=result.get("conversation_id"),
            tokens_used=result.get("tokens_used")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/nl-to-sql")
async def natural_language_to_sql(request: NLToSQLRequest):
    """
    Natural Language → SQL query convert karo using Groq LLM
    """
    try:
        schema = request.table_schema or sql_service.get_schema_info()
        sql_query = await groq_service.convert_to_sql(
            natural_language=request.natural_language,
            schema=schema
        )
        return {
            "natural_language": request.natural_language,
            "sql_query": sql_query,
            "schema_used": schema
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/analyze-data")
async def analyze_data_with_ai(request: SQLQueryRequest):
    """
    SQL query run karo aur result ko AI se analyze karwao
    """
    try:
        # Step 1: SQL se data lao
        data = sql_service.execute_query(request.query)

        # Step 2: Groq se analyze karwao
        analysis = await groq_service.analyze_data(data=data, query=request.query)

        return {
            "query": request.query,
            "raw_data": data,
            "ai_analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── SQL / Database Routes ─────────────────────────────────────────────────────

@app.post("/sql/execute")
def execute_sql(request: SQLQueryRequest):
    """
    Direct SQL query execute karo (SELECT only for safety)
    """
    try:
        if not request.query.strip().upper().startswith("SELECT"):
            raise HTTPException(status_code=400, detail="Sirf SELECT queries allowed hain")
        result = sql_service.execute_query(request.query)
        return {"data": result, "row_count": len(result)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sql/tables")
def list_tables():
    """Database mein saari tables dekhho"""
    try:
        tables = sql_service.get_all_tables()
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sql/schema")
def get_schema():
    """Full database schema dekhho"""
    try:
        schema = sql_service.get_schema_info()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Chat History Routes ───────────────────────────────────────────────────────

@app.post("/history/save")
def save_chat(request: SaveChatRequest, db=Depends(get_db)):
    """Chat history MySQL mein save karo"""
    try:
        chat = models.ChatHistory(
            conversation_id=request.conversation_id,
            user_message=request.user_message,
            ai_response=request.ai_response
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return {"id": chat.id, "message": "Chat history saved!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{conversation_id}")
def get_chat_history(conversation_id: str, db=Depends(get_db)):
    """Kisi conversation ki poori history lao"""
    chats = db.query(models.ChatHistory)\
              .filter(models.ChatHistory.conversation_id == conversation_id)\
              .order_by(models.ChatHistory.created_at)\
              .all()
    return {"conversation_id": conversation_id, "history": chats}


# ─── Sample CRUD Routes (Users & Products) ────────────────────────────────────

@app.post("/users/")
def create_user(user: UserCreate, db=Depends(get_db)):
    db_user = models.User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/")
def get_users(db=Depends(get_db)):
    return db.query(models.User).all()

@app.post("/products/")
def create_product(product: ProductCreate, db=Depends(get_db)):
    db_product = models.Product(
        name=product.name,
        price=product.price,
        description=product.description
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/")
def get_products(db=Depends(get_db)):
    return db.query(models.Product).all()


# ─── File Upload Routes ────────────────────────────────────────────────────────

@app.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    File upload karo — image, PDF, CSV, TXT, JSON support.
    Max size: 10 MB. Response mein direct URL milta hai.
    """
    result = file_service.save_file(file)
    return {"message": "File upload ho gayi!", **result}


@app.post("/files/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """
    Ek saath multiple files upload karo (max 5)
    """
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Ek baar mein max 5 files upload kar sakte ho")

    results = []
    errors = []
    for file in files:
        try:
            result = file_service.save_file(file)
            results.append(result)
        except HTTPException as e:
            errors.append({"file": file.filename, "error": e.detail})

    return {
        "uploaded": results,
        "failed": errors,
        "total_uploaded": len(results)
    }


@app.get("/files/list")
def list_uploaded_files():
    """Saari uploaded files ki list dekhho"""
    files = file_service.list_files()
    return {"files": files, "total": len(files)}


@app.delete("/files/{filename}")
def delete_file(filename: str):
    """Kisi file ko delete karo"""
    return file_service.delete_file(filename)


@app.post("/files/analyze/{filename}")
async def analyze_file_with_ai(filename: str):
    """
    Text/CSV/JSON file ko Groq AI se analyze karwao.
    File pehle /files/upload se upload karni hogi.
    """
    try:
        content = file_service.read_text_file(filename)
        analysis = await groq_service.chat(
            message=f"Yeh file ka content hai:\n\n{content}\n\nIs file ka summary aur key points batao.",
            system_prompt="Tum ek data analyst ho. File content padho aur clear summary do Hindi ya English mein."
        )
        return {
            "filename": filename,
            "ai_analysis": analysis["reply"],
            "content_preview": content[:300] + "..." if len(content) > 300 else content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)