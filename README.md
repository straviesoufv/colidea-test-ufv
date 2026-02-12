# colidea-test-ufv · Generador de preguntas inteligentes para evaluación (UFV)

colidea-test-ufv es el MVP de la Comisión de IA de la Universidad Francisco de Vitoria para facilitar la creación de preguntas tipo test y de desarrollo a partir de guías docentes, temarios o contenidos compartidos por el profesorado. Arranca con un servicio web ligero y puede enfocar la exportación a Excel/Word y Canvas en fases siguientes.

## Estructura

- `src/colidea_app/main.py`: FastAPI + OpenAI (o compatibles) para generar preguntas a partir del texto que cargue el profesor.
- `scripts/sample_generate.py`: simulador local que imprime preguntas de ejemplo sin depender de la API.
- `requirements.txt`: dependencias mínimas.

## Flujo mínimo viable

1. El profesor sube el temario (texto, Word o PDF convertido a texto) y selecciona niveles de Bloom y tipos de pregunta.
2. colidea-test-ufv construye un prompt configurable con los datos y llama a la API (OpenAI/otro) para generar preguntas + pistas + metadatos.
3. Devuelve un JSON que se puede exportar a CSV/Excel y, más adelante, transformarse en QTI para Canvas.

## Arranque local (pruebas)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.colidea_app.main:app --reload
```

Define `OPENAI_API_KEY` en el entorno y opcionalmente `COLIDEA_MODEL` (por defecto `gpt-4o-mini`).

colidea-test-ufv siempre puede apuntar a OpenRouter configurando `COLIDEA_PROVIDER=openrouter`, `COLIDEA_MODEL=openrouter/openai/gpt-4o-mini` y pasando `OPENROUTER_API_KEY`. Por ejemplo:

```bash
COLIDEA_PROVIDER=openrouter \
  COLIDEA_MODEL=openrouter/google/gpt-4o-mini \
  OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  docker run -e COLIDEA_PROVIDER -e COLIDEA_MODEL -e OPENROUTER_API_KEY -p 8080:8080 colidea-test-ufv:latest
```

También puedes ejecutar el simulador offline:

```bash
python scripts/sample_generate.py
```

## Interfaz web (maqueta UFV)
La aplicación suma una landing básica en `/` con la paleta UFV (header hero, tarjetas y botones con `Roboto Slab`/sans-serif y colores institucionales). Está servida desde `src/colidea_app/templates/index.html` y `src/colidea_app/static/css/main.css`. En el formulario puedes ajustar el número de preguntas entre 3 y 10 con el control deslizante, seleccionar niveles de Bloom y tipos de pregunta, definir cuántas alternativas (2-5) debe tener cada pregunta, e incluso extraer un PDF/DOCX/TXT para que vaya directo al prompt. Al pulsar “Generar preguntas” la landing llama a `/generate` y las preguntas devueltas (normalizadas para evitar `[object Object]`) se muestran en la tarjeta derecha junto con el tipo, nivel cognitivo y pista; el texto que se envía incluye un matiz del modelo Formar para Transformar (aprendizaje aplicado, formación humana, acompañamiento, actualización crítica). Cuando el contenedor está en marcha (`http://localhost:8080`) puedes navegar a esa vista para enseñársela a la Comisión.

También existe una página de administración en `/admin` para cambiar proveedor, modelo y la plantilla de prompt sin tocar código o reiniciar el contenedor. Lánzala desde el botón "Administración" en la cabecera; la configuración se guarda en `src/colidea_app/admin_config.json` y puedes editarla desde la GUI para probar prompts distintos antes de generar las preguntas. La plantilla puede usar `${number_of_questions}` y `${number_of_alternatives}` para que el modelo sepa cuántas preguntas y alternativas debe devolver.

## Carga de documentos
Para preparar preguntas a partir de documentos ya existentes (PDF/Word/TXT), usa el control “Extraer texto” que sube el archivo al endpoint `/extract`. El backend usa `pdfplumber` y `python-docx` para leer el contenido y devuelve el texto plano a la aplicación, que lo muestra en el textarea principal y lo usa en el prompt. Si el archivo no contiene texto legible se mostrará un error en pantalla.

La API permanece accesible en `/generate` y `/health` muestra el modelo activo. Mantén `OPENAI_API_KEY` o `OPENROUTER_API_KEY` en el entorno según el proveedor.

## Próximos pasos inmediatos

- Añadir carga de archivos (Word/PDF) con `python-multipart` y `pdfminer`/`python-docx`.
- Guardar plantillas de Bloom/preferencias del docente para reutilizar en cada curso.
- Exportador a Excel/Word (p. ej. `pandas` + `xlsxwriter`, `python-docx`).
- Conectar a Canvas (QTI o APIs de Canvas) en una fase 2 cuando el MVP esté validado.
- Empaquetar en Docker para entregarlo a la comisión y facilitar despliegue en Reaway o cualquier contenedor.

## Ejecutar en Docker

```bash
docker build -t colidea-test-ufv:latest .
docker run -p 8080:8080 colidea-test-ufv:latest
```

La API escucha en el puerto 8080 y expone `/generate` y `/` (sanity check). Asegúrate de pasar `OPENAI_API_KEY` en tiempo de ejecución (por ejemplo, `docker run -e OPENAI_API_KEY=$OPENAI_API_KEY -p 8080:8080 colidea-test-ufv:latest`).

## Requisitos para producción

- Rotación de claves y secret management.
- Revisión humana de las preguntas sensibles.
- Monitorización del consumo y de los prompts para ajustar costes.
