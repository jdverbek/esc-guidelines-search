#!/usr/bin/env python3
"""
Advanced ESC Guidelines Search System
Enhanced query processing and retrieval with better result presentation
"""

import os
import json
import re
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedESCSearch:
    """
    Advanced search system for ESC Guidelines with enhanced query processing
    """
    
    def __init__(self, processed_dir: str = "processed_guidelines"):
        self.processed_dir = processed_dir
        self.chunks_file = os.path.join(processed_dir, "chunks.json")
        self.index_file = os.path.join(processed_dir, "faiss_index.bin")
        self.metadata_file = os.path.join(processed_dir, "metadata.json")
        
        # Load embedding model
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load processed data
        self.load_data()
        
        # Medical synonyms for query expansion
        self.medical_synonyms = {
            'hypertension': ['high blood pressure', 'elevated blood pressure', 'arterial hypertension'],
            'myocardial infarction': ['heart attack', 'MI', 'acute MI'],
            'atrial fibrillation': ['AF', 'AFib', 'irregular heartbeat'],
            'heart failure': ['HF', 'cardiac failure', 'congestive heart failure', 'CHF'],
            'coronary artery disease': ['CAD', 'coronary heart disease', 'CHD'],
            'diabetes': ['diabetes mellitus', 'DM', 'diabetic'],
            'stroke': ['cerebrovascular accident', 'CVA'],
            'anticoagulation': ['blood thinning', 'anticoagulant therapy'],
            'stent': ['percutaneous coronary intervention', 'PCI'],
            'bypass': ['CABG', 'coronary artery bypass graft']
        }
    
    def load_data(self):
        """Load processed chunks, metadata, and FAISS index"""
        logger.info("Loading processed data...")
        
        # Load chunks
        with open(self.chunks_file, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
        
        # Load metadata
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        # Load FAISS index
        self.index = faiss.read_index(self.index_file)
        
        logger.info(f"Loaded {len(self.chunks)} chunks and index with {self.index.ntotal} vectors")
    
    def expand_query(self, query: str) -> str:
        """
        Expand query with medical synonyms and related terms
        """
        expanded_terms = [query]
        query_lower = query.lower()
        
        # Add synonyms
        for term, synonyms in self.medical_synonyms.items():
            if term in query_lower:
                expanded_terms.extend(synonyms)
            for synonym in synonyms:
                if synonym in query_lower:
                    expanded_terms.append(term)
                    expanded_terms.extend([s for s in synonyms if s != synonym])
                    break
        
        # Create expanded query
        expanded_query = ' '.join(set(expanded_terms))
        
        if expanded_query != query:
            logger.info(f"Query expanded from: '{query}' to: '{expanded_query}'")
        
        return expanded_query
    
    def search(self, query: str, top_k: int = 10, expand_query: bool = True, 
               filter_guideline: Optional[str] = None) -> List[Dict]:
        """
        Enhanced search with query expansion and filtering
        """
        # Expand query if requested
        if expand_query:
            search_query = self.expand_query(query)
        else:
            search_query = query
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([search_query])
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding.astype('float32'), min(top_k * 3, len(self.chunks)))
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                
                # Apply guideline filter if specified
                if filter_guideline and filter_guideline.lower() not in chunk['document_name'].lower():
                    continue
                
                # Calculate relevance score (lower FAISS distance = higher relevance)
                chunk['similarity_score'] = float(score)
                chunk['relevance_score'] = max(0, 1 - score)  # Convert to 0-1 scale
                chunk['rank'] = len(results) + 1
                
                # Add query highlighting
                chunk['highlighted_text'] = self.highlight_query_terms(chunk['text'], query)
                
                results.append(chunk)
                
                if len(results) >= top_k:
                    break
        
        return results
    
    def highlight_query_terms(self, text: str, query: str) -> str:
        """
        Highlight query terms in text
        """
        query_terms = query.lower().split()
        highlighted_text = text
        
        for term in query_terms:
            if len(term) > 2:  # Only highlight terms longer than 2 characters
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                highlighted_text = pattern.sub(f"**{term.upper()}**", highlighted_text)
        
        return highlighted_text
    
    def get_document_summary(self, document_name: str) -> Dict:
        """
        Get summary information about a specific document
        """
        if document_name in self.metadata:
            meta = self.metadata[document_name]
            
            # Count chunks by section
            doc_chunks = [c for c in self.chunks if c['document_name'] == document_name]
            sections = {}
            for chunk in doc_chunks:
                section = chunk.get('section_title', 'General')
                sections[section] = sections.get(section, 0) + 1
            
            return {
                'document_name': document_name,
                'filename': meta['filename'],
                'total_pages': meta['total_pages'],
                'total_chunks': meta['total_chunks'],
                'sections': sections,
                'processed_date': meta['processed_date']
            }
        return {}
    
    def search_by_document(self, document_name: str, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search within a specific document
        """
        return self.search(query, top_k=top_k, filter_guideline=document_name)
    
    def get_similar_chunks(self, chunk_id: str, top_k: int = 5) -> List[Dict]:
        """
        Find chunks similar to a given chunk
        """
        # Find the chunk
        target_chunk = None
        target_idx = None
        
        for i, chunk in enumerate(self.chunks):
            if chunk['chunk_id'] == chunk_id:
                target_chunk = chunk
                target_idx = i
                break
        
        if not target_chunk:
            return []
        
        # Get embedding for this chunk
        chunk_embedding = self.embedding_model.encode([target_chunk['text']])
        
        # Search for similar chunks
        scores, indices = self.index.search(chunk_embedding.astype('float32'), top_k + 1)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != target_idx and idx < len(self.chunks):  # Exclude the original chunk
                chunk = self.chunks[idx].copy()
                chunk['similarity_score'] = float(score)
                chunk['relevance_score'] = max(0, 1 - score)
                results.append(chunk)
        
        return results[:top_k]
    
    def format_search_results(self, results: List[Dict], query: str) -> str:
        """
        Format search results for display
        """
        if not results:
            return f"No results found for query: '{query}'"
        
        output = []
        output.append(f"Search Results for: '{query}'")
        output.append("=" * 60)
        output.append(f"Found {len(results)} relevant passages\\n")
        
        for i, result in enumerate(results, 1):
            output.append(f"{i}. **{result['document_name']}** (Page {result['page_number']})")
            output.append(f"   Section: {result.get('section_title', 'General')}")
            output.append(f"   Relevance: {result['relevance_score']:.3f}")
            output.append(f"   Source: {result['chunk_id']}")
            output.append("")
            
            # Show excerpt with highlighting
            text = result.get('highlighted_text', result['text'])
            if len(text) > 300:
                text = text[:300] + "..."
            output.append(f"   {text}")
            output.append("")
        
        return "\\n".join(output)
    
    def clinical_question_search(self, question: str, top_k: int = 8) -> Dict:
        """
        Enhanced search specifically for clinical questions
        """
        # Extract key medical terms
        medical_terms = self.extract_medical_terms(question)
        
        # Perform search
        results = self.search(question, top_k=top_k, expand_query=True)
        
        # Group results by guideline
        by_guideline = {}
        for result in results:
            guideline = result['document_name']
            if guideline not in by_guideline:
                by_guideline[guideline] = []
            by_guideline[guideline].append(result)
        
        return {
            'question': question,
            'medical_terms': medical_terms,
            'total_results': len(results),
            'results_by_guideline': by_guideline,
            'all_results': results
        }
    
    def extract_medical_terms(self, text: str) -> List[str]:
        """
        Extract potential medical terms from text
        """
        medical_terms = []
        text_lower = text.lower()
        
        # Check for known medical terms
        for term in self.medical_synonyms.keys():
            if term in text_lower:
                medical_terms.append(term)
        
        # Check for synonyms
        for term, synonyms in self.medical_synonyms.items():
            for synonym in synonyms:
                if synonym in text_lower and term not in medical_terms:
                    medical_terms.append(term)
        
        return medical_terms

def main():
    """
    Demonstration of the advanced search system
    """
    print("Initializing Advanced ESC Guidelines Search System...")
    search_system = AdvancedESCSearch()
    
    print("\\n" + "="*80)
    print("ADVANCED ESC GUIDELINES SEARCH SYSTEM")
    print("="*80)
    
    # Demo clinical questions
    clinical_questions = [
        "What are the blood pressure targets for patients with diabetes?",
        "How should atrial fibrillation be managed in elderly patients?",
        "What are the indications for coronary angiography in acute coronary syndrome?",
        "When should anticoagulation be started after myocardial infarction?",
        "What are the contraindications for beta-blockers in heart failure?"
    ]
    
    for question in clinical_questions:
        print(f"\\n{'='*60}")
        print(f"CLINICAL QUESTION: {question}")
        print('='*60)
        
        # Perform clinical question search
        result = search_system.clinical_question_search(question, top_k=3)
        
        print(f"Medical terms identified: {', '.join(result['medical_terms'])}")
        print(f"Total relevant passages found: {result['total_results']}")
        print()
        
        # Show top results
        for i, res in enumerate(result['all_results'][:3], 1):
            print(f"{i}. **{res['document_name']}** (Page {res['page_number']})")
            print(f"   Relevance: {res['relevance_score']:.3f}")
            print(f"   Text: {res['text'][:200]}...")
            print()
    
    print("\\n" + "="*80)
    print("DOCUMENT SUMMARIES")
    print("="*80)
    
    # Show document summaries
    for doc_name in search_system.metadata.keys():
        summary = search_system.get_document_summary(doc_name)
        print(f"\\n**{doc_name}**")
        print(f"  - Pages: {summary['total_pages']}")
        print(f"  - Chunks: {summary['total_chunks']}")
        print(f"  - Top sections: {list(summary['sections'].keys())[:3]}")

if __name__ == "__main__":
    main()

