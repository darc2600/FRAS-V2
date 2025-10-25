import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../api.service';

interface ScheduleCell {
  courseCode?: string;
  section?: string;
  professor?: string;
  room?: string;
}

interface ActionHistory {
  type: 'fill' | 'clear';
  row: number;
  col: number;
  oldCell: ScheduleCell;
  newCell: ScheduleCell;
}

const TIME_SLOTS = [
  "07:00AM - 08:10AM", "08:10AM - 09:20AM", "09:20AM - 10:30AM", "10:30AM - 11:40AM",
  "11:40AM - 12:50PM", "12:50PM - 02:00PM", "02:00PM - 03:10PM", "03:10PM - 04:20PM",
  "04:20PM - 05:30PM", "05:30PM - 06:40PM", "06:40PM - 07:50PM", "07:50PM - 09:00PM"
];
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

@Component({
  selector: 'app-room-schedule-editor',
  templateUrl: './room-schedule-editor.component.html',
  styleUrls: ['./room-schedule-editor.component.css'],
})
export class RoomScheduleEditorComponent implements OnInit {
  room = '';
  message = '';
  isLoading = false;
  isSaving = false;
  messageType: 'error' | 'success' | 'info' = 'info';
  days = DAYS;
  timeSlots = TIME_SLOTS;

  grid: ScheduleCell[][] = this.timeSlots.map(() => this.days.map(() => ({})));
  originalGrid: ScheduleCell[][] = this.timeSlots.map(() => this.days.map(() => ({})));
  actionHistory: ActionHistory[] = [];

  courseCode = '';
  section = '';
  professor = '';

  // Validation data
  validCourses: any[] = []; // {code: string, name: string}
  validInstructors: string[] = [];
  filteredInstructors: string[] = [];
  filteredCourses: any[] = [];
  showInstructorSuggestions = false;
  showCourseSuggestions = false;

  // Delete modal properties
  showDeleteModal = false;
  deleteConfirmationText = '';
  isDeleting = false;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadValidationData();
  }

  loadValidationData() {
    // Load valid courses
    this.api.getCourses().subscribe({
      next: (courses: any[]) => {
        this.validCourses = courses;
      },
      error: (error) => {
        console.error('Error loading courses:', error);
      }
    });

    // Load valid instructors
    this.api.getInstructors().subscribe({
      next: (instructors: string[]) => {
        this.validInstructors = instructors;
      },
      error: (error) => {
        console.error('Error loading instructors:', error);
      }
    });
  }

  onProfessorInputChange() {
    if (this.professor.trim().length === 0) {
      this.filteredInstructors = [];
      this.showInstructorSuggestions = false;
      return;
    }

    const searchTerm = this.professor.trim().toLowerCase().replace(/,/g, '').replace(/\s+/g, ' ');
    this.filteredInstructors = this.validInstructors.filter(instructor => {
      const normalizedInstructor = instructor.toLowerCase().replace(/,/g, '').replace(/\s+/g, ' ');
      return normalizedInstructor.includes(searchTerm);
    }).slice(0, 10); // Limit to 10 suggestions

    this.showInstructorSuggestions = this.filteredInstructors.length > 0;
  }

  onCourseInputChange() {
    if (this.courseCode.trim().length === 0) {
      this.filteredCourses = [];
      this.showCourseSuggestions = false;
      return;
    }

    const searchTerm = this.courseCode.trim().toLowerCase();
    this.filteredCourses = this.validCourses.filter(course =>
      course.code.toLowerCase().includes(searchTerm) ||
      course.name.toLowerCase().includes(searchTerm)
    ).slice(0, 10); // Limit to 10 suggestions

    this.showCourseSuggestions = this.filteredCourses.length > 0;
  }

  selectInstructor(instructor: string) {
    this.professor = instructor;
    this.showInstructorSuggestions = false;
  }

  selectCourse(course: any) {
    this.courseCode = course.code;
    this.showCourseSuggestions = false;
  }

  hideSuggestions() {
    // Hide suggestions after a short delay to allow clicks
    setTimeout(() => {
      this.showInstructorSuggestions = false;
      this.showCourseSuggestions = false;
    }, 150);
  }

  loadSchedule() {
    if (!this.room) {
      this.message = 'Please enter a room number.';
      this.messageType = 'error';
      return;
    }
    this.isLoading = true;
    this.message = '';
    this.api.getRoomSchedule(this.room).subscribe({
      next: (data: any) => {
        // Reset grid
        this.grid = this.timeSlots.map(() => this.days.map(() => ({})));
        // Fill grid with loaded data
        const scheduleList = (data && data.schedule) ? data.schedule : [];
        scheduleList.forEach((entry: any) => {
          const col = this.days.findIndex(d => d === entry.day);
          if (col === -1) return;
          // Find all slots covered by this class
          let inRange = false;
          for (let row = 0; row < this.timeSlots.length; row++) {
            const [slotStart, slotEnd] = this.timeSlots[row].split(' - ');
            // If the slot matches the start or is within the range, fill it
            if (slotStart === entry.startTime) inRange = true;
            if (inRange) {
              this.grid[row][col] = {
                courseCode: entry.courseCode,
                section: entry.section,
                professor: entry.professor,
                room: this.room
              };
            }
            if (slotEnd === entry.endTime) {
              inRange = false;
            }
          }
        });
        // Save original state for revert functionality
        this.originalGrid = JSON.parse(JSON.stringify(this.grid));
        this.actionHistory = [];
        this.message = scheduleList.length > 0 ? `Loaded ${scheduleList.length} schedule entries.` : 'No schedule found for this room.';
        this.messageType = scheduleList.length > 0 ? 'success' : 'info';
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading schedule:', error);
        this.message = 'Failed to load schedule. Please try again.';
        this.messageType = 'error';
        this.isLoading = false;
      }
    });
  }

  fillCell(row: number, col: number) {
    if (!this.courseCode || !this.section || !this.professor) {
      this.message = 'Please enter Course Code, Section, and Professor first.';
      this.messageType = 'error';
      return;
    }

    // Basic validation
    if (this.courseCode.trim().length === 0 || this.section.trim().length === 0 || this.professor.trim().length === 0) {
      this.message = 'All fields must be filled out.';
      this.messageType = 'error';
      return;
    }

    // Validate course code
    const courseCodeUpper = this.courseCode.trim().toUpperCase();
    const validCourseCodes = this.validCourses.map(c => c.code.toUpperCase());
    if (!validCourseCodes.includes(courseCodeUpper)) {
      this.message = `Invalid course code: ${courseCodeUpper}. Please select a valid course.`;
      this.messageType = 'error';
      return;
    }

    // Validate professor name (flexible matching)
    const professorTrimmed = this.professor.trim();
    const normalizedInput = professorTrimmed.toLowerCase().replace(/,/g, '').replace(/\s+/g, ' ');
    
    const isValidProfessor = this.validInstructors.some(instructor => {
      const normalizedInstructor = instructor.toLowerCase().replace(/,/g, '').replace(/\s+/g, ' ');
      return normalizedInstructor.includes(normalizedInput) || normalizedInput.includes(normalizedInstructor);
    });

    if (!isValidProfessor) {
      this.message = `Invalid professor name: ${professorTrimmed}. Please select from the suggestions or enter a valid instructor name.`;
      this.messageType = 'error';
      return;
    }

    // Track action for undo
    const oldCell = { ...this.grid[row][col] };

    console.log('Filling cell:', row, col, this.courseCode, this.section, this.professor);
    this.grid[row][col] = {
      courseCode: this.courseCode.trim().toUpperCase(),
      section: this.section.trim().toUpperCase(),
      professor: this.professor.trim(),
      room: this.room
    };

    // Add to action history
    this.actionHistory.push({
      type: 'fill',
      row,
      col,
      oldCell,
      newCell: { ...this.grid[row][col] }
    });

    this.message = `Added ${this.courseCode.trim().toUpperCase()}-${this.section.trim().toUpperCase()} to ${this.days[col]} ${this.timeSlots[row]}`;
    this.messageType = 'success';
  }

  clearCell(row: number, col: number) {
    // Track action for undo
    const oldCell = { ...this.grid[row][col] };

    this.grid[row][col] = {};

    // Add to action history
    this.actionHistory.push({
      type: 'clear',
      row,
      col,
      oldCell,
      newCell: {}
    });

    this.message = `Cleared ${this.days[col]} ${this.timeSlots[row]}`;
    this.messageType = 'success';
  }

  undoLastAction() {
    if (this.actionHistory.length === 0) {
      this.message = 'No actions to undo.';
      this.messageType = 'info';
      return;
    }

    const lastAction = this.actionHistory.pop()!;
    this.grid[lastAction.row][lastAction.col] = { ...lastAction.oldCell };

    this.message = `Undid last action on ${this.days[lastAction.col]} ${this.timeSlots[lastAction.row]}`;
    this.messageType = 'success';
  }

  revertChanges() {
    if (confirm('Are you sure you want to revert all unsaved changes? This will restore the schedule to its last saved state.')) {
      this.grid = JSON.parse(JSON.stringify(this.originalGrid));
      this.actionHistory = [];
      this.message = 'All changes have been reverted to the last saved state.';
      this.messageType = 'success';
    }
  }

  openDeleteModal() {
    if (!this.room) {
      this.message = 'Please enter a room number first.';
      this.messageType = 'error';
      return;
    }
    this.showDeleteModal = true;
    this.deleteConfirmationText = '';
  }

  closeDeleteModal() {
    this.showDeleteModal = false;
    this.deleteConfirmationText = '';
  }

  confirmDeleteSchedule() {
    if (this.deleteConfirmationText !== 'DELETE') {
      this.message = 'Please type "DELETE" to confirm.';
      this.messageType = 'error';
      return;
    }

    this.isDeleting = true;
    this.api.deleteRoomSchedule(this.room).subscribe({
      next: (response) => {
        // Clear the grid after successful deletion
        this.grid = this.timeSlots.map(() => this.days.map(() => ({})));
        this.originalGrid = JSON.parse(JSON.stringify(this.grid));
        this.actionHistory = [];
        
        this.message = `Schedule for Room ${this.room} has been deleted.`;
        this.messageType = 'success';
        this.closeDeleteModal();
        this.isDeleting = false;
      },
      error: (error) => {
        this.message = 'Failed to delete schedule.';
        this.messageType = 'error';
        this.isDeleting = false;
      }
    });
  }

  saveSchedule() {
    // Flatten grid to array of entries
    const schedule: any[] = [];
    for (let row = 0; row < this.timeSlots.length; row++) {
      for (let col = 0; col < this.days.length; col++) {
        const cell = this.grid[row][col];
        if (cell && cell.courseCode && cell.section) {
          const [startTime, endTime] = this.timeSlots[row].split(' - ');
          schedule.push({
            courseCode: cell.courseCode,
            section: cell.section,
            professor: cell.professor,
            day: this.days[col],
            startTime,
            endTime
          });
        }
      }
    }

    if (schedule.length === 0) {
      this.message = 'No schedule entries to save.';
      return;
    }

    console.log('Saving schedule:', schedule);
    this.isSaving = true;
    this.message = 'Saving schedule...';

    this.api.updateRoomSchedule(this.room, schedule).subscribe({
      next: () => {
        this.message = `Schedule saved successfully! (${schedule.length} entries)`;
        this.messageType = 'success';
        this.isSaving = false;
      },
      error: (error) => {
        console.error('Error saving schedule:', error);
        this.message = 'Failed to save schedule. Please try again.';
        this.messageType = 'error';
        this.isSaving = false;
      }
    });
  }
}
