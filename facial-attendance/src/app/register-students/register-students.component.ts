import {
  Component, ElementRef, OnDestroy, OnInit, ViewChild
} from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { RegisterStudentsService } from './register-students.service';
import { Subscription } from 'rxjs';
import { CommonModule } from '@angular/common';

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
  scheduleRoom = '';
  schedule: { course_code: string; section: string; room: string }[] = [];

  // For guided angle capture
  faceAngles = [
    { label: 'Center', captured: false },
    { label: 'Left', captured: false },
    { label: 'Right', captured: false },
    { label: 'Up', captured: false },
    { label: 'Down', captured: false }
  ];
  currentAngleIndex = 0;

  private subs = new Subscription();

  constructor(
    private fb: FormBuilder,
    private regSvc: RegisterStudentsService
  ) {
    this.form = this.fb.group({
      studentId: ['', [Validators.required, Validators.maxLength(40)]],
      lastName: ['', [Validators.required, Validators.maxLength(100)]],
      firstName: ['', [Validators.required, Validators.maxLength(100)]],
      email: ['', [Validators.email, Validators.maxLength(100)]],
      imageCount: [this.defaultTarget, [Validators.required, Validators.min(1), Validators.max(50)]],
    });
  }

    // Add missing properties and methods for template
    get currentAngleLabel(): string {
      return this.faceAngles[this.currentAngleIndex]?.label || '';
    }

    captureAngle(): void {
      // Mark current angle as captured
      if (this.currentAngleIndex < this.faceAngles.length) {
        this.faceAngles[this.currentAngleIndex].captured = true;
        // Move to next angle if available
        if (this.currentAngleIndex < this.faceAngles.length - 1) {
          this.currentAngleIndex++;
        }
      }
      // Add capture logic here if needed
    }

    resetAngles(): void {
      this.faceAngles.forEach(a => a.captured = false);
      this.currentAngleIndex = 0;
    }

    removeShot(index: number): void {
      this.previews.splice(index, 1);
    }

    submit(): void {
      this.submitting = true;
      // Add submit logic here
      setTimeout(() => { this.submitting = false; }, 1000);
    }

    addScheduleEntry(): void {
      if (this.scheduleCourseCode && this.scheduleSection && this.scheduleRoom) {
        this.schedule.push({
          course_code: this.scheduleCourseCode,
          section: this.scheduleSection,
          room: this.scheduleRoom
        });
        this.scheduleCourseCode = '';
        this.scheduleSection = '';
        this.scheduleRoom = '';
      }
    }

    removeScheduleEntry(index: number): void {
      this.schedule.splice(index, 1);
    }

  ngOnInit() {}
  ngOnDestroy() { this.subs.unsubscribe(); }
  // ...rest of logic from original component
}
