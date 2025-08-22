# Duwiligence

A Flask application for processing emails and generating newsletters with AI-powered content analysis.

## Features

- Email processing and analysis
- AI-powered content generation using LLMs
- PDF newsletter generation
- Google Cloud Tasks integration
- Asynchronous processing

## Installation

1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Create virtual environment: `uv venv`
3. Activate virtual environment: `source .venv/bin/activate`
4. Install dependencies: `uv pip install -r requirements.txt`

## Usage

Run the application:

```bash
python main.py
```

## Environment Variables

Set the following environment variables:

- `GCP_PROJECT`: Google Cloud Project ID
- `WORKER_URL`: Cloud Run worker URL
- `TASK_SERVICE_ACCOUNT`: Service account email for tasks
- `LLM_API_KEY`: OpenAI API key
- `GMAIL_USER`: Gmail username
- `GMAIL_APP_PASSWORD`: Gmail app password

## License

MIT
