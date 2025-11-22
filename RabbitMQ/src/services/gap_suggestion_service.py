"""
Gap Suggestion Service - LLM-based gap suggestion generation for leaf nodes

This service generates intelligent gap suggestions for leaf nodes in the knowledge graph
using LLM analysis, similar to the Backend's GapSuggestionService.cs
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from src.model.GapSuggestion import GapSuggestion
from src.pipeline.llm_analysis import call_llm_sync

logger = logging.getLogger('GapSuggestionService')


class GapSuggestionService:
    """
    Service for generating intelligent gap suggestions using LLM analysis
    """
    
    def __init__(self, clova_api_key: str, clova_api_url: str):
        """
        Initialize gap suggestion service
        
        Args:
            clova_api_key: API key for LLM service
            clova_api_url: URL for LLM service endpoint
        """
        self.clova_api_key = clova_api_key
        self.clova_api_url = clova_api_url
        
    def generate_gap_suggestions_for_leaf_node(
        self,
        leaf_node: Dict[str, Any],
        all_nodes_in_workspace: List[Dict[str, Any]],
        evidences: List[Dict[str, Any]] = None
    ) -> List[GapSuggestion]:
        """
        Generate gap suggestions for a single leaf node using LLM
        
        This method follows the pattern from Backend's GapSuggestionService.cs:
        - BuildGapSuggestionPrompt: Constructs context-aware prompt
        - Calls LLM with the prompt
        - ParseGapSuggestions: Extracts suggestions from LLM response
        
        Args:
            leaf_node: The leaf node dictionary with id, name, synthesis, level, type
            all_nodes_in_workspace: List of all nodes for context
            evidences: Optional list of evidence items for this node
            
        Returns:
            List of GapSuggestion objects (typically 1 suggestion per call)
        """
        try:
            logger.info(
                f"Generating gap suggestions for leaf node: {leaf_node.get('id')} - {leaf_node.get('name')}"
            )
            
            # Build LLM prompt with context
            prompt = self._build_gap_suggestion_prompt(
                leaf_node=leaf_node,
                all_nodes_in_workspace=all_nodes_in_workspace,
                evidences=evidences or []
            )
            
            # Call LLM to generate suggestion
            llm_response = call_llm_sync(
                prompt=prompt,
                max_tokens=150,  # Keep it concise - single question
                system_message="You are a knowledge graph expert who identifies knowledge gaps and generates thought-provoking questions.",
                clova_api_key=self.clova_api_key,
                clova_api_url=self.clova_api_url
            )
            
            if not llm_response or not isinstance(llm_response, dict):
                logger.warning(
                    f"LLM returned empty or invalid response for node: {leaf_node.get('id')}"
                )
                return []
            
            # Parse LLM response to extract gap suggestion
            suggestions = self._parse_gap_suggestions(llm_response, leaf_node, evidences)
            
            logger.info(
                f"Successfully generated {len(suggestions)} gap suggestion(s) for node: {leaf_node.get('id')}"
            )
            
            return suggestions
            
        except Exception as e:
            logger.error(
                f"Error generating gap suggestions for node: {leaf_node.get('id')}: {e}",
                exc_info=True
            )
            return []
    
    def _build_gap_suggestion_prompt(
        self,
        leaf_node: Dict[str, Any],
        all_nodes_in_workspace: List[Dict[str, Any]],
        evidences: List[Dict[str, Any]]
    ) -> str:
        """
        Build LLM prompt for gap suggestion generation
        
        This mirrors the Backend's BuildGapSuggestionPrompt method in C#
        """
        prompt_lines = [
            "You are a knowledge graph expert. Analyze the following leaf node and suggest potential knowledge gaps or areas that need further exploration.",
            "",
            "=== LEAF NODE INFORMATION ===",
            f"Name: {leaf_node.get('name', 'Unknown')}",
            f"Type: {leaf_node.get('type', 'Unknown')}",
            f"Synthesis: {leaf_node.get('synthesis', 'No synthesis available')}",
            f"Level: {leaf_node.get('level', 'Unknown')}",
            ""
        ]
        
        # Add evidence context if available
        if evidences and len(evidences) > 0:
            prompt_lines.append("=== EVIDENCES ===")
            for evidence in evidences[:3]:  # Limit to first 3 evidences
                source_name = evidence.get('source_name', 'Unknown source')
                text = evidence.get('text', '')
                # Truncate text to 200 chars
                text_preview = text[:200] + "..." if len(text) > 200 else text
                prompt_lines.append(f"- Source: {source_name}")
                prompt_lines.append(f"  Text: {text_preview}")
                prompt_lines.append("")
        
        # Add workspace context
        prompt_lines.append("=== OTHER NODES IN WORKSPACE (for context) ===")
        
        # Filter and sort relevant nodes (exclude current node, sort by level descending)
        relevant_nodes = [
            n for n in all_nodes_in_workspace 
            if n.get('id') != leaf_node.get('id')
        ]
        relevant_nodes = sorted(
            relevant_nodes,
            key=lambda x: x.get('level', 0),
            reverse=True
        )[:10]  # Take top 10 by level
        
        for node in relevant_nodes:
            prompt_lines.append(
                f"- {node.get('name', 'Unknown')} (Level {node.get('level', '?')}, Type: {node.get('type', 'Unknown')})"
            )
        
        prompt_lines.extend([
            "",
            "=== TASK ===",
            "Based on the leaf node information and workspace context, generate ONE thought-provoking open-ended question that:",
            "- Identifies a knowledge gap or unexplored area",
            "- Encourages users to explore and develop new content",
            "- Connects the current topic to potential future research directions",
            "",
            "IMPORTANT REQUIREMENTS:",
            "- Write a single question (one sentence, maximum 50 words)",
            "- DO NOT use markdown formatting (no **, __, *, #, etc.)",
            "- Write in plain text only",
            "- Make it specific to the topic but broad enough to inspire exploration",
            "- DO NOT include explanations or additional context",
            "",
            "Example responses:",
            "How might real-time variations in UAV battery levels influence the dynamic selection of relay nodes in energy-constrained aerial networks?",
            "",
            "What trade-offs exist between energy-aware scheduling algorithms and overall network performance in space-air-ground integrated systems?",
            "",
            "Provide ONLY the question, no additional text, explanations, or formatting."
        ])
        
        return "\n".join(prompt_lines)
    
    def _parse_gap_suggestions(
        self,
        llm_response: Dict[str, Any],
        leaf_node: Dict[str, Any],
        evidences: List[Dict[str, Any]]
    ) -> List[GapSuggestion]:
        """
        Parse LLM response to extract gap suggestions
        
        This mirrors the Backend's ParseGapSuggestions method in C#
        """
        suggestions = []
        
        try:
            # Extract content from LLM response
            # The response might be a dict with different structures depending on LLM
            cleaned_response = ""
            
            if isinstance(llm_response, dict):
                # Try different keys that might contain the response
                cleaned_response = (
                    llm_response.get('response', '') or
                    llm_response.get('text', '') or
                    llm_response.get('content', '') or
                    llm_response.get('answer', '') or
                    str(llm_response)
                )
            else:
                cleaned_response = str(llm_response)
            
            cleaned_response = cleaned_response.strip()
            
            # Remove code blocks if present
            if cleaned_response.startswith("```"):
                first_newline = cleaned_response.find('\n')
                if first_newline > 0:
                    cleaned_response = cleaned_response[first_newline + 1:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            # Remove surrounding quotes if the entire response is wrapped
            cleaned_response = cleaned_response.strip()
            if cleaned_response.startswith('"') and cleaned_response.endswith('"'):
                cleaned_response = cleaned_response[1:-1]
            if cleaned_response.startswith("'") and cleaned_response.endswith("'"):
                cleaned_response = cleaned_response[1:-1]
            
            cleaned_response = cleaned_response.strip()
            
            logger.debug(
                f"Parsed gap suggestion. Length: {len(cleaned_response)}, "
                f"Preview: {cleaned_response[:200] if len(cleaned_response) > 200 else cleaned_response}"
            )
            
            # Create gap suggestion if we have valid content
            if cleaned_response and len(cleaned_response) > 10:  # At least 10 chars
                # Get source_id from first evidence if available
                source_id = ""
                if evidences and len(evidences) > 0:
                    source_id = evidences[0].get('source_id', '')
                
                suggestion = GapSuggestion(
                    Id=f"gap-{uuid.uuid4().hex[:8]}",
                    SuggestionText=cleaned_response,
                    TargetNodeId=leaf_node.get('id', ''),
                    TargetFileId=source_id,
                    SimilarityScore=0.8  # Default similarity score
                )
                
                suggestions.append(suggestion)
                logger.info(f"Successfully created gap suggestion for node {leaf_node.get('id')}")
            else:
                logger.warning(
                    f"LLM returned empty or too short response for node {leaf_node.get('id')}"
                )
                
        except Exception as e:
            logger.error(
                f"Error parsing gap suggestions for node {leaf_node.get('id')}: {e}",
                exc_info=True
            )
        
        return suggestions
    
    async def generate_gap_suggestions_async(
        self,
        leaf_node: Dict[str, Any],
        all_nodes_in_workspace: List[Dict[str, Any]],
        evidences: List[Dict[str, Any]] = None
    ) -> List[GapSuggestion]:
        """
        Async version of gap suggestion generation
        
        For now, wraps the sync version. Can be enhanced with async LLM calls later.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate_gap_suggestions_for_leaf_node,
            leaf_node,
            all_nodes_in_workspace,
            evidences
        )
