# Vector Strike

A multi-domain gaming platform with a React frontend, Django backend, and modular game collections.

## Architecture

- `frontend/` — client application and UI
- `backend/` — server, apps, and business logic
- `games/` — game category modules and original game content
- `docs/` — documentation and planning files
- `scripts/` — automation and utility scripts

## Quick start

1. Set up the frontend in `frontend/`
2. Set up the backend in `backend/`
3. Add game content under `games/`
4. Document design decisions in `docs/`

## Project structure

```text
vector-strike/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── features/
│   │   ├── games/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   ├── utils/
│   │   ├── constants/
│   │   ├── types/
│   │   ├── routes/
│   │   ├── styles/
│   │   └── App.tsx
│   └── package.json
├── backend/
│   ├── config/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── profiles/
│   │   ├── games/
│   │   ├── achievements/
│   │   ├── progression/
│   │   ├── leaderboard/
│   │   ├── recommendations/
│   │   ├── social/
│   │   ├── notifications/
│   │   ├── moderation/
│   │   ├── tournaments/
│   │   ├── marketplace/
│   │   └── analytics/
│   ├── manage.py
│   └── requirements.txt
├── games/
│   ├── classic/
│   ├── mathematics/
│   ├── science/
│   ├── logic/
│   ├── language/
│   ├── strategy/
│   ├── racing/
│   └── original/
├── docs/
├── scripts/
└── README.md
```
