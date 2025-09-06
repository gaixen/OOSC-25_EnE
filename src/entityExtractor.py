import json
import os
from collections import defaultdict

import spacy
from spacy.tokens import Span
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


class InfoExtractionAgent:
    def __init__(self, model_name: str = "en_core_web_sm", gemini_model: str = "gemini-1.5-flash"):
        """Load spaCy and initialize Gemini client."""
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            raise RuntimeError(
                f"spaCy model '{model_name}' not found. Install it with: python -m spacy download {model_name}"
            )

        self.gemini_model = gemini_model
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Please set your Gemini API key as environment variable: GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.llm = genai.GenerativeModel(self.gemini_model)

    def _extract_with_spacy(self, text: str) -> dict:
        """Initial lightweight extraction using spaCy only, with label corrections."""
        doc = self.nlp(text)
        entities = {}

        for ent in doc.ents:
            label = ent.label_

            if label == "ORG":
                tokens = ent.text.split()
                if len(tokens) in (2, 3) and all(tok[0].isupper() for tok in tokens if tok):
                    label = "PERSON"

            key = ent.text
            if key not in entities:
                entities[key] = {
                    "name": ent.text,
                    "type": label,
                    "specifications": [],
                    "original_mentions": [ent.text],
                }
            else:
                entities[key]["original_mentions"].append(ent.text)

        return {"extracted_entities": list(entities.values())}

    def _refine_with_gemini(self, raw_output: dict, text: str) -> dict:
        """Send raw extraction to Gemini to resolve coref + rank specifications."""
        prompt = f"""
You are an advanced NLP assistant.
Here is the raw entity extraction (from spaCy):

{json.dumps(raw_output, indent=2)}

Original sentence: "{text}"

Tasks:
1. Resolve pronouns and link them to the correct entities.
2. Correct entity types if they are mislabeled (e.g., treat human names as PERSON, universities as ORG/FAC).
3. Add or improve specifications for each entity (e.g., roles, descriptors, achievements).
4. Rank specifications so that the most important come first.
5. Return valid JSON only, in the same schema:
{{
    "extracted_entities": [
        {{
            "name": "...",
            "type": "...",
            "specifications": ["...", "..."],
            "original_mentions": ["...", "..."]
        }}
    ]
}}
"""
        response = self.llm.generate_content(prompt)
        try:
            refined = json.loads(response.text)
        except Exception:
            refined = raw_output  # fallback if Gemini returns non-JSON
        return refined

    def process_text(self, text: str) -> dict:
        """Run spaCy extraction then refine with Gemini."""
        raw_output = self._extract_with_spacy(text)
        refined_output = self._refine_with_gemini(raw_output, text)
        return refined_output


if __name__ == "__main__":
    # Example run
    example_text = (
        "Jeff bezos is a CEO of Amazon "
        "He is known for his work in amazon"
    )

    agent = InfoExtractionAgent()
    result = agent.process_text(example_text)

    os.makedirs("src", exist_ok=True)
    with open("src/extracted_data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print("Extraction complete. Results written to src/extracted_data.json")
