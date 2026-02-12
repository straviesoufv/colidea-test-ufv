# Colidea · Generador de preguntas inteligentes para evaluación (UFV)

Colidea es el MVP de la Comisión de IA de la Universidad Francisco de Vitoria para facilitar la creación de preguntas tipo test y de desarrollo a partir de guías docentes, temarios o contenidos compartidos por el profesorado. Arranca con un servicio web ligero y puede enfocar la exportación a Excel/Word y Canvas en fases siguientes.

## Estructura

- `src/colidea_app/main.py`: FastAPI + OpenAI (o compatibles) para generar preguntas a partir del texto que cargue el profesor.
- `scripts/sample_generate.py`: simulador local que imprime preguntas de ejemplo sin depender de la API.
- `requirements.txt`: dependencias mínimas.

## Flujo mínimo viable

1. El profesor sube el temario (texto, Word o PDF convertido a texto) y selecciona niveles de Bloom y tipos de pregunta.
2. Colidea construye un prompt configurable con los datos y llama a la API (OpenAI/otro) para generar preguntas + pistas + metadatos.
3. Devuelve un JSON que se puede exportar a CSV/Excel y, más adelante, transformarse en QTI para Canvas.

## Arranque local (pruebas)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.colidea_app.main:app --reload
```

Define `OPENAI_API_KEY` en el entorno y opcionalmente `COLIDEA_MODEL` (por defecto `gpt-4o-mini`).

También puedes ejecutar el simulador offline:

```bash
python scripts/sample_generate.py
```

## Próximos pasos inmediatos

- Añadir carga de archivos (Word/PDF) con `python-multipart` y `pdfminer`/`python-docx`.
- Guardar plantillas de Bloom/preferencias del docente para reutilizar en cada curso.
- Exportador a Excel/Word (p. ej. `pandas` + `xlsxwriter`, `python-docx`).
- Conectar a Canvas (QTI o APIs de Canvas) en una fase 2 cuando el MVP esté validado.

## Requisitos para producción

- Rotación de claves y secret management.
- Revisión humana de las preguntas sensibles.
- Monitorización del consumo y de los prompts para ajustar costes.
