from entityExtractor import InfoExtractionAgent

agent = InfoExtractionAgent()
text = "Elon Musk founded SpaceX. He also runs Tesla."
result = agent.process_text(text)
print(result)
