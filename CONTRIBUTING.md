# Contributing Guidelines

Thank you for contributing to the **Blockchain-Based Student Project Ownership Registry (SIH 2026 - Problem Statement CYB05)**.

This repository is maintained by a 3-developer team. To avoid conflicts and maintain a production-grade codebase, everyone must adhere to the following workflow and standards.

---

## 1. Team Responsibilities & Ownership Boundaries

| Developer | Primary Responsibility | Dedicated Directory |
| :--- | :--- | :--- |
| **Developer 1** | Frontend (React, Vite, Tailwind, UI/UX, Client Services) | `frontend/` |
| **Developer 2** | Backend & Database (FastAPI, PostgreSQL, SQLAlchemy, Alembic) | `backend/` |
| **Developer 3** | Blockchain & IPFS (Hardhat, Solidity, Web3.py, Node scripts) | `blockchain/` |

> [!WARNING]
> **Strict Boundary Rule**: Do not make uncoordinated changes in another developer's module. If an API contract or interface needs modification, discuss and document it in `docs/api/API_CONTRACT.md` before coding.

---

## 2. Git Branching Strategy

We follow a structured Git branching model:

```
main (Production-ready releases)
  └── develop (Integration & staging)
        ├── feature/frontend-<feature-name>
        ├── feature/backend-<feature-name>
        ├── feature/blockchain-<feature-name>
        ├── feature/database-<feature-name>
        ├── feature/ipfs-<feature-name>
        └── feature/verification-<feature-name>
```

### Branch Rules:
1. **`main` is protected**: Never push directly to `main` or `develop`.
2. **Feature branches**: Always branch off the latest `develop` branch:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/backend-healthcheck-v2
   ```
3. **Pull Requests (PRs)**: All changes merge into `develop` via PRs with at least one code review.
4. **Clean Merges**: Rebase or squash feature commits prior to merging if requested.

---

## 3. Commit Message Conventions

We use standard **Conventional Commits**:

Format: `<type>(<scope>): <short description>`

### Types:
- `feat`: A new feature (e.g., `feat(frontend): add project health view`)
- `fix`: A bug fix (e.g., `fix(backend): correct database connection retry`)
- `test`: Adding or updating test cases (e.g., `test(blockchain): add HealthCheck deployment test`)
- `docs`: Documentation updates (e.g., `docs(architecture): update system diagram`)
- `refactor`: Code changes that neither fix a bug nor add a feature
- `chore`: Build tasks, dependency updates, configuration tweaks (e.g., `chore(root): update .gitignore`)

---

## 4. Security & Secret Management

> [!CAUTION]
> **Zero Secrets in Git**:
> - Never commit `.env`, `.env.local`, `.pem`, `.key`, or any sensitive credentials.
> - Never commit real private keys, IPFS project secrets, database production passwords, or JWT secrets.
> - Always put template placeholders in `.env.example`.
> - If a secret is accidentally committed, immediately notify the team to rotate credentials and scrub git history.

---

## 5. Development Checklist Before Submitting a PR

Before opening a Pull Request:
1. Ensure your module's local tests pass:
   - **Frontend**: `npm test` inside `frontend/`
   - **Backend**: `pytest` inside `backend/`
   - **Blockchain**: `npx hardhat test` inside `blockchain/`
2. Check that code compiles without warnings or errors.
3. Verify no temporary logs, cache folders, or `.env` files are staged (`git status`).
4. Update relevant documentation in `docs/` if modifying shared schemas, contracts, or workflows.
