# ESC Guidelines AI Search Tool - Fully Functional Render Deployment

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

A **fully functional** AI-powered search tool for navigating European Society of Cardiology (ESC) Guidelines. This deployment automatically downloads and processes the latest ESC Guidelines during build time, so it's ready to use immediately after deployment.

## 🌟 Features

- **🔍 Semantic Search**: Understands medical terminology and context
- **🏥 Clinical Question Answering**: Direct answers to clinical questions
- **📚 Multi-Document Search**: Search across 9 latest ESC Guidelines
- **⚡ Fast Results**: Sub-second search with FAISS vector indexing
- **📱 Responsive Design**: Works on desktop and mobile devices
- **🔗 RESTful API**: Programmatic access for integration
- **🚀 Zero Setup**: Fully functional immediately after deployment

## 🚀 One-Click Deployment to Render

### Quick Deploy (Recommended)

1. **Click the "Deploy to Render" button above**
2. **Connect your GitHub account** if not already connected
3. **Fork this repository** or create a new one
4. **Configure the service** in Render dashboard:
   - **Plan**: Standard ($7/month) - Required for processing
   - **Build time**: 15-20 minutes (downloads and processes guidelines)
5. **Wait for deployment** to complete
6. **Start searching** immediately!

### Manual Deployment

1. **Fork this repository** on GitHub
2. **Create a new Web Service** on [Render](https://render.com)
3. **Connect your GitHub repository**
4. **Configure the service:**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Environment**: `Python 3`
   - **Plan**: `Starter` (free tier available)

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │◄──►│   Flask App      │◄──►│  Search Engine  │
│                 │    │  (Render Host)   │    │   (FAISS +      │
│  - Search UI    │    │  - API Endpoints │    │ SentenceTransf) │
│  - Results      │    │  - CORS Enabled  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ ESC Guidelines  │
                       │   (PDF Data)    │
                       │ - 9 Documents   │
                       │ - 940 Pages     │
                       │ - 1,407 Chunks  │
                       └─────────────────┘
```

## 🏥 Available Guidelines

The system processes these ESC Guidelines:

| Year | Guideline | Pages | Status |
|------|-----------|-------|--------|
| 2024 | Elevated Blood Pressure and Hypertension | 107 | ✅ |
| 2024 | Atrial Fibrillation | 101 | ✅ |
| 2024 | Chronic Coronary Syndromes | 123 | ✅ |
| 2024 | Peripheral Arterial and Aortic Diseases | 163 | ✅ |
| 2023 | Acute Coronary Syndromes | 107 | ✅ |
| 2023 | Cardiovascular Disease in Diabetes | 98 | ✅ |
| 2023 | Endocarditis | 95 | ✅ |
| 2023 | Heart Failure (Focused Update) | 13 | ✅ |
| 2022 | Cardio-oncology | 133 | ✅ |

## 🔧 Local Development

### Prerequisites

- Python 3.8+
- 4GB+ RAM (for processing)
- 2GB+ disk space

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/esc-guidelines-render.git
   cd esc-guidelines-render
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download ESC Guidelines:**
   - Visit [ESC Guidelines](https://www.escardio.org/Guidelines/Clinical-Practice-Guidelines)
   - Download the 9 guidelines listed above
   - Place PDF files in `ESC_Guidelines/` directory

5. **Process the guidelines:**
   ```bash
   python esc_guidelines_processor.py
   ```

6. **Start the application:**
   ```bash
   python app.py
   ```

7. **Open browser:** http://localhost:5000

## 🌐 API Documentation

### Endpoints

#### `GET /health`
Check system health and status.

**Response:**
```json
{
  "status": "healthy",
  "total_chunks": 1407,
  "total_documents": 9,
  "index_size": 1407
}
```

#### `POST /search`
Perform semantic search across all guidelines.

**Request:**
```json
{
  "query": "hypertension management",
  "top_k": 10
}
```

**Response:**
```json
{
  "query": "hypertension management",
  "total_results": 10,
  "results": [
    {
      "document_name": "2024_ESC_Hypertension_Guidelines",
      "page_number": 45,
      "section_title": "Management Strategies",
      "text": "...",
      "similarity_score": 0.89,
      "chunk_id": "..."
    }
  ]
}
```

#### `POST /clinical-search`
Answer clinical questions with context.

**Request:**
```json
{
  "question": "What are the blood pressure targets for diabetic patients?",
  "top_k": 5
}
```

**Response:**
```json
{
  "question": "What are the blood pressure targets for diabetic patients?",
  "medical_terms": ["blood pressure", "diabetes", "targets"],
  "total_results": 5,
  "all_results": [...]
}
```

#### `GET /documents`
List all available guidelines.

#### `GET /setup-status`
Check if the system is properly configured.

## 🎯 Usage Examples

### Web Interface

1. **Regular Search**: 
   - Enter: "atrial fibrillation anticoagulation"
   - Get: Relevant passages about AF anticoagulation therapy

2. **Clinical Questions**:
   - Ask: "When should I start anticoagulation in AF patients?"
   - Get: Evidence-based recommendations with page references

### Python API Client

```python
import requests

# Initialize client
base_url = "https://your-app.onrender.com"

# Search for information
response = requests.post(f"{base_url}/search", 
                        json={"query": "heart failure beta blockers", "top_k": 5})
results = response.json()

# Ask clinical question
response = requests.post(f"{base_url}/clinical-search", 
                        json={"question": "What are the contraindications for ACE inhibitors?"})
answer = response.json()

print(f"Found {answer['total_results']} relevant passages")
for result in answer['all_results']:
    print(f"- {result['document_name']}, Page {result['page_number']}")
```

## 🔒 Environment Variables

For Render deployment, these environment variables are automatically set:

- `PORT`: Application port (set by Render)
- `PYTHON_VERSION`: Python version (3.11.0)
- `RENDER`: Set to 'true' in Render environment

## 📈 Performance & Scaling

### Current Performance
- **Search Time**: <1 second average
- **Memory Usage**: ~500MB (including models)
- **Concurrent Users**: 10-50 (Starter plan)
- **Index Size**: ~5MB

### Scaling Options
- **Render Pro**: Higher memory and CPU for more concurrent users
- **Redis Caching**: Cache frequent queries for faster responses
- **CDN**: Serve static assets from CDN
- **Load Balancing**: Multiple instances for high availability

## 🛠️ Troubleshooting

### Common Issues

1. **"Search system not initialized"**
   - Ensure ESC Guidelines PDFs are in `ESC_Guidelines/` directory
   - Run `python esc_guidelines_processor.py`
   - Check logs for processing errors

2. **Memory errors during processing**
   - Process guidelines one at a time
   - Use smaller chunk sizes
   - Upgrade to higher memory plan

3. **Slow search responses**
   - Check if FAISS index is properly loaded
   - Consider caching frequent queries
   - Monitor memory usage

### Render-Specific Issues

1. **Build timeouts**
   - Large dependencies may cause build timeouts
   - Consider using Docker for faster builds
   - Split processing into separate build step

2. **Memory limits**
   - Starter plan has 512MB RAM limit
   - Consider upgrading to Pro plan for full functionality
   - Optimize model loading and caching

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **European Society of Cardiology** for comprehensive clinical guidelines
- **Render** for excellent deployment platform
- **Open source community** for amazing libraries

## 📞 Support

- **Issues**: Open a GitHub issue
- **Questions**: Check the discussions tab
- **Documentation**: See the wiki for detailed guides

---

**⚠️ Medical Disclaimer**: This tool is for educational and research purposes only. Always consult qualified healthcare professionals for clinical decisions.

