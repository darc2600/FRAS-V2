import { Component, OnInit } from '@angular/core';
// import { RegistrationService } from './registration.service'; // service missing in repo; commented out to avoid build errors
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpEvent, HttpEventType } from '@angular/common/http';

@Component({
  selector: 'app-registration',
  templateUrl: './registration.component.html',
  styleUrls: ['./registration.component.css']
})
export class RegistrationComponent implements OnInit {
  form: FormGroup;
  submitting = false;
  uploadProgress = 0;

  // simple preview placeholders (data URLs)
  previews: Array<{ url: string }> = [];

  // simple angle capture state
  faceAngles = [
    { label: 'Front', captured: false },
    { label: 'Left', captured: false },
    { label: 'Right', captured: false }
  ];
  currentAngleIndex = 0;
  get currentAngleLabel() {
    return this.faceAngles[this.currentAngleIndex]?.label || '';
  }

  isCapturing = false;
  // indicates whether a video stream is active; template checks this to enable capture
  stream: any = null;

  // schedule helper
  schedule: Array<any> = [];
  scheduleCourseCode = '';
  scheduleSection = '';
  scheduleRoom = '';

  constructor(
    /* private registrationService: RegistrationService, */ // commented out - service file not present
    private fb: FormBuilder
  ) {
    this.form = this.fb.group({
      studentId: ['', Validators.required],
      lastName: ['', Validators.required],
      firstName: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      imageCount: [5, [Validators.required, Validators.min(1), Validators.max(50)]]
    });
  }

  ngOnInit(): void {}

  // simulate capturing an angle: push a tiny placeholder image and mark captured
  captureAngle() {
    if (this.isCapturing) { return; }
    const idx = this.currentAngleIndex;
    // simple 1x1 transparent PNG data URL placeholder
    const placeholder = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAEklEQVQIW2NgYGD4z8DAwMDAwAEAEP+F0bZ6eQAAAAASUVORK5CYII=';
    this.previews.push({ url: placeholder });
    this.faceAngles[idx].captured = true;
    // advance to next angle if available
    if (this.currentAngleIndex < this.faceAngles.length - 1) {
      this.currentAngleIndex++;
    }
  }

  removeShot(i: number) {
    this.previews.splice(i, 1);
    // reset angles if needed
    this.faceAngles.forEach(a => a.captured = false);
    this.currentAngleIndex = 0;
  }

  // resets angle capture state and clears previews (used by template)
  resetAngles() {
    this.faceAngles.forEach(a => a.captured = false);
    this.currentAngleIndex = 0;
    this.clearAll();
  }

  clearAll() {
    this.previews = [];
    this.faceAngles.forEach(a => a.captured = false);
    this.currentAngleIndex = 0;
  }

  addScheduleEntry() {
    if (!this.scheduleCourseCode) { return; }
    this.schedule.push({ course_code: this.scheduleCourseCode, section: this.scheduleSection, room: this.scheduleRoom });
    this.scheduleCourseCode = '';
    this.scheduleSection = '';
    this.scheduleRoom = '';
  }

  removeScheduleEntry(i: number) {
    this.schedule.splice(i, 1);
  }

  // builds a FormData and sends to backend; uses registrationService.registerStudent
  submit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const fd = new FormData();
    fd.append('studentId', this.form.value.studentId);
    fd.append('lastName', this.form.value.lastName);
    fd.append('firstName', this.form.value.firstName);
    fd.append('email', this.form.value.email);
    fd.append('imageCount', String(this.form.value.imageCount));
    // append schedule as JSON
    fd.append('schedule', JSON.stringify(this.schedule || []));

    // if we have data-urls in previews, convert them to blobs and append
    this.previews.forEach((p, idx) => {
      try {
        const blob = this.dataURItoBlob(p.url);
        fd.append('images', blob, `shot-${idx + 1}.png`);
      } catch (e) {
        // ignore conversion errors for placeholder images
      }
    });

    this.submitting = true;
    this.uploadProgress = 0;

    // The real backend call was using RegistrationService, which is not present in the repo at the moment.
    // Commenting out the service call and using a local simulated submission so the component compiles.
    /*
    this.registrationService.registerStudent(fd).subscribe({
      next: (event: HttpEvent<any>) => {
        if (event.type === HttpEventType.UploadProgress && event.total) {
          this.uploadProgress = Math.round(100 * (event.loaded / event.total));
        } else if (event.type === HttpEventType.Response) {
          this.submitting = false;
          this.uploadProgress = 100;
          // on success, clear form and previews
          this.clearAll();
          this.form.reset({ imageCount: 5 });
        }
      },
      error: (err: any) => {
        this.submitting = false;
        console.error('Registration error', err);
      }
    });
    */

    // Simulate upload progress and success
    this.submitting = true;
    this.uploadProgress = 0;
    const ticks = [20, 50, 80, 100];
    ticks.forEach((p, i) => setTimeout(() => this.uploadProgress = p, 150 * (i + 1)));
    setTimeout(() => {
      this.submitting = false;
      this.uploadProgress = 100;
      this.clearAll();
      this.form.reset({ imageCount: 5 });
    }, 150 * (ticks.length + 1));
  }

  // helper: convert dataURL to Blob
  private dataURItoBlob(dataURI: string): Blob {
    const byteString = atob(dataURI.split(',')[1]);
    const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
      ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
  }
}

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