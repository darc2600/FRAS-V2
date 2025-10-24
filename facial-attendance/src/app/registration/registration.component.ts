// import { Component, OnInit } from '@angular/core';
// // import { RegistrationService } from './registration.service'; // service missing in repo; commented out to avoid build errors
// import { FormBuilder, FormGroup, Validators } from '@angular/forms';
// import { HttpEvent, HttpEventType } from '@angular/common/http';

// @Component({
//   selector: 'app-registration',
//   templateUrl: './registration.component.html',
//   styleUrls: ['./registration.component.css']
// })
// export class RegistrationComponent implements OnInit {
//   form: FormGroup;
//   submitting = false;
//   uploadProgress = 0;

//   // simple preview placeholders (data URLs)
//   previews: Array<{ url: string }> = [];

//   // simple angle capture state
//   faceAngles = [
//     { label: 'Front', captured: false },
//     { label: 'Left', captured: false },
//     { label: 'Right', captured: false }
//   ];
//   currentAngleIndex = 0;
//   get currentAngleLabel() {
//     return this.faceAngles[this.currentAngleIndex]?.label || '';
//   }

//   isCapturing = false;
//   // indicates whether a video stream is active; template checks this to enable capture
//   stream: any = null;

//   // schedule helper
//   schedule: Array<any> = [];
//   scheduleCourseCode = '';
//   scheduleSection = '';
//   scheduleRoom = '';

//   constructor(
//     /* private registrationService: RegistrationService, */ // commented out - service file not present
//     private fb: FormBuilder
//   ) {
//     this.form = this.fb.group({
//       studentId: ['', Validators.required],
//       lastName: ['', Validators.required],
//       firstName: ['', Validators.required],
//       email: ['', [Validators.required, Validators.email]],
//       imageCount: [5, [Validators.required, Validators.min(1), Validators.max(50)]]
//     });
//   }

//   ngOnInit(): void {}

//   // simulate capturing an angle: push a tiny placeholder image and mark captured
//   captureAngle() {
//     if (this.isCapturing) { return; }
//     const idx = this.currentAngleIndex;
//     // simple 1x1 transparent PNG data URL placeholder
//     const placeholder = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAEklEQVQIW2NgYGD4z8DAwMDAwAEAEP+F0bZ6eQAAAAASUVORK5CYII=';
//     this.previews.push({ url: placeholder });
//     this.faceAngles[idx].captured = true;
//     // advance to next angle if available
//     if (this.currentAngleIndex < this.faceAngles.length - 1) {
//       this.currentAngleIndex++;
//     }
//   }

//   removeShot(i: number) {
//     this.previews.splice(i, 1);
//     // reset angles if needed
//     this.faceAngles.forEach(a => a.captured = false);
//     this.currentAngleIndex = 0;
//   }

//   // resets angle capture state and clears previews (used by template)
//   resetAngles() {
//     this.faceAngles.forEach(a => a.captured = false);
//     this.currentAngleIndex = 0;
//     this.clearAll();
//   }

//   clearAll() {
//     this.previews = [];
//     this.faceAngles.forEach(a => a.captured = false);
//     this.currentAngleIndex = 0;
//   }

//   addScheduleEntry() {
//     if (!this.scheduleCourseCode) { return; }
//     this.schedule.push({ course_code: this.scheduleCourseCode, section: this.scheduleSection, room: this.scheduleRoom });
//     this.scheduleCourseCode = '';
//     this.scheduleSection = '';
//     this.scheduleRoom = '';
//   }

//   removeScheduleEntry(i: number) {
//     this.schedule.splice(i, 1);
//   }

//   // builds a FormData and sends to backend; uses registrationService.registerStudent
//   submit() {
//     if (this.form.invalid) {
//       this.form.markAllAsTouched();
//       return;
//     }

//     const fd = new FormData();
//     fd.append('studentId', this.form.value.studentId);
//     fd.append('lastName', this.form.value.lastName);
//     fd.append('firstName', this.form.value.firstName);
//     fd.append('email', this.form.value.email);
//     fd.append('imageCount', String(this.form.value.imageCount));
//     // append schedule as JSON
//     fd.append('schedule', JSON.stringify(this.schedule || []));

//     // if we have data-urls in previews, convert them to blobs and append
//     this.previews.forEach((p, idx) => {
//       try {
//         const blob = this.dataURItoBlob(p.url);
//         fd.append('images', blob, `shot-${idx + 1}.png`);
//       } catch (e) {
//         // ignore conversion errors for placeholder images
//       }
//     });

//     this.submitting = true;
//     this.uploadProgress = 0;

//     // The real backend call was using RegistrationService, which is not present in the repo at the moment.
//     // Commenting out the service call and using a local simulated submission so the component compiles.
//     /*
//     this.registrationService.registerStudent(fd).subscribe({
//       next: (event: HttpEvent<any>) => {
//         if (event.type === HttpEventType.UploadProgress && event.total) {
//           this.uploadProgress = Math.round(100 * (event.loaded / event.total));
//         } else if (event.type === HttpEventType.Response) {
//           this.submitting = false;
//           this.uploadProgress = 100;
//           // on success, clear form and previews
//           this.clearAll();
//           this.form.reset({ imageCount: 5 });
//         }
//       },
//       error: (err: any) => {
//         this.submitting = false;
//         console.error('Registration error', err);
//       }
//     });
//     */

//     // Simulate upload progress and success
//     this.submitting = true;
//     this.uploadProgress = 0;
//     const ticks = [20, 50, 80, 100];
//     ticks.forEach((p, i) => setTimeout(() => this.uploadProgress = p, 150 * (i + 1)));
//     setTimeout(() => {
//       this.submitting = false;
//       this.uploadProgress = 100;
//       this.clearAll();
//       this.form.reset({ imageCount: 5 });
//     }, 150 * (ticks.length + 1));
//   }

//   // helper: convert dataURL to Blob
//   private dataURItoBlob(dataURI: string): Blob {
//     const byteString = atob(dataURI.split(',')[1]);
//     const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
//     const ab = new ArrayBuffer(byteString.length);
//     const ia = new Uint8Array(ab);
//     for (let i = 0; i < byteString.length; i++) {
//       ia[i] = byteString.charCodeAt(i);
//     }
//     return new Blob([ab], { type: mimeString });
//   }
// }

/*
 ORIGINAL CODE (commented out):
import { Component } from '@angular/core';
import { RegistrationService } from './registration.service';

@Component({
  selector: 'app-registration',
  templateUrl: './registration.component.html',
  styleUrls: ['./registration.component.css']
})
export class RegistrationComponent {
  username = '';
  password = '';
  email = '';
  error = '';
  success = '';

  constructor(private registrationService: RegistrationService) {}

  register() {
    if (this.username && this.password && this.email) {
      this.error = '';
      this.success = '';
      this.registrationService.register({
        username: this.username,
        password: this.password,
        email: this.email
      }).subscribe({
        next: () => {
          this.success = 'Registration successful!';
          this.username = '';
          this.password = '';
          this.email = '';
        },
        error: err => {
          this.error = err?.error?.message || 'Registration failed.';
        }
      });
    } else {
      this.error = 'All fields are required';
    }
  }

  resetAngles() {
    this.faceAngles.forEach(a => a.captured = false);
    this.currentAngleIndex = 0;
    this.clearAll();
  }
}
*/

import {
  Component, ElementRef, OnDestroy, OnInit, ViewChild
} from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { RegistrationService } from './registration.service';
import { Subscription } from 'rxjs';
import { CommonModule } from '@angular/common';

interface PreviewImage {
  url: string;
  blob: Blob;
  angle?: string;
}

@Component({
  selector: 'app-registration',
  templateUrl: './registration.component.html',
  styleUrls: ['./registration.component.css'],
})
export class RegistrationComponent implements OnInit, OnDestroy {
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
    private regSvc: RegistrationService
  ) {
    this.form = this.fb.group({
      studentId: ['', [Validators.required, Validators.maxLength(40)]],
      lastName: ['', [Validators.required, Validators.maxLength(100)]],
      firstName: ['', [Validators.required, Validators.maxLength(100)]],
      email: ['', [Validators.email, Validators.maxLength(100)]],
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

  const formData = new FormData();

  formData.append('student_number', this.form.value.studentId);
  formData.append('last_name', this.form.value.lastName);
  formData.append('first_name', this.form.value.firstName);
  formData.append('email', this.form.value.email || '');
  // Set created_at to current date/time in ISO format
  formData.append('created_at', new Date().toISOString());
  // Send schedule as JSON string
  formData.append('schedule', JSON.stringify(this.schedule));
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

  get currentAngleLabel() {
    return this.faceAngles[this.currentAngleIndex]?.label || '';
  }

  async captureAngle() {
    if (!this.stream) return;
    const shot = await this.snapOnce();
    shot.angle = this.currentAngleLabel;
    this.previews.push(shot);
    this.faceAngles[this.currentAngleIndex].captured = true;
    // Move to next angle if available
    if (this.currentAngleIndex < this.faceAngles.length - 1) {
      this.currentAngleIndex++;
    }
  }

  resetAngles() {
    this.faceAngles.forEach(a => a.captured = false);
    this.currentAngleIndex = 0;
    this.clearAll();
  }
}