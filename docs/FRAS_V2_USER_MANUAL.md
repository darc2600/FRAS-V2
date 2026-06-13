# FRAS V2 User Manual

## 1. Introduction

FRAS V2 is an instructor-focused classroom presence monitoring system. It helps professors view their assigned classes, manage student face profiles, monitor live attendance using facial recognition, handle session breaks, review attendance evidence, finalize attendance, and export attendance files for Blackboard.

This manual is written for professors or instructors using the FRAS V2 web application.

## 2. Recommended Setup

Before using FRAS V2, prepare the following:

1. Use a modern browser such as Google Chrome or Microsoft Edge.
2. Make sure the device has a working webcam.
3. Allow camera permission when the browser asks for it.
4. Use a stable internet or local network connection.
5. Log in using a professor account provided by the system administrator or development team.

If the camera does not appear, check the browser permission icon near the address bar and make sure camera access is allowed for the FRAS website.

## 3. How To Log In

1. Open the FRAS V2 website in the browser.
2. Wait for the login page to load.
3. Enter the professor email address.
4. Enter the professor password.
5. Click **Login**.
6. After successful login, the system opens the professor Classes page.

If login fails:

1. Check if the email address is typed correctly.
2. Check if the password is typed correctly.
3. Make sure the professor account exists in the database.
4. Ask the system administrator or developer to verify the account.

## 4. How To Sign Out

1. Look at the left sidebar.
2. Click **Sign Out** at the bottom of the sidebar.
3. The system logs out the professor account.
4. The login page is shown again.

Always sign out after using FRAS on a shared computer.

## 5. Understanding The Sidebar

The sidebar is the main navigation area of FRAS V2.

Common sidebar items:

1. **Classes** - opens the main professor class dashboard.
2. **Session History** - opens the professor session history page.
3. **Schedule** - shows the professor schedule view.
4. **Sign Out** - logs out the current professor account.

The professor card under the Mapua logo shows the logged-in professor name and department.

## 6. How To View Today’s Classes

1. Log in to FRAS V2.
2. Click **Classes** in the sidebar.
3. The page shows classes assigned to the professor.
4. Check the date shown near the top of the page.
5. Review the class cards displayed for the selected date.

Each class card may show:

1. Course code.
2. Section.
3. Room.
4. Scheduled time.
5. Student count.
6. Available actions such as **Start Monitor**, **Student List**, and **Session History**.

If there are no classes for the current date, the page may show the next class or the assigned class schedule.

## 7. How To View Current Class Session

1. Open the **Classes** page.
2. Look for the class that is currently scheduled.
3. Check if the class time matches the current time.
4. If the class is active or ready to start, click **Start Monitor**.
5. The system opens the Live Session Monitoring page.

If the class is not currently active, the **Start Monitor** button may be disabled or unavailable depending on the system rules.

## 8. How To View The Professor Schedule

1. Open the **Classes** page.
2. Select **Schedule View** if available.
3. Alternatively, click **Schedule** in the sidebar.
4. The weekly schedule grid is displayed.
5. Review classes by day and time.

Each schedule entry usually shows:

1. Course code.
2. Section.
3. Room.

Example:

```text
ITS161-1L
BM8
MPO402
```

The current day and current time slot may be highlighted to help the professor identify the ongoing schedule.

## 9. How To Switch Between Card View And Schedule View

1. Open the **Classes** page.
2. Find the view control near the date selector.
3. Click **Card View** to see classes as individual cards.
4. Click **Schedule View** to see classes in a weekly timetable.

Use **Card View** for quick class actions. Use **Schedule View** to inspect the full teaching schedule.

## 10. How To View Student List

1. Open the **Classes** page.
2. Find the class you want to inspect.
3. Click **Student List**.
4. The Class Roster page opens.
5. Review the list of enrolled students.

The Student List page may show:

1. Student avatar or initials.
2. Student number.
3. Student name.
4. Face profile status.
5. Recognition status.
6. Attendance rate.
7. Last face update.

## 11. How To Search Or Filter Students

1. Open the **Student List** page.
2. Click the search field.
3. Type a student name or student number.
4. The list updates based on the search text.
5. Clear the search field to show all students again.

If filters are available on a history page:

1. Select the date range or status filter.
2. Click **Apply Filters**.
3. Review the filtered table results.
4. Clear or reset filters when needed.

## 12. How To View Student Details

1. Open the **Student List** page.
2. Click a student row.
3. The student detail panel opens.
4. Review the student information.

The student detail panel may show:

1. Student name.
2. Student number.
3. Course and section.
4. Face profile status.
5. Last face update.
6. Recognition confidence.
7. Attendance summary.
8. Recent attendance or recognition history.

## 13. Face Profile Status Meanings

FRAS V2 uses face profile statuses to show whether a student can be recognized by the system.

1. **Registered** - the student has active face data and can be used for recognition.
2. **Needs Update** - the student has face data, but it may need to be retaken.
3. **No Face Profile** - the student does not have face data yet.

If a student has no face profile, facial recognition cannot automatically identify that student until registration is completed.

## 14. How To Register Or Update Face Data

1. Open the **Student List** page.
2. Select the student.
3. Click **Register / Update Face Data**.
4. The Face Profile Registration page opens.
5. Allow camera access if the browser asks for permission.
6. Position the student’s face inside the camera guide.
7. Wait for the quality checks to show that capture is ready.
8. Click **Capture Frame**.
9. Review the captured image or capture status.
10. Retake if needed.
11. Click **Save Face Profile**.
12. After saving, return to the Student List.

The saved face profile is shared by the student across classes. The student does not need a separate face profile for every class.

## 15. How To Capture A Good Face Profile

For best recognition results:

1. Make sure only one face is visible in the camera.
2. Ask the student to face the camera directly.
3. Keep the face centered in the guide frame.
4. Avoid very dark lighting.
5. Avoid strong backlight.
6. Avoid blurry movement.
7. Remove objects that block the face, if possible.
8. Retake the photo if the system reports poor quality or ambiguous recognition.

If the system says the image is ambiguous, the face may be too similar to another stored profile, the image may be low quality, or the captured face may not be clear enough.

## 16. What To Do If Face Registration Fails

If registration does not work:

1. Check that the camera is visible.
2. Check browser camera permission.
3. Improve lighting.
4. Move closer to the camera.
5. Make sure only one face is inside the frame.
6. Retake the capture.
7. Try again from the Student List page.

If registration repeatedly fails for a student, mark that student for manual attendance during testing and retake the face profile later.

## 17. How To View Student Attendance History

1. Open the **Student List** page.
2. Select a student.
3. Click **View Details** or **Attendance History**, depending on the available button.
4. The Student Attendance History page opens.
5. Review the student’s attendance records for the selected class.

The page may show:

1. Total sessions.
2. Present sessions.
3. Late sessions.
4. Absent sessions.
5. Excused sessions.
6. Attendance rate.
7. Session-by-session attendance table.

## 18. How To View Class History

1. Open the **Classes** page.
2. Find the class you want to inspect.
3. Click **Session History**.
4. The Session History page opens for that class.
5. Review previous sessions for the selected class.

The table may show:

1. Date.
2. Time range.
3. Attendance count.
4. Attendance rate.
5. Average presence duration.
6. Warning count.
7. Excused count.
8. Session status.

## 19. How To View Professor Session History

1. Click **Session History** in the sidebar.
2. The system shows the professor’s completed or review-needed sessions.
3. Use filters if needed.
4. Click a session action to open the session review or summary.

For a more focused view, open session history from a specific class card.

## 20. How To Start A Session

1. Open the **Classes** page.
2. Find the class to monitor.
3. Click **Start Monitor**.
4. The Live Session Monitoring page opens.
5. Confirm that the class header shows the correct course, section, room, and schedule.
6. Click **Start Session** if the session has not started yet.
7. The session timer begins counting.

The session timer measures the actual monitored duration of the class. If a class is scheduled for three hours but the professor monitors only one hour, attendance is based on the actual monitored session.

## 21. Live Session Page Overview

The Live Session page usually contains:

1. Session header.
2. Camera or recognition panel.
3. Recognition activity feed.
4. Live roster.
5. Session controls.
6. Student detail panel when a student is clicked.

The live roster shows each student’s current session status.

Common statuses:

1. **Present** - student has been counted as present.
2. **Late** - student arrived after the allowed present window.
3. **Absent** - student has not been counted as present or late.
4. **Excused** - professor or review process marked the student as excused.
5. **Break** - student is currently outside or on break.

## 22. Difference Between Auto Capture, Manual Capture, And Manual Attendance

FRAS V2 has different attendance methods.

**Auto Capture**

1. Main monitoring workflow.
2. The system continuously checks the camera.
3. Recognized students are recorded automatically.
4. Best for live classroom presence monitoring.

**Manual Capture**

1. Professor manually triggers one recognition attempt.
2. Useful when the professor wants to capture a student at a specific moment.
3. Still uses facial recognition.

**Manual Attendance**

1. Professor directly marks students as present, late, absent, or excused.
2. Useful when the professor does not want to use facial recognition.
3. Manual present or late can create a time-in record if the student has not timed in yet.
4. Manual absent can remain provisional, so facial recognition can still update the student later if allowed by the session flow.

## 23. How To Use Auto Capture

1. Open the Live Session page.
2. Make sure the camera panel is visible.
3. Click **Start Auto Capture**.
4. The system begins automatic recognition.
5. Students who are recognized are updated in the live roster.
6. Recognition events appear in the activity feed.
7. Click **Stop Auto Capture** when automatic monitoring should stop.

If a face is unclear, weak, or too similar to another student, the system may return no recognition or ambiguous recognition instead of marking attendance.

## 24. How To Use Manual Capture

1. Open the Live Session page.
2. Make sure the student is visible in the camera.
3. Click **Manual Capture**.
4. The system performs one recognition attempt.
5. If the student is confidently recognized, the roster and activity feed update.
6. If the system cannot recognize the face, reposition the student and try again.

Manual Capture is useful when the professor wants direct control over when a recognition attempt happens.

## 25. How To Manually Take Attendance

1. Open the Live Session page.
2. Click **Manual Attendance**.
3. A Manual Attendance modal opens.
4. Search for a student if needed.
5. For each student, select one status:
   - **Absent**
   - **Excused**
   - **Late**
   - **Present**
6. Review the selected statuses.
7. Click **Save Attendance**.
8. The live roster updates immediately.

Use Manual Attendance when facial recognition is not preferred, unavailable, or when the professor wants to quickly record attendance for multiple students.

## 26. How To Start Session Break

1. Open an active Live Session.
2. Click **Session Break**.
3. The system sets the session status to break mode.
4. Active students are marked with break-out events.
5. The system enters Return Detection Mode.

Session Break is intended for class-wide breaks, such as lunch break or a long professor-approved pause.

## 27. What Happens During Session Break

During Session Break:

1. The session status becomes **On Break**.
2. Active students receive break-out events.
3. Auto Capture switches to Return Detection Mode.
4. Return Detection Mode only records break-in events.
5. Students who return and are recognized are marked as returned.
6. The page shows returned count and still-outside count.
7. Professor controls are locked for safety.

Controls are locked so students cannot use the unattended device to change attendance, override statuses, finalize attendance, or end the session.

## 28. How Students Break In From Session Break

1. The professor starts Session Break.
2. Return Detection Mode remains active.
3. A student returns to the room.
4. The student faces the camera.
5. The system recognizes the student.
6. A break-in event is recorded.
7. The student is counted as returned.

Students who have not returned remain on break until recognized or manually updated after the professor unlocks controls.

## 29. How To Resume Class From Session Break

1. Return to the Live Session page.
2. Unlock professor controls using the required password, PIN, or re-authentication flow.
3. Click **End Break** or **Resume Monitoring**.
4. The session returns to **In Progress**.
5. Normal monitoring controls become available again.
6. Students still on break remain marked as out until they are recognized or updated manually.

## 30. How To Break Out A Specific Student

1. Open the Live Session page.
2. Click the student in the live roster.
3. The student detail panel opens.
4. Set or confirm the student break time limit if available.
5. Click **Break Out**.
6. The system records the student break-out event.
7. The student status changes to break or outside.

Use this for individual bathroom breaks, canteen trips, or professor-approved errands.

## 31. How To Break In A Specific Student

1. Open the Live Session page.
2. Click the student in the live roster.
3. If the student is currently out, click **Break In**.
4. The system records the student break-in event.
5. The student status returns to the appropriate in-class status.

The student may also break in through facial recognition if the return event is recognized by the system.

## 32. How To Change A Student Break Time Limit

1. Open the Live Session page.
2. Click the student in the live roster.
3. Find the student break limit field.
4. Change the allowed minutes.
5. Use **Break Out** to start the individual break.

The professor may adjust the limit depending on the reason for the student’s break.

## 33. How To Override A Specific Student During Live Session

1. Open the Live Session page.
2. Click the student in the live roster.
3. Click **Override**.
4. Select the new status:
   - Present
   - Late
   - Absent
   - Excused
5. Confirm the override.
6. The student status updates in the roster.

Use override only when the professor needs to correct or confirm the system result.

## 34. How To End A Session

1. Open the active Live Session.
2. Make sure attendance monitoring is complete.
3. Click **End Session**.
4. Confirm the action if the system asks for confirmation.
5. The session ends.
6. The system opens the Post-Session Review page.

End Session closes the live monitoring flow and moves the professor to review.

## 35. Post-Session Review Overview

The Post-Session Review page allows the professor to review all student attendance records before finalizing.

The page may show:

1. Course and session information.
2. Summary metrics.
3. Student review table.
4. View Details action.
5. Override tools.
6. Mark Excused action.
7. Finalize Attendance button.
8. Export buttons.

This step is important because it lets the professor validate attendance before exporting final records.

## 36. How To Override Attendance In Post-Session Review

1. Open the Post-Session Review page.
2. Find the student in the review table.
3. Use the override control or open the override mode.
4. Select the correct final status:
   - Present
   - Late
   - Absent
   - Excused
5. Enter a reason if required.
6. Save the override.
7. Confirm that the table updates.

Only professor-reviewed final statuses should be used for final export.

## 37. How To Mark A Student Excused

1. Open the Post-Session Review page.
2. Find the student.
3. Click **Mark Excused** if available.
4. Confirm the action.
5. The student’s final status changes to **Excused**.

The student can also be marked excused through the override status flow.

## 38. How To View Post-Session Student Details

1. Open the Post-Session Review page.
2. Find the student in the review table.
3. Click **View Details**.
4. The Student Evidence page opens.
5. Review the student’s attendance evidence.

The Student Evidence page explains why the system assigned the attendance result.

## 39. Student Evidence Page Overview

The Student Evidence page may show:

1. Student name.
2. Student number.
3. Course and section.
4. Session date and time.
5. Attendance status.
6. Presence duration.
7. Outside duration.
8. Break count.
9. Session duration.
10. Attendance timeline.
11. Evidence summary.
12. Assessment notes.

Use this page to inspect detailed attendance history for one student in one session.

## 40. How To Accept Or Confirm A Student Status

1. Open the Student Evidence page.
2. Review the timeline and assessment notes.
3. If the status is correct, click **Confirm Attendance**.
4. The student record is marked as reviewed or confirmed.
5. Return to the Post-Session Review page.

Confirm Attendance is like approving one student’s result. Finalize Attendance is still the main action for the whole session.

## 41. How To Override A Student From The Evidence Page

1. Open the Student Evidence page.
2. Click **Override Status**.
3. Select the new status.
4. Enter the reason for the override.
5. Save the override.
6. Review the updated status.
7. Return to Post-Session Review.

## 42. How To Finalize Attendance

1. Open the Post-Session Review page.
2. Review all student statuses.
3. Resolve students requiring review.
4. Apply overrides or excused marks if needed.
5. Click **Finalize Attendance**.
6. Confirm finalization.
7. The session becomes finalized.

Finalization means the professor has accepted the final attendance records for the session. The Blackboard final attendance export should use these finalized statuses.

## 43. Export Types

FRAS V2 may provide several export options.

**Activity Logs**

1. Lists raw session events.
2. Includes time-in, break-out, break-in, manual attendance, and recognition events.
3. Useful for audit and troubleshooting.

**Session Summary / Review CSV**

1. Lists student-level attendance results.
2. Includes presence duration, outside duration, break count, and assessment.
3. Useful for reviewing why students were marked present, late, absent, or excused.

**Blackboard Final Attendance CSV**

1. Contains finalized attendance statuses.
2. Intended for Blackboard attendance import or manual upload.
3. Should be exported only after finalization.

**Full Class Session History**

1. Exports historical session records for a selected class.
2. Useful for reports and class-level attendance review.

## 44. How To Export Activity Logs

1. Open the Post-Session Review page.
2. Click **Export Activity Logs**.
3. The system downloads a CSV file.
4. Open the file to review session events.

Activity logs help explain what happened during the session minute by minute.

## 45. How To Export Session Summary

1. Open the Post-Session Review page.
2. Click **Export Review CSV** or **Export Session Summary**.
3. The system downloads a CSV file.
4. Open the file to review student-level attendance results.

This export is useful before or after finalization for checking attendance calculations.

## 46. How To Export Blackboard Final Attendance CSV

1. Open the Post-Session Review page.
2. Finalize the attendance first.
3. After finalization, click **Export Blackboard CSV**.
4. The system downloads the Blackboard-ready attendance file.
5. Review the file before uploading or submitting it.

If the export button is disabled, the session may not be finalized yet.

## 47. How To Export Full Class Session History

1. Open the **Classes** page.
2. Click **Session History** for a specific class.
3. On the Session History page, click **Export Full History**.
4. The system downloads the class history CSV.

Use this export to review attendance trends across multiple sessions.

## 48. Attendance Status Rules

FRAS V2 focuses on Blackboard-compatible final statuses:

1. Present.
2. Late.
3. Absent.
4. Excused.

The system may still keep notes about partial presence or very late arrivals. For example, a student may be marked absent but have a review note saying the student arrived very late.

Final status should still be reviewed by the professor before export.

## 49. What To Do If A Student Is Not Recognized

1. Check if the student has a registered face profile.
2. Make sure the student is enrolled in the class.
3. Make sure the student is facing the camera.
4. Improve lighting.
5. Try Manual Capture.
6. If recognition still fails, use Manual Attendance.
7. After the session, update the student’s face profile if needed.

## 50. What To Do If Recognition Is Ambiguous

1. Do not force the system to accept the match.
2. Ask the student to reposition.
3. Try again with better lighting and a clearer face.
4. If still ambiguous, record attendance manually.
5. Update the student’s face profile after the session.

Ambiguous recognition means the system is not confident enough to safely choose one student.

## 51. What To Do If Camera Permission Is Blocked

1. Check the browser address bar.
2. Click the camera or permission icon.
3. Change camera permission to **Allow**.
4. Refresh the page.
5. If needed, close other apps that may be using the webcam.
6. Reopen FRAS V2.

If the camera still does not work, try another browser or restart the computer.

## 52. What To Do If A Page Keeps Loading

1. Refresh the page.
2. Check if the backend server is running.
3. Check if the database is running.
4. Check if the logged-in professor account exists.
5. Try signing out and logging in again.
6. Ask the developer or administrator to check backend logs.

## 53. What To Do If Session Break Cannot Start

1. Confirm that the session is already started.
2. Confirm that the session is not already ended or finalized.
3. Refresh the Live Session page.
4. Try the Session Break button again.
5. If testing outside a real schedule, ask the developer whether test bypass mode is enabled.

## 54. What To Do If Export Is Disabled

1. Check if the session has ended.
2. Check if the attendance has been finalized.
3. Resolve review-needed student records if required.
4. Refresh the Post-Session Review page.
5. Try the export again.

Blackboard final attendance export should only be available after finalization.

## 55. Recommended Professor Workflow

For a normal class session:

1. Log in.
2. Open **Classes**.
3. Select the class.
4. Start the monitor.
5. Start the session.
6. Use Auto Capture as the main monitoring workflow.
7. Use Manual Capture or Manual Attendance only when needed.
8. Use Session Break if the whole class goes on break.
9. Use individual Break Out/Break In for specific student breaks.
10. End the session.
11. Review attendance.
12. Inspect student evidence if needed.
13. Override or mark excused if needed.
14. Finalize attendance.
15. Export Blackboard CSV.
16. Sign out.

## 56. Important Reminders

1. Always check the correct class before starting a session.
2. Do not leave professor controls unlocked during Session Break.
3. Use Auto Capture for the main monitoring workflow.
4. Use Manual Attendance only when facial recognition is not practical or when the professor intentionally wants manual checking.
5. Review attendance before finalizing.
6. Export Blackboard CSV only after finalization.
7. Keep face profiles updated for better recognition accuracy.
8. Sign out after use.
