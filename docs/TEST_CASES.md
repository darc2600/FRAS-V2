# FRAS V2 Test Cases

## Functional Tests

| Test Case ID | Module | Scenario | Preconditions | Steps | Expected Result | Priority |
|---|---|---|---|---|---|---|
| FT-LOGIN-001 | Professor Login | Login with valid professor account | Seeded professor account exists | Open login page. Enter valid email and password. Submit. | User is authenticated and redirected to `/v2/classes`. | Critical |
| FT-LOGIN-002 | Professor Login | Login with invalid password | Professor account exists | Enter valid email and wrong password. Submit. | Login fails with unauthorized message. User remains on login page. | Critical |
| FT-LOGIN-003 | Professor Login | Instructor profile mapping | Logged-in user has linked professor row | Login as seeded professor. Open Classes. | Classes shown are for the linked professor only. | Critical |
| FT-CLASSES-001 | Today's Classes | View current day classes | Professor has classes today | Login and open `/v2/classes`. | Current, upcoming, completed, and assigned classes display correctly for selected date. | Critical |
| FT-CLASSES-002 | Today's Classes | Show next class when no current class | Professor has future class but no current class | Open Classes outside active schedule time. | Page shows next class information instead of empty workflow. | High |
| FT-CLASSES-003 | Today's Classes | Start Monitor only for current class | Professor has current and non-current classes | Compare action buttons on assigned classes. | Current class has enabled Start Monitor. Non-current classes are disabled or unavailable. | Critical |
| FT-CLASSES-004 | Today's Classes | Navigate to class roster | Class has students | Click Student List on a class card. | App navigates to `/v2/classes/:classId/students` and loads roster. | Critical |
| FT-CLASSES-005 | Today's Classes | Navigate to class history | Class exists | Click History on class card. | App navigates to `/classes/:classId/session-history`. | High |
| FT-SCHEDULE-001 | Schedule View | Show Mapua-style weekly grid | Professor has weekly schedules | Open Schedule view. | Schedule grid shows days and standard time slots. | High |
| FT-SCHEDULE-002 | Schedule View | Class cell format | Class exists in schedule grid | Inspect class cell. | Cell shows course code, section, and room only. | Medium |
| FT-SCHEDULE-003 | Schedule View | Today and current time highlight | Current date/time intersects grid | Open schedule around a class time. | Current day and current time slot are visually highlighted. | Medium |
| FT-ROSTER-001 | Class Roster | Load enrolled students | Class has active enrollments | Open class roster. | Student table displays enrolled students only. | Critical |
| FT-ROSTER-002 | Class Roster | Select student profile | Roster loaded | Click a student row. | Profile panel opens for selected student. | High |
| FT-ROSTER-003 | Class Roster | Face profile status | Students have mixed profile states | Inspect roster status badges. | Registered, Needs Update, and No Face Profile display correctly. | High |
| FT-ROSTER-004 | Class Roster | Search students | Roster has multiple students | Type name or student number in search. | Table filters matching students. | Medium |
| FT-ROSTER-005 | Class Roster | Register / update face data navigation | Student row selected | Click Register / Update Face Data. | App opens `/classes/:classId/students/:studentId/face-profile`. | Critical |
| FT-STUHIST-001 | Student Attendance History | Open student class history | Student has class history route | Click View Details or Attendance History from roster profile. | App opens `/classes/:classId/students/:studentId/history`. | High |
| FT-STUHIST-002 | Student Attendance History | Summary metrics | Student has session records | Open student history. | Total, present, late, absent, excused, and rate metrics are accurate. | High |
| FT-STUHIST-003 | Student Attendance History | View session evidence | Student has at least one session record | Click View Session Evidence. | App navigates to `/student-evidence/:sessionId/:studentId`. | High |
| FT-FACE-001 | Face Profile Registration | Register student face profile | Student has no face profile. Camera permission granted | Open face profile page. Capture front image. Save. | Face profile status becomes Registered. Embedding is saved/upserted. | Critical |
| FT-FACE-002 | Face Profile Update | Update existing face profile | Student has registered face profile | Open face profile page. Capture replacement image. Save. | Existing active profile is replaced/deactivated and new active profile is saved. | Critical |
| FT-FACE-003 | Face Profile Registration | Save disabled without capture | Face profile page opened | Do not capture image. Inspect Save button. | Save Face Profile is disabled or blocked. | High |
| FT-FACE-004 | Face Profile Registration | Retake captured frame | Captured image exists | Click retake/reset and capture again. | Previous temporary capture is replaced before save. | Medium |
| FT-LIVE-001 | Live Session | Start session | Current class exists with enrolled students | Click Start Monitor. | Session is created and app opens `/live-session/:sessionId`. | Critical |
| FT-LIVE-002 | Live Session | Header information | Live session loaded | Inspect header. | Course, section, room, schedule, timer, and status display. | High |
| FT-LIVE-003 | Live Session | Session timer | Session started | Wait at least 1 minute. | Timer counts actual monitored duration from session start. | High |
| FT-LIVE-004 | Live Session | Camera panel placeholder/preview | Live session opened | Grant or deny camera permission. | Camera preview appears when granted; helpful permission message appears when denied. | Critical |
| FT-LIVE-005 | Live Session | Live roster counts | Session has enrolled students | Inspect roster summary. | Present, Late, Break, Absent, Excused counts match record statuses. | Critical |
| FT-LIVE-006 | Live Session | Student drawer opens only on click | Live roster loaded | Observe page, then click student. | Drawer is closed by default and opens only after clicking a student. | High |
| FT-LIVE-007 | Live Session | Student break out/in | Student drawer opened | Click Break Out, then Break In. | Student event log and status update correctly. | High |
| FT-LIVE-008 | Live Session | Student override quick panel | Student drawer opened | Click Override and choose status. | Selected student status updates and is locked as professor-confirmed. | High |
| FT-AUTO-001 | Auto Capture | Start auto capture | Live session loaded, camera available | Click Start Auto Capture. | Auto capture becomes active and primary button changes to Stop Auto Capture. | Critical |
| FT-AUTO-002 | Auto Capture | Stop auto capture | Auto capture active | Click Stop Auto Capture. | Auto capture stops and button returns to Start Auto Capture. | Critical |
| FT-AUTO-003 | Auto Capture | Recognition updates roster | Student face registered and visible | Start auto capture or trigger capture. | Recognized student receives time in or break in event and roster updates. | Critical |
| FT-MANUAL-001 | Manual Attendance | Open manual attendance modal | Live session loaded | Click Manual Attendance. | Modal opens with student list and Absent, Excused, Late, Present options. | Critical |
| FT-MANUAL-002 | Manual Attendance | Mark present manually | Student is absent | Choose Present and save. | Student receives manual attendance event, time in is set if missing, and status becomes Present. | Critical |
| FT-MANUAL-003 | Manual Attendance | Mark late manually | Student is absent | Choose Late and save. | Student receives manual attendance event, time in is set if missing, and status becomes Late. | High |
| FT-MANUAL-004 | Manual Attendance | Mark absent provisionally | Student is absent | Choose Absent and save, then recognize student. | Recognition can update the student to Present or Late according to policy if not professor-confirmed. | High |
| FT-MANUAL-005 | Manual Attendance | Mark excused manually | Student is absent | Choose Excused and save. | Student status becomes Excused and remains professor-confirmed. | High |
| FT-BREAK-001 | Session Break | Start session break | Live session in progress with present students | Click Session Break. | Session status becomes On Break and break_out events are created for active present/late students. | Critical |
| FT-BREAK-002 | Session Break | Break mode screen | Session is on break | Observe live session screen. | Read-only break mode screen shows Return Detection Mode, returned count, outside count, and recent break in events. | Critical |
| FT-BREAK-003 | Return Detection Mode | Returned student breaks in automatically | Session on break. Student is on break. Face registered | Recognize returning student. | System creates break_in event and returned count increases. | Critical |
| FT-BREAK-004 | Session Break | End break unlock | Session on break | Enter professor password/PIN and end break. | Session returns to In Progress and controls unlock. | Critical |
| FT-END-001 | End Session | End in-progress session | Live session in progress | Click End Session and confirm if prompted. | Session ends and app navigates to `/session-review/:sessionId`. | Critical |
| FT-REVIEW-001 | Post Session Review | Load review page | Session ended | Open session review. | Header, summary metrics, roster table, actions, and footer actions display. | Critical |
| FT-REVIEW-002 | Post Session Review | View student evidence | Review page loaded | Click View Details. | App navigates to `/student-evidence/:sessionId/:studentId`. | High |
| FT-REVIEW-003 | Post Session Review | Override status | Review page loaded | Enable or open override. Choose Present, Late, Absent, or Excused. Save. | Student final status updates and record is professor-confirmed. | Critical |
| FT-REVIEW-004 | Post Session Review | Mark excused | Review page loaded | Mark student as Excused through override/manual action. | Student status becomes Excused and review metrics update. | High |
| FT-REVIEW-005 | Post Session Review | Reviewed indicator | Student accepted or overridden | Return to review page. | Row shows Reviewed or equivalent professor-confirmed state. | High |
| FT-EVIDENCE-001 | Student Evidence | Load evidence page | Session and student record exist | Open `/student-evidence/:sessionId/:studentId`. | Breadcrumb, student header, assessment, metrics, timeline, evidence summary, notes, and actions display. | Critical |
| FT-EVIDENCE-002 | Student Evidence | Accept current status | Evidence page loaded | Click Accept Current Status. | Record becomes professor-confirmed and review flag clears. | High |
| FT-EVIDENCE-003 | Student Evidence | Override with reason | Evidence page loaded | Open override. Choose new status and reason. Save. | Record status changes, reason is logged, and page updates. | Critical |
| FT-FINAL-001 | Finalize Attendance | Finalize session | Review page loaded | Click Finalize Attendance. | Session status becomes finalized and records are locked. | Critical |
| FT-FINAL-002 | Finalize Attendance | Export enabled after finalize | Session finalized | Inspect Export Blackboard CSV button. | CSV export is enabled after finalization. | Critical |
| FT-CSV-001 | CSV Export | Export Blackboard CSV | Finalized session exists | Click Export Blackboard CSV. | CSV downloads with final professor-reviewed statuses only. | Critical |
| FT-CSV-002 | CSV Export | CSV filename format | Finalized session exists | Export CSV. | Filename includes FRAS/session/course/date context using agreed format. | Medium |
| FT-HISTORY-001 | Class Session History | Open class-specific history | Class has sessions | Open `/classes/:classId/session-history`. | Page shows only sessions for selected class. | Critical |
| FT-HISTORY-002 | Professor Session History | Open sidebar history | Professor has sessions across classes | Click sidebar Session History or open `/session-history`. | Page shows sessions across all classes for logged-in professor. | Critical |
| FT-HISTORY-003 | Session History | Filter sessions | History page has multiple sessions | Apply date, rate, status, and review filters. | Table updates to matching sessions only. | High |
| FT-HISTORY-004 | Session History | View Session Summary | History row exists | Click View Session Summary. | App opens `/session-review/:sessionId`. | High |
| FT-HISTORY-005 | Session History | Export full history | History page has sessions | Click Export Full History. | CSV downloads for currently filtered rows. | Medium |

## Integration Tests

| Test Case ID | Module | Scenario | Preconditions | Steps | Expected Result | Priority |
|---|---|---|---|---|---|---|
| IT-FLOW-001 | Full Workflow | Complete professor attendance lifecycle | Test professor, current class, enrolled students | Login. Start session. Capture/mark attendance. End session. Review. Finalize. Export CSV. Open history. | Full flow completes without broken navigation or data mismatch. | Critical |
| IT-FLOW-002 | Roster to face profile to recognition | Student has no face profile | Open roster. Register face. Start session. Recognize student. | Student recognition succeeds and roster status updates. | Critical |
| IT-FLOW-003 | Student history to evidence | Completed session exists | Open roster. Open student history. Click View Session Evidence. | Evidence page loads correct student/session record. | High |
| IT-FLOW-004 | Review to history consistency | Session finalized | Finalize session. Open class history. Open professor history. | Same finalized session appears in both histories with consistent status. | Critical |
| IT-FLOW-005 | Manual attendance and recognition | Live session active | Mark student absent manually. Recognize student after late threshold. | Student can move to Late/Present if not professor-confirmed. | High |
| IT-FLOW-006 | Override survives recalculation | Student overridden in review | Override status. Refresh review page. Open evidence. | Override remains and recalculation does not replace professor-confirmed status. | Critical |
| IT-FLOW-007 | Break return detection | Live session with present students | Start break. Recognize returning students. End break. End session. | Break_out and break_in events affect outside duration and returned count. | Critical |
| IT-FLOW-008 | Professor isolation | Two professor accounts with sessions | Login as professor A, open `/session-history`; login as professor B, open same. | Each professor sees only their own sessions. | Critical |
| IT-FLOW-009 | Finalized CSV consistency | Finalized session with overrides | Export CSV and compare with review table. | CSV statuses match final reviewed statuses. | Critical |
| IT-FLOW-010 | Seed data consistency | Fresh seeded database | Run seed. Login test professor. Open classes, roster, history. | Professor, courses, rooms, classes, students, and enrollments are linked. | Critical |

## UI Tests

| Test Case ID | Module | Scenario | Preconditions | Steps | Expected Result | Priority |
|---|---|---|---|---|---|---|
| UI-NAV-001 | Sidebar | Professor-only navigation | Logged in as instructor | Inspect sidebar. | Sidebar shows instructor pages only. Admin/settings/user management V1 noise is absent. | High |
| UI-NAV-002 | Sidebar | Active nav state | Navigate between Classes, Session History, Schedule | Inspect active item. | Only current page is highlighted. | Medium |
| UI-CLASSES-001 | Classes | Responsive class cards | Desktop and smaller viewport | Resize viewport. | Text does not overlap and buttons remain visible. | Medium |
| UI-ROSTER-001 | Roster | Search input style | Roster loaded | Inspect search field. | Font size and input styling match V2 design system. | Medium |
| UI-ROSTER-002 | Roster | Student avatar initials | Roster/profile panel loaded | Inspect avatar. | Initials are centered horizontally and vertically. | Medium |
| UI-FACE-001 | Face Profile | Camera panel layout | Face profile page opened | Inspect preview and controls. | Camera area, guide, status, and controls are aligned and not clipped. | Medium |
| UI-LIVE-001 | Live Session | Camera and controls visibility | Live session loaded | Inspect above-the-fold layout. | Camera, roster, and primary controls are visible without awkward stretching. | High |
| UI-LIVE-002 | Live Session | Session controls hierarchy | Live session loaded | Inspect controls. | Auto Capture is primary. Manual actions are secondary. Session Break is warning. End Session is destructive but visually separated. | High |
| UI-LIVE-003 | Live Session | Student drawer scroll behavior | Student has long activity log | Open drawer. | Activity summary scrolls without pushing action buttons below page. | Medium |
| UI-BREAK-001 | Break Mode | Read-only break UI | Session on break | Inspect break screen. | Locked controls and return detection status are clear. | Critical |
| UI-REVIEW-001 | Post Session Review | Table overflow | Review table has many columns | Resize viewport. | Table scrolls horizontally without overlapping. | High |
| UI-EVIDENCE-001 | Student Evidence | Timeline readability | Evidence has many events | Inspect timeline. | Latest events appear clearly and long timelines remain readable. | Medium |
| UI-HISTORY-001 | Session History | Professor-wide table | Open `/session-history` | Inspect table. | Course column appears and page no longer shows placeholder-only message. | High |
| UI-HISTORY-002 | Session History | Class-specific table | Open `/classes/:classId/session-history` | Inspect table. | Class context appears and table omits redundant Course column. | Medium |

## Negative Tests

| Test Case ID | Module | Scenario | Preconditions | Steps | Expected Result | Priority |
|---|---|---|---|---|---|---|
| NT-AUTH-001 | Auth Guard | Access V2 page without login | Logged out | Open `/v2/classes`. | User is redirected to login or blocked. | Critical |
| NT-AUTH-002 | Auth Guard | Access live session without login | Logged out | Open `/live-session/:sessionId`. | User is redirected to login or blocked. | Critical |
| NT-PROF-001 | Professor Isolation | Open another professor's session history by URL | Logged in as professor A | Open professor B's class history URL if known. | Access is blocked or data isolation is enforced by backend/frontend policy. | Critical |
| NT-FACE-001 | Face Profile | Save with no camera/image | Face profile page opened | Try saving without capture. | Save is blocked with clear message. | High |
| NT-FACE-002 | Face Profile | Camera permission denied | Browser camera permission denied | Open face profile or live session. | App shows camera permission message and does not crash. | Critical |
| NT-RECOG-001 | Recognition | Unknown face | Live session active | Capture face not registered in class. | No student is marked present. Unknown/no match state appears. | Critical |
| NT-RECOG-002 | Recognition | Face registered but not enrolled in class | Student embedding exists outside class | Capture student in another class session. | Student is not matched for this class. | Critical |
| NT-BREAK-001 | Session Break | Manual attendance while on break | Session on break | Attempt manual attendance. | Backend blocks action and UI keeps controls locked. | Critical |
| NT-BREAK-002 | Session Break | End session while on break | Session on break | Attempt End Session. | Backend returns locked error and session remains on break. | Critical |
| NT-BREAK-003 | Session Break | Finalize while on break | Session on break | Attempt finalize through URL/API. | Backend blocks finalization. | Critical |
| NT-BREAK-004 | Session Break | Override while on break | Session on break | Attempt override through UI or API. | Backend blocks override. | Critical |
| NT-BREAK-005 | Session Break | Navigation while on break | Session on break | Click sidebar or browser back. | Route guard blocks navigation or returns to break screen. | Critical |
| NT-REVIEW-001 | Review | Override finalized session | Session finalized | Attempt override or mark excused. | Backend blocks changes. | Critical |
| NT-CSV-001 | CSV Export | Export before finalization | Session under review | Click Export Blackboard CSV. | Export is disabled or blocked until finalized. | High |
| NT-HISTORY-001 | Session History | No history rows | Professor has no sessions | Open `/session-history`. | Empty state appears without error. | Medium |

## Edge Case Tests

| Test Case ID | Module | Scenario | Preconditions | Steps | Expected Result | Priority |
|---|---|---|---|---|---|---|
| EC-TIME-001 | Attendance Policy | Student arrives within first 15 minutes | Live session started | Recognize student 1 to 15 minutes after actual start. | Student is Present, subject to presence ratio. | Critical |
| EC-TIME-002 | Attendance Policy | Student arrives after 15 minutes | Live session started | Recognize student 16 to 30 minutes after actual start. | Student is Late. | Critical |
| EC-TIME-003 | Attendance Policy | Student arrives after 30 minutes | Live session started | Recognize student more than 30 minutes after actual start. | Student is Absent with review note that they arrived very late. | Critical |
| EC-TIME-004 | Attendance Policy | Professor starts class late | Scheduled start is earlier than actual start | Start session late and recognize students. | Late calculation uses actual monitored start, not scheduled start. | Critical |
| EC-TIME-005 | Attendance Policy | Professor ends class early | Scheduled class is long | End session early. | Session duration and presence ratios use actual monitored duration. | Critical |
| EC-BREAK-001 | Session Break | Student not present before break | Student has no time in | Start Session Break. | Student without time in remains Absent and does not receive break_out. | High |
| EC-BREAK-002 | Return Detection | Student returns after break ended | Student still on break | End break, then recognize student. | Student receives valid break_in/time event according to current session state. | High |
| EC-BREAK-003 | Return Detection | Student tries to time in during break | Student absent before break | Recognize absent student while session on break. | System handles according to policy. Expected behavior should be confirmed and documented. | High |
| EC-RECOG-001 | Recognition | Multiple faces in registration frame | Face registration page open | Capture frame with multiple faces. | System uses first detected face only or warns clearly. | High |
| EC-RECOG-002 | Recognition | Duplicate face profile update | Student has active embedding | Update face data multiple times. | Only one active embedding per student/model/angle remains. | Critical |
| EC-ROSTER-001 | Roster | Class with zero students | Class exists with no enrollments | Open class roster and start session if allowed. | Empty roster state displays. No crash. | Medium |
| EC-HISTORY-001 | Session History | Filter removes all rows | History has rows | Apply restrictive filters. | Empty filtered state appears. | Medium |
| EC-CSV-001 | CSV Export | Student names with comma | Student has comma in display name | Export CSV. | CSV escapes values correctly. | High |
| EC-CSV-002 | CSV Export | Excused and reviewed statuses | Session has excused and overrides | Export CSV. | CSV uses final status values: Present, Late, Absent, Excused. | Critical |

