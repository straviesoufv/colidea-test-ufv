"""Generador de preguntas ficticio para pruebas locales sin llamar a la API."""
from dataclasses import dataclass
from typing import List

@dataclass
class QuestionSample:
    question: str
    question_type: str
    cognitive_level: str
    answer_hint: str


def create_sample_questions() -> List[QuestionSample]:
    return [
        QuestionSample(
            question="Describe las tres capas del modelo de responsabilidad social de la UFV.",
            question_type="Desarrollo",
            cognitive_level="Análisis",
            answer_hint="Relaciona ética, impacto y compromiso personal.",
        ),
        QuestionSample(
            question="Selecciona la afirmación verdadera sobre la evaluación formativa.",
            question_type="Tipo test",
            cognitive_level="Comprensión",
            answer_hint="Pista: se centra en acompañar el aprendizaje, no solo en calificar.",
        ),
    ]


def main():
    preguntas = create_sample_questions()
    for idx, pregunta in enumerate(preguntas, 1):
        print(f"{idx}. {pregunta.question} [{pregunta.question_type} - {pregunta.cognitive_level}]")
        print(f"   + Pista: {pregunta.answer_hint}\n")


if __name__ == "__main__":
    main()
