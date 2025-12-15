# Deploy to Modal.ai

## Setup

1. Install Modal:
```bash
pip install modal
```

2. Authenticate:
```bash
modal token new
```

## Deploy

```bash
modal deploy deploy.py
```

## Endpoints

After deployment, you'll get URLs like:
- `https://<workspace>--health.modal.run` - Health check
- `https://<workspace>--weapon-detect.modal.run` - Weapon detection
- `https://<workspace>--pose-extract-template.modal.run` - Extract template
- `https://<workspace>--pose-score.modal.run` - Score pose

## Update Main Server

Update `AI_SERVER_URL` in main server to point to Modal endpoints.

