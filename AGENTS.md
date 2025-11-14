# Repository Guidelines

## Project Structure & Module Organization
NavNexus is split into `Frontend/` (React + Vite) and a placeholder `Backend/` for the upcoming ASP.NET Core services. Most day-to-day work happens under `Frontend/src`, which is further grouped into `config`, `services`, `store` (Zustand), `pages`, `hooks`, `utils`, and `styles`. Keep feature-specific UI inside the relevant page subfolder (for example, new workspace widgets belong in `src/pages/workspace/components`).

## Build, Test, and Development Commands
Run `npm install` inside `Frontend/` once per checkout. Key scripts:
- `npm run dev` — Vite dev server with hot reload; pass `--host` when testing on LAN.
- `npm run build` — Type-checks via `tsc` then creates the production bundle in `dist/`.
- `npm run preview` — Serves the last build for smoke tests.
- `npm run lint` — ESLint over all `.ts`/`.tsx` files; required before pushing.
Backend services will be wired through Docker; when the compose file lands, start everything with `docker compose up --build` from the repo root.

## Coding Style & Naming Conventions
TypeScript + React 19, Tailwind 4, and Zustand are standard. Use 2-space indentation, single quotes, and keep files under 300 lines. Components are `PascalCase.tsx`, hooks start with `use` (e.g., `useTreeNavigation.ts`), stores end with `Store.ts`. Keep API contracts in `src/types`, route constants in `src/config/routes.ts`, and avoid inline styles when a Tailwind utility exists. Run the linter before committing; add inline comments only to explain non-obvious logic.

## Testing Guidelines
There is no automated test harness yet, so document manual verification steps in your pull request. When adding tests, prefer Vitest + React Testing Library, colocate specs next to the component (`TreeNode.test.tsx`), and mock API services behind the Zustand stores. Maintain at least smoke coverage for navigation and upload flows before requesting review.

## Commit & Pull Request Guidelines
Follow Conventional Commits (`feat(workspace): add bookmark panel`). Branch names mirror the commit type (`feat/graph-search`, `fix/auth-timeout`). Each PR should include: purpose summary, linked issue or Trello card, screenshots or recordings for UI changes, a list of commands run (`npm run dev`, `npm run lint`), and any deployment caveats. Squash noisy work-in-progress commits locally; reviewers expect a clean history.

## Security & Configuration Tips
Copy `.env.development` before running the app and never commit secrets—`api.config.ts` should read from `import.meta.env`. Use mock keys in screenshots. If you touch authentication or document-ingestion flows, validate CORS and storage permissions before merging to protect NCP resources.
