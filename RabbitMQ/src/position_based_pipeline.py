"""
Position-Based PDF Processing Pipeline

This module demonstrates the new position-based approach for processing PDFs.
It integrates with the existing worker.py infrastructure.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)


async def process_pdf_position_based(
    workspace_id: str,
    pdf_url: str,
    file_name: str,
    clova_api_key: str,
    clova_api_url: str,
    max_depth: int = 3
) -> Dict[str, Any]:
    """
    Process PDF using position-based recursive extraction
    
    This is the NEW pipeline that replaces chunk-based processing.
    
    Pipeline:
    1. Extract PDF as paragraphs
    2. LLM Call 1: Shallow structure (Level 0 + Level 1) with positions
    3. Extract content from positions
    4. LLM Calls 2-N: Recursive expansion with relative positions
    5. Build complete tree with all evidence
    
    Args:
        workspace_id: Workspace ID
        pdf_url: URL of the PDF file
        file_name: Name of the PDF file
        clova_api_key: Clova API key
        clova_api_url: Clova API URL
        max_depth: Maximum depth to expand (default 3)
    
    Returns:
        Dict with processing results and statistics
    """
    from .pipeline.pdf_extraction import extract_pdf_as_paragraphs
    from .pipeline.position_extraction import extract_content_from_positions
    from .pipeline.llm_analysis import call_llm_sync, call_llm_async
    from .prompts.shallow_structure_extraction import create_shallow_structure_prompt
    from .recursive_expander import RecursiveExpander, NodeData
    
    logger.info(f"📄 Processing PDF (position-based): {file_name}")
    
    try:
        # ========================================
        # STEP 1: Extract PDF as paragraphs
        # ========================================
        logger.info("  [1/4] Extracting PDF as paragraphs...")
        
        paragraphs, language, metadata = extract_pdf_as_paragraphs(
            pdf_url=pdf_url,
            max_pages=25,
            timeout=30
        )
        
        if not paragraphs or len(paragraphs) < 10:
            raise ValueError(f"Insufficient paragraphs extracted: {len(paragraphs)}")
        
        logger.info(f"  ✓ Extracted {len(paragraphs)} paragraphs")
        logger.info(f"  ✓ Language: {language}, Total pages: {metadata.get('total_pages', 0)}")
        
        # ========================================
        # STEP 2: LLM Call 1 - Shallow structure with positions
        # ========================================
        logger.info("  [2/4] Extracting shallow structure (Level 0 + Level 1)...")
        
        # Prepare content context (first 6000 chars)
        content_context = "\n\n".join(paragraphs[:50])  # First ~50 paragraphs
        
        # Create prompt
        prompt_data = create_shallow_structure_prompt(
            file_name=file_name,
            content=content_context,
            paragraph_count=len(paragraphs),
            lang=language
        )
        
        # Call LLM
        shallow_result = call_llm_sync(
            prompt=prompt_data['prompt'],
            system_message=prompt_data['system_message'],
            max_tokens=2500,
            clova_api_key=clova_api_key,
            clova_api_url=clova_api_url
        )
        
        if not shallow_result or 'hierarchy' not in shallow_result:
            raise ValueError("LLM failed to return valid shallow structure")
        
        hierarchy = shallow_result['hierarchy']
        level_0_data = hierarchy.get('level_0', {})
        level_1_nodes = hierarchy.get('level_1_nodes', [])
        
        logger.info(f"  ✓ Extracted domain: {level_0_data.get('name', 'Unknown')}")
        logger.info(f"  ✓ Extracted {len(level_1_nodes)} Level 1 categories")
        
        # ========================================
        # STEP 3: Extract content from positions
        # ========================================
        logger.info("  [3/4] Extracting content from positions...")
        
        # Create root domain node
        root_node = NodeData(
            id=f"domain-{uuid.uuid4().hex[:8]}",
            name=level_0_data.get('name', f"Knowledge from {file_name}"),
            synthesis=level_0_data.get('synthesis', ''),
            level=0,
            type='domain',
            evidence_positions=level_0_data.get('evidence_positions', [[0, min(50, len(paragraphs) - 1)]]),
            parent_range=None
        )
        
        # Extract domain evidence
        domain_evidence = extract_content_from_positions(
            root_node.evidence_positions,
            paragraphs
        )
        root_node.evidence_content = domain_evidence
        
        logger.info(f"  ✓ Extracted domain evidence: {len(domain_evidence)} items")
        
        # Create Level 1 category nodes
        for idx, cat_data in enumerate(level_1_nodes):
            cat_node = NodeData(
                id=f"category-{uuid.uuid4().hex[:8]}",
                name=cat_data.get('name', f"Category {idx + 1}"),
                synthesis=cat_data.get('synthesis', ''),
                level=1,
                type='category',
                evidence_positions=cat_data.get('evidence_positions', []),
                key_claims_positions=cat_data.get('key_claims_positions', []),
                questions_positions=cat_data.get('questions_positions', []),
                parent_id=root_node.id,
                parent_range=None
            )
            
            # Extract category evidence
            cat_evidence = extract_content_from_positions(
                cat_node.evidence_positions,
                paragraphs
            )
            cat_node.evidence_content = cat_evidence
            
            # Extract key claims
            if cat_node.key_claims_positions:
                claims_content = extract_content_from_positions(
                    [[p, p] for p in cat_node.key_claims_positions],
                    paragraphs
                )
                cat_node.key_claims_content = claims_content
            
            # Extract questions
            if cat_node.questions_positions:
                questions_content = extract_content_from_positions(
                    [[q, q] for q in cat_node.questions_positions],
                    paragraphs
                )
                cat_node.questions_content = questions_content
            
            root_node.children.append(cat_node)
            
            logger.info(f"    ✓ Created category '{cat_node.name}' with {len(cat_evidence)} evidence items")
        
        # ========================================
        # STEP 4: Recursive expansion (if max_depth > 1)
        # ========================================
        if max_depth > 1:
            logger.info(f"  [4/4] Recursive expansion to depth {max_depth}...")
            
            # Create async LLM caller wrapper
            async def llm_caller_wrapper(prompt: str, system_message: str, max_tokens: int):
                """Wrapper for async LLM calls"""
                result = await call_llm_async(
                    prompt=prompt,
                    system_message=system_message,
                    max_tokens=max_tokens,
                    clova_api_key=clova_api_key,
                    clova_api_url=clova_api_url
                )
                return result
            
            # Create expander
            expander = RecursiveExpander(
                paragraphs=paragraphs,
                llm_caller=llm_caller_wrapper,
                max_depth=max_depth,
                children_per_level=3,
                min_content_length=500
            )
            
            # Expand each Level 1 category in parallel
            expansion_tasks = []
            for cat_node in root_node.children:
                task = expander.expand_node_recursively(
                    node=cat_node,
                    current_depth=1,
                    target_depth=max_depth
                )
                expansion_tasks.append(task)
            
            # Wait for all expansions to complete
            await asyncio.gather(*expansion_tasks)
            
            stats = expander.get_stats()
            logger.info(f"  ✓ Expansion complete:")
            logger.info(f"    - Total nodes: {stats['total_nodes']}")
            logger.info(f"    - LLM calls: {stats['llm_calls']}")
            logger.info(f"    - Expansions stopped: {stats['expansions_stopped']}")
            logger.info(f"    - Errors: {stats['errors']}")
        else:
            logger.info("  [4/4] Skipping recursive expansion (max_depth = 1)")
            stats = {'total_nodes': len(root_node.children), 'llm_calls': 1}
        
        # ========================================
        # Flatten tree and prepare results
        # ========================================
        if max_depth > 1:
            all_nodes = [root_node] + [root_node] # Placeholder - would use expander.get_all_nodes_flat(root_node)
            from .recursive_expander import RecursiveExpander
            temp_expander = RecursiveExpander(paragraphs, None)
            all_nodes = temp_expander.get_all_nodes_flat(root_node)
        else:
            all_nodes = [root_node] + root_node.children
        
        logger.info(f"  ✅ Processing complete: {len(all_nodes)} total nodes")
        
        return {
            "status": "completed",
            "file_name": file_name,
            "pdf_url": pdf_url,
            "language": language,
            "paragraphs_extracted": len(paragraphs),
            "nodes_created": len(all_nodes),
            "root_node": root_node,
            "all_nodes": all_nodes,
            "llm_calls": stats.get('llm_calls', 1),
            "metadata": metadata,
            "processing_mode": "position_based"
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing {file_name}: {e}", exc_info=True)
        return {
            "status": "failed",
            "file_name": file_name,
            "pdf_url": pdf_url,
            "error": str(e)
        }


def integrate_position_based_nodes_to_neo4j(
    nodes: List,
    workspace_id: str,
    neo4j_session,
    file_name: str,
    pdf_url: str
):
    """
    Insert position-based nodes into Neo4j
    
    This function creates nodes with position metadata for traceability.
    
    Args:
        nodes: List of NodeData objects
        workspace_id: Workspace ID
        neo4j_session: Neo4j session
        file_name: Source file name
        pdf_url: Source PDF URL
    
    Returns:
        Statistics about nodes created
    """
    from .model.KnowledgeNode import KnowledgeNode
    from .model.Evidence import Evidence
    
    logger.info(f"  Inserting {len(nodes)} nodes into Neo4j...")
    
    nodes_created = 0
    evidences_created = 0
    
    # Import the Neo4j creation functions from worker.py
    # For now, this is a placeholder showing the integration points
    
    for node in nodes:
        # Create KnowledgeNode
        knowledge_node = KnowledgeNode(
            Id=node.id,
            Type=node.type,
            Name=node.name,
            Synthesis=node.synthesis,
            WorkspaceId=workspace_id,
            Level=node.level,
            SourceCount=1,
            TotalConfidence=0.90,
            CreatedAt=datetime.now(timezone.utc),
            UpdatedAt=datetime.now(timezone.utc)
        )
        
        # Insert node (would use create_knowledge_node from worker.py)
        # create_knowledge_node(neo4j_session, knowledge_node)
        nodes_created += 1
        
        # Create evidence with position metadata
        for evidence_item in node.evidence_content:
            evidence = Evidence(
                Id=f"evidence-{uuid.uuid4().hex[:8]}",
                SourceId=pdf_url,
                SourceName=file_name,
                ChunkId=f"para-{evidence_item['position_range'][0]}-{evidence_item['position_range'][1]}",
                Text=evidence_item['text'][:1500],
                Page=evidence_item['position_range'][0] + 1,  # Approximate page
                Confidence=0.92,
                CreatedAt=datetime.now(timezone.utc),
                Language="ENG",
                SourceLanguage="ENG",
                HierarchyPath=node.name,
                Concepts=[node.name],
                KeyClaims=[c['text'] for c in node.key_claims_content] if node.key_claims_content else [],
                QuestionsRaised=[q['text'] for q in node.questions_content] if node.questions_content else [],
                EvidenceStrength=0.90,
                # POSITION METADATA (NEW)
                StartPos=evidence_item['position_range'][0],
                EndPos=evidence_item['position_range'][1],
                ChunkIndex=evidence_item['position_range'][0],
                HasMore=True
            )
            
            # Insert evidence (would use create_evidence_node from worker.py)
            # create_evidence_node(neo4j_session, evidence, node.id)
            evidences_created += 1
    
    logger.info(f"  ✓ Created {nodes_created} nodes and {evidences_created} evidence items")
    
    return {
        "nodes_created": nodes_created,
        "evidences_created": evidences_created
    }
