import {
  Component, ElementRef, OnDestroy, OnInit, ViewChild
} from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { RegisterStudentsService } from './register-students.service';
import { Subscription } from 'rxjs';
import { HttpEventType } from '@angular/common/http';
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
      if (!this.stream || this.isCapturing || this.faceAngles[this.currentAngleIndex].captured) return;

      // Mark current angle as captured
      if (this.currentAngleIndex < this.faceAngles.length) {
        this.faceAngles[this.currentAngleIndex].captured = true;

        // Actually capture the image
        this.captureOne().then(() => {
          // Move to next angle if available
          if (this.currentAngleIndex < this.faceAngles.length - 1) {
            this.currentAngleIndex++;
          }
        });
      }
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
      if (!this.form.valid || this.previews.length === 0) {
        alert('Please fill all required fields and capture at least one image.');
        return;
      }

      this.submitting = true;
      this.uploadProgress = 0;

      const formData = new FormData();
      formData.append('student_id', this.form.value.studentId);
      formData.append('last_name', this.form.value.lastName);
      formData.append('first_name', this.form.value.firstName);
      formData.append('email', this.form.value.email || '');
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
          error: (err) => {
            console.error('Registration failed:', err);
            alert('Registration failed. Please try again.');
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

  async ngOnInit() {
    await this.startCamera();
  }

  ngOnDestroy() {
    this.stopCamera();
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
  }
}
