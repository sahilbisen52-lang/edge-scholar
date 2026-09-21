"""Quiz question generator using local LLM."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from app.ai.base_provider import AIProvider
from app.documents.document_store import DocumentStore
from app.rag.prompt_templates import quiz_prompt
from app.core.errors import ModelNotLoadedError

logger = logging.getLogger("edge_scholar.study")


@dataclass
class QuizQuestion:
    question_text: str
    question_type: str  # mcq | true_false | short_answer
    options: list[str] = field(default_factory=list)
    correct_answer: str = ""
    source_hint: str = ""


class QuizGenerator:
    def __init__(self, provider: AIProvider, document_store: DocumentStore) -> None:
        self.provider = provider
        self.document_store = document_store

    def generate(
        self,
        document_id: str,
        num_questions: int = 5,
        max_tokens: int = 900,
    ) -> tuple[str, list[QuizQuestion]]:
        """Return (raw_text, parsed_questions)."""
        meta = self.document_store.get_document(document_id)
        if not meta:
            raise ValueError(f"Document not found: {document_id}")

        pages = self.document_store.get_pages(document_id)
        text = " ".join(p.text for p in pages)[:6000]

        prompt = quiz_prompt(text, meta.filename, num_questions)
        try:
            result = self.provider.generate(prompt, max_tokens=max_tokens, temperature=0.4)
            return result.text, self._parse_questions(result.text)
        except ModelNotLoadedError:
            return "⚠️ No model loaded.", []
        except Exception as e:
            logger.exception("Quiz generation failed: %s", e)
            return f"⚠️ Failed: {e}", []

    @staticmethod
    def _parse_questions(text: str) -> list[QuizQuestion]:
        """Best-effort parse of LLM quiz output."""
        questions = []
        blocks = re.split(r"\n(?=Q\d+[:.]|Question \d+[:.])", text, flags=re.IGNORECASE)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            lines = block.split("\n")
            q_text = lines[0].strip()
            # Detect type
            if any(x in block.lower() for x in ["true or false", "true/false"]):
                qtype = "true_false"
            elif any(x in block for x in ["A)", "B)", "a)", "b)", "A.", "B."]):
                qtype = "mcq"
            else:
                qtype = "short_answer"

            options = []
            correct = ""
            for line in lines[1:]:
                line = line.strip()
                m = re.match(r"^([A-Da-d])[).:]\s+(.*)", line)
                if m:
                    options.append(f"{m.group(1).upper()}) {m.group(2).strip()}")
                if re.search(r"answer[:\s]+([A-Da-d])", line, re.IGNORECASE):
                    correct_match = re.search(r"answer[:\s]+([A-Da-d])", line, re.IGNORECASE)
                    if correct_match:
                        correct = correct_match.group(1).upper()

            if q_text:
                questions.append(QuizQuestion(
                    question_text=q_text,
                    question_type=qtype,
                    options=options,
                    correct_answer=correct,
                ))

        return questions
