"""LLM-based evidence optimization service

This module uses LLM to:
1. Optimize evidence text (ensure complete sentences, add context)
2. Extract KeyClaims from the evidence
3. Generate QuestionsRaised from the evidence
"""

import os
from typing import Dict, List, Tuple
import anthropic
import json


class EvidenceOptimizer:
    """Optimize evidence chunks using Claude LLM"""

    def __init__(self, api_key: str = None):
        """Initialize with Anthropic API key"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def optimize_evidence(
        self,
        chunk_text: str,
        previous_context: str = "",
        next_context: str = "",
        source_info: Dict = None
    ) -> Dict:
        """
        Optimize evidence chunk and extract KeyClaims and QuestionsRaised

        Args:
            chunk_text: The chunk text to optimize
            previous_context: Context from previous chunk (for continuity)
            next_context: Context from next chunk (for continuity)
            source_info: Information about the source document

        Returns:
            Dictionary with:
            - optimized_text: Improved text with complete sentences
            - key_claims: List of key claims extracted
            - questions_raised: List of questions raised by the text
        """
        source_context = ""
        if source_info:
            source_context = f"""
Document context:
- Title: {source_info.get('title', 'N/A')}
- Source: {source_info.get('source', 'N/A')}
- Type: {source_info.get('type', 'N/A')}
"""

        prompt = f"""You are an expert at analyzing and optimizing text evidence. Your task is to:

1. OPTIMIZE the chunk text to ensure:
   - Complete sentences (fix any cut-off at start/end using context)
   - Keep original meaning intact
   - Add minimal context if needed for clarity
   - DO NOT remove or significantly change content

2. EXTRACT Key Claims:
   - Identify 3-5 main factual claims or statements
   - Keep claims concise and specific
   - Focus on verifiable information

3. GENERATE Questions Raised:
   - What questions does this text naturally raise?
   - What follow-up information might be needed?
   - 2-4 questions maximum

{source_context}

CHUNK TEXT TO OPTIMIZE:
```
{chunk_text}
```

PREVIOUS CONTEXT (for reference):
```
{previous_context if previous_context else "(Start of document)"}
```

NEXT CONTEXT (for reference):
```
{next_context if next_context else "(End of document)"}
```

Please respond in JSON format:
{{
  "optimized_text": "The optimized text here...",
  "key_claims": [
    "Claim 1",
    "Claim 2",
    "Claim 3"
  ],
  "questions_raised": [
    "Question 1?",
    "Question 2?"
  ]
}}

IMPORTANT: Return ONLY the JSON object, no additional text."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text.strip()

            # Parse JSON response
            result = json.loads(response_text)

            return {
                "optimized_text": result.get("optimized_text", chunk_text),
                "key_claims": result.get("key_claims", []),
                "questions_raised": result.get("questions_raised", [])
            }

        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse LLM response as JSON: {e}")
            # Fallback: return original text
            return {
                "optimized_text": chunk_text,
                "key_claims": [],
                "questions_raised": []
            }

        except Exception as e:
            print(f"⚠️  Error optimizing evidence: {e}")
            return {
                "optimized_text": chunk_text,
                "key_claims": [],
                "questions_raised": []
            }

    def batch_optimize(
        self,
        chunks: List[Dict],
        source_info: Dict = None,
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Optimize multiple chunks in sequence

        Args:
            chunks: List of chunk dictionaries with 'text' field
            source_info: Information about source document
            show_progress: Show progress messages

        Returns:
            List of optimized chunks with additional fields
        """
        optimized_chunks = []

        for i, chunk in enumerate(chunks):
            if show_progress:
                print(f"🔄 Optimizing chunk {i+1}/{len(chunks)}...")

            # Get context from adjacent chunks
            prev_context = chunks[i-1]["text"][-200:] if i > 0 else ""
            next_context = chunks[i+1]["text"][:200] if i < len(chunks)-1 else ""

            # Optimize
            result = self.optimize_evidence(
                chunk_text=chunk["text"],
                previous_context=prev_context,
                next_context=next_context,
                source_info=source_info
            )

            # Create optimized chunk with all fields
            optimized_chunk = {
                **chunk,  # Keep all original fields (index, start_pos, end_pos, etc.)
                "optimized_text": result["optimized_text"],
                "key_claims": result["key_claims"],
                "questions_raised": result["questions_raised"]
            }

            optimized_chunks.append(optimized_chunk)

            if show_progress:
                print(f"  ✓ Claims: {len(result['key_claims'])}, Questions: {len(result['questions_raised'])}")

        return optimized_chunks


def optimize_single_chunk(
    chunk: Dict,
    previous_chunk: Dict = None,
    next_chunk: Dict = None,
    source_info: Dict = None,
    api_key: str = None
) -> Dict:
    """
    Convenience function to optimize a single chunk

    Args:
        chunk: Chunk dictionary with 'text' field
        previous_chunk: Previous chunk for context
        next_chunk: Next chunk for context
        source_info: Source document information
        api_key: Anthropic API key

    Returns:
        Optimized chunk dictionary
    """
    optimizer = EvidenceOptimizer(api_key=api_key)

    prev_context = previous_chunk["text"][-200:] if previous_chunk else ""
    next_context = next_chunk["text"][:200] if next_chunk else ""

    result = optimizer.optimize_evidence(
        chunk_text=chunk["text"],
        previous_context=prev_context,
        next_context=next_context,
        source_info=source_info
    )

    return {
        **chunk,
        "optimized_text": result["optimized_text"],
        "key_claims": result["key_claims"],
        "questions_raised": result["questions_raised"]
    }
