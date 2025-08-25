import {
  Component, ElementRef, OnDestroy, OnInit, ViewChild
} from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule } from '@angular/forms';
import { RegistrationService } from './registration.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-registration',
  standalone: true,
  templateUrl: './registration.component.html',
  styleUrls: ['./registration.component.css'],
  imports: [ReactiveFormsModule],
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

  form: any; // <-- Change to late initialization

  private subs = new Subscription();

  constructor(
    private fb: FormBuilder,
    private regSvc: RegistrationService
  ) {
    // Initialize form here
    this.form = this.fb.group({
      courseCode: ['', [Validators.required, Validators.maxLength(20)]],
      section: ['', [Validators.required, Validators.maxLength(20)]],
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

  submit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    if (this.previews.length === 0) {
      alert('Please capture at least 1 image.');
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
    };
    const blobs = this.previews.map(p => p.blob);
    this.subs.add(
      this.regSvc.registerStudent(payload, blobs).subscribe({
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
        }
      })
    );
  }
}
