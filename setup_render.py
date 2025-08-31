#!/usr/bin/env python3
"""
Setup script for ESC Guidelines AI Search Tool - Render Deployment
"""

import os
import sys
import subprocess
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ESC Guidelines download URLs (these would need to be updated with actual URLs)
ESC_GUIDELINES_URLS = {
    "2024_ESC_Hypertension_Guidelines.pdf": "https://academic.oup.com/eurheartj/article-pdf/45/38/3912/59404653/ehae178.pdf",
    "2024_ESC_Atrial_Fibrillation_Guidelines.pdf": "https://academic.oup.com/eurheartj/article-pdf/45/36/3314/59404654/ehae176.pdf",
    # Add more URLs as needed
}

def download_file(url, filename):
    """Download a file from URL"""
    try:
        logger.info(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, filename)
        logger.info(f"✅ Downloaded {filename}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download {filename}: {e}")
        return False

def run_command(command, description):
    """Run a shell command"""
    logger.info(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    """Main setup function"""
    logger.info("🚀 Setting up ESC Guidelines AI Search Tool for Render")
    
    # Create directories
    os.makedirs('ESC_Guidelines', exist_ok=True)
    os.makedirs('processed_guidelines', exist_ok=True)
    
    # Check if we're in a Render environment
    is_render = os.environ.get('RENDER') == 'true'
    
    if is_render:
        logger.info("🌐 Render environment detected")
        
        # In Render, we might need to download guidelines from a cloud storage
        # For now, we'll create a placeholder system
        logger.info("⚠️  ESC Guidelines need to be downloaded manually")
        logger.info("   Please follow the setup instructions in README.md")
        
        # Create a minimal processed data structure for demo
        demo_data = {
            "chunks": [],
            "metadata": {},
            "message": "Please run the full setup to process ESC Guidelines"
        }
        
        with open('processed_guidelines/chunks.json', 'w') as f:
            json.dump(demo_data, f)
        
        logger.info("✅ Demo setup completed for Render")
    else:
        logger.info("💻 Local environment detected")
        
        # Download guidelines if URLs are available
        downloaded_count = 0
        for filename, url in ESC_GUIDELINES_URLS.items():
            filepath = os.path.join('ESC_Guidelines', filename)
            if not os.path.exists(filepath):
                if download_file(url, filepath):
                    downloaded_count += 1
        
        logger.info(f"📥 Downloaded {downloaded_count} guidelines")
        
        # Process guidelines if we have PDFs
        pdf_files = [f for f in os.listdir('ESC_Guidelines') if f.endswith('.pdf')]
        if pdf_files:
            logger.info("🔄 Processing guidelines...")
            if run_command("python esc_guidelines_processor.py", "Processing ESC Guidelines"):
                logger.info("✅ Setup completed successfully!")
            else:
                logger.error("❌ Processing failed")
        else:
            logger.warning("⚠️  No PDF files found. Please download ESC Guidelines manually.")

if __name__ == "__main__":
    main()

