#!/usr/bin/env python3
"""
InfoExtractionAgent

A runnable Python script that performs simple information extraction from a single English
sentence using spaCy for NER and (optionally) neuralcoref for coreference resolution.

Notes:
- The script attempts to load `en_core_web_sm`. If it's not installed, it will instruct the user
  how to install it.
- The script tries to attach `neuralcoref` to the spaCy pipeline. If `neuralcoref` is not
  available or fails to attach, the script falls back to a lightweight heuristic pronoun
  resolution so it can still run.

This file defines the class `InfoExtractionAgent` with a `process_text(text)` method that
returns a dictionary matching the structure requested.

Example usage is included in the `if __name__ == "__main__"` block. The output JSON is
written to `extracted_data.json`.
"""

import json
import sys
from collections import defaultdict

try:
    import spacy
    from spacy.tokens import Span
except Exception as e:
    print("spaCy is not installed or couldn't be imported. Install with: pip install spacy")
    raise


class InfoExtractionAgent:
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Load spaCy model and attempt to attach neuralcoref (best-effort).

        If neuralcoref is unavailable, we'll continue without it and use a
        simple heuristic for linking pronouns to nearby entities.
        """
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            raise RuntimeError(
                f"spaCy model '{model_name}' not found. Install it with: python -m spacy download {model_name}"
            )

        # Try to attach neuralcoref if available (legacy package). This is optional.
        self.use_neuralcoref = False
        try:
            import neuralcoref  # type: ignore

            neuralcoref.add_to_pipe(self.nlp)
            self.use_neuralcoref = True
        except Exception:
            # neuralcoref often fails to install/attach for newer spaCy versions.
            # We'll fall back to a heuristic pronoun linking later.
            self.use_neuralcoref = False

    def _heuristic_coref(self, doc):
        """Simple heuristic coref resolver: maps pronoun spans to the nearest preceding
        named entity of a compatible type.

        Returns a dict: {pronoun_span_text: resolved_entity_span_text}
        """
        pronoun_to_entity = {}
        # Build a list of entities in order
        ents = list(doc.ents)
        # For every token that's a pronoun, find nearest preceding entity
        for tok in doc:
            if tok.pos_ == "PRON" and tok.tag_ in {"PRP", "PRP$"}:  # he, she, it, they, his, her
                # look backwards for an entity
                resolved = None
                for e in reversed(ents):
                    if e.end <= tok.i:  # entity ends before pronoun index
                        resolved = e
                        break
                if resolved:
                    pronoun_to_entity[tok.text] = resolved.text
        return pronoun_to_entity

    def _extract_specifications(self, ent_span, sent):
        """Extract short specifications/descriptors for an entity span from its sentence.

        Strategies used:
        - appositional phrases (appos)
        - noun chunks that contain the entity and adjacent modifiers
        - adjectival complements and adjectival modifiers
        - relative clauses (acl, relcl)
        - prepositional phrases immediately following the entity

        This function returns a list of strings (may be empty).
        """
        specs = []
        # tokens covering the entity
        start, end = ent_span.start, ent_span.end
        # 1) Check for appositions: tokens with dependency 'appos' that modify the entity
        for tok in sent:
            if tok.dep_ == "appos" and tok.head.i >= start and tok.head.i < end:
                specs.append(tok.text + ("" if tok.nbor(1).text == "," else ""))

        # 2) Look for adjectival modifiers (amod) within the entity noun chunk or adjacent
        for chunk in sent.noun_chunks:
            if ent_span.start >= chunk.start and ent_span.end <= chunk.end:
                # any amod inside this noun chunk
                for tok in chunk:
                    if tok.dep_ == "amod":
                        specs.append(tok.text)
                # also take the full noun chunk text (minus the entity itself) if it has extra words
                extra = [t.text for t in chunk if t.i < start or t.i >= end]
                if extra:
                    specs.append(" ".join(extra).strip())

        # 3) adjectival complement or predicate adjectives: e.g., "is a great engineer"
        for tok in sent:
            if tok.dep_ in {"acomp", "attr"}:
                # find subject attached
                subj = None
                for c in tok.children:
                    if c.dep_ in {"nsubj", "nsubjpass"}:
                        subj = c
                if subj:
                    # check if subject overlaps with entity
                    if subj.i >= start and subj.i < end:
                        # take the phrase around tok
                        specs.append(tok.subtree.__str__())
                    else:
                        # sometimes subject is a pronoun
                        # handled elsewhere via coref
                        pass

        # 4) prepositional phrases immediately following entity: "CEO of Apple"
        for tok in sent:
            # look for a token that's a preposition whose head is inside the entity
            if tok.dep_ == "prep" and tok.head.i >= start and tok.head.i < end:
                specs.append(tok.text + " " + " ".join([t.text for t in tok.subtree if t.i != tok.i]))

        # 5) relative clause modifiers (relcl) attached to the entity
        for tok in sent:
            if tok.dep_ == "relcl" and tok.head.i >= start and tok.head.i < end:
                specs.append(" ".join([t.text for t in tok.subtree]))

        # Clean specs: deduplicate and strip
        cleaned = []
        for s in specs:
            s_clean = s.strip().strip(",.")
            if s_clean and s_clean not in cleaned:
                cleaned.append(s_clean)
        return cleaned

    def process_text(self, text: str) -> dict:
        """Process text and return a structured dictionary of extracted entities.

        Output schema:
        {
            "extracted_entities": [
                {
                    "name": ..., "type": ..., "specifications": [...], "original_mentions": [...]
                }, ...
            ]
        }
        """
        doc = self.nlp(text)

        # Prepare mapping from canonical entity text -> data
        entities = {}

        # 1) Seed entities from NER
        for ent in doc.ents:
            key = ent.text
            if key not in entities:
                entities[key] = {
                    "name": ent.text,
                    "type": ent.label_,
                    "specifications": [],
                    "original_mentions": [ent.text],
                    "span": ent,
                }
            else:
                entities[key]["original_mentions"].append(ent.text)

        # 2) Coreference resolution
        pronoun_map = {}
        if self.use_neuralcoref and hasattr(doc._, "coref_clusters"):
            try:
                for cluster in doc._.coref_clusters:
                    main = cluster.main.text
                    # ensure main exists in entities, or create a placeholder
                    if main not in entities:
                        # If the main mention was not tagged by NER, create an entry
                        entities[main] = {
                            "name": main,
                            "type": "UNKNOWN",
                            "specifications": [],
                            "original_mentions": [main],
                            "span": None,
                        }
                    for mention in cluster.mentions:
                        m_text = mention.text
                        if m_text == main:
                            continue
                        entities[main]["original_mentions"].append(m_text)
                        # record pronoun mapping for later specification extraction
                        if mention.root.pos_ == "PRON":
                            pronoun_map[m_text] = main
            except Exception:
                # if neuralcoref fails here, fallback
                pronoun_map = self._heuristic_coref(doc)
        else:
            pronoun_map = self._heuristic_coref(doc)

        # 3) For any pronouns mapped to entity names, add the pronoun forms to original_mentions
        for pronoun, resolved in pronoun_map.items():
            if resolved in entities:
                if pronoun not in entities[resolved]["original_mentions"]:
                    entities[resolved]["original_mentions"].append(pronoun)
            else:
                # if resolved entity wasn't an NER result, create placeholder
                entities[resolved] = {
                    "name": resolved,
                    "type": "UNKNOWN",
                    "specifications": [],
                    "original_mentions": [resolved, pronoun],
                    "span": None,
                }

        # 4) Extract specifications for each entity using dependency patterns
        # We'll attempt to find the sentence that contains the canonical mention
        for key, info in list(entities.items()):
            span = info.get("span")
            sent = None
            if span is not None:
                sent = span.sent
            else:
                # try to locate any occurrence of the name in the doc
                for try_span in doc.ents:
                    if try_span.text == key:
                        sent = try_span.sent
                        break
            if sent is None:
                # fallback: use the whole doc
                sent = doc
            # get specifications
            specs = []
            if span is not None:
                specs = self._extract_specifications(span, sent)
            else:
                # try to find a token span that matches the name
                for token in sent:
                    if token.text == key:
                        pseudo_span = Span(doc, token.i, token.i + 1)
                        specs = self._extract_specifications(pseudo_span, sent)
                        break
            info["specifications"] = specs

        # 5) Final formatting: remove internal span objects
        out_entities = []
        for info in entities.values():
            out_entities.append(
                {
                    "name": info["name"],
                    "type": info["type"],
                    "specifications": info.get("specifications", []),
                    "original_mentions": list(dict.fromkeys(info.get("original_mentions", []))),
                }
            )

        return {"extracted_entities": out_entities}


if __name__ == "__main__":
    # Demonstrate the agent with the example input from the prompt
    example_text = (
        "Tim Cook is the CEO of Apple. He is known for his work in supply chain management and is a very good dancer."
    )

    agent = InfoExtractionAgent()
    result = agent.process_text(example_text)

    # Save to JSON file
    with open("extracted_data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print("Extraction complete. Results written to extracted_data.json")
