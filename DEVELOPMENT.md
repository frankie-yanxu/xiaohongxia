# Xiaohongxia Project

## Project Structure

```
xiaohongxia/
├── index.html          # Main HTML (structure only)
├── style.css           # All CSS styles
├── app.js              # All JavaScript logic
├── vercel.json         # Vercel deployment config
├── README.md           # Project documentation
├── VISION.md           # Project vision
├── STRATEGY.md         # Strategy document
├── RESEARCH_VISION.md  # Research vision
├── backend/
│   ├── requirements.txt    # Python dependencies
│   └── app/
│       ├── main.py         # FastAPI application
│       └── core/
│           ├── __init__.py     # Module exports
│           ├── beacon.py       # Handshake verification
│           ├── reputation.py   # Vouch chain system
│           └── snapshot_engine.py  # Visual generation
└── admin/
    └── *.md            # Admin documentation
```

## Development

### Frontend
Just open `index.html` in browser, or:
```bash
npx serve .
```

### Backend
```bash
cd backend
pip install -r requirements.txt
cd app
uvicorn main:app --reload
```

API docs available at: http://localhost:8000/docs

## Deployment
Frontend is deployed via Vercel (auto-deploy on push).
