
from typing import List, Dict
from .config import PROJECT_ID, LOCATION, GEMINI_MODEL, MAX_TOKENS, TEMPERATURE
from google import genai
from google.genai import types
from .reranking import rerank
from .base import Chunk

system_prompt = """
You are a helpful assistant that provides answers based only on the provided context.

STRICT RULES:
1. Use ONLY the information present in the provided CONTEXT.
2. Do NOT invent or assume missing values.
3. If any part of the answer is incomplete in the context, state:
   "These are the information present in the document."
4. When answering:
   - Preserve full tables exactly as written.
   - Do not truncate rows.
   - Present structured data clearly in table format.
5. If answer is not found, respond exactly:
   "Not found in document."
6. Do NOT summarize unless explicitly asked.
7. Ensure the answer is complete and fully readable before finishing.
"""



def _format_chunks(chunks: List[Dict]) -> str:
    parts: List[str] = []
    for i, c in enumerate(chunks, start=1):
        cid = c.get("id", "")
        src = c.get("source", "")
        page = c.get("page", "")
        text = c.get("chunk_text", c.get("text", ""))
        parts.append(f"[{i}] id={cid} source={src} page={page}\n{text}")
    return "\n\n".join(parts)



def generate_answer(query: str, chunks: List[Dict]) -> str:
    query = query.strip()
    if not query:
        return "Empty query provided."
    if not chunks:
        return "No relevant information found in the documents."

    
    client = genai.Client(
		vertexai=True, project=PROJECT_ID, location=LOCATION
        )
    

    prompt = f"""{system_prompt}

		CONTEXT:
		{_format_chunks(chunks)}

		USER QUERY:
		{query}
		"""

    response = client.models.generate_content(
		model=GEMINI_MODEL,
		contents=prompt,
		config=types.GenerateContentConfig(
			temperature=TEMPERATURE,
			top_p=0.95,
			top_k=20,
		),
	)


    return response.text



# if __name__ == "__main__":
    
#     query = "What are AI applications in mental health?"
#     chunks = rerank(query)
#     print(f"reranked_chunks={len(chunks)}")
#     ans = generate_answer(query, chunks)
#     print(f"Final response: {ans}")
    



