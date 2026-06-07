import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { ApiService } from '../../../api.service';
import { V2FaceProfileContextResponse, V2FaceProfileStatus } from '../../models/v2-attendance.models';
import { V2StatusTone } from '../../components';

type CaptureStatus = 'pending' | 'captured';

interface FaceAngle {
  key: 'front' | 'left' | 'right' | 'up' | 'down';
  label: string;
  instruction: string;
  status: CaptureStatus;
  blob?: Blob;
  previewUrl?: string;
}

@Component({
  selector: 'app-v2-face-profile',
  templateUrl: './face-profile.component.html',
  styleUrls: ['./face-profile.component.scss']
})
export class V2FaceProfileComponent implements OnInit, OnDestroy {
  @ViewChild('videoEl') videoEl?: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasEl') canvasEl?: ElementRef<HTMLCanvasElement>;

  classId = 0;
  studentId = 0;
  context: V2FaceProfileContextResponse | null = null;
  isLoading = true;
  isSaving = false;
  errorMessage = '';
  successMessage = '';
  stream: MediaStream | null = null;
  cameraReady = false;
  lightingScore = 0;

  angles: FaceAngle[] = [
    { key: 'front', label: 'Front', instruction: 'Face the camera directly.', status: 'pending' },
    { key: 'left', label: 'Left', instruction: 'Turn slightly to your left.', status: 'pending' },
    { key: 'right', label: 'Right', instruction: 'Turn slightly to your right.', status: 'pending' },
    { key: 'up', label: 'Up', instruction: 'Tilt your chin slightly up.', status: 'pending' },
    { key: 'down', label: 'Down', instruction: 'Tilt your chin slightly down.', status: 'pending' }
  ];
  currentAngleIndex = 0;

  constructor(
    private api: ApiService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.classId = Number(this.route.snapshot.paramMap.get('classId')) || 0;
    this.studentId = Number(this.route.snapshot.paramMap.get('studentId')) || 0;
    this.loadContext();
    setTimeout(() => this.startCamera(), 0);
  }

  ngOnDestroy(): void {
    this.stopCamera();
    this.angles.forEach((angle) => {
      if (angle.previewUrl) URL.revokeObjectURL(angle.previewUrl);
    });
  }

  loadContext(): void {
    if (!this.classId || !this.studentId) {
      this.errorMessage = 'Open face profile registration from a specific class roster student.';
      this.isLoading = false;
      return;
    }

    this.isLoading = true;
    this.api.getV2FaceProfileContext(this.classId, this.studentId).subscribe({
      next: (context) => {
        this.context = context;
        this.isLoading = false;
      },
      error: () => {
        this.errorMessage = 'Unable to load face profile context.';
        this.isLoading = false;
      }
    });
  }

  async startCamera(): Promise<void> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      });
      if (this.videoEl?.nativeElement) {
        this.videoEl.nativeElement.srcObject = this.stream;
        await this.videoEl.nativeElement.play();
      }
      this.cameraReady = true;
      this.errorMessage = '';
    } catch (error) {
      this.cameraReady = false;
      this.errorMessage = 'Camera permission is needed to capture face profile images.';
    }
  }

  stopCamera(): void {
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.cameraReady = false;
  }

  get currentAngle(): FaceAngle {
    return this.angles[this.currentAngleIndex];
  }

  get capturedCount(): number {
    return this.angles.filter((angle) => angle.status === 'captured').length;
  }

  get allCaptured(): boolean {
    return this.capturedCount === this.angles.length;
  }

  get recognitionQuality(): number {
    const completion = (this.capturedCount / this.angles.length) * 70;
    const lighting = Math.min(30, Math.round((this.lightingScore / 100) * 30));
    return Math.min(100, Math.round(completion + lighting));
  }

  get qualityStatus(): 'Good' | 'Needs Improvement' | 'Poor' {
    if (this.recognitionQuality >= 80) return 'Good';
    if (this.recognitionQuality >= 50) return 'Needs Improvement';
    return 'Poor';
  }

  get pageTitle(): string {
    if (!this.context) return 'Register Face Profile';
    return this.context.face_profile_status === 'no_face_profile' ? 'Register Face Profile' : 'Update Face Profile';
  }

  async captureCurrentFrame(): Promise<void> {
    if (!this.cameraReady || !this.videoEl?.nativeElement || !this.canvasEl?.nativeElement) return;
    const video = this.videoEl.nativeElement;
    const canvas = this.canvasEl.nativeElement;
    const width = video.videoWidth || 1280;
    const height = video.videoHeight || 720;
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext('2d');
    if (!context) return;

    context.drawImage(video, 0, 0, width, height);
    this.lightingScore = this.estimateLighting(context, width, height);
    const blob = await new Promise<Blob>((resolve) => {
      canvas.toBlob((value) => resolve(value as Blob), 'image/jpeg', 0.92);
    });

    const angle = this.currentAngle;
    if (angle.previewUrl) URL.revokeObjectURL(angle.previewUrl);
    angle.blob = blob;
    angle.previewUrl = URL.createObjectURL(blob);
    angle.status = 'captured';
    this.successMessage = `${angle.label} angle captured.`;

    const nextIndex = this.angles.findIndex((item) => item.status === 'pending');
    if (nextIndex >= 0) this.currentAngleIndex = nextIndex;
  }

  selectAngle(index: number): void {
    this.currentAngleIndex = index;
  }

  retakeCurrentAngle(): void {
    const angle = this.currentAngle;
    if (angle.previewUrl) URL.revokeObjectURL(angle.previewUrl);
    angle.previewUrl = undefined;
    angle.blob = undefined;
    angle.status = 'pending';
    this.successMessage = '';
  }

  resetCaptures(): void {
    this.angles.forEach((angle) => {
      if (angle.previewUrl) URL.revokeObjectURL(angle.previewUrl);
      angle.previewUrl = undefined;
      angle.blob = undefined;
      angle.status = 'pending';
    });
    this.currentAngleIndex = 0;
    this.lightingScore = 0;
    this.successMessage = '';
  }

  saveFaceProfile(): void {
    if (!this.allCaptured || this.isSaving) return;
    const formData = new FormData();
    this.angles.forEach((angle) => {
      if (!angle.blob) return;
      formData.append('angles', angle.key);
      formData.append('images', angle.blob, `${angle.key}.jpg`);
    });

    this.isSaving = true;
    this.errorMessage = '';
    this.api.saveV2FaceProfile(this.classId, this.studentId, formData).subscribe({
      next: () => {
        this.isSaving = false;
        this.router.navigate(['/v2/classes', this.classId, 'students']);
      },
      error: () => {
        this.errorMessage = 'Unable to save face profile. Please try again.';
        this.isSaving = false;
      }
    });
  }

  backToRoster(): void {
    this.router.navigate(['/v2/classes', this.classId, 'students']);
  }

  faceTone(status: V2FaceProfileStatus): V2StatusTone {
    if (status === 'registered') return 'success';
    if (status === 'needs_update') return 'warning';
    return 'danger';
  }

  faceStatusLabel(status: V2FaceProfileStatus): string {
    const labels: Record<V2FaceProfileStatus, string> = {
      registered: 'Registered',
      needs_update: 'Needs Update',
      no_face_profile: 'No Face Profile'
    };
    return labels[status];
  }

  qualityTone(): V2StatusTone {
    if (this.qualityStatus === 'Good') return 'success';
    if (this.qualityStatus === 'Needs Improvement') return 'warning';
    return 'danger';
  }

  formatDate(value?: string | null): string {
    if (!value) return 'No update yet';
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(new Date(value));
  }

  private estimateLighting(context: CanvasRenderingContext2D, width: number, height: number): number {
    const sampleWidth = Math.min(180, width);
    const sampleHeight = Math.min(120, height);
    const imageData = context.getImageData(
      Math.floor((width - sampleWidth) / 2),
      Math.floor((height - sampleHeight) / 2),
      sampleWidth,
      sampleHeight
    );
    let total = 0;
    for (let index = 0; index < imageData.data.length; index += 4) {
      total += (imageData.data[index] + imageData.data[index + 1] + imageData.data[index + 2]) / 3;
    }
    const average = total / (imageData.data.length / 4);
    return Math.max(0, Math.min(100, Math.round((average / 255) * 100)));
  }
}
