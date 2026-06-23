# FRAS V2 Frontend

This Angular/Ionic application contains the professor-facing FRAS V2 user interface. The final V2 workflow is located primarily under:

```text
src/app/v2/
```

## V2 Pages

| Page | Path |
|---|---|
| Today's Classes / Schedule | `src/app/v2/pages/todays-classes/` |
| Class Roster | `src/app/v2/pages/class-roster/` |
| Face Profile Registration/Update | `src/app/v2/pages/face-profile/` |
| Live Session Monitoring | `src/app/v2/pages/live-session/` |
| Post-Session Review | `src/app/v2/pages/post-session-review/` |
| Student Evidence | `src/app/v2/pages/student-evidence/` |
| Student Class History | `src/app/v2/pages/student-class-history/` |
| Session History | `src/app/v2/pages/session-history/` |

Shared V2 UI components are in:

```text
src/app/v2/components/
```

The TypeScript API contract for V2 is in:

```text
src/app/v2/models/v2-attendance.models.ts
```

The HTTP wrapper methods are in:

```text
src/app/api.service.ts
```

## API Integration

The frontend calls the V2 FastAPI backend under:

```text
/api/v2
```

Important V2 methods in `api.service.ts` include:

| Method | Purpose |
|---|---|
| `getV2TodayClasses` | Loads professor classes for the selected date |
| `getV2ClassRoster` | Loads class roster and face profile status |
| `saveV2FaceProfile` | Uploads face profile images |
| `recognizeV2Face` | Sends recognition capture image |
| `startV2Session` | Starts live monitoring session |
| `createV2SessionEvent` | Records attendance/break/recognition events |
| `saveV2ManualAttendance` | Saves manual attendance, overrides, and Mark Excused |
| `getV2SessionReview` | Loads post-session review |
| `finalizeV2Session` | Finalizes attendance |

## Blackboard-ready CSV Export

Blackboard-ready CSV export is generated in the browser by:

```text
src/app/v2/pages/post-session-review/post-session-review.component.ts
```

It is a frontend CSV download after finalization. It is not direct Blackboard API synchronization.

## Local Development

Install dependencies:

```bash
npm install
```

Run local dev server:

```bash
npm start
```

or:

```bash
ng serve
```

Build:

```bash
npm run build
```

## Docker Frontend

The V2 Docker frontend files are:

```text
Dockerfile.v2
nginx.v2.conf
```

For full-stack V2 deployment, run Docker Compose from the repository root:

```bash
docker compose -f docker-compose.v2.yml up -d --build
```

## Scope Note

Older admin, report, room schedule, and V1 pages may still exist in the repository for history or earlier work. The final thesis workflow should use the V2 pages under `src/app/v2/`.
