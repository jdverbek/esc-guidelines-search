#!/usr/bin/env python3
"""
ESC Guidelines AI Search Tool - Render Deployment Version
"""

import os
import sys
import json
import logging
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Get port from environment (Render sets this)
PORT = int(os.environ.get('PORT', 5000))

# HTML template for the search interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESC Guidelines AI Search Tool</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; text-align: center; }
        .header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .header p { font-size: 1.1rem; opacity: 0.9; }
        .search-section { background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        .search-form { display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; }
        .search-input { flex: 1; min-width: 300px; padding: 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 16px; }
        .search-input:focus { outline: none; border-color: #667eea; }
        .search-btn { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; transition: background 0.3s; }
        .search-btn:hover { background: #5a6fd8; }
        .search-btn:disabled { background: #ccc; cursor: not-allowed; }
        .search-options { display: flex; gap: 1rem; align-items: center; margin-top: 1rem; flex-wrap: wrap; }
        .search-type { display: flex; gap: 0.5rem; align-items: center; }
        .results-section { background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); display: none; }
        .result-item { border: 1px solid #eee; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; transition: box-shadow 0.3s; }
        .result-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .result-title { font-weight: bold; color: #667eea; font-size: 1.1rem; margin-bottom: 0.5rem; }
        .result-meta { color: #666; font-size: 0.9rem; margin-bottom: 1rem; }
        .result-text { line-height: 1.6; color: #444; }
        .relevance-score { background: #e8f2ff; color: #0066cc; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
        .loading { text-align: center; padding: 2rem; color: #666; }
        .error { background: #fee; color: #c33; padding: 1rem; border-radius: 6px; margin: 1rem 0; }
        .stats { background: #f8f9fa; padding: 1rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.9rem; color: #666; }
        .example-queries { margin-top: 1rem; }
        .example-query { display: inline-block; background: #f0f0f0; padding: 6px 12px; margin: 4px; border-radius: 20px; cursor: pointer; font-size: 0.9rem; transition: background 0.3s; }
        .example-query:hover { background: #e0e0e0; }
        .setup-notice { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 1rem; border-radius: 6px; margin-bottom: 2rem; }
        .setup-notice h3 { margin-bottom: 0.5rem; }
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .header h1 { font-size: 2rem; }
            .search-form { flex-direction: column; }
            .search-input { min-width: auto; }
            .search-options { flex-direction: column; align-items: flex-start; gap: 0.5rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ESC Guidelines AI Search Tool</h1>
            <p>Search through European Society of Cardiology Guidelines using AI-powered semantic search</p>
        </div>
        
        <div class="setup-notice" id="setupNotice">
            <h3>⚠️ Setup Required</h3>
            <p>This deployment requires ESC Guidelines data to be processed. Please follow the setup instructions in the GitHub repository to download and process the guidelines.</p>
        </div>
        
        <div class="search-section">
            <form class="search-form" id="searchForm">
                <input type="text" class="search-input" id="searchInput" placeholder="Enter your medical question or search term..." required>
                <button type="submit" class="search-btn" id="searchBtn">Search</button>
            </form>
            
            <div class="search-options">
                <div class="search-type">
                    <input type="radio" id="regular" name="searchType" value="regular" checked>
                    <label for="regular">Regular Search</label>
                </div>
                <div class="search-type">
                    <input type="radio" id="clinical" name="searchType" value="clinical">
                    <label for="clinical">Clinical Question</label>
                </div>
                <div class="search-type">
                    <label for="topK">Results:</label>
                    <select id="topK">
                        <option value="5">5</option>
                        <option value="10" selected>10</option>
                        <option value="15">15</option>
                        <option value="20">20</option>
                    </select>
                </div>
            </div>
            
            <div class="example-queries">
                <strong>Example queries:</strong>
                <span class="example-query" onclick="setQuery('hypertension management in diabetes')">Hypertension in diabetes</span>
                <span class="example-query" onclick="setQuery('atrial fibrillation anticoagulation')">AF anticoagulation</span>
                <span class="example-query" onclick="setQuery('acute coronary syndrome diagnosis')">ACS diagnosis</span>
                <span class="example-query" onclick="setQuery('heart failure beta blockers')">HF beta blockers</span>
                <span class="example-query" onclick="setQuery('endocarditis prophylaxis')">Endocarditis prophylaxis</span>
            </div>
        </div>
        
        <div class="results-section" id="resultsSection">
            <div id="resultsContent"></div>
        </div>
    </div>

    <script>
        const searchForm = document.getElementById('searchForm');
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        const resultsSection = document.getElementById('resultsSection');
        const resultsContent = document.getElementById('resultsContent');
        const setupNotice = document.getElementById('setupNotice');
        
        function setQuery(query) {
            searchInput.value = query;
            searchInput.focus();
        }
        
        function showLoading() {
            resultsContent.innerHTML = '<div class="loading">🔍 Searching through ESC Guidelines...</div>';
            resultsSection.style.display = 'block';
            searchBtn.disabled = true;
            searchBtn.textContent = 'Searching...';
        }
        
        function hideLoading() {
            searchBtn.disabled = false;
            searchBtn.textContent = 'Search';
        }
        
        function showError(message, data = null) {
            let errorHtml = `<div class="error">❌ ${message}</div>`;
            
            if (data && data.setup_required) {
                errorHtml += `
                    <div class="setup-notice" style="margin-top: 1rem;">
                        <h3>🔧 Setup Required</h3>
                        <p><strong>This is a deployment template.</strong> To enable full search functionality:</p>
                        <ol style="margin: 1rem 0; padding-left: 2rem;">
                            <li>Download ESC Guidelines PDFs from the official ESC website</li>
                            <li>Process the data using the provided scripts in the repository</li>
                            <li>Or visit a fully configured demo instance</li>
                        </ol>
                        <p><strong>Repository:</strong> <a href="https://github.com/jdverbek/esc-guidelines-search" target="_blank">https://github.com/jdverbek/esc-guidelines-search</a></p>
                    </div>
                `;
            }
            
            resultsContent.innerHTML = errorHtml;
            hideLoading();
        }
        
        function formatResults(data) {
            const isClinicaSearch = document.querySelector('input[name="searchType"]:checked').value === 'clinical';
            
            let html = '';
            
            if (isClinicaSearch && data.medical_terms && data.medical_terms.length > 0) {
                html += `<div class="stats">
                    <strong>Medical terms identified:</strong> ${data.medical_terms.join(', ')}<br>
                    <strong>Total results:</strong> ${data.total_results}
                </div>`;
            } else {
                html += `<div class="stats">
                    <strong>Query:</strong> "${data.query}"<br>
                    <strong>Total results:</strong> ${data.total_results}
                </div>`;
            }
            
            const results = data.all_results || data.results || [];
            
            results.forEach((result, index) => {
                const relevanceScore = (result.relevance_score || (1 - result.similarity_score) || 0).toFixed(3);
                const text = result.highlighted_text || result.text || '';
                const displayText = text.length > 400 ? text.substring(0, 400) + '...' : text;
                
                html += `
                    <div class="result-item">
                        <div class="result-title">${result.document_name}</div>
                        <div class="result-meta">
                            Page ${result.page_number} • 
                            Section: ${result.section_title || 'General'} • 
                            <span class="relevance-score">Relevance: ${relevanceScore}</span>
                        </div>
                        <div class="result-text">${displayText}</div>
                    </div>
                `;
            });
            
            if (results.length === 0) {
                html += '<div class="error">No results found. Try different search terms.</div>';
            }
            
            return html;
        }
        
        async function performSearch(query, searchType, topK) {
            showLoading();
            
            try {
                const endpoint = searchType === 'clinical' ? '/clinical-search' : '/search';
                const body = searchType === 'clinical' 
                    ? { question: query, top_k: topK }
                    : { query: query, top_k: topK };
                
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.error) {
                    showError(data.error, data);
                    return;
                }
                
                resultsContent.innerHTML = formatResults(data);
                hideLoading();
                
            } catch (error) {
                console.error('Search error:', error);
                showError(error.message);
            }
        }
        
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const query = searchInput.value.trim();
            const searchType = document.querySelector('input[name="searchType"]:checked').value;
            const topK = parseInt(document.getElementById('topK').value);
            
            if (!query) {
                showError('Please enter a search query');
                return;
            }
            
            performSearch(query, searchType, topK);
        });
        
        // Test API connection on page load
        window.addEventListener('load', async () => {
            try {
                const response = await fetch('/health');
                if (response.ok) {
                    const data = await response.json();
                    console.log('API Health Check:', data);
                    if (data.status === 'healthy') {
                        setupNotice.style.display = 'none';
                    }
                } else {
                    console.warn('API health check failed');
                }
            } catch (error) {
                console.warn('Could not connect to API:', error);
            }
        });
    </script>
</body>
</html>
"""

# Initialize search system (will be None if data not available)
search_system = None

def initialize_search_system():
    """Initialize the search system if data is available"""
    global search_system
    try:
        # Check if processed data exists
        if os.path.exists('processed_guidelines/chunks.json'):
            from advanced_search_system import AdvancedESCSearch
            search_system = AdvancedESCSearch()
            logger.info("Search system initialized successfully")
        else:
            logger.warning("Processed guidelines data not found. Please run setup first.")
    except Exception as e:
        logger.error(f"Failed to initialize search system: {e}")

@app.route('/')
def index():
    """Serve the main search interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    """Main search endpoint"""
    if not search_system:
        return jsonify({
            'error': 'ESC Guidelines data not available. This deployment requires manual setup of the medical guidelines data.',
            'setup_required': True,
            'instructions': [
                '1. Download ESC Guidelines PDFs from https://www.escardio.org/Guidelines/Clinical-Practice-Guidelines',
                '2. Process the data using the provided scripts',
                '3. For a fully functional demo, visit the original deployment'
            ],
            'demo_available': True,
            'demo_message': 'This is a deployment template. The search functionality requires ESC Guidelines data to be processed.'
        }), 200  # Changed to 200 to avoid browser errors
    
    try:
        data = request.get_json()
        query = data.get('query', '')
        top_k = data.get('top_k', 10)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        results = search_system.search(query, top_k=top_k)
        
        return jsonify({
            'query': query,
            'total_results': len(results),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/clinical-search', methods=['POST'])
def clinical_search():
    """Clinical question search endpoint"""
    if not search_system:
        return jsonify({
            'error': 'ESC Guidelines data not available. This deployment requires manual setup of the medical guidelines data.',
            'setup_required': True,
            'instructions': [
                '1. Download ESC Guidelines PDFs from https://www.escardio.org/Guidelines/Clinical-Practice-Guidelines',
                '2. Process the data using the provided scripts',
                '3. For a fully functional demo, visit the original deployment'
            ],
            'demo_available': True,
            'demo_message': 'This is a deployment template. The clinical search functionality requires ESC Guidelines data to be processed.'
        }), 200  # Changed to 200 to avoid browser errors
    
    try:
        data = request.get_json()
        question = data.get('question', '')
        top_k = data.get('top_k', 8)
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        result = search_system.clinical_question_search(question, top_k=top_k)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Clinical search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/documents', methods=['GET'])
def get_documents():
    """Get list of available documents"""
    if not search_system:
        return jsonify({
            'error': 'Search system not initialized',
            'setup_required': True
        }), 503
    
    try:
        documents = []
        for doc_name in search_system.metadata.keys():
            summary = search_system.get_document_summary(doc_name)
            documents.append(summary)
        
        return jsonify({
            'total_documents': len(documents),
            'documents': documents
        })
        
    except Exception as e:
        logger.error(f"Documents error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if search_system:
            return jsonify({
                'status': 'healthy',
                'total_chunks': len(search_system.chunks),
                'total_documents': len(search_system.metadata),
                'index_size': search_system.index.ntotal if search_system.index else 0
            })
        else:
            return jsonify({
                'status': 'setup_required',
                'message': 'Search system not initialized. Data processing required.'
            })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/setup-status', methods=['GET'])
def setup_status():
    """Check setup status"""
    status = {
        'processed_data_exists': os.path.exists('processed_guidelines/chunks.json'),
        'pdf_directory_exists': os.path.exists('ESC_Guidelines/'),
        'search_system_loaded': search_system is not None
    }
    
    pdf_count = 0
    if status['pdf_directory_exists']:
        pdf_files = [f for f in os.listdir('ESC_Guidelines/') if f.endswith('.pdf')]
        pdf_count = len(pdf_files)
    
    status['pdf_count'] = pdf_count
    status['setup_complete'] = all([
        status['processed_data_exists'],
        status['search_system_loaded']
    ])
    
    return jsonify(status)

if __name__ == '__main__':
    # Initialize search system on startup
    initialize_search_system()
    
    # Run the app
    logger.info(f"Starting ESC Guidelines AI Search Tool on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)

