# Frontend Module — Developer 1 Guide

> **Module Owner**: Developer 1  
> **Stack**: React 18, Vite, TypeScript, Tailwind CSS, React Router, Axios, Vitest  
> **Phase**: Phase 0 (Environment Shell)

---

## 1. Directory Structure

```
frontend/
├── public/               # Static assets
├── src/
│   ├── components/       # Reusable UI components
│   ├── pages/            # Page-level route views
│   ├── services/         # Axios API service clients
│   ├── tests/            # Vitest unit & component tests
│   ├── App.tsx           # Environment shell entry view
│   ├── index.css         # Tailwind & custom typography styles
│   └── main.tsx          # React DOM root entrypoint
├── Dockerfile            # Container configuration
├── package.json          # Dependencies & scripts
├── tailwind.config.js    # Tailwind configuration
├── tsconfig.json         # TypeScript configuration
├── vite.config.ts        # Vite & Vitest configuration
└── README.md             # This document
```

---

## 2. Setup & Development

### 2.1 Prerequisites
- Node.js `v18+` or `v20+`
- npm `v9+`

### 2.2 Installation
```bash
cd frontend
npm install
```

### 2.3 Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default configuration:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 2.4 Running the Dev Server
```bash
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 3. Running Frontend Tests

```bash
# Run unit tests once
npm test

# Run unit tests in watch mode
npm run test:watch
```

---

## 4. Developer Rules for Frontend

1. **No Hardcoded URLs**: Always access backend endpoints using `apiClient` defined in `src/services/api.ts` or through `import.meta.env.VITE_API_BASE_URL`.
2. **Component Isolation**: Place modular UI components in `src/components/` and page-level routes in `src/pages/`.
3. **No Premature Business Logic**: Follow the phase roadmap. Do not create unreviewed schemas or mock state until the API contract in `docs/api/API_CONTRACT.md` is approved.
