"""
chat.py — Text-to-SQL AI Chat Agent for Urban Bike.

Uses Google Gemini to convert natural-language questions into SQL queries,
executes them on the local SQLite database, and returns human-friendly answers.
"""

import os
import re
import time
import sqlite3
import google.generativeai as genai
from dotenv import load_dotenv
from db import DB_PATH, get_conn, list_sensors

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

QUERY_TIMEOUT = 5  # seconds
MAX_RESULT_ROWS = 100


def _build_system_prompt() -> str:
    """Build the system prompt with the current DB schema and sensor list."""
    sensors = list_sensors()
    sensor_lines = "\n".join(
        f"  - device_id='{s['id']}', name='{s['name']}', location='{s.get('location', s['name'])}', "
        f"lat={s['lat']}, lon={s['lon']}, active={'Da' if s['is_active'] else 'Nu'}"
        for s in sensors
    )

    return f"""Ești un asistent AI specializat în analiza datelor de calitate a aerului din Sibiu, România.
Ai acces la o bază de date SQLite cu date de la senzori de mediu.

SCHEMA BAZEI DE DATE:
```sql
CREATE TABLE sensor_data (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id   TEXT      NOT NULL,
    location    TEXT      NOT NULL,
    timestamp   TIMESTAMP NOT NULL,
    temperature REAL,      -- Temperatură în °C
    pressure    REAL,      -- Presiune atmosferică în Pa
    humidity    REAL,      -- Umiditate relativă în %
    pm1         REAL,      -- Particule PM1 în µg/m³
    pm25        REAL,      -- Particule PM2.5 în µg/m³
    pm10        REAL,      -- Particule PM10 în µg/m³
    UNIQUE (device_id, timestamp)
);
CREATE INDEX idx_device_ts ON sensor_data (device_id, timestamp);
```

SENZORI DISPONIBILI:
{sensor_lines}

ATENȚIE la coloanele `location` din tabelul `sensor_data` — valorile stocate pot diferi ușor de `name` din lista de senzori.
Folosește `LIKE '%..%'` pentru matching flexibil.

REGULI:
1. Generează DOAR interogări SELECT. Nu genera INSERT, UPDATE, DELETE, DROP, ALTER, CREATE.
2. Folosește LIMIT {MAX_RESULT_ROWS} dacă query-ul poate returna multe rânduri.
3. Timestamp-urile sunt stocate ca TEXT ISO 8601 (ex: '2026-05-25T14:30:00').
4. Pentru date relative (ieri, săptămâna trecută), folosește funcții SQLite: date('now'), datetime('now','-1 day'), etc.
5. Răspunde MEREU în limba română.
6. Când generezi SQL, pune-l într-un bloc ```sql ... ```.
7. După ce primești rezultatul, formulează un răspuns natural, uman, cu date concrete.
8. Dacă nu ai suficiente informații pentru a răspunde, spune clar ce lipsește.
9. Rotunjește valorile numerice la 1-2 zecimale în răspunsul final.
10. Dacă întrebarea nu are legătură cu datele de mediu, răspunde politicos că ești specializat doar pe date de calitate a aerului.

EXEMPLE DE ÎNTREBĂRI ȘI SQL:
- "Care e temperatura medie în Centru?" → SELECT AVG(temperature) FROM sensor_data WHERE location LIKE '%Centru%'
- "Când a fost cel mai poluat?" → SELECT location, timestamp, pm25 FROM sensor_data ORDER BY pm25 DESC LIMIT 1
- "Compară umiditatea Gusterița vs Caposu" → SELECT location, ROUND(AVG(humidity),1) FROM sensor_data WHERE location LIKE '%Guster%' OR location LIKE '%Caposu%' GROUP BY location
"""


class ChatAgent:
    """Text-to-SQL chat agent using Google Gemini."""

    def __init__(self):
        self.system_prompt = _build_system_prompt()
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=self.system_prompt,
        )
        self.chat = self.model.start_chat(history=[])
        self.history = []  # [{role, content}, ...]

    def _send_with_retry(self, message: str, max_retries: int = 3):
        """Send message to Gemini with retry on rate limit (429) errors."""
        for attempt in range(max_retries):
            try:
                return self.chat.send_message(message)
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                    print(f"[chat] Rate limited, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise

    def _extract_sql(self, text: str) -> str | None:
        """Extract SQL from a ```sql ... ``` block in the LLM response."""
        pattern = r"```sql\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            sql = match.group(1).strip()
            return sql
        return None

    def _is_safe_sql(self, sql: str) -> bool:
        """Only allow SELECT statements."""
        normalized = sql.strip().upper()
        dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE", "TRUNCATE", "EXEC"]
        for keyword in dangerous:
            if normalized.startswith(keyword):
                return False
        # Also check for dangerous statements after semicolons (multi-statement injection)
        if ";" in sql:
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            for stmt in statements:
                if not stmt.upper().startswith("SELECT") and not stmt.upper().startswith("WITH"):
                    return False
        return normalized.startswith("SELECT") or normalized.startswith("WITH")

    def _execute_sql(self, sql: str) -> dict:
        """Execute a safe SQL query and return results."""
        if not self._is_safe_sql(sql):
            return {"error": "Interogarea nu este permisă (doar SELECT este acceptat)."}

        try:
            conn = sqlite3.connect(DB_PATH, timeout=QUERY_TIMEOUT)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql)
            rows = cursor.fetchmany(MAX_RESULT_ROWS)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            result = [dict(row) for row in rows]
            conn.close()
            return {"columns": columns, "data": result, "row_count": len(result)}
        except sqlite3.OperationalError as e:
            return {"error": f"Eroare SQL: {e}"}
        except Exception as e:
            return {"error": f"Eroare: {e}"}

    def ask(self, question: str) -> str:
        """
        Full pipeline: question → LLM → SQL → execute → LLM → answer.
        Returns the final human-readable answer.
        """
        self.history.append({"role": "user", "content": question})

        try:
            # Step 1: Ask LLM to generate SQL
            response = self._send_with_retry(question)
            llm_text = response.text

            sql = self._extract_sql(llm_text)

            if sql is None:
                # LLM responded without SQL (maybe a general question)
                self.history.append({"role": "assistant", "content": llm_text})
                return llm_text

            # Step 2: Execute SQL
            result = self._execute_sql(sql)

            if "error" in result:
                # Retry: tell LLM about the error
                retry_msg = (
                    f"Interogarea SQL a returnat o eroare: {result['error']}\n"
                    f"SQL-ul tău a fost: {sql}\n"
                    f"Te rog să corectezi interogarea și să încerci din nou."
                )
                retry_response = self._send_with_retry(retry_msg)
                retry_text = retry_response.text
                retry_sql = self._extract_sql(retry_text)

                if retry_sql and self._is_safe_sql(retry_sql):
                    result = self._execute_sql(retry_sql)
                    if "error" in result:
                        error_msg = f"Nu am reușit să execut interogarea. Eroare: {result['error']}"
                        self.history.append({"role": "assistant", "content": error_msg})
                        return error_msg
                    sql = retry_sql
                else:
                    self.history.append({"role": "assistant", "content": retry_text})
                    return retry_text

            # Step 3: Send results back to LLM for natural language answer
            result_summary = f"Rezultatul interogării SQL:\n"
            if result["data"]:
                result_summary += f"Coloane: {result['columns']}\n"
                # Limit data sent to LLM
                display_data = result["data"][:20]
                for row in display_data:
                    result_summary += f"  {row}\n"
                if result["row_count"] > 20:
                    result_summary += f"  ... ({result['row_count']} rânduri total)\n"
            else:
                result_summary += "Nu s-au găsit rezultate.\n"

            result_summary += "\nFormulează un răspuns clar și natural în limba română, bazat pe aceste date."

            final_response = self._send_with_retry(result_summary)
            answer = final_response.text

            self.history.append({"role": "assistant", "content": answer})
            return answer

        except Exception as e:
            error_msg = f"Eroare la procesarea întrebării: {str(e)}"
            self.history.append({"role": "assistant", "content": error_msg})
            return error_msg

    def get_history(self) -> list[dict]:
        """Return the conversation history."""
        return self.history.copy()

    def reset(self):
        """Reset conversation history and start a new chat session."""
        self.chat = self.model.start_chat(history=[])
        self.history = []
