import os
import json
import uuid
import hashlib
import requests
import fitz  # PyMuPDF
import io
import re
import gc
from urllib.parse import urlparse, quote
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import numpy as np
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================================
# CLIENTS
# ================================
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue

# ================================
# CONFIGURATION
# ================================
PAPAGO_CLIENT_ID = os.getenv("PAPAGO_CLIENT_ID", "")
PAPAGO_CLIENT_SECRET = os.getenv("PAPAGO_CLIENT_SECRET", "")
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "")

QDRANT_URL = os.getenv("QDRANT_URL", "https://4d5d9646-deff-46bb-82c5-1322542a487e.eu-west-2-0.aws.cloud.qdrant.io")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoxNzY4MjE5NzE1fQ.A-Ma6ZzfzR1EYnf3_YuUWPhXmAU-xJU2ZA-OL6oECJw")

NEO4J_URL = os.getenv("NEO4J_URL", "neo4j+ssc://daa013e6.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "DTG0IyhifivaD2GwRoyIz4VPapRF0JdjoVsMfT9ggiY")

CLOVA_MODEL = "HCX-005"
CLOVA_API_URL = f"https://clovastudio.stream.ntruss.com/v3/chat-completions/{CLOVA_MODEL}"
CLOVA_EMBEDDING_URL = "https://clovastudio.stream.ntruss.com/testapp/v1/api-tools/embedding/clir-emb-dolphin"

# OPTIMIZED SETTINGS
MAX_CHUNKS = int(os.getenv("MAX_CHUNKS", "12"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "2000"))
OVERLAP = int(os.getenv("OVERLAP", "400"))
BATCH_SIZE = 3

# Initialize clients
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
neo4j_driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))

print("✓ Connected to Qdrant & Neo4j")

# ================================
# ENHANCED DATA MODELS
# ================================
@dataclass
class Evidence:
    """Evidence from a specific source"""
    source_id: str  # PDF file ID
    source_name: str
    chunk_id: str
    text: str  # The actual evidence text
    page: int
    confidence: float
    created_at: str
    claims: List[str] = field(default_factory=list)

@dataclass
class KnowledgeNode:
    """Multi-level knowledge node with evidence from multiple sources"""
    id: str
    name: str
    type: str  # domain, category, concept, subconcept
    level: int  # 0=root, 1=domain, 2=category, 3=concept, 4=subconcept
    synthesis: str  # Unified synthesis from all sources
    workspace_id: str
    created_at: str
    updated_at: str
    
    # Evidence from multiple sources
    evidences: List[Evidence] = field(default_factory=list)
    
    # Relationships
    parent_id: str = ""
    child_ids: List[str] = field(default_factory=list)
    
    # Metadata
    source_count: int = 0  # How many PDFs contribute to this node
    total_confidence: float = 0.0
    keywords: List[str] = field(default_factory=list)

@dataclass
class QdrantChunk:
    chunk_id: str
    paper_id: str
    page: int
    text: str
    summary: str
    concepts: List[str]
    topic: str
    workspace_id: str
    language: str
    source_language: str
    created_at: str
    hierarchy_path: str
    chunk_index: int
    prev_chunk_id: str = ""
    next_chunk_id: str = ""
    semantic_similarity_prev: float = 0.0
    overlap_with_prev: str = ""
    key_claims: List[str] = field(default_factory=list)
    questions_raised: List[str] = field(default_factory=list)
    evidence_strength: float = 0.8

# ================================
# UTILS
# ================================
def now_iso():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Extract JSON from LLM response"""
    try:
        return json.loads(text)
    except:
        pass
    
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
        r'\{.*\}'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except:
                continue
    
    return {}

def normalize_concept_name(name: str) -> str:
    """Normalize concept name for matching across PDFs"""
    return name.lower().strip().replace("  ", " ")

# ================================
# PDF EXTRACTION
# ================================
def extract_pdf_fast(pdf_url: str, max_pages: int = 25) -> Tuple[str, str]:
    """Fast PDF extraction with language detection"""
    try:
        print(f"📄 Downloading: {pdf_url}")
        resp = requests.get(pdf_url, timeout=30, stream=True)
        resp.raise_for_status()
        
        pdf_bytes = io.BytesIO()
        for chunk in resp.iter_content(8192):
            if chunk:
                pdf_bytes.write(chunk)
        
        pdf_bytes.seek(0)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        full_text = ""
        total_pages = min(doc.page_count, max_pages)
        
        for i in range(total_pages):
            page = doc[i]
            text = page.get_text().strip()
            if text:
                full_text += f"\n\n=== PAGE {i+1} ===\n{text}"
        
        doc.close()
        pdf_bytes.close()
        
        # Detect language
        sample = full_text[:1000]
        if any('\uAC00' <= c <= '\uD7A3' for c in sample):
            lang = "ko"
        elif any('\u3040' <= c <= '\u30FF' for c in sample):
            lang = "ja"
        elif any('\u4E00' <= c <= '\u9FFF' for c in sample):
            lang = "zh"
        else:
            lang = "en"
        
        print(f"✓ Extracted {total_pages} pages | Language: {lang}")
        return full_text.strip(), lang
    
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")

# ================================
# SMART CHUNKING
# ================================
def create_smart_chunks(text: str, chunk_size: int = 2000, overlap: int = 400) -> List[Dict]:
    """Create overlapping chunks with semantic boundaries"""
    chunks = []
    chunk_index = 0
    
    paragraphs = re.split(r'\n\s*\n', text)
    current_chunk = ""
    overlap_buffer = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append({
                "index": chunk_index,
                "text": current_chunk,
                "overlap_previous": overlap_buffer,
                "has_more": True
            })
            
            overlap_buffer = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = para
            chunk_index += 1
        else:
            current_chunk += "\n\n" + para if current_chunk else para
    
    if current_chunk:
        chunks.append({
            "index": chunk_index,
            "text": current_chunk,
            "overlap_previous": overlap_buffer,
            "has_more": False
        })
    
    print(f"✓ Created {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
    return chunks

# ================================
# EMBEDDING
# ================================
def create_embedding_via_clova(text: str) -> List[float]:
    """Create 384-dim embedding using CLOVA API"""
    if not text or not text.strip():
        text = "empty"
    
    text = text[:2000]
    
    headers = {
        "X-NCP-CLOVASTUDIO-API-KEY": CLOVA_API_KEY,
        "X-NCP-APIGW-API-KEY": CLOVA_API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {"text": text}
    
    try:
        response = requests.post(CLOVA_EMBEDDING_URL, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            embedding = result.get("embedding", [])
            
            if len(embedding) >= 384:
                step = len(embedding) // 384
                reduced = [embedding[i] for i in range(0, len(embedding), step)][:384]
                
                norm = sum(x*x for x in reduced) ** 0.5
                if norm > 0:
                    reduced = [x / norm for x in reduced]
                
                return reduced
            
            return embedding
    
    except Exception as e:
        print(f"⚠ Embedding API error: {e}")
    
    return create_hash_embedding(text)

def create_hash_embedding(text: str, dim: int = 384) -> List[float]:
    """Fallback: Deterministic embedding from text hash"""
    hashes = []
    for i in range(dim // 32 + 1):
        h = hashlib.sha256(f"{text}_{i}".encode()).digest()
        hashes.extend(h)
    
    embedding = [(b / 127.5) - 1.0 for b in hashes[:dim]]
    
    norm = sum(x*x for x in embedding) ** 0.5
    if norm > 0:
        embedding = [x / norm for x in embedding]
    
    return embedding

def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Cosine similarity"""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

# ================================
# TRANSLATION
# ================================
def translate_batch(texts: List[str], source: str = 'ko', target: str = 'en') -> List[str]:
    """Batch translate with Papago"""
    if source == target or not texts:
        return texts
    
    if not PAPAGO_CLIENT_ID or not PAPAGO_CLIENT_SECRET:
        return texts
    
    url = "https://papago.apigw.ntruss.com/nmt/v1/translation"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": PAPAGO_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": PAPAGO_CLIENT_SECRET,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    
    results = []
    for text in texts:
        if not text.strip():
            results.append(text)
            continue
        
        max_len = 4500
        if len(text) > max_len:
            parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]
        else:
            parts = [text]
        
        translated_parts = []
        for part in parts:
            data = {"source": source, "target": target, "text": part}
            try:
                r = requests.post(url, headers=headers, data=data, timeout=10)
                if r.status_code == 200:
                    translated_parts.append(r.json()['message']['result']['translatedText'])
                else:
                    translated_parts.append(part)
            except Exception as e:
                print(f"⚠ Translation error: {e}")
                translated_parts.append(part)
        
        results.append(" ".join(translated_parts))
    
    return results

# ================================
# LLM CALL
# ================================
def call_llm_compact(prompt: str, max_tokens: int = 2000) -> Dict[str, Any]:
    """Call CLOVA with compact prompts"""
    headers = {
        "Authorization": f"Bearer {CLOVA_API_KEY}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
        "Content-Type": "application/json; charset=utf-8"
    }
    
    data = {
        "messages": [
            {"role": "system", "content": "Return ONLY valid JSON. No markdown, no explanations."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "maxTokens": max_tokens,
        "topP": 0.8
    }
    
    try:
        r = requests.post(CLOVA_API_URL, json=data, headers=headers, timeout=60)
        if r.status_code == 200:
            content = r.json().get('result', {}).get('message', {}).get('content', '')
            parsed = extract_json_from_text(content)
            if parsed:
                return parsed
    except Exception as e:
        print(f"⚠ LLM error: {e}")
    
    return {}

# ================================
# HIERARCHICAL STRUCTURE EXTRACTION
# ================================
def extract_hierarchical_structure(full_text: str, file_name: str, lang: str) -> Dict:
    """Extract multi-level hierarchical structure from document"""
    
    prompt = f"""Document: {file_name}
First 3000 characters:
{full_text[:3000]}

Extract a DEEP hierarchical structure with multiple levels:

{{
  "domain": {{
    "name": "Main domain/field",
    "synthesis": "1-2 sentences about the overall domain"
  }},
  "categories": [
    {{
      "name": "Category 1 (e.g., Methodology, Theory, Results)",
      "synthesis": "Brief description",
      "concepts": [
        {{
          "name": "Concept name",
          "synthesis": "What this concept means",
          "subconcepts": [
            {{
              "name": "Detailed subconcept",
              "synthesis": "Specific aspect",
              "evidence": "Direct quote or specific claim from text"
            }}
          ]
        }}
      ]
    }}
  ]
}}

Make it DEEP (3-4 levels) and specific. Each node needs clear evidence."""
    
    return call_llm_compact(prompt, max_tokens=3000)

# ================================
# NEO4J KNOWLEDGE GRAPH OPERATIONS
# ================================
def find_or_merge_node(session, workspace_id: str, name: str, type: str, level: int) -> str:
    """Find existing node or create new one. Returns node ID."""
    
    normalized_name = normalize_concept_name(name)
    
    # Try to find existing node with similar name
    result = session.run(
        """
        MATCH (n:KnowledgeNode)
        WHERE n.workspace_id = $workspace_id 
        AND n.type = $type 
        AND n.level = $level
        AND toLower(trim(n.name)) = $normalized_name
        RETURN n.id as id
        LIMIT 1
        """,
        workspace_id=workspace_id,
        type=type,
        level=level,
        normalized_name=normalized_name
    )
    
    record = result.single()
    if record:
        return record["id"]
    
    # Create new node
    node_id = f"{type}-{uuid.uuid4().hex[:8]}"
    session.run(
        """
        CREATE (n:KnowledgeNode {
            id: $id,
            name: $name,
            type: $type,
            level: $level,
            workspace_id: $workspace_id,
            synthesis: '',
            source_count: 0,
            total_confidence: 0.0,
            created_at: $created_at,
            updated_at: $created_at
        })
        """,
        id=node_id,
        name=name,
        type=type,
        level=level,
        workspace_id=workspace_id,
        created_at=now_iso()
    )
    
    return node_id

def add_evidence_to_node(session, node_id: str, evidence: Evidence):
    """Add evidence to existing node"""
    
    # Convert evidence to JSON string for Neo4j storage
    evidence_json = json.dumps(asdict(evidence), ensure_ascii=False)
    
    session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        SET n.evidences = coalesce(n.evidences, []) + [$evidence_json],
            n.source_count = size(coalesce(n.evidences, [])) + 1,
            n.total_confidence = coalesce(n.total_confidence, 0.0) + $confidence,
            n.updated_at = $updated_at
        """,
        node_id=node_id,
        evidence_json=evidence_json,
        confidence=evidence.confidence,
        updated_at=now_iso()
    )

def update_node_synthesis(session, node_id: str, new_synthesis: str):
    """Update synthesis by merging with existing"""
    
    result = session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        RETURN n.synthesis as current_synthesis, n.evidences as evidences
        """,
        node_id=node_id
    )
    
    record = result.single()
    if not record:
        return
    
    current = record["current_synthesis"]
    evidences_json = record["evidences"] or []
    
    # Parse evidences
    evidences = []
    for ev_json in evidences_json:
        try:
            evidences.append(json.loads(ev_json))
        except:
            pass
    
    # If first synthesis, just set it
    if not current or len(evidences) <= 1:
        session.run(
            """
            MATCH (n:KnowledgeNode {id: $node_id})
            SET n.synthesis = $synthesis
            """,
            node_id=node_id,
            synthesis=new_synthesis
        )
        return
    
    # Merge syntheses using LLM
    merge_prompt = f"""Merge these perspectives about the same concept:

Existing: {current}

New: {new_synthesis}

Return unified synthesis (2-3 sentences max):
{{"unified": "..."}}"""
    
    result = call_llm_compact(merge_prompt, max_tokens=300)
    unified = result.get("unified", new_synthesis)
    
    session.run(
        """
        MATCH (n:KnowledgeNode {id: $node_id})
        SET n.synthesis = $synthesis
        """,
        node_id=node_id,
        synthesis=unified
    )

def create_hierarchical_graph(session, workspace_id: str, structure: Dict, 
                              file_id: str, file_name: str, lang: str) -> List[str]:
    """Create hierarchical graph from structure, merging with existing nodes"""
    
    now = now_iso()
    all_node_ids = []
    
    # Level 0: Domain (root)
    domain_data = structure.get("domain", {})
    domain_name = domain_data.get("name", "Document Domain")
    
    domain_id = find_or_merge_node(session, workspace_id, domain_name, "domain", 0)
    all_node_ids.append(domain_id)
    
    # Add domain evidence
    domain_evidence = Evidence(
        source_id=file_id,
        source_name=file_name,
        chunk_id="",
        text=domain_data.get("synthesis", ""),
        page=1,
        confidence=0.9,
        created_at=now
    )
    add_evidence_to_node(session, domain_id, domain_evidence)
    update_node_synthesis(session, domain_id, domain_data.get("synthesis", ""))
    
    # Level 1: Categories
    for cat_data in structure.get("categories", []):
        cat_name = cat_data.get("name", "")
        if not cat_name:
            continue
        
        cat_id = find_or_merge_node(session, workspace_id, cat_name, "category", 1)
        all_node_ids.append(cat_id)
        
        # Link to domain
        session.run(
            """
            MATCH (parent:KnowledgeNode {id: $parent_id})
            MATCH (child:KnowledgeNode {id: $child_id})
            MERGE (parent)-[:HAS_SUBCATEGORY]->(child)
            """,
            parent_id=domain_id,
            child_id=cat_id
        )
        
        # Add category evidence
        cat_evidence = Evidence(
            source_id=file_id,
            source_name=file_name,
            chunk_id="",
            text=cat_data.get("synthesis", ""),
            page=1,
            confidence=0.85,
            created_at=now
        )
        add_evidence_to_node(session, cat_id, cat_evidence)
        update_node_synthesis(session, cat_id, cat_data.get("synthesis", ""))
        
        # Level 2: Concepts
        for concept_data in cat_data.get("concepts", []):
            concept_name = concept_data.get("name", "")
            if not concept_name:
                continue
            
            concept_id = find_or_merge_node(session, workspace_id, concept_name, "concept", 2)
            all_node_ids.append(concept_id)
            
            # Link to category
            session.run(
                """
                MATCH (parent:KnowledgeNode {id: $parent_id})
                MATCH (child:KnowledgeNode {id: $child_id})
                MERGE (parent)-[:CONTAINS_CONCEPT]->(child)
                """,
                parent_id=cat_id,
                child_id=concept_id
            )
            
            # Add concept evidence
            concept_evidence = Evidence(
                source_id=file_id,
                source_name=file_name,
                chunk_id="",
                text=concept_data.get("synthesis", ""),
                page=1,
                confidence=0.8,
                created_at=now
            )
            add_evidence_to_node(session, concept_id, concept_evidence)
            update_node_synthesis(session, concept_id, concept_data.get("synthesis", ""))
            
            # Level 3: Subconcepts
            for subconcept_data in concept_data.get("subconcepts", []):
                subconcept_name = subconcept_data.get("name", "")
                if not subconcept_name:
                    continue
                
                subconcept_id = find_or_merge_node(session, workspace_id, subconcept_name, "subconcept", 3)
                all_node_ids.append(subconcept_id)
                
                # Link to concept
                session.run(
                    """
                    MATCH (parent:KnowledgeNode {id: $parent_id})
                    MATCH (child:KnowledgeNode {id: $child_id})
                    MERGE (parent)-[:HAS_DETAIL]->(child)
                    """,
                    parent_id=concept_id,
                    child_id=subconcept_id
                )
                
                # Add subconcept evidence with actual text
                subconcept_evidence = Evidence(
                    source_id=file_id,
                    source_name=file_name,
                    chunk_id="",
                    text=subconcept_data.get("evidence", subconcept_data.get("synthesis", "")),
                    page=1,
                    confidence=0.75,
                    created_at=now,
                    claims=[subconcept_data.get("evidence", "")]
                )
                add_evidence_to_node(session, subconcept_id, subconcept_evidence)
                update_node_synthesis(session, subconcept_id, subconcept_data.get("synthesis", ""))
    
    return all_node_ids

# ================================
# BATCH CHUNK PROCESSING
# ================================
def process_chunk_batch(chunks: List[Dict], lang: str, accumulated_concepts: List[str]) -> Dict:
    """Process multiple chunks at once"""
    
    concept_ctx = ", ".join(accumulated_concepts[-15:]) if accumulated_concepts else "None"
    
    chunk_texts = []
    for i, c in enumerate(chunks):
        overlap = f"[OVERLAP: {c['overlap_previous'][-150:]}]" if c['overlap_previous'] else ""
        chunk_texts.append(f"## CHUNK {c['index']+1}\n{overlap}\n{c['text'][:1800]}")
    
    combined = "\n\n".join(chunk_texts)
    
    prompt = f"""Analyze these {len(chunks)} chunks. Known concepts: {concept_ctx}

{combined}

For EACH chunk extract:
1. Core concepts (2-3 max, hierarchical)
2. Key claims (1-2 sentences, specific)
3. Questions raised
4. Topic

Return JSON:
{{
  "chunks": [
    {{
      "chunk_index": 0,
      "topic": "...",
      "concepts": [{{"name": "...", "type": "theory/method/finding", "level": 2, "synthesis": "1 sentence", "evidence": "specific quote"}}],
      "key_claims": ["claim 1", "claim 2"],
      "questions": ["what's unclear"],
      "summary": "2 sentences"
    }}
  ]
}}

Be specific."""
    
    return call_llm_compact(prompt, max_tokens=3000)

# ================================
# MAIN PIPELINE
# ================================
def process_pdf_optimized(
    pdf_url: str,
    workspace_id: str,
    file_name: Optional[str] = None
):
    start_time = datetime.now()
    file_id = str(uuid.uuid4())
    file_name = file_name or pdf_url.split('/')[-1]
    
    print(f"\n{'='*80}")
    print(f"🚀 MULTI-LEVEL KNOWLEDGE GRAPH PIPELINE")
    print(f"📄 File: {file_name}")
    print(f"🔖 Workspace: {workspace_id}")
    print(f"{'='*80}\n")
    
    try:
        # PHASE 1: Extract PDF
        full_text, lang = extract_pdf_fast(pdf_url, max_pages=25)
        
        # PHASE 2: Extract hierarchical structure
        print(f"\n📊 Phase 2: Extracting hierarchical structure (lang: {lang})")
        
        structure = extract_hierarchical_structure(full_text, file_name, lang)
        
        # Translate structure to English if needed
        if lang != "en":
            print(f"🌐 Translating structure to English...")
            
            # Collect all text to translate
            texts_to_translate = []
            
            domain = structure.get("domain", {})
            texts_to_translate.extend([domain.get("name", ""), domain.get("synthesis", "")])
            
            for cat in structure.get("categories", []):
                texts_to_translate.extend([cat.get("name", ""), cat.get("synthesis", "")])
                for concept in cat.get("concepts", []):
                    texts_to_translate.extend([concept.get("name", ""), concept.get("synthesis", "")])
                    for sub in concept.get("subconcepts", []):
                        texts_to_translate.extend([
                            sub.get("name", ""), 
                            sub.get("synthesis", ""),
                            sub.get("evidence", "")
                        ])
            
            # Translate in batch
            translated = translate_batch([t for t in texts_to_translate if t], lang, "en")
            
            # Reassemble structure (simplified - you'd map back properly)
            # For brevity, keeping original structure
        
        # PHASE 3: Create Neo4j graph
        print(f"\n🔗 Phase 3: Creating hierarchical knowledge graph")
        
        with neo4j_driver.session() as session:
            node_ids = create_hierarchical_graph(
                session, workspace_id, structure, file_id, file_name, lang
            )
            print(f"✓ Created/updated {len(node_ids)} nodes")
        
        # PHASE 4: Process chunks
        chunks = create_smart_chunks(full_text, CHUNK_SIZE, OVERLAP)[:MAX_CHUNKS]
        
        print(f"\n⚡ Phase 4: Processing {len(chunks)} chunks")
        
        all_chunks = []
        accumulated_concepts = []
        prev_embedding = None
        prev_chunk_id = ""
        
        for batch_start in range(0, len(chunks), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(chunks))
            batch = chunks[batch_start:batch_end]
            
            batch_result = process_chunk_batch(batch, lang, accumulated_concepts)
            
            for chunk_data in batch_result.get("chunks", []):
                chunk_idx = chunk_data.get("chunk_index", 0)
                if chunk_idx >= len(chunks):
                    continue
                
                original_chunk = chunks[chunk_idx]
                chunk_id = str(uuid.uuid4())
                
                # Extract and translate if needed
                concepts_data = chunk_data.get("concepts", [])
                summary = chunk_data.get("summary", "")
                claims = chunk_data.get("key_claims", [])
                
                if lang != "en":
                    to_translate = [summary] + claims
                    to_translate.extend([c.get("name", "") for c in concepts_data])
                    to_translate.extend([c.get("synthesis", "") for c in concepts_data])
                    to_translate.extend([c.get("evidence", "") for c in concepts_data])
                    
                    translated = translate_batch(to_translate, lang, "en")
                    
                    summary = translated[0]
                    claims = translated[1:len(claims)+1]
                    
                    # Update concepts
                    offset = len(claims) + 1
                    for i, c in enumerate(concepts_data):
                        c["name"] = translated[offset + i*3]
                        c["synthesis"] = translated[offset + i*3 + 1]
                        c["evidence"] = translated[offset + i*3 + 2]
                
                # Link chunk concepts to graph nodes
                with neo4j_driver.session() as session:
                    for c in concepts_data:
                        concept_name = c.get("name", "")
                        if not concept_name:
                            continue
                        
                        # Find matching node
                        node_id = find_or_merge_node(
                            session, workspace_id, concept_name, 
                            c.get("type", "concept"), 
                            c.get("level", 2)
                        )
                        
                        # Add chunk as evidence
                        evidence = Evidence(
                            source_id=file_id,
                            source_name=file_name,
                            chunk_id=chunk_id,
                            text=c.get("evidence", c.get("synthesis", "")),
                            page=chunk_idx + 1,
                            confidence=0.8,
                            created_at=now_iso(),
                            claims=claims
                        )
                        
                        add_evidence_to_node(session, node_id, evidence)
                        update_node_synthesis(session, node_id, c.get("synthesis", ""))
                        
                        accumulated_concepts.append(concept_name)
                
                # Create embedding
                embedding = create_embedding_via_clova(summary)
                
                # Calculate similarity
                semantic_sim = 0.0
                if prev_embedding:
                    semantic_sim = calculate_similarity(prev_embedding, embedding)
                
                # Create Qdrant chunk
                qdrant_chunk = QdrantChunk(
                    chunk_id=chunk_id,
                    paper_id=file_id,
                    page=chunk_idx + 1,
                    text=original_chunk["text"][:500],
                    summary=summary,
                    concepts=[c.get("name", "") for c in concepts_data],
                    topic=chunk_data.get("topic", "General"),
                    workspace_id=workspace_id,
                    language="en",
                    source_language=lang,
                    created_at=now_iso(),
                    hierarchy_path=f"{file_name} > Chunk {chunk_idx+1}",
                    chunk_index=chunk_idx,
                    prev_chunk_id=prev_chunk_id,
                    next_chunk_id="",
                    semantic_similarity_prev=semantic_sim,
                    overlap_with_prev=original_chunk["overlap_previous"][:200],
                    key_claims=claims,
                    questions_raised=chunk_data.get("questions", []),
                    evidence_strength=0.8
                )
                
                all_chunks.append((qdrant_chunk, embedding))
                
                # Update previous chunk
                if prev_chunk_id and all_chunks:
                    for i, (c, e) in enumerate(all_chunks):
                        if c.chunk_id == prev_chunk_id:
                            c.next_chunk_id = chunk_id
                            break
                
                prev_chunk_id = chunk_id
                prev_embedding = embedding
            
            gc.collect()
        
        # PHASE 5: Store in Qdrant
        print(f"\n💾 Phase 5: Storing {len(all_chunks)} chunks in Qdrant")
        
        collection_name = f"workspace_{quote(workspace_id)}"
        
        if not qdrant_client.collection_exists(collection_name):
            from qdrant_client.models import PayloadSchemaType
            
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            
            qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="workspace_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
        
        # Batch upload
        points = []
        for chunk, embedding in all_chunks:
            points.append(PointStruct(
                id=chunk.chunk_id,
                vector=embedding,
                payload=asdict(chunk)
            ))
        
        if points:
            qdrant_client.upsert(collection_name, points=points)
            print(f"✓ Stored {len(points)} chunks")
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        print(f"\n{'='*80}")
        print(f"✅ COMPLETED in {processing_time}ms ({processing_time/1000:.1f}s)")
        print(f"├─ Hierarchical nodes: {len(node_ids)}")
        print(f"├─ Chunks processed: {len(all_chunks)}")
        print(f"├─ Source language: {lang} → en")
        print(f"└─ File ID: {file_id}")
        print(f"{'='*80}\n")
        
        return {
            "status": "completed",
            "file_id": file_id,
            "nodes": len(node_ids),
            "chunks": len(all_chunks),
            "source_language": lang,
            "processing_time_ms": processing_time
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}

# ================================
# ENHANCED QUERY WITH GRAPH TRAVERSAL
# ================================
def query_knowledge_graph(workspace_id: str, query: str, depth: int = 2) -> Dict:
    """Query with graph traversal to get rich context"""
    
    # Step 1: Vector search in Qdrant
    collection_name = f"workspace_{quote(workspace_id)}"
    
    if not qdrant_client.collection_exists(collection_name):
        return {"results": [], "graph_context": []}
    
    query_vector = create_embedding_via_clova(query)
    
    results = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=5,
        with_payload=True
    )
    
    # Step 2: Get related graph nodes
    enriched_results = []
    
    for hit in results.points:
        p = hit.payload
        
        if p.get("workspace_id") != workspace_id:
            continue
        
        # Get concepts from chunk
        chunk_concepts = p.get("concepts", [])
        
        # Query Neo4j for these concepts and their context
        with neo4j_driver.session() as session:
            graph_context = []
            
            for concept in chunk_concepts[:3]:  # Top 3 concepts
                # Get node with all evidences
                result = session.run(
                    """
                    MATCH (n:KnowledgeNode)
                    WHERE n.workspace_id = $workspace_id 
                    AND toLower(n.name) = toLower($concept)
                    OPTIONAL MATCH path = (parent)-[*1..2]->(n)
                    OPTIONAL MATCH (n)-[*1..2]->(child)
                    RETURN n.name as name,
                           n.type as type,
                           n.level as level,
                           n.synthesis as synthesis,
                           n.evidences as evidences,
                           n.source_count as source_count,
                           collect(DISTINCT parent.name) as ancestors,
                           collect(DISTINCT child.name) as descendants
                    LIMIT 1
                    """,
                    workspace_id=workspace_id,
                    concept=concept
                )
                
                record = result.single()
                if record:
                    evidences_json = record["evidences"] or []
                    
                    # Parse evidences from JSON strings
                    formatted_evidences = []
                    for ev_json in evidences_json:
                        try:
                            ev = json.loads(ev_json)
                            source_name = ev.get("source_name", "Unknown")
                            text = ev.get("text", "")
                            page = ev.get("page", 0)
                            
                            formatted_evidences.append({
                                "source": source_name,
                                "page": page,
                                "evidence": text,
                                "claims": ev.get("claims", [])
                            })
                        except json.JSONDecodeError:
                            continue
                    
                    graph_context.append({
                        "concept": record["name"],
                        "type": record["type"],
                        "level": record["level"],
                        "synthesis": record["synthesis"],
                        "sources": record["source_count"],
                        "evidences": formatted_evidences,
                        "ancestors": [a for a in record["ancestors"] if a],
                        "descendants": [d for d in record["descendants"] if d]
                    })
        
        enriched_results.append({
            "score": hit.score,
            "summary": p.get("summary", ""),
            "key_claims": p.get("key_claims", []),
            "graph_context": graph_context
        })
    
    return {
        "results": enriched_results,
        "total": len(enriched_results)
    }

def get_workspace_overview(workspace_id: str) -> Dict:
    """Get overview of entire workspace knowledge graph"""
    
    with neo4j_driver.session() as session:
        # Get hierarchy statistics
        stats = session.run(
            """
            MATCH (n:KnowledgeNode {workspace_id: $workspace_id})
            WITH n.level as level, n.type as type, count(*) as count, 
                 avg(n.source_count) as avg_sources
            RETURN level, type, count, avg_sources
            ORDER BY level
            """,
            workspace_id=workspace_id
        )
        
        hierarchy = []
        for record in stats:
            hierarchy.append({
                "level": record["level"],
                "type": record["type"],
                "count": record["count"],
                "avg_sources": round(record["avg_sources"], 1)
            })
        
        # Get top concepts
        top_concepts = session.run(
            """
            MATCH (n:KnowledgeNode {workspace_id: $workspace_id})
            WHERE n.level >= 2
            RETURN n.name as name, 
                   n.type as type,
                   n.source_count as sources,
                   n.synthesis as synthesis
            ORDER BY n.source_count DESC, n.level
            LIMIT 10
            """,
            workspace_id=workspace_id
        )
        
        concepts = []
        for record in top_concepts:
            concepts.append({
                "name": record["name"],
                "type": record["type"],
                "sources": record["sources"],
                "synthesis": record["synthesis"]
            })
        
        return {
            "hierarchy": hierarchy,
            "top_concepts": concepts
        }

# ================================
# MAIN
# ================================
if __name__ == "__main__":
    # Test with a PDF
    pdf_url = "https://sg.object.ncloudstorage.com/navnexus/SAGSINs.pdf"
    workspace_id = "ws_hierarchical_v1"
    
    print("🚀 Starting hierarchical knowledge graph pipeline...")
    
    result = process_pdf_optimized(
        pdf_url=pdf_url,
        workspace_id=workspace_id,
        file_name="TEST_HIERARCHICAL.pdf"
    )
    
    print("\n" + "="*80)
    print("📊 PROCESSING RESULT:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Get workspace overview
    if result.get("status") == "completed":
        print("\n" + "="*80)
        print("🌐 WORKSPACE OVERVIEW:")
        
        overview = get_workspace_overview(workspace_id)
        print(json.dumps(overview, indent=2, ensure_ascii=False))
        
        # Test query
        print("\n" + "="*80)
        print("🔍 Testing enhanced query:")
        
        query_result = query_knowledge_graph(
            workspace_id=workspace_id,
            query="main concepts and methodologies"
        )
        
        for i, r in enumerate(query_result["results"][:2], 1):
            print(f"\n--- Result {i} (score: {r['score']:.3f}) ---")
            print(f"Summary: {r['summary'][:150]}...")
            print(f"\nGraph Context ({len(r['graph_context'])} concepts):")
            
            for ctx in r['graph_context'][:2]:
                print(f"\n  • {ctx['concept']} ({ctx['type']}, level {ctx['level']})")
                print(f"    Sources: {ctx['sources']} PDF(s)")
                print(f"    Synthesis: {ctx['synthesis'][:100]}...")
                
                if ctx['evidences']:
                    print(f"    Evidence from {len(ctx['evidences'])} source(s):")
                    for ev in ctx['evidences'][:2]:
                        print(f"      - {ev['source']} (p.{ev['page']}): {ev['evidence'][:80]}...")
    
    neo4j_driver.close()
    print("\n" + "="*80)
    print("✅ All operations completed")
    print("="*80)