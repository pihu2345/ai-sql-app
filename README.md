# 🤖 AI SQL App

A full-stack AI-powered application built with **FastAPI + Groq LLM + MySQL**. This app lets you chat with an AI, run SQL queries, convert natural language to SQL, upload and analyze files — all from a clean dashboard.

---

## ✨ Features

- 💬 **AI Chat** — Chat with Groq LLM (LLaMA 3) in Hindi or English
- 🗄️ **SQL Runner** — Run SELECT queries directly on your MySQL database
- ✨ **Natural Language → SQL** — Type in plain English/Hindi, get a SQL query
- 📊 **Data Analysis** — Let AI analyze your SQL query results
- 📁 **File Upload** — Upload images, PDFs, CSVs and analyze them with AI
- 👥 **User & Product CRUD** — Create and list users and products

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| LLM | Groq API (LLaMA 3.1) |
| Database | MySQL |
| ORM | SQLAlchemy |
| Frontend | HTML + CSS + JS |

---

## 📁 Project Structure

```
ai_sql_app/
├── main.py           # FastAPI app — all routes
├── groq_service.py   # Groq LLM integration
├── database.py       # MySQL connection + SQLService
├── models.py         # Database models (User, Product, ChatHistory)
├── file_service.py   # File upload & analysis
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variables template
└── index.html        # Frontend dashboard
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11+
- MySQL (or XAMPP)
- Groq API Key (free at [console.groq.com](https://console.groq.com))

### 1. Clone the repository
```bash
git clone https://github.com/pihu2345/ai-sql-app.git
cd ai-sql-app
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup environment variables
```bash
cp .env.example .env
```
Edit `.env` and add your values:
```
GROQ_API_KEY=gsk_your_key_here
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=ai_app_db
```

### 5. Create MySQL database
```sql
CREATE DATABASE ai_app_db;
```

### 6. Run the server
```bash
python main.py
```

Server will start at: `http://localhost:8000`

### 7. Open Frontend
Open `index.html` in your browser — or run:
```bash
start index.html
```

---

## 🔑 Get Groq API Key (Free)

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Go to **API Keys** → **Create API Key**
4. Copy the key starting with `gsk_...`
5. Paste it in your `.env` file

---

## 🛣️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/ai/chat` | Chat with Groq LLM |
| POST | `/ai/nl-to-sql` | Natural language to SQL |
| POST | `/ai/analyze-data` | AI data analysis |
| POST | `/sql/execute` | Run SELECT query |
| GET | `/sql/tables` | List all tables |
| GET | `/sql/schema` | View DB schema |
| POST | `/files/upload` | Upload a file |
| GET | `/files/list` | List uploaded files |
| POST | `/users/` | Create user |
| GET | `/users/` | Get all users |
| POST | `/products/` | Create product |
| GET | `/products/` | Get all products |

---

## 📸 API Docs

Visit `http://localhost:8000/docs` for interactive Swagger UI.

---

## 👩‍💻 Author

**Pihu** — [@pihu2345](https://github.com/pihu2345)

---
## 🎥 Demo Video
[Click here to watch the demo](https://drive.google.com/file/d/1wAxb5TJx89hQwAuJZBv_hfVxwCEmaHUT/view?usp=drivesdk)


## 📄 License

This project is open source and available under the [MIT License](LICENSE).
