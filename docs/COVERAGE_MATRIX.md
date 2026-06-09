# FRAS V2 Coverage Matrix

## Requirement to Test Case Mapping

| Requirement | Test Cases |
|---|---|
| Professor can log in with seeded account | FT-LOGIN-001, FT-LOGIN-002, FT-LOGIN-003, IT-FLOW-010 |
| Unauthenticated users cannot access V2 pages | NT-AUTH-001, NT-AUTH-002 |
| Classes page shows professor-specific schedule | FT-CLASSES-001, FT-CLASSES-002, FT-CLASSES-003, IT-FLOW-008 |
| Classes page supports Student List navigation | FT-CLASSES-004, FT-ROSTER-001 |
| Classes page supports class Session History navigation | FT-CLASSES-005, FT-HISTORY-001 |
| Schedule view shows weekly professor schedule | FT-SCHEDULE-001, FT-SCHEDULE-002, FT-SCHEDULE-003 |
| Class roster loads enrolled students | FT-ROSTER-001, FT-ROSTER-002, FT-ROSTER-004 |
| Class roster shows face profile and recognition states | FT-ROSTER-003, UI-ROSTER-001, UI-ROSTER-002 |
| Student Attendance History loads class-specific student records | FT-STUHIST-001, FT-STUHIST-002, FT-STUHIST-003, IT-FLOW-003 |
| Register Face Profile works | FT-FACE-001, FT-FACE-003, FT-FACE-004, NT-FACE-001, NT-FACE-002 |
| Update Face Profile replaces old active profile | FT-FACE-002, EC-RECOG-002 |
| Face registration uses first detected face only | EC-RECOG-001 |
| Live Session can be started from current class | FT-LIVE-001, IT-FLOW-001 |
| Live Session header and timer are accurate | FT-LIVE-002, FT-LIVE-003, EC-TIME-004, EC-TIME-005 |
| Camera panel works or handles permission failure | FT-LIVE-004, NT-FACE-002, UI-FACE-001, UI-LIVE-001 |
| Live roster counts update | FT-LIVE-005, FT-AUTO-003, FT-MANUAL-002, FT-MANUAL-003, FT-MANUAL-005 |
| Student drawer opens on click and shows actions | FT-LIVE-006, FT-LIVE-007, FT-LIVE-008, UI-LIVE-003 |
| Auto Capture is primary workflow | FT-AUTO-001, FT-AUTO-002, FT-AUTO-003, UI-LIVE-002 |
| Manual Capture supports recognition fallback | FT-AUTO-003, NT-RECOG-001, NT-RECOG-002 |
| Manual Attendance modal supports Present, Late, Absent, Excused | FT-MANUAL-001, FT-MANUAL-002, FT-MANUAL-003, FT-MANUAL-004, FT-MANUAL-005 |
| Manual attendance present/late sets time in when missing | FT-MANUAL-002, FT-MANUAL-003, IT-FLOW-005 |
| Manual absent remains provisional unless finalized/confirmed | FT-MANUAL-004, IT-FLOW-005 |
| Professor-confirmed overrides survive recalculation | FT-REVIEW-003, IT-FLOW-006 |
| Session Break creates break_out events for active students | FT-BREAK-001, EC-BREAK-001 |
| Session Break locks professor controls and navigation | FT-BREAK-002, NT-BREAK-001, NT-BREAK-002, NT-BREAK-003, NT-BREAK-004, NT-BREAK-005, UI-BREAK-001 |
| Return Detection Mode creates break_in events | FT-BREAK-003, FT-BREAK-004, IT-FLOW-007, EC-BREAK-002 |
| End Session navigates to Post Session Review | FT-END-001, IT-FLOW-001 |
| Post Session Review displays summary and roster | FT-REVIEW-001, UI-REVIEW-001 |
| View Details opens Student Evidence | FT-REVIEW-002, FT-EVIDENCE-001 |
| Mark Excused / override updates final status | FT-REVIEW-003, FT-REVIEW-004, FT-EVIDENCE-003 |
| Accept Current Status marks record reviewed | FT-EVIDENCE-002, FT-REVIEW-005 |
| Finalize Attendance locks session | FT-FINAL-001, NT-REVIEW-001 |
| CSV Export is enabled only after finalization | FT-FINAL-002, NT-CSV-001 |
| CSV Export contains final professor-reviewed statuses | FT-CSV-001, FT-CSV-002, IT-FLOW-009, EC-CSV-001, EC-CSV-002 |
| Class-specific Session History shows one class only | FT-HISTORY-001, FT-HISTORY-003, FT-HISTORY-004, UI-HISTORY-002 |
| Professor-wide Session History shows all classes for logged-in professor | FT-HISTORY-002, FT-HISTORY-003, FT-HISTORY-004, FT-HISTORY-005, IT-FLOW-004, IT-FLOW-008, UI-HISTORY-001, NT-HISTORY-001 |
| Session History filters work | FT-HISTORY-003, EC-HISTORY-001 |
| Very late arrivals are absent with review notes | EC-TIME-003 |
| Attendance policy uses actual monitored duration | EC-TIME-004, EC-TIME-005 |
| UI follows V2 design system | UI-NAV-001, UI-NAV-002, UI-CLASSES-001, UI-ROSTER-001, UI-ROSTER-002, UI-FACE-001, UI-LIVE-001, UI-LIVE-002, UI-LIVE-003, UI-BREAK-001, UI-REVIEW-001, UI-EVIDENCE-001, UI-HISTORY-001, UI-HISTORY-002 |

## Coverage Gaps

| Gap ID | Area | Gap | Risk | Recommended Next Action |
|---|---|---|---|---|
| GAP-001 | Blackboard CSV | Exact Blackboard column format may still need validation against real Blackboard import rules. | Export may be syntactically valid CSV but not accepted by Blackboard. | Get Blackboard sample import format and add exact CSV validation tests. |
| GAP-002 | Return Detection Policy | Behavior for students who were absent before Session Break but are recognized during break needs final product decision. | Inconsistent attendance behavior during professor break. | Decide whether absent students can time in during break or only active students can break in. |
| GAP-003 | Camera Reliability | Camera tests require real browser/device and cannot be fully proven by build tests. | Face capture may fail on some devices or browsers. | Run browser camera QA on Chrome and Edge with multiple webcams if available. |
| GAP-004 | Face Recognition Accuracy | Recognition confidence depends on lighting, camera, model, and face data quality. | False positives or false negatives during live monitoring. | Create controlled test images and record recognition confidence across repeated captures. |
| GAP-005 | Multi-face Registration | System should use first detected face only, but UI warning may need improvement. | Wrong student could be registered if multiple faces appear. | Add stronger UI instruction/warning and an automated backend assertion if feasible. |
| GAP-006 | Backend Authorization | Some professor isolation may rely on frontend professor mapping unless backend auth scoping is enforced per endpoint. | A user may access another professor's class/session by direct URL or API call. | Add backend auth dependency checks once auth token scoping is finalized. |
| GAP-007 | Route Guard Refresh | Session Break lock behavior should be tested for browser refresh, direct URL navigation, and back button. | Professor controls could become available while session is on break. | Add explicit route guard tests and manual browser scenarios. |
| GAP-008 | Mobile Layout | V2 is optimized for desktop classroom monitoring. Mobile support may be partial. | Tables/camera panels may be awkward on small screens. | Define minimum supported viewport and test responsive breakpoints. |
| GAP-009 | Seed Data Drift | Seed data can change if the DOCX is updated or scripts are run destructively. | QA results may not reproduce across machines. | Keep seed docs updated and prefer non-destructive seed commands unless full reset is intended. |
| GAP-010 | Performance | Large rosters and frequent auto capture are not yet load-tested. | UI or backend may slow during real classroom use. | Add timing tests for 30, 60, and 100 student rosters with auto capture active. |

## Critical Path Coverage

The critical professor workflow is covered by:

- Login: FT-LOGIN-001, FT-LOGIN-003
- Classes: FT-CLASSES-001, FT-CLASSES-003
- Roster: FT-ROSTER-001, FT-ROSTER-005
- Face Profile: FT-FACE-001, FT-FACE-002
- Live Session: FT-LIVE-001 through FT-LIVE-008
- Auto Capture: FT-AUTO-001 through FT-AUTO-003
- Session Break: FT-BREAK-001 through FT-BREAK-004
- Review: FT-REVIEW-001 through FT-REVIEW-005
- Evidence: FT-EVIDENCE-001 through FT-EVIDENCE-003
- Finalize and CSV: FT-FINAL-001, FT-FINAL-002, FT-CSV-001
- History: FT-HISTORY-001 through FT-HISTORY-005
- Full integration: IT-FLOW-001, IT-FLOW-004, IT-FLOW-007, IT-FLOW-009

