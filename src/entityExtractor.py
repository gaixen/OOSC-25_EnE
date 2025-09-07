import json
import os
from collections import defaultdict

import spacy
from spacy.tokens import Span
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


class InfoExtractionAgent:
    def __init__(self, model_name: str = "en_core_web_sm", gemini_model: str = "gemini-2.0-flash"):
        """Initialize with Gemini Pro as primary extraction method."""
        # Keep spaCy as optional fallback but use Gemini as primary
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            print(f"Warning: spaCy model '{model_name}' not found. Using Gemini only.")
            self.nlp = None

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
        """Extract entities directly using Gemini Pro for better accuracy."""
        prompt = f"""
Extract all entities from the following text and return a JSON response with the exact structure shown below.

Text to analyze: "{text}"

Required JSON structure:
{{
    "extracted_entities": [
        {{
            "name": "entity_name",
            "type": "PERSON|ORG|PRODUCT|LOCATION|MISC",
            "specifications": [],
            "original_mentions": ["mention1", "mention2"]
        }}
    ]
}}

Entity type guidelines:
- PERSON: Individual people (e.g., "Sundar Pichai", "Elon Musk")
- ORG: Companies, organizations (e.g., "Google", "Microsoft", "Tesla")
- PRODUCT: Products, services, brands (e.g., "iPhone", "Windows", "Gmail")
- LOCATION: Places, countries, cities (e.g., "California", "New York")
- MISC: Other significant entities

Important rules:
1. Extract ALL entities, don't miss any
2. For people, use their full name if available
3. For organizations, use the proper company name
4. Return ONLY the JSON, no other text
5. Ensure the JSON is valid and properly formatted
"""

        try:
            response = self.llm.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            result = json.loads(response_text)
            
            # Validate the structure
            if "extracted_entities" not in result:
                result = {"extracted_entities": []}
                
            print(f"🔍 Gemini extracted {len(result['extracted_entities'])} entities: {[e['name'] for e in result['extracted_entities']]}")
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"Raw response: {response.text}")
            # Fallback to empty result
            return {"extracted_entities": []}
        except Exception as e:
            print(f"❌ Gemini extraction failed: {e}")
            # Fallback to spaCy if available
            if self.nlp:
                print("🔄 Falling back to spaCy extraction")
                raw_output = self._extract_with_spacy(text)
                return {"extracted_entities": list(raw_output.values())}
            else:
                return {"extracted_entities": []}


if __name__ == "__main__":
    # Example run
    example_text = (
        "sundar pichai is the ceo of google."
    )

    agent = InfoExtractionAgent()
    result = agent.process_text(example_text)

    os.makedirs("src", exist_ok=True)
    with open("src/extracted_data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print("Extraction complete. Results written to src/extracted_data.json")
