# DF-InfoUI: Adaptive Multi-Agent Accessibility Evaluator & Fixer

A production-ready, end-to-end web tool for evaluating and fixing accessibility issues in automotive infotainment UI codebases. Upload a ZIP file containing your source code, and the system will automatically detect, fix, and validate accessibility issues according to WCAG 2.1 guidelines.

## Features

- **Multi-Agent Architecture**: Brain Agent (planner/supervisor) + four POUR Neuron Agents (Perceivable/Operable/Understandable/Robust)
- **Comprehensive Analysis**: Static analysis using regex, AST parsing (Babel), and LLM-powered detection
- **Automated Fixing**: AI-powered fixes with confidence scoring and validation
- **Multiple Validation**: ESLint with jsx-a11y plugin and axe-core integration
- **Rich Reporting**: PDF reports with before/after code snippets and validation results
- **Modern UI**: React-based frontend with drag-and-drop upload and real-time progress tracking

## Architecture

### Backend (Python/FastAPI)
- **FastAPI** with async support
- **OpenAI GPT-4** for intelligent analysis and fixing
- **Multi-agent system** with specialized POUR agents
- **File processing** with ZIP handling and patch application
- **Validation pipeline** using ESLint and axe-core
- **PDF generation** with detailed reports

### Frontend (React/TypeScript)
- **React 18** with TypeScript
- **Vite** for fast development and building
- **React Query** for data fetching and caching
- **Drag-and-drop** file upload interface
- **Real-time progress** tracking with polling
- **Interactive diff viewer** for before/after code

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key

### 1. Clone and Setup
```bash
git clone <repository-url>
cd DF-InfoUI
```

### 2. Environment Configuration
```bash
# Copy environment template
cp server/env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
```

### 3. Run with Docker Compose
```bash
# Start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Development Setup

### Backend Development
```bash
cd server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd web
npm install
npm run dev
```

## Usage

1. **Upload**: Drag and drop a ZIP file containing your HTML, JS, JSX, TS, TSX, and CSS files
2. **Analysis**: The Brain Agent analyzes your code using static rules and AI-powered detection
3. **Fixing**: POUR agents automatically fix detected issues with confidence scoring
4. **Validation**: ESLint and axe-core validate the fixes
5. **Download**: Get the fixed ZIP file and detailed PDF report

## API Endpoints

### Upload
```http
POST /api/upload
Content-Type: multipart/form-data

file: <zip-file>
```

### Job Status
```http
GET /api/status/{job_id}
```

### Downloads
```http
GET /api/download/{job_id}/fixed.zip
GET /api/download/{job_id}/report.pdf
```

## Supported File Types

- **HTML**: Static HTML files
- **JavaScript**: `.js` files
- **TypeScript**: `.ts` files  
- **React JSX**: `.jsx` files
- **React TSX**: `.tsx` files
- **CSS**: `.css` files

## Accessibility Standards

The tool follows **WCAG 2.1 AA** guidelines and checks for:

### Perceivable
- Alt text for images
- Color contrast ratios
- Text alternatives for non-text content

### Operable
- Keyboard navigation
- Focus management
- Form labels and ARIA attributes

### Understandable
- Heading hierarchy
- Form instructions
- Error identification

### Robust
- Valid HTML structure
- ARIA role definitions
- Screen reader compatibility

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4-turbo-preview` |
| `DATA_DIR` | Directory for temporary files | `/app/data` |

### Model Configuration

The system uses OpenAI's GPT models for intelligent analysis. You can configure the model via the `OPENAI_MODEL` environment variable:

- `gpt-4-turbo-preview` (recommended)
- `gpt-4`
- `gpt-3.5-turbo`

## Production Deployment

### Docker Production Build
```bash
# Build production images
docker-compose -f docker-compose.prod.yml up --build

# Or use individual builds
docker build -t df-infoui-backend ./server
docker build -t df-infoui-frontend ./web
```

### Environment Setup
1. Set up a reverse proxy (nginx/Apache)
2. Configure SSL certificates
3. Set up persistent storage for the data directory
4. Configure monitoring and logging

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**: Ensure your API key is valid and has sufficient credits
2. **File Upload Issues**: Check file size limits and ZIP file integrity
3. **Validation Failures**: Ensure Node.js and required packages are installed
4. **Memory Issues**: Increase Docker memory limits for large files

### Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Open an issue on GitHub

---

**DF-InfoUI** - Making automotive infotainment UIs accessible for everyone.
