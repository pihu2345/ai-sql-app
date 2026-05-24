import os
import json
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class GroqService:
    """
    Groq API ke saath interact karne ka service class.
    Groq bahut fast inference deta hai — LLaMA 3, Mixtral models use karta hai.
    """

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = "llama-3.1-8b-instant"   # Fast & capable — llama3-70b-8192 bhi use kar sakte ho

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable set nahi hai! .env file check karo.")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # In-memory conversation store (production mein Redis/DB use karo)
        self.conversations: dict = {}

    async def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> dict:
        """
        Groq LLM se general purpose chat karo.
        Conversation history maintain karta hai conversation_id ke through.
        """
        # System prompt default
        if not system_prompt:
            system_prompt = (
                "Tum ek helpful AI assistant ho. "
                "Tum Hindi aur English dono mein baat kar sakte ho. "
                "Sawal ka seedha aur clear jawab do."
            )

        # Conversation history load karo
        history = self.conversations.get(conversation_id, []) if conversation_id else []

        # Naya message add karo
        history.append({"role": "user", "content": message})

        messages = [{"role": "system", "content": system_prompt}] + history

        payload = {
            "model": self.DEFAULT_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.GROQ_API_URL,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        reply = data["choices"][0]["message"]["content"]
        tokens_used = data.get("usage", {}).get("total_tokens")

        # History update karo
        history.append({"role": "assistant", "content": reply})
        if conversation_id:
            self.conversations[conversation_id] = history[-20:]  # Last 20 messages rakho

        return {
            "reply": reply,
            "conversation_id": conversation_id,
            "tokens_used": tokens_used
        }

    async def convert_to_sql(self, natural_language: str, schema: str) -> str:
        """
        Natural Language query ko SQL mein convert karo using Groq.
        """
        system_prompt = f"""
Tum ek expert SQL developer ho. 
Neeche diya gaya MySQL database schema hai:

{schema}

User jo bhi natural language mein poochhe, usse valid MySQL SELECT query mein convert karo.
- Sirf SQL query return karo, koi explanation nahi
- Query ko ```sql``` blocks mein mat wrap karo
- Sirf SELECT statements generate karo (no INSERT/UPDATE/DELETE)
- MySQL syntax use karo
"""
        payload = {
            "model": self.DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": natural_language}
            ],
            "temperature": 0.1,   # Low temperature for precise SQL
            "max_tokens": 512,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.GROQ_API_URL,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        sql_query = data["choices"][0]["message"]["content"].strip()
        # Clean up any markdown if model adds it
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        return sql_query

    async def analyze_data(self, data: list, query: str) -> str:
        """
        SQL query ke result ko AI se analyze karwao — insights, patterns, summary.
        """
        system_prompt = (
            "Tum ek data analyst ho. "
            "User ko diye gaye data ka clear aur useful analysis do. "
            "Hindi ya English mein jawab do jaise user ne poochha ho."
        )

        user_message = f"""
Yeh SQL query thi: {query}

Aur yeh result aaya:
{json.dumps(data, indent=2, default=str)}

Is data ka brief analysis do:
1. Key findings kya hain?
2. Koi interesting patterns hain?
3. Koi actionable insight?
"""

        payload = {
            "model": self.DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.5,
            "max_tokens": 1024,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.GROQ_API_URL,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data_resp = response.json()

        return data_resp["choices"][0]["message"]["content"]