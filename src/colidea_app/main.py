from typing import List, Optional
import json
import os

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None

app = FastAPI(title="Colidea – Generador de preguntas de evaluación")

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

PROVIDER = os.environ.get("COLIDEA_PROVIDER", "openrouter").lower().strip()
DEFAULT_MODEL = "openrouter/google/gpt-4o-mini" if PROVIDER == "openrouter" else "gpt-4o-mini"
MODEL = os.environ.get("COLIDEA_MODEL", DEFAULT_MODEL)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")


class PromptConfig(BaseModel):
    bloom_levels: List[str]
    question_types: List[str]
    context: Optional[str]
    number_of_questions: int = 8
    target_audience: Optional[str]


class QuestionResponse(BaseModel):
    question: str
    answer_hint: str
    cognitive_level: str
    question_type: str


class GenerationPayload(BaseModel):
    syllabus_text: str
    prompt_config: PromptConfig


def build_prompt(payload: GenerationPayload) -> str:
    config = payload.prompt_config
    lines = [
        "Eres el asistente de evaluación de la UFV.",
        "Genera preguntas que el profesorado pueda reutilizar en quices y pruebas escritas.",
        f"Nivel cognitivo: {', '.join(config.bloom_levels)}.",
        f"Tipos de pregunta: {', '.join(config.question_types)}.",
    ]
    if config.target_audience:
        lines.append(f"Dirigido a: {config.target_audience}.")
    if config.context:
        lines.append(f"Detalles adicionales: {config.context}.")
    lines.append(
        f"Contexto/temario: {payload.syllabus_text.strip()}"
    )
    lines.append("Devuelve un JSON con campos: question, question_type, cognitive_level, answer_hint.")
    lines.append("Incluye al menos una sugerencia para exportarlo a Excel/Word.")
    return "\n".join(lines)


def call_model(prompt: str) -> List[dict]:
    if PROVIDER == "openrouter":
        return call_openrouter_model(prompt)
    return call_openai_model(prompt)


def call_openai_model(prompt: str) -> List[dict]:
    if not openai:
        raise HTTPException(
            status_code=503,
            detail="No se ha instalado la biblioteca openai. Ejecuta pip install -r requirements.txt",
        )
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=412,
            detail="No hay clave OPENAI_API_KEY en el entorno.",
        )
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.responses.create(
        model=MODEL,
        input=prompt,
        max_tokens=800,
        temperature=0.3,
    )
    output = response.output[0].content
    return _parse_model_output(output)


OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/responses"


def call_openrouter_model(prompt: str) -> List[dict]:
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=412,
            detail="No hay clave OPENROUTER_API_KEY en el entorno.",
        )
    payload = {
        "model": MODEL,
        "input": prompt,
        "temperature": 0.3,
        "max_output_tokens": 800,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(OPENROUTER_ENDPOINT, json=payload, headers=headers, timeout=30)
    if not response.ok:
        detail = response.text
        raise HTTPException(status_code=response.status_code or 502, detail=f"OpenRouter: {detail}")
    body = response.json()
    raw_output = _extract_response_text(body)
    return _parse_model_output(raw_output)


def _extract_response_text(body: dict) -> str:
    def _from_item(item):
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            content = item.get("content")
            if isinstance(content, list):
                parts = []
                for piece in content:
                    if isinstance(piece, dict):
                        parts.append(piece.get("text") or piece.get("content"))
                    elif isinstance(piece, str):
                        parts.append(piece)
                return "".join(filter(None, parts))
            if isinstance(content, str):
                return content
            text = item.get("text")
            if isinstance(text, str):
                return text
        return None

    for key in ("output", "choices", "response"):  # openrouter usa varias claves
        chunk = body.get(key)
        if chunk is None:
            continue
        if isinstance(chunk, list):
            for item in chunk:
                value = _from_item(item)
                if value:
                    return value
        else:
            value = _from_item(chunk)
            if value:
                return value
    raise HTTPException(status_code=500, detail="OpenRouter no devolvió texto válido")


def _parse_model_output(output: str) -> List[dict]:
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Respuesta de IA no tiene JSON válido")


@app.post("/generate", response_model=List[QuestionResponse])
def generate_questions(payload: GenerationPayload):
    prompt = build_prompt(payload)
    raw = call_model(prompt)
    return raw


@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    context = {
        "request": request,
        "model": MODEL,
        "provider": PROVIDER.upper(),
    }
    return templates.TemplateResponse("index.html", context)


@app.get("/health")
def healthcheck():
    return {
        "status": "ready",
        "model": MODEL,
        "provider": PROVIDER,
        "notes": "Carga syllabus, define niveles de Bloom y tipos de preguntas."
    }
