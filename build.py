#!/usr/bin/env python3
"""
Automated build script for Render deployment
Downloads and processes ESC Guidelines during build
"""

import os
import sys
import json
import logging
import urllib.request
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ESC Guidelines URLs (direct PDF links)
ESC_GUIDELINES_URLS = {
    "2024_ESC_Hypertension_Guidelines.pdf": "https://academic.oup.com/eurheartj/article-pdf/45/38/3912/59404653/ehae178.pdf",
    "2024_ESC_Atrial_Fibrillation_Guidelines.pdf": "https://academic.oup.com/eurheartj/article-pdf/45/36/3314/59404654/ehae176.pdf",
    "2024_ESC_Chronic_Coronary_Syndromes_Guidelines.pdf": "https://academic.oup.com/eurheartj/article-pdf/45/36/3415/59404655/ehae177.pdf",
    "2024_ESC_Peripheral_Arterial_Guidelines.pdf": "https://academic.oup.com/eurheartj/article-pdf/45/36/3538/59404656/ehae179.pdf",
    "2023_ESC_Acute_Coronary_Syndromes_Guidelines.pdf": "https://academic.oup.com/eurheartj/article-pdf/44/38/3720/51353776/ehad191.pdf",
    "2023_ESC_Cardiovascular_Disease_Diabetes_Guidelines.pdf": "https://academic.oup.com/eurheartj/article-pdf/44/31/2945/51353777/ehad192.pdf",
    "2023_ESC_Endocarditis_Guidelines.pdf": "https://academic.oup.com/eurheartj/article-pdf/44/39/3948/51353778/ehad193.pdf",
    "2023_ESC_Heart_Failure_Update.pdf": "https://academic.oup.com/eurheartj/article-pdf/44/37/3627/51353779/ehad194.pdf",
    "2022_ESC_Cardio_oncology_Guidelines.pdf": "https://academic.oup.com/eurheartj/article-pdf/43/41/4229/46581413/ehac244.pdf"
}

def download_file(url, filepath, max_retries=3):
    """Download a file with retry logic"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading {filepath.name} (attempt {attempt + 1}/{max_retries})...")
            
            # Add headers to mimic browser request
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Accept', 'application/pdf,application/octet-stream,*/*')
            
            with urllib.request.urlopen(req, timeout=60) as response:
                with open(filepath, 'wb') as f:
                    f.write(response.read())
            
            # Verify file size
            if filepath.stat().st_size > 100000:  # At least 100KB
                logger.info(f"✅ Successfully downloaded {filepath.name} ({filepath.stat().st_size} bytes)")
                return True
            else:
                logger.warning(f"⚠️ Downloaded file {filepath.name} seems too small, retrying...")
                filepath.unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"❌ Failed to download {filepath.name}: {e}")
            filepath.unlink(missing_ok=True)
            if attempt < max_retries - 1:
                logger.info("Retrying in 5 seconds...")
                import time
                time.sleep(5)
    
    return False

def run_command(command, description, cwd=None):
    """Run a shell command with proper error handling"""
    logger.info(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd,
            timeout=600  # 10 minute timeout
        )
        logger.info(f"✅ {description} completed successfully")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {description} timed out")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    """Main build function"""
    logger.info("🚀 Starting automated ESC Guidelines build process")
    
    # Create directories
    guidelines_dir = Path("ESC_Guidelines")
    processed_dir = Path("processed_guidelines")
    
    guidelines_dir.mkdir(exist_ok=True)
    processed_dir.mkdir(exist_ok=True)
    
    # Check if we already have ESC Guidelines files
    pdf_files = list(guidelines_dir.glob("*.pdf"))
    
    if pdf_files:
        logger.info(f"📚 Found {len(pdf_files)} existing ESC Guidelines PDFs")
        for pdf_file in pdf_files:
            logger.info(f"   - {pdf_file.name} ({pdf_file.stat().st_size / 1024 / 1024:.1f} MB)")
    else:
        logger.info("📥 No existing PDFs found, attempting to download...")
        
        # Download ESC Guidelines (this will likely fail due to 403 errors)
        downloaded_count = 0
        
        for filename, url in ESC_GUIDELINES_URLS.items():
            filepath = guidelines_dir / filename
            
            if not filepath.exists():
                if download_file(url, filepath):
                    downloaded_count += 1
                else:
                    logger.warning(f"⚠️ Failed to download {filename}, continuing with others...")
            else:
                logger.info(f"📄 {filename} already exists, skipping download")
                downloaded_count += 1
        
        logger.info(f"📊 Downloaded {downloaded_count}/{len(ESC_GUIDELINES_URLS)} guidelines")
        
        if downloaded_count == 0:
            logger.error("❌ No guidelines were downloaded successfully")
            logger.error("💡 Please provide ESC Guidelines PDFs manually in the ESC_Guidelines directory")
            return False
        
        # Re-check for PDF files after download attempt
        pdf_files = list(guidelines_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.error("❌ No PDF files found after download attempt")
        return False
    
    logger.info(f"📚 Processing {len(pdf_files)} PDF files...")
    
    # Process the guidelines
    logger.info("🔄 Processing ESC Guidelines...")
    
    # Install additional dependencies if needed
    run_command("pip install --no-cache-dir sentence-transformers faiss-cpu", "Installing processing dependencies")
    
    # Run the processor
    if run_command("python esc_guidelines_processor.py", "Processing ESC Guidelines", cwd="."):
        logger.info("✅ ESC Guidelines processed successfully!")
        
        # Verify processed data
        chunks_file = processed_dir / "chunks.json"
        if chunks_file.exists():
            with open(chunks_file, 'r') as f:
                data = json.load(f)
                chunk_count = len(data.get('chunks', []))
                doc_count = len(data.get('metadata', {}))
                logger.info(f"📊 Processed {chunk_count} chunks from {doc_count} documents")
        
        return True
    else:
        logger.error("❌ Failed to process ESC Guidelines")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("❌ Build process failed")
        sys.exit(1)
    else:
        logger.info("🎉 Build process completed successfully!")
        sys.exit(0)

