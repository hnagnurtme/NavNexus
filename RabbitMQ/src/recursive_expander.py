"""
Recursive Node Expansion Module

This module implements the core recursive expansion algorithm for building
deep hierarchical knowledge graphs using position-based extraction.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, cast
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .pipeline.position_extraction import (
    extract_content_from_positions,
    convert_relative_to_absolute,
    validate_positions,
    split_text_to_paragraphs,
    clamp_positions_to_range
)
from .pipeline.content_normalization import normalize_text, clean_for_llm
from .prompts.recursive_expansion import create_recursive_expansion_prompt

logger = logging.getLogger(__name__)


@dataclass
class NodeData:
    """
    Data class representing a node in the knowledge graph
    """
    id: str
    name: str
    synthesis: str
    level: int
    type: str  # domain, category, concept, subconcept, detail
    
    # Position data
    evidence_positions: List[List[int]] = field(default_factory=list)
    key_claims_positions: List[int] = field(default_factory=list)
    questions_positions: List[int] = field(default_factory=list)
    
    # Extracted content (populated after position extraction)
    evidence_content: List[Dict] = field(default_factory=list)
    key_claims_content: List[Dict] = field(default_factory=list)
    questions_content: List[Dict] = field(default_factory=list)

    # Direct text from LLM (NEW - higher quality than position extraction)
    key_claims_text: List[str] = field(default_factory=list)  # Actual claims from LLM
    questions_raised_text: List[str] = field(default_factory=list)  # Actual questions from LLM
    
    # Parent tracking
    parent_id: Optional[str] = None
    parent_range: Optional[List[int]] = None  # For relative position conversion
    
    # Children
    children: List['NodeData'] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j insertion"""
        return {
            'id': self.id,
            'name': self.name,
            'synthesis': self.synthesis,
            'level': self.level,
            'type': self.type,
            'evidence_positions': self.evidence_positions,
            'key_claims_positions': self.key_claims_positions,
            'questions_positions': self.questions_positions,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat()
        }


class RecursiveExpander:
    """
    Recursive expansion engine for building deep knowledge hierarchies
    """
    
    def __init__(
        self,
        paragraphs: List[str],
        llm_caller: Callable,
        max_depth: int = 3,
        children_per_level: int = 3,
        min_content_length: int = 500
    ):
        """
        Initialize recursive expander
        
        Args:
            paragraphs: Full paragraph array from PDF
            llm_caller: Async function to call LLM (returns parsed JSON)
            max_depth: Maximum depth to expand (0 = domain, 1 = category, 2 = concept, ...)
            children_per_level: Number of children per node (default 3)
            min_content_length: Minimum content length to continue expansion
        """
        self.paragraphs = paragraphs
        self.llm_caller = llm_caller
        self.max_depth = max_depth
        self.children_per_level = children_per_level
        self.min_content_length = min_content_length
        
        # Statistics
        self.stats = {
            'total_nodes': 0,
            'llm_calls': 0,
            'expansions_stopped': 0,
            'errors': 0
        }
    
    async def expand_node_recursively(
        self,
        node: NodeData,
        current_depth: int,
        target_depth: int
    ) -> None:
        """
        Recursively expand a node to target depth
        
        This is the main recursive expansion function that:
        1. Extracts parent evidence content from positions
        2. Calls LLM to get children with relative positions
        3. Converts relative positions to absolute
        4. Extracts children content
        5. Recursively expands children in parallel
        
        Args:
            node: Current node to expand
            current_depth: Current level (0, 1, 2, ...)
            target_depth: Maximum depth to expand to
        """
        # Stop condition 1: Reached target depth
        if current_depth >= target_depth:
            logger.debug(f"  Reached target depth {target_depth} for '{node.name}'")
            return
        
        # Stop condition 2: No evidence positions
        if not node.evidence_positions:
            logger.warning(f"  No evidence positions for '{node.name}', skipping expansion")
            self.stats['expansions_stopped'] += 1
            return
        
        try:
            # Step 1: Extract parent evidence content
            logger.info(f"  Expanding '{node.name}' (Level {current_depth} → {current_depth + 1})")
            
            parent_content_list = extract_content_from_positions(
                cast(List[List[int] | int], node.evidence_positions),
                self.paragraphs,
                parent_range=node.parent_range
            )
            
            if not parent_content_list:
                logger.warning(f"  No content extracted for '{node.name}', skipping expansion")
                self.stats['expansions_stopped'] += 1
                return
            
            # Combine all evidence content
            parent_content = "\n\n".join([item['text'] for item in parent_content_list])
            
            # Store extracted content in node
            node.evidence_content = parent_content_list
            
            # Stop condition 3: Content too short
            if len(parent_content) < self.min_content_length:
                logger.info(f"  Content too short for '{node.name}' ({len(parent_content)} < {self.min_content_length}), stopping")
                self.stats['expansions_stopped'] += 1
                return
            
            # Normalize content for LLM
            normalized_content = clean_for_llm(parent_content, max_length=4000)
            
            # Step 2: LLM Call - Extract children with relative positions
            prompt_data = create_recursive_expansion_prompt(
                parent_name=node.name,
                parent_synthesis=node.synthesis,
                parent_content=normalized_content,
                current_level=current_depth,
                target_level=current_depth + 1,
                children_count=self.children_per_level
            )
            
            logger.debug(f"  Calling LLM to expand '{node.name}'...")
            
            llm_result = await self.llm_caller(
                prompt=prompt_data['prompt'],
                system_message=prompt_data['system_message'],
                max_tokens=2000
            )
            
            self.stats['llm_calls'] += 1
            
            if not llm_result or not isinstance(llm_result, dict):
                logger.warning(f"  Invalid LLM response for '{node.name}'")
                self.stats['errors'] += 1
                return
            
            # Check if LLM decided to stop expansion
            if llm_result.get('stop_expansion', False):
                logger.info(f"  LLM stopped expansion: {llm_result.get('stop_reason', 'No reason given')}")
                self.stats['expansions_stopped'] += 1
                return
            
            children_data = llm_result.get('children', [])
            
            if not children_data or len(children_data) < 2:
                logger.warning(f"  Insufficient children returned for '{node.name}' ({len(children_data)} < 2)")
                self.stats['expansions_stopped'] += 1
                return
            
            logger.info(f"  ✓ Extracted {len(children_data)} children for '{node.name}'")
            
            # Step 3: Create child nodes and convert positions
            parent_paragraphs = split_text_to_paragraphs(normalized_content)
            parent_paragraph_count = len(parent_paragraphs)
            
            # Determine parent_range for children
            # If node has a parent_range, use the first evidence position's start
            # Otherwise, use the first evidence position as-is
            if node.parent_range:
                child_parent_range = node.evidence_positions[0] if node.evidence_positions else [0, 0]
            else:
                child_parent_range = node.evidence_positions[0] if node.evidence_positions else [0, 0]
            
            for idx, child_data in enumerate(children_data):
                # Extract actual text content from LLM (NEW)
                child_key_claims_text = child_data.get('key_claims', [])  # List of actual claim texts
                child_questions_text = child_data.get('questions_raised', [])  # List of actual question texts

                # Validate and clamp positions
                child_evidence_positions = child_data.get('evidence_positions', [])
                child_claims_positions = child_data.get('key_claims_positions', [])
                child_questions_positions = child_data.get('questions_positions', [])
                
                # Validate positions
                is_valid, errors = validate_positions(
                    child_evidence_positions + [[p, p] for p in child_claims_positions] + [[q, q] for q in child_questions_positions],
                    parent_paragraph_count
                )
                
                if not is_valid:
                    logger.warning(f"  Invalid positions in child '{child_data.get('name', 'Unknown')}': {errors}")
                    # Clamp to valid range
                    child_evidence_positions = clamp_positions_to_range(child_evidence_positions, parent_paragraph_count)
                    child_claims_positions = [max(0, min(p, parent_paragraph_count - 1)) for p in child_claims_positions]
                    child_questions_positions = [max(0, min(q, parent_paragraph_count - 1)) for q in child_questions_positions]
                
                # Convert relative positions to absolute
                abs_evidence_positions = convert_relative_to_absolute(
                    child_evidence_positions,
                    child_parent_range
                )
                
                abs_claims_positions = convert_relative_to_absolute(
                    [[pos] for pos in child_claims_positions],
                    child_parent_range
                )
                
                abs_questions_positions = convert_relative_to_absolute(
                    [[q] for q in child_questions_positions],
                    child_parent_range
                )
                
                # Determine child type based on level
                child_type_map = {
                    0: 'domain',
                    1: 'category',
                    2: 'concept',
                    3: 'subconcept',
                    4: 'detail'
                }
                child_type = child_type_map.get(current_depth + 1, 'detail')
                
                # Create deterministic ID using uuid
                import uuid
                node_name_hash = f"{child_data.get('name', f'child-{idx}')}-{node.id}-{idx}"
                child_id = f"{child_type}-{uuid.uuid5(uuid.NAMESPACE_DNS, node_name_hash).hex[:8]}"
                
                # Create child node
                child_node = NodeData(
                    id=child_id,
                    name=child_data.get('name', f'Child {idx + 1}'),
                    synthesis=child_data.get('synthesis', ''),
                    level=current_depth + 1,
                    type=child_type,
                    evidence_positions=[pos if isinstance(pos, list) else [pos] for pos in abs_evidence_positions],
                    key_claims_positions=[pos[0] for pos in abs_claims_positions if isinstance(pos, list)],
                    questions_positions=[pos[0] if isinstance(pos, list) else pos for pos in abs_questions_positions],
                    parent_id=node.id,
                    parent_range=child_parent_range,
                    # ✅ NEW: Store actual text from LLM (higher quality)
                    key_claims_text=child_key_claims_text if isinstance(child_key_claims_text, list) else [],
                    questions_raised_text=child_questions_text if isinstance(child_questions_text, list) else []
                )

                # Extract child content immediately
                child_evidence_content = extract_content_from_positions(
                    child_evidence_positions,
                    parent_paragraphs,
                    parent_range=None  # Already relative
                )
                child_node.evidence_content = child_evidence_content

                # Extract key claims (for backup/positions only - prefer key_claims_text)
                if child_claims_positions:
                    child_claims_content = extract_content_from_positions(
                        [[p, p] for p in child_claims_positions],
                        parent_paragraphs,
                        parent_range=None
                    )
                    child_node.key_claims_content = child_claims_content

                # Extract questions (for backup/positions only - prefer questions_raised_text)
                if child_questions_positions:
                    child_questions_content = extract_content_from_positions(
                        [[q, q] for q in child_questions_positions],
                        parent_paragraphs,
                        parent_range=None
                    )
                    child_node.questions_content = child_questions_content
                
                node.children.append(child_node)
                self.stats['total_nodes'] += 1
                
                logger.debug(f"    ✓ Created child '{child_node.name}' (Level {child_node.level})")
            
            # Step 4: Recursively expand all children in parallel
            if current_depth + 1 < target_depth and node.children:
                logger.info(f"  Expanding {len(node.children)} children of '{node.name}' in parallel...")
                
                expansion_tasks = [
                    self.expand_node_recursively(
                        child,
                        current_depth + 1,
                        target_depth
                    )
                    for child in node.children
                ]
                
                await asyncio.gather(*expansion_tasks)
                
                logger.info(f"  ✓ Completed expansion of children for '{node.name}'")
        
        except Exception as e:
            logger.error(f"  Error expanding '{node.name}': {e}", exc_info=True)
            self.stats['errors'] += 1
    
    def get_all_nodes_flat(self, root: NodeData) -> List[NodeData]:
        """
        Flatten the tree to a list of all nodes
        
        Args:
            root: Root node of the tree
        
        Returns:
            List of all nodes in the tree (depth-first traversal)
        """
        nodes = [root]
        for child in root.children:
            nodes.extend(self.get_all_nodes_flat(child))
        return nodes
    
    def print_tree(self, node: NodeData, indent: int = 0) -> None:
        """
        Print the tree structure for debugging
        
        Args:
            node: Node to print
            indent: Indentation level
        """
        prefix = "  " * indent
        print(f"{prefix}├─ [{node.level}] {node.name}")
        print(f"{prefix}   Synthesis: {node.synthesis[:60]}...")
        print(f"{prefix}   Evidence: {len(node.evidence_content)} items, Positions: {node.evidence_positions}")
        
        for child in node.children:
            self.print_tree(child, indent + 1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get expansion statistics"""
        return {
            **self.stats,
            'paragraphs_total': len(self.paragraphs),
            'max_depth': self.max_depth,
            'children_per_level': self.children_per_level
        }
