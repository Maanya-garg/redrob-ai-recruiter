"""
Utility Functions Module
Provides pure-Python string similarity and date parsing utilities.
"""

from datetime import date
import math


def jaro_similarity(s1: str, s2: str) -> float:
    """Calculates Jaro Similarity between two strings."""
    s1_len = len(s1)
    s2_len = len(s2)

    if s1_len == 0 and s2_len == 0:
        return 1.0
    if s1_len == 0 or s2_len == 0:
        return 0.0

    # Maximum distance for matching characters
    match_distance = max(s1_len, s2_len) // 2 - 1
    if match_distance < 0:
        match_distance = 0

    s1_matches = [False] * s1_len
    s2_matches = [False] * s2_len

    matches = 0
    transpositions = 0

    # Find matching characters
    for i in range(s1_len):
        start = max(0, i - match_distance)
        end = min(s2_len, i + match_distance + 1)
        for j in range(start, end):
            if s2_matches[j]:
                continue
            if s1[i] == s2[j]:
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break

    if matches == 0:
        return 0.0

    # Count transpositions
    k = 0
    for i in range(s1_len):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    transpositions //= 2

    return (matches / s1_len + matches / s2_len + (matches - transpositions) / matches) / 3.0


def jaro_winkler_similarity(s1: str, s2: str, scaling=0.1) -> float:
    """Calculates Jaro-Winkler Similarity between two strings."""
    s1 = s1.strip().lower()
    s2 = s2.strip().lower()
    
    j_sim = jaro_similarity(s1, s2)
    
    # Calculate common prefix length (up to 4 characters)
    prefix_len = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2:
            prefix_len += 1
        else:
            break
        if prefix_len == 4:
            break
            
    return j_sim + prefix_len * scaling * (1.0 - j_sim)


def safe_date_parse(date_str: str) -> date:
    """Safely parse a date string in YYYY-MM-DD format."""
    try:
        return date.fromisoformat(date_str)
    except Exception:
        return date(2000, 1, 1)


def get_token_cosine_similarity(text1: str, text2: str) -> float:
    """Computes a simple token-based cosine similarity."""
    def get_tokens(text: str):
        return [w for w in re.split(r"\W+", text.lower()) if w]

    import re
    tokens1 = get_tokens(text1)
    tokens2 = get_tokens(text2)

    if not tokens1 or not tokens2:
        return 0.0

    vocab = set(tokens1 + tokens2)
    freq1 = {word: tokens1.count(word) for word in vocab}
    freq2 = {word: tokens2.count(word) for word in vocab}

    dot_product = sum(freq1[word] * freq2[word] for word in vocab)
    norm1 = math.sqrt(sum(freq1[word] ** 2 for word in vocab))
    norm2 = math.sqrt(sum(freq2[word] ** 2 for word in vocab))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)
