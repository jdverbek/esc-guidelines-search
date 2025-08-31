#!/usr/bin/env python3
"""
Deployment helper for Render
"""

import os
import sys
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_render_environment():
    """Check if running in Render environment"""
    return os.environ.get('RENDER') == 'true'

def setup_for_render():
    """Setup the application for Render deployment"""
    logger.info("🌐 Setting up for Render deployment...")
    
    # Create necessary directories
    os.makedirs('ESC_Guidelines', exist_ok=True)
    os.makedirs('processed_guidelines', exist_ok=True)
    
    # Create placeholder data for initial deployment
    placeholder_data = {
        "chunks": [],
        "metadata": {},
        "setup_required": True,
        "message": "Please complete the setup process to download and process ESC Guidelines"
    }
    
    with open('processed_guidelines/chunks.json', 'w') as f:
        json.dump(placeholder_data, f)
    
    logger.info("✅ Render setup completed")
    return True

def main():
    """Main deployment function"""
    if check_render_environment():
        logger.info("🌐 Render environment detected")
        setup_for_render()
    else:
        logger.info("💻 Local environment - no special setup needed")
        logger.info("📋 To deploy to Render:")
        logger.info("   1. Push this repository to GitHub")
        logger.info("   2. Connect GitHub repo to Render")
        logger.info("   3. Deploy as Web Service")

if __name__ == "__main__":
    main()

