import re
from collections import Counter


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def score_chunk(chunk: str, question: str) -> int:
    chunk_words = Counter(tokenize(chunk))
    question_words = tokenize(question)
    return sum(chunk_words[word] for word in question_words)


def retrieve_relevant_chunks(chunks: list[str], question: str, top_k: int = 5) -> list[str]:
    if not chunks:
        return []

    scored = [(chunk, score_chunk(chunk, question)) for chunk in chunks]
    scored = [item for item in scored if item[1] > 0]
    ranked_chunks = sorted(scored, key=lambda x: x[1], reverse=True)

    if not ranked_chunks:
        return chunks[:1]

    return [chunk for chunk, _ in ranked_chunks[:top_k]]