#!/usr/bin/env python3
"""
ESC Guidelines AI Search Tool
Implementation of the methodology described in the uploaded document
"""

import os
import json
import re
import fitz  # PyMuPDF
import pdfplumber
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ESCGuidelinesProcessor:
    """
    Main class for processing ESC Guidelines PDFs and building searchable index
    """
    
    def __init__(self, guidelines_dir: str = "/home/ubuntu/ESC_Guidelines", 
                 output_dir: str = "/home/ubuntu/processed_guidelines"):
        self.guidelines_dir = guidelines_dir
        self.output_dir = output_dir
        self.chunks_file = os.path.join(output_dir, "chunks.json")
        self.index_file = os.path.join(output_dir, "faiss_index.bin")
        self.metadata_file = os.path.join(output_dir, "metadata.json")
        
        # Initialize embedding model
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize storage
        self.chunks = []
        self.metadata = {}
        self.index = None
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from PDF with page and section information
        """
        logger.info(f"Extracting text from {os.path.basename(pdf_path)}")
        
        pages_data = []
        
        try:
            # Use PyMuPDF for fast text extraction with coordinates
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Clean and process text
                text = self._clean_text(text)
                
                if text.strip():  # Only add non-empty pages
                    pages_data.append({
                        'page_number': page_num + 1,
                        'text': text,
                        'char_count': len(text),
                        'word_count': len(text.split())
                    })
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return []
        
        logger.info(f"Extracted {len(pages_data)} pages from {os.path.basename(pdf_path)}")
        return pages_data
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page headers/footers patterns (common in medical guidelines)
        text = re.sub(r'Page \d+ of \d+', '', text)
        text = re.sub(r'ESC Guidelines.*?\d{4}', '', text)
        
        # Remove URLs and DOIs
        text = re.sub(r'https?://[^\s]+', '', text)
        text = re.sub(r'doi:\s*[^\s]+', '', text)
        
        return text.strip()
    
    def chunk_text(self, pages_data: List[Dict], document_name: str) -> List[Dict]:
        """
        Chunk text into searchable segments with overlap
        """
        logger.info(f"Chunking text for {document_name}")
        
        chunks = []
        chunk_size = 800  # words per chunk
        overlap = 100     # words overlap
        
        for page_data in pages_data:
            page_text = page_data['text']
            page_num = page_data['page_number']
            words = page_text.split()
            
            # Create chunks from this page
            start = 0
            chunk_id = 0
            
            while start < len(words):
                end = min(start + chunk_size, len(words))
                chunk_text = ' '.join(words[start:end])
                
                # Try to detect section headers
                section_title = self._extract_section_title(chunk_text)
                
                chunk = {
                    'chunk_id': f"{document_name}_page{page_num}_chunk{chunk_id}",
                    'document_name': document_name,
                    'page_number': page_num,
                    'chunk_number': chunk_id,
                    'text': chunk_text,
                    'section_title': section_title,
                    'word_count': len(chunk_text.split()),
                    'char_count': len(chunk_text)
                }
                
                chunks.append(chunk)
                
                # Move start position with overlap
                start += chunk_size - overlap
                chunk_id += 1
                
                # Break if we've reached the end
                if end >= len(words):
                    break
        
        logger.info(f"Created {len(chunks)} chunks for {document_name}")
        return chunks
    
    def _extract_section_title(self, text: str) -> str:
        """
        Try to extract section title from chunk text
        """
        lines = text.split('\n')
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            # Look for numbered sections or capitalized headers
            if re.match(r'^\d+\.?\s+[A-Z][^.]*$', line) or \
               re.match(r'^[A-Z][A-Z\s]{10,}$', line):
                return line
        return "General"
    
    def generate_embeddings(self, chunks: List[Dict]) -> np.ndarray:
        """
        Generate embeddings for all chunks
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings in batches to avoid memory issues
        batch_size = 32
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.embedding_model.encode(batch, show_progress_bar=True)
            embeddings.extend(batch_embeddings)
        
        return np.array(embeddings)
    
    def build_faiss_index(self, embeddings: np.ndarray):
        """
        Build FAISS index for fast similarity search
        """
        logger.info("Building FAISS index...")
        
        dimension = embeddings.shape[1]
        
        # Use HNSW index for better performance with large datasets
        self.index = faiss.IndexHNSWFlat(dimension, 32)
        self.index.hnsw.efConstruction = 40
        
        # Add embeddings to index
        self.index.add(embeddings.astype('float32'))
        
        logger.info(f"FAISS index built with {self.index.ntotal} vectors")
    
    def process_all_guidelines(self):
        """
        Process all PDF files in the guidelines directory
        """
        logger.info("Starting processing of all ESC Guidelines...")
        
        pdf_files = [f for f in os.listdir(self.guidelines_dir) if f.endswith('.pdf')]
        
        if not pdf_files:
            logger.error(f"No PDF files found in {self.guidelines_dir}")
            return
        
        all_chunks = []
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.guidelines_dir, pdf_file)
            document_name = os.path.splitext(pdf_file)[0]
            
            # Extract text from PDF
            pages_data = self.extract_text_from_pdf(pdf_path)
            
            if not pages_data:
                logger.warning(f"No text extracted from {pdf_file}")
                continue
            
            # Chunk the text
            chunks = self.chunk_text(pages_data, document_name)
            all_chunks.extend(chunks)
            
            # Store metadata
            self.metadata[document_name] = {
                'filename': pdf_file,
                'total_pages': len(pages_data),
                'total_chunks': len(chunks),
                'processed_date': datetime.now().isoformat()
            }
        
        self.chunks = all_chunks
        logger.info(f"Total chunks created: {len(all_chunks)}")
        
        # Generate embeddings
        embeddings = self.generate_embeddings(all_chunks)
        
        # Build FAISS index
        self.build_faiss_index(embeddings)
        
        # Save everything
        self.save_processed_data()
    
    def save_processed_data(self):
        """
        Save chunks, metadata, and FAISS index to disk
        """
        logger.info("Saving processed data...")
        
        # Save chunks
        with open(self.chunks_file, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, indent=2, ensure_ascii=False)
        
        # Save metadata
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        
        # Save FAISS index
        if self.index:
            faiss.write_index(self.index, self.index_file)
        
        logger.info("All data saved successfully!")
    
    def load_processed_data(self):
        """
        Load previously processed data
        """
        logger.info("Loading processed data...")
        
        # Load chunks
        if os.path.exists(self.chunks_file):
            with open(self.chunks_file, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
        
        # Load metadata
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        
        # Load FAISS index
        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)
        
        logger.info(f"Loaded {len(self.chunks)} chunks and index with {self.index.ntotal if self.index else 0} vectors")
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search for relevant chunks based on query
        """
        if not self.index or not self.chunks:
            logger.error("Index or chunks not loaded. Please process guidelines first.")
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                chunk['similarity_score'] = float(score)
                chunk['rank'] = i + 1
                results.append(chunk)
        
        return results

def main():
    """
    Main function to run the processing
    """
    processor = ESCGuidelinesProcessor()
    
    # Check if processed data exists
    if os.path.exists(processor.chunks_file) and os.path.exists(processor.index_file):
        logger.info("Found existing processed data. Loading...")
        processor.load_processed_data()
    else:
        logger.info("No existing processed data found. Processing guidelines...")
        processor.process_all_guidelines()
    
    # Print summary
    print("\n" + "="*60)
    print("ESC GUIDELINES PROCESSING SUMMARY")
    print("="*60)
    print(f"Total documents processed: {len(processor.metadata)}")
    print(f"Total chunks created: {len(processor.chunks)}")
    print(f"FAISS index size: {processor.index.ntotal if processor.index else 0}")
    print("\nDocuments processed:")
    for doc_name, meta in processor.metadata.items():
        print(f"  - {doc_name}: {meta['total_pages']} pages, {meta['total_chunks']} chunks")
    
    # Test search functionality
    print("\n" + "="*60)
    print("TESTING SEARCH FUNCTIONALITY")
    print("="*60)
    
    test_queries = [
        "hypertension management",
        "atrial fibrillation treatment",
        "acute coronary syndrome diagnosis"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = processor.search(query, top_k=3)
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['document_name']} (Page {result['page_number']})")
            print(f"     Score: {result['similarity_score']:.4f}")
            print(f"     Text: {result['text'][:100]}...")
            print()

if __name__ == "__main__":
    main()

