# FRAS V2 – Classroom Presence Monitoring Workflow

## System Overview

FRAS V2 is a Classroom Presence Monitoring System designed to monitor and validate student presence throughout an entire class session using facial recognition and event-based attendance tracking.

Unlike traditional attendance systems that only verify a student's presence at a single point in time, FRAS V2 records classroom presence events throughout the session and calculates attendance based on actual presence duration.

The primary user of the system is the Professor.

No student portal, student login, administrator dashboard, faculty management, or course management workflows are included in this revision.

---

# Main Navigation

The professor interface contains the following pages:

1. Today's Classes
2. Session History
3. Schedule
4. Settings

Optional:

5. Help / Support

---

# 1. Login

## Inputs

* Email Address
* Password

## Flow

Login Page
→ Today's Classes

---

# 2. Today's Classes

Purpose:

Allow professors to view scheduled classes and start monitoring sessions.

## Dashboard Sections

### Current Class

Displays the currently active class.

### Next Class

Displays the upcoming scheduled class.

### Completed Classes

Displays classes already completed for the day.

## Class Card Information

Each class card displays:

* Course Code
* Course Name
* Section
* Room
* Schedule (Start–End Time)
* Student Count
* Status

Status Values:

* Current
* Upcoming
* Completed

## Available Actions

### Start Monitoring

Begins a classroom presence monitoring session.

Flow:

Today's Classes
→ Live Session Monitoring

### Student List

Displays enrolled students and attendance summaries.

Student information includes:

* Student Number
* Student Name
* Attendance Summary
* Previous Session Results

### Session History

Displays historical attendance sessions for the selected class.

Flow:

Today's Classes
→ Session History

---

# 3. Live Session Monitoring

Purpose:

Monitor student classroom presence in real time.

## Session Information

Displays:

* Course Code
* Course Name
* Section
* Room
* Scheduled Time
* Session Timer
* Session Status

Session Status Values:

* Not Started
* In Progress
* On Break
* Completed

## Classroom Camera Feed

Displays:

* Live Camera Feed
* Recognized Students
* Recognition Confidence
* Unknown Faces
* Recognition Status

Recognition operates using manual capture or automatic capture intervals.

## Live Roster

Displays all students enrolled in the class.

Current Student Status Values:

* Present
* Late
* Absent
* Excused
* On Break

Selecting a student opens a quick detail panel.

Displayed Information:

* Student Name
* Student Number
* Time In
* Last Event
* Presence Duration
* Outside Duration

## Recognition Activity Feed

Displays recent attendance events.

Supported Events:

* Time In
* Break Out
* Break In
* Time Out
* Manual Attendance
* Professor Override

Events are displayed chronologically.

## Session Controls

### Manual Attendance

Allows professors to manually assign attendance.

### Manual Capture

Captures and processes a single classroom image.

### Start Auto Capture

Enables automatic facial recognition at configured intervals.

### Stop Auto Capture

Disables automatic facial recognition.

### Start Break

Temporarily pauses monitoring.

Professor may optionally define a break duration.

### End Session

Stops monitoring and begins attendance validation.

Flow:

Live Session Monitoring
→ Post Session Review

---

# 4. Post Session Review

Purpose:

Allow professors to validate attendance before finalization.

## Session Summary

Displays:

* Presence Validation Rate
* Present Count
* Late Count
* Partial Count
* Absent Count
* Excused Count
* Students Requiring Review

## Student Review Table

Displays:

* Student Name
* Attendance Status
* Presence Duration
* Outside Duration
* Break Count
* System Assessment

## Attendance Status Values

* Present
* Late
* Partial
* Absent
* Excused

## System Assessment Values

* Valid Presence
* Attendance Warning
* Requires Review

## Professor Actions

### View Details

Displays detailed attendance evidence.

### Mark Excused

Assigns excused attendance status.

### Override Status

Allows professor to replace the system-generated attendance result.

All overrides are logged.

## Session Actions

### Finalize Attendance

Locks attendance records.

Attendance calculations are no longer modified after finalization.

### Export Blackboard CSV

Generates a CSV file containing attendance results and supporting evidence.

Flow:

Post Session Review
→ Session History

or

Post Session Review
→ Student Session Detail

---

# 5. Student Session Detail

Purpose:

Provide evidence supporting the assigned attendance result.

This page is the primary justification page for attendance decisions.

## Attendance Summary

Displays:

* Student Name
* Student Number
* Course
* Section
* Session Date
* Attendance Status
* System Assessment

## Session Metrics

Displays:

* Presence Duration
* Outside Duration
* Break Count
* Session Duration

## Attendance Timeline

Chronological event history.

Supported Events:

* Time In
* Break Out
* Break In
* Time Out
* Manual Attendance
* Professor Override

Each event includes:

* Timestamp
* Event Type
* Recognition Source
* Additional Notes

## Presence Evidence Summary

Displays:

### Inside Classroom Duration

Total confirmed classroom presence.

### Outside Classroom Duration

Total confirmed absence after Time In.

### Break Duration

Total approved break duration.

### Presence Ratio

Visual comparison between:

* Inside Classroom Duration
* Outside Classroom Duration

## Assessment Notes

Displays explanation for:

* Valid Presence
* Attendance Warning
* Requires Review

## Professor Actions

### Mark Excused

Changes attendance status to Excused.

### Override Status

Changes attendance result.

### Confirm Attendance

Accepts the final attendance decision.

---

# 6. Session History

Purpose:

Provide historical attendance records for completed sessions.

## Session Statistics

Displays:

* Total Sessions
* Average Attendance Rate
* Average Presence Duration
* Sessions Requiring Review
* Excused Students

## Filters

Available filters:

* Date Range
* Attendance Percentage
* Session Status
* Review Flag

## Session Table

Displays:

* Date
* Time Range
* Attendance Count
* Attendance Rate
* Average Presence Duration
* Warning Count
* Excused Count
* Session Status

## Session Status Values

* Completed
* Needs Review

## Available Actions

### View Session Summary

Opens Post Session Review.

Flow:

Session History
→ Post Session Review

### View Student Evidence

Opens Student Session Detail.

Flow:

Post Session Review
→ Student Session Detail

---

# Attendance Event Lifecycle

Student enters classroom

→ Time In

Student leaves classroom

→ Break Out

Student returns to classroom

→ Break In

Student leaves before session ends

→ Time Out

Professor modifies attendance

→ Professor Override

All events are stored as attendance evidence and contribute to attendance assessment calculations.

---

# Attendance Finalization Workflow

Today's Classes
→ Live Session Monitoring
→ Post Session Review
→ Student Session Detail (optional)
→ Finalize Attendance
→ Export Blackboard or CSV
→ Session History

This is the complete FRAS V2 attendance lifecycle.
