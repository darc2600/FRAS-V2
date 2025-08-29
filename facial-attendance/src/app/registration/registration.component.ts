import {
  Component, ElementRef, OnDestroy, OnInit, ViewChild
} from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { RegistrationService } from './registration.service';
import { Subscription } from 'rxjs';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-registration',
  standalone: true,
  templateUrl: './registration.component.html',
  styleUrls: ['./registration.component.css'],
  imports: [ReactiveFormsModule, FormsModule, CommonModule],
})
export class RegistrationComponent implements OnInit, OnDestroy {
  @ViewChild('videoEl', { static: true }) videoEl!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasEl', { static: true }) canvasEl!: ElementRef<HTMLCanvasElement>;

  stream?: MediaStream;
  isCapturing = false;
  submitting = false;
  uploadProgress = 0;
  previews: { url: string; blob: Blob }[] = [];
  defaultTarget = 10;

  form: any;
  // For schedule entry
  scheduleCourseCode = '';
  scheduleSection = '';
  scheduleRoom = '';
  schedule: { course_code: string; section: string; room: string }[] = [];

  private subs = new Subscription();

  constructor(
    private fb: FormBuilder,
    private regSvc: RegistrationService
  ) {
    this.form = this.fb.group({
      studentId: ['', [Validators.required, Validators.maxLength(40)]],
      studentName: ['', [Validators.required, Validators.maxLength(80)]],
      imageCount: [this.defaultTarget, [Validators.required, Validators.min(1), Validators.max(50)]],
    });
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

  private async snapOnce(): Promise<{ url: string; blob: Blob }> {
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

  removeShot(i: number) {
    const [removed] = this.previews.splice(i, 1);
    if (removed) URL.revokeObjectURL(removed.url);
  }

  clearAll() {
    this.previews.forEach(p => URL.revokeObjectURL(p.url));
    this.previews = [];
  }

  // --- Schedule Section ---
  addScheduleEntry() {
    const code = this.scheduleCourseCode.trim();
    const section = this.scheduleSection.trim();
    const room = this.scheduleRoom.trim();
    if (code && section && room) {
      // Prevent duplicates
      if (!this.schedule.find(e =>
        e.course_code === code &&
        e.section === section &&
        e.room === room
      )) {
        this.schedule.push({ course_code: code, section, room });
        this.scheduleCourseCode = '';
        this.scheduleSection = '';
        this.scheduleRoom = '';
      }
    }
  }

  removeScheduleEntry(index: number) {
    this.schedule.splice(index, 1);
  }

  // --- Registration Submission ---
  submit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    if (this.previews.length === 0) {
      alert('Please capture at least 1 image.');
      return;
    }
    if (this.schedule.length === 0) {
      alert('Please add at least one schedule entry.');
      return;
    }
    this.submitting = true;
    this.uploadProgress = 0;
    const payload = {
      courseCode: this.form.value.courseCode!,
      section: this.form.value.section!,
      studentId: this.form.value.studentId!,
      studentName: this.form.value.studentName!,
      imageCount: this.previews.length,
      schedule: this.schedule
    };
    const blobs = this.previews.map(p => p.blob);
    const formData = new FormData();
    formData.append('courseCode', this.form.value.courseCode);
    formData.append('section', this.form.value.section);
    formData.append('studentId', this.form.value.studentId);
    formData.append('studentName', this.form.value.studentName);
    formData.append('imageCount', this.previews.length.toString());

    // Add schedule as JSON string
    formData.append('schedule', JSON.stringify(this.schedule));

    // Add images
    this.previews.forEach((p, i) => formData.append('images', p.blob, `img${i + 1}.jpg`));

    // Then POST to the backend
    this.subs.add(
      this.regSvc.registerStudent(formData).subscribe({
        next: evt => {
          // @ts-ignore
          if (evt?.type === 1 && evt.total) {
            // @ts-ignore
            this.uploadProgress = Math.round((evt.loaded / evt.total) * 100);
          }
        },
        error: (err) => {
          console.error(err);
          alert('Upload failed. See console for details.');
          this.submitting = false;
        },
        complete: () => {
          this.submitting = false;
          this.uploadProgress = 100;
          alert('Registration uploaded successfully!');
          this.clearAll();
          this.form.patchValue({ imageCount: this.defaultTarget });
          this.schedule = [];
        }
      })
    );
  }
}
