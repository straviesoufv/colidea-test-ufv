from typing import List, Optional
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None

app = FastAPI(title="Colidea – Generador de preguntas de evaluación")

MODEL = os.environ.get("COLIDEA_MODEL", "gpt-4o-mini")


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
    if not openai:
        raise HTTPException(
            status_code=503,
            detail="No se ha instalado la biblioteca openai. Ejecuta pip install -r requirements.txt",
        )
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=412,
            detail="No hay clave OPENAI_API_KEY en el entorno.",
        )
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.responses.create(
        model=MODEL,
        input=prompt,
        max_tokens=800,
        temperature=0.3,
    )
    output = response.output[0].content
    # Suponer que output es JSON en formato listo para parsear.
    import json

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Respuesta de IA no tiene JSON válido")


@app.post("/generate", response_model=List[QuestionResponse])
def generate_questions(payload: GenerationPayload):
    prompt = build_prompt(payload)
    raw = call_model(prompt)
    return raw


@app.get("/")
def healthcheck():
    return {
        "status": "ready",
        "model": MODEL,
        "notes": "Carga syllabus, define niveles de Bloom y tipos de preguntas."
    }
