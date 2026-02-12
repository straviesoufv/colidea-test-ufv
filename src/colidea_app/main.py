from typing import List, Optional
import json
import os
from pathlib import Path
from string import Template
from threading import Lock

import requests
import docx
import logging
import pdfplumber
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None

app = FastAPI(title="colidea-test-ufv – Generador de preguntas de evaluación")
logger = logging.getLogger("uvicorn.error")


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    logger.warning("RequestValidationError %s %s", exc.errors(), exc.body)
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
CONFIG_PATH = Path(os.environ.get("COLIDEA_ADMIN_CONFIG", os.path.join(BASE_DIR, "admin_config.json")))

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

ENV_PROVIDER = os.environ.get("COLIDEA_PROVIDER", "openrouter").lower().strip()
DEFAULT_MODEL = "openrouter/google/gpt-4o-mini" if ENV_PROVIDER == "openrouter" else "gpt-4o-mini"
ENV_MODEL = os.environ.get("COLIDEA_MODEL", DEFAULT_MODEL)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

DEFAULT_PROMPT_TEMPLATE = (
    "Eres el asistente de evaluación de la UFV.\n"
    "Genera ${number_of_questions} preguntas que el profesorado pueda reutilizar en quices y pruebas escritas.\n"
    "Nivel cognitivo: ${bloom_levels}.\n"
    "Tipos de pregunta: ${question_types}.\n"
    "Cada pregunta debe incluir ${number_of_alternatives} opciones de respuesta (una correcta y el resto distractores).\n"
    "Integra suavemente el espíritu del modelo Formar para Transformar: aprendizaje aplicado, formación humana, acompañamiento del talento y actualización crítica de los conocimientos, sin exagerar.\n"
    "${target_audience}\n"
    "${context}\n"
    "Contexto/temario: ${syllabus_text}\n"
    "Devuelve un JSON con campos: question, question_type, cognitive_level, answer_hint.\n"
    "Incluye al menos una sugerencia para exportarlo a Excel/Word."
)

config_lock = Lock()
admin_config = {}


def _default_admin_config():
    return {
        "provider": ENV_PROVIDER,
        "model": ENV_MODEL,
        "prompt_template": DEFAULT_PROMPT_TEMPLATE,
    }


def load_admin_config() -> dict:
    if not CONFIG_PATH.exists():
        write_admin_config(_default_admin_config())
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError:
            return _default_admin_config()


def write_admin_config(data: dict):
    with CONFIG_PATH.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


with config_lock:
    admin_config = load_admin_config()


def _provider_default_model(provider: str) -> str:
    return "openrouter/google/gpt-4o-mini" if provider == "openrouter" else "gpt-4o-mini"


def get_active_provider() -> str:
    return (admin_config.get("provider") or ENV_PROVIDER).lower().strip()


def get_active_model() -> str:
    model = admin_config.get("model")
    if model:
        return model
    provider = get_active_provider()
    if provider == ENV_PROVIDER and ENV_MODEL:
        return ENV_MODEL
    return _provider_default_model(provider)


class PromptConfig(BaseModel):
    bloom_levels: List[str]
    question_types: List[str]
    context: Optional[str]
    number_of_questions: int = 8
    number_of_alternatives: int = 4
    target_audience: Optional[str]


class QuestionResponse(BaseModel):
    question: str
    answer_hint: str
    cognitive_level: str
    question_type: str


class GenerationPayload(BaseModel):
    syllabus_text: str
    prompt_config: PromptConfig


class AdminConfigPayload(BaseModel):
    provider: str
    model: str
    prompt_template: str


async def _read_file(file: UploadFile) -> str:
    file.file.seek(0)
    if file.filename.lower().endswith(".pdf"):
        with pdfplumber.open(file.file) as pdf:
            text = "\n".join((page.extract_text() or "") for page in pdf.pages)
    elif file.filename.lower().endswith(".docx") or file.filename.lower().endswith(".doc"):
        file.file.seek(0)
        document = docx.Document(file.file)
        text = "\n".join(para.text for para in document.paragraphs if para.text)
    else:
        contents = await file.read()
        text = contents.decode("utf-8", errors="ignore")
    file.file.seek(0)
    return text.strip()


@app.post("/extract")
async def extract_text(file: UploadFile = File(...)):
    try:
        extracted = await _read_file(file)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo extraer el texto: {exc}")
    if not extracted:
        raise HTTPException(status_code=400, detail="El documento no contiene texto legible.")
    return {"text": extracted}


def build_prompt(payload: GenerationPayload) -> str:
    template_str = admin_config.get("prompt_template") or DEFAULT_PROMPT_TEMPLATE
    template = Template(template_str)
    config = payload.prompt_config
    context_notes = f"Detalles adicionales: {config.context}." if config.context else ""
    audience_tags = f"Dirigido a: {config.target_audience}." if config.target_audience else ""
    return template.safe_substitute(
        syllabus_text=payload.syllabus_text.strip(),
        bloom_levels=", ".join(config.bloom_levels),
        question_types=", ".join(config.question_types),
        context=context_notes,
        target_audience=audience_tags,
        number_of_questions=config.number_of_questions,
        number_of_alternatives=config.number_of_alternatives,
    )


def call_model(prompt: str) -> List[dict]:
    provider = get_active_provider()
    if provider == "openrouter":
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
        model=get_active_model(),
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
        "model": get_active_model(),
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
        "model": get_active_model(),
        "provider": get_active_provider().upper(),
    }
    return templates.TemplateResponse("index.html", context)


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "provider": get_active_provider(),
            "model": get_active_model(),
            "prompt_template": admin_config.get("prompt_template", DEFAULT_PROMPT_TEMPLATE),
            "default_prompt": DEFAULT_PROMPT_TEMPLATE,
        },
    )


@app.get("/admin/config")
def admin_config_get():
    with config_lock:
        return {
            "provider": get_active_provider(),
            "model": get_active_model(),
            "prompt_template": admin_config.get("prompt_template", DEFAULT_PROMPT_TEMPLATE),
        }


@app.post("/admin/config")
def admin_config_update(payload: AdminConfigPayload):
    with config_lock:
        admin_config["provider"] = payload.provider.lower().strip()
        admin_config["model"] = payload.model.strip()
        admin_config["prompt_template"] = payload.prompt_template.strip()
        write_admin_config(admin_config)
    return {"status": "ok"}


@app.get("/health")
def healthcheck():
    return {
        "status": "ready",
        "model": get_active_model(),
        "provider": get_active_provider(),
        "notes": "Carga syllabus, define niveles de Bloom y tipos de preguntas."
    }
