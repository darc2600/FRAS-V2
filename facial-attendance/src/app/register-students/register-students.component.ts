import {
  Component, ElementRef, OnDestroy, OnInit, ViewChild
} from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { RegisterStudentsService } from './register-students.service';
import { Subscription } from 'rxjs';
import { HttpEventType } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { ApiService } from '../api.service';

interface PreviewImage {
  url: string;
  blob: Blob;
  angle?: string;
}

@Component({
  selector: 'app-register-students',
  templateUrl: './register-students.component.html',
  styleUrls: ['./register-students.component.css'],
})
export class RegisterStudentsComponent implements OnInit, OnDestroy {
  @ViewChild('videoEl', { static: true }) videoEl!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasEl', { static: true }) canvasEl!: ElementRef<HTMLCanvasElement>;

  stream?: MediaStream;
  isCapturing = false;
  submitting = false;
  uploadProgress = 0;
  previews: PreviewImage[] = [];
  defaultTarget = 10;

  form: any;
  // For schedule entry
  scheduleCourseCode = '';
  scheduleSection = '';
  schedule: { course_code: string; section: string; room?: string; class_id?: number }[] = [];

  // Validation states
  studentValidated = false;
  validationErrors: { [key: string]: string } = {};
  expectedStudentData: any = null;

  // Course/Section search properties
  availableCourseSections: string[] = [];

  // Autocomplete properties
  availableCourses: any[] = [];
  filteredCourses: any[] = [];
  showCourseSuggestions = false;
  availableSections: string[] = [];
  filteredSections: string[] = [];
  showSectionSuggestions = false;

  // For guided angle capture
  faceAngles = [
    { label: 'Center', captured: false },
    { label: 'Left', captured: false },
    { label: 'Right', captured: false },
    { label: 'Up', captured: false },
    { label: 'Down', captured: false }
  ];
  currentAngleIndex = 0;
  autoCaptureActive = false;
  autoCaptureInterval: any = null;

  private subs = new Subscription();

  constructor(
    private fb: FormBuilder,
    private regSvc: RegisterStudentsService,
    private api: ApiService
  ) {
    this.form = this.fb.group({
      studentId: ['', [Validators.required, Validators.maxLength(40)]],
      lastName: ['', [Validators.required, Validators.maxLength(100)]],
      firstName: ['', [Validators.required, Validators.maxLength(100)]],
      email: ['', [Validators.email, Validators.maxLength(100)]],
    });
  }

    // Add missing properties and methods for template
    get currentAngleLabel(): string {
      return this.faceAngles[this.currentAngleIndex]?.label || '';
    }

    get validationErrorsCount(): number {
      return Object.keys(this.validationErrors).length;
    }

    get allAnglesCaptured(): boolean {
      return this.faceAngles.every(angle => angle.captured);
    }

    getAngleCueClass(): string {
      const angle = this.faceAngles[this.currentAngleIndex];
      if (!angle || angle.captured) return '';
      return `cue-${this.currentAngleLabel.toLowerCase()}`;
    }

    getArrowDirection(): string {
      const angle = this.faceAngles[this.currentAngleIndex];
      if (!angle || angle.captured) return '';
      return `arrow-${this.currentAngleLabel.toLowerCase()}`;
    }

    validateStudentId(): void {
      const studentId = this.form.value.studentId?.trim();
      if (!studentId) {
        this.validationErrors['studentId'] = 'Student ID is required';
        this.studentValidated = false;
        this.expectedStudentData = null;
        return;
      }

      // Clear previous validation errors
      delete this.validationErrors['studentId'];
      delete this.validationErrors['lastName'];
      delete this.validationErrors['firstName'];
      delete this.validationErrors['email'];

      // Reset form values except student ID
      this.form.patchValue({
        lastName: '',
        firstName: '',
        email: ''
      });

      this.studentValidated = false;
      this.expectedStudentData = null;

      // Call API to validate student ID
      this.regSvc.getStudentByNumber(studentId).subscribe({
        next: (student: any) => {
          if (student) {
            this.studentValidated = true;
            this.expectedStudentData = student;
            // Clear form values - don't pre-fill for privacy
            this.form.patchValue({
              lastName: '',
              firstName: '',
              email: ''
            });
          } else {
            this.validationErrors['studentId'] = 'Student ID does not exist or is invalid';
            this.studentValidated = false;
            this.expectedStudentData = null;
            // Clear other fields when student ID is invalid
            this.form.patchValue({
              lastName: '',
              firstName: '',
              email: ''
            });
            // Clear other validation errors
            delete this.validationErrors['lastName'];
            delete this.validationErrors['firstName'];
            delete this.validationErrors['email'];
          }
        },
        error: (err: any) => {
          console.error('Error validating student ID:', err);
          this.validationErrors['studentId'] = 'Error validating student ID';
          this.studentValidated = false;
          this.expectedStudentData = null;
          // Clear other fields on error
          this.form.patchValue({
            lastName: '',
            firstName: '',
            email: ''
          });
          // Clear other validation errors
          delete this.validationErrors['lastName'];
          delete this.validationErrors['firstName'];
          delete this.validationErrors['email'];
        }
      });
    }

    validateField(fieldName: string): void {
      if (!this.studentValidated || !this.expectedStudentData) {
        return;
      }

      const formValue = this.form.value[fieldName]?.trim();
      const expectedValue = this.expectedStudentData[fieldName === 'lastName' ? 'last_name' : fieldName === 'firstName' ? 'first_name' : fieldName];

      if (formValue && expectedValue && formValue.toLowerCase() !== expectedValue.toLowerCase()) {
        const fieldLabels = {
          lastName: 'Last name',
          firstName: 'First name',
          email: 'Email'
        };
        this.validationErrors[fieldName] = `${fieldLabels[fieldName as keyof typeof fieldLabels]} does not match our records`;
      } else {
        delete this.validationErrors[fieldName];
      }
    }

    onStudentIdBlur(): void {
      this.validateStudentId();
    }

    onFieldBlur(fieldName: string): void {
      this.validateField(fieldName);
    }

    loadAvailableCourseSections(): void {
      // Load available courses for autocomplete
      this.api.getCourses().subscribe({
        next: (courses: any[]) => {
          this.availableCourses = courses;
        },
        error: (err: any) => {
          console.error('Error loading courses:', err);
        }
      });
    }

    onCourseSectionSelect(): void {
      // This method is no longer used since we have separate course and section inputs
    }

    onCourseInputChange(): void {
      if (this.scheduleCourseCode.trim().length === 0) {
        this.filteredCourses = [];
        this.showCourseSuggestions = false;
        return;
      }

      const searchTerm = this.scheduleCourseCode.trim().toLowerCase();
      this.filteredCourses = this.availableCourses.filter(course =>
        course.code.toLowerCase().includes(searchTerm) ||
        course.name.toLowerCase().includes(searchTerm)
      ).slice(0, 10); // Limit to 10 suggestions

      this.showCourseSuggestions = this.filteredCourses.length > 0;
    }

    onSectionInputChange(): void {
      if (this.scheduleSection.trim().length === 0) {
        this.filteredSections = [];
        this.showSectionSuggestions = false;
        return;
      }

      const searchTerm = this.scheduleSection.trim().toLowerCase();
      // For now, provide common section patterns. In a real implementation,
      // you'd load sections based on the selected course
      this.availableSections = ['A', 'B', 'C', 'D', 'AM1', 'AM2', 'PM1', 'PM2', '1', '2', '3', '4'];
      this.filteredSections = this.availableSections.filter(section =>
        section.toLowerCase().includes(searchTerm)
      ).slice(0, 10); // Limit to 10 suggestions

      this.showSectionSuggestions = this.filteredSections.length > 0;
    }

    selectCourse(course: any): void {
      this.scheduleCourseCode = course.code;
      this.showCourseSuggestions = false;
    }

    selectSection(section: string): void {
      this.scheduleSection = section;
      this.showSectionSuggestions = false;
    }

    hideSuggestions(): void {
      // Hide suggestions after a short delay to allow clicks
      setTimeout(() => {
        this.showCourseSuggestions = false;
        this.showSectionSuggestions = false;
      }, 150);
    }

    captureAngle(): void {
      if (!this.stream || this.isCapturing || this.faceAngles[this.currentAngleIndex].captured) return;

      // Mark current angle as captured
      if (this.currentAngleIndex < this.faceAngles.length) {
        this.faceAngles[this.currentAngleIndex].captured = true;

        // Actually capture the image
        this.captureOne().then(() => {
          // Move to next angle if available
          if (this.currentAngleIndex < this.faceAngles.length - 1) {
            this.currentAngleIndex++;
          } else {
            // All angles captured, stop if auto-capture was active
            if (this.autoCaptureActive) {
              this.stopAutoCapture();
            }
          }
        });
      }
    }

    startAutoCapture(): void {
      if (!this.stream || this.isCapturing || this.autoCaptureActive) return;

      this.autoCaptureActive = true;
      this.resetAngles();

      // Start automatic capture sequence
      this.autoCaptureInterval = setInterval(() => {
        if (this.currentAngleIndex < this.faceAngles.length && !this.faceAngles[this.currentAngleIndex].captured) {
          this.captureAngle();
        } else {
          this.stopAutoCapture();
        }
      }, 2000); // Capture every 2 seconds
    }

    stopAutoCapture(): void {
      if (this.autoCaptureInterval) {
        clearInterval(this.autoCaptureInterval);
        this.autoCaptureInterval = null;
      }
      this.autoCaptureActive = false;
    }

    resetAngles(): void {
      this.faceAngles.forEach(a => a.captured = false);
      this.currentAngleIndex = 0;
      // Clear all captured images
      this.previews.forEach(p => URL.revokeObjectURL(p.url));
      this.previews = [];
    }

    removeShot(index: number): void {
      this.previews.splice(index, 1);
    }

    submit(): void {
      // Check if student ID is validated
      if (!this.studentValidated) {
        alert('Please enter a valid student ID first.');
        return;
      }

      // Check for validation errors
      const hasErrors = this.validationErrorsCount > 0;
      if (hasErrors) {
        alert('Please correct the validation errors before submitting.');
        return;
      }

      if (!this.form.valid) {
        alert('Please fill all required fields.');
        return;
      }

      // Check if all angles are captured
      const allAnglesCaptured = this.faceAngles.every(angle => angle.captured);
      if (!allAnglesCaptured) {
        alert('Please capture images for all angles (Center, Left, Right, Up, Down) before submitting.');
        return;
      }

      // Check if schedule has at least one entry
      if (this.schedule.length === 0) {
        alert('Please add at least one course and section to your schedule before submitting.');
        return;
      }

      this.submitting = true;
      this.uploadProgress = 0;

      const formData = new FormData();
      formData.append('student_number', this.form.value.studentId);
      formData.append('last_name', this.form.value.lastName);
      formData.append('first_name', this.form.value.firstName);
      formData.append('email', this.form.value.email || '');
      formData.append('created_at', new Date().toISOString());
      formData.append('schedule', JSON.stringify(this.schedule));

      // Add captured images
      this.previews.forEach((preview, index) => {
        formData.append('images', preview.blob, `capture_${index + 1}.jpg`);
      });

      this.subs.add(
        this.regSvc.registerStudent(formData).subscribe({
          next: (event) => {
            if (event.type === HttpEventType.UploadProgress) {
              this.uploadProgress = Math.round(100 * event.loaded / (event.total || 1));
            }
          },
          error: (err: any) => {
            console.error('Registration failed:', err);
            if (err.status === 409) {
              alert('Registration failed: ' + (err.error?.detail || 'Student with this number is already registered.'));
            } else {
              alert('Registration failed. Please try again.');
            }
            this.submitting = false;
          },
          complete: () => {
            alert('Registration successful!');
            this.submitting = false;
            this.resetForm();
          }
        })
      );
    }

    addScheduleEntry(): void {
      if (this.scheduleCourseCode && this.scheduleSection) {
        // Check for duplicates
        const isDuplicate = this.schedule.some(entry =>
          entry.course_code.toLowerCase() === this.scheduleCourseCode.toLowerCase() &&
          entry.section.toLowerCase() === this.scheduleSection.toLowerCase()
        );

        if (isDuplicate) {
          alert('This course and section combination is already in your schedule.');
          return;
        }

        // In a real implementation, you'd look up the class_id from course_code + section
        // For now, we'll use a placeholder
        this.schedule.push({
          course_code: this.scheduleCourseCode,
          section: this.scheduleSection,
          // room will be determined by the backend from the class lookup
        });
        this.scheduleCourseCode = '';
        this.scheduleSection = '';
        this.hideSuggestions();
      }
    }

    removeScheduleEntry(index: number): void {
      this.schedule.splice(index, 1);
    }

  async ngOnInit() {
    await this.startCamera();
    this.loadAvailableCourseSections();
  }

  ngOnDestroy() {
    this.stopCamera();
    this.stopAutoCapture();
    this.subs.unsubscribe();
  }

  async startCamera() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      this.videoEl.nativeElement.srcObject = this.stream;
      await this.videoEl.nativeElement.play();
    } catch (err) {
      alert('Unable to access webcam. Please allow camera permissions.');
      console.error(err);
    }
  }

  stopCamera() {
    this.stream?.getTracks().forEach(t => t.stop());
    this.stream = undefined;
  }

  private async snapOnce(): Promise<PreviewImage> {
    const video = this.videoEl.nativeElement;
    const canvas = this.canvasEl.nativeElement;
    const w = video.videoWidth || 1280;
    const h = video.videoHeight || 720;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d')!;
    ctx.drawImage(video, 0, 0, w, h);
    const blob: Blob = await new Promise(res => canvas.toBlob(b => res(b as Blob), 'image/jpeg', 0.92)!);
    const url = URL.createObjectURL(blob);
    return { url, blob };
  }

  async captureOne() {
    if (!this.stream) return;
    const shot = await this.snapOnce();
    this.previews.push(shot);
  }

  async captureSeries() {
    if (!this.stream || this.isCapturing) return;
    this.isCapturing = true;
    const target = this.form.value.imageCount ?? this.defaultTarget;
    try {
      while (this.previews.length < target) {
        const shot = await this.snapOnce();
        this.previews.push(shot);
        await new Promise(r => setTimeout(r, 180));
      }
    } finally {
      this.isCapturing = false;
    }
  }

  private resetForm(): void {
    this.form.reset();
    this.schedule = [];
    this.previews.forEach(p => URL.revokeObjectURL(p.url));
    this.previews = [];
    this.resetAngles();
    // Clear validation state
    this.studentValidated = false;
    this.validationErrors = {};
    this.expectedStudentData = null;
  }
}
