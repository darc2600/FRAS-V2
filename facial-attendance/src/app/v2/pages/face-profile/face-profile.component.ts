import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { ApiService } from '../../../api.service';
import { V2FaceProfileContextResponse, V2FaceProfileStatus } from '../../models/v2-attendance.models';
import { V2StatusTone } from '../../components';

type CaptureStatus = 'pending' | 'captured';
type FaceQualityState = 'good' | 'warning' | 'bad' | 'unknown';

type BrowserFaceDetection = {
  boundingBox: DOMRectReadOnly;
};

type BrowserFaceDetector = {
  detect(image: CanvasImageSource): Promise<BrowserFaceDetection[]>;
};

declare global {
  interface Window {
    FaceDetector?: new (options?: { fastMode?: boolean; maxDetectedFaces?: number }) => BrowserFaceDetector;
  }
}

interface FaceAngle {
  key: 'front';
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
  cameraAspectRatio = '16 / 9';
  cameraResolutionLabel = 'Camera resolution pending';
  lightingScore = 0;
  blurScore = 0;
  faceCount: number | null = null;
  faceCentered = false;
  faceLargeEnough = false;
  qualityMessage = 'Start the camera and align the face inside the guide.';
  autoCaptureEnabled = true;
  autoCaptureProgress = 0;
  isAutoCapturing = false;
  private qualityTimer: any;
  private faceDetector: BrowserFaceDetector | null = null;
  private qualityStableStartedAt: number | null = null;

  angles: FaceAngle[] = [
    { key: 'front', label: 'Front', instruction: 'Face the camera directly inside the guide frame.', status: 'pending' }
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
        setTimeout(() => this.startCamera(), 0);
      },
      error: () => {
        this.errorMessage = 'Unable to load face profile context.';
        this.isLoading = false;
      }
    });
  }

  async startCamera(): Promise<void> {
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        this.cameraReady = false;
        this.errorMessage = 'Camera access is not available in this browser or connection.';
        return;
      }

      this.stopCamera();
      this.stream = await this.requestBestCameraStream();

      if (!this.videoEl?.nativeElement) {
        this.cameraReady = false;
        this.errorMessage = 'Camera preview is still loading. Please retry camera access.';
        return;
      }

      this.videoEl.nativeElement.srcObject = this.stream;
      this.videoEl.nativeElement.onloadedmetadata = () => this.updateCameraAspectRatio();
      await this.videoEl.nativeElement.play();
      this.updateCameraAspectRatio();
      this.cameraReady = true;
      this.setupFaceDetector();
      this.startQualityLoop();
      this.errorMessage = '';
    } catch (error) {
      this.cameraReady = false;
      this.errorMessage = this.cameraErrorMessage(error);
    }
  }

  stopCamera(): void {
    this.stopQualityLoop();
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.cameraReady = false;
    this.cameraResolutionLabel = 'Camera resolution pending';
    this.qualityStableStartedAt = null;
    this.autoCaptureProgress = 0;
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
    const lighting = this.checkPassed(this.lightingState) ? 25 : this.lightingState === 'warning' ? 12 : 0;
    const blur = this.checkPassed(this.blurState) ? 25 : this.blurState === 'warning' ? 12 : 0;
    const face = this.checkPassed(this.faceCountState) ? 20 : this.faceCountState === 'unknown' ? 10 : 0;
    const position = this.checkPassed(this.facePositionState) ? 15 : this.facePositionState === 'unknown' ? 8 : 0;
    const size = this.checkPassed(this.faceSizeState) ? 15 : this.faceSizeState === 'unknown' ? 8 : 0;
    return Math.min(100, lighting + blur + face + position + size);
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

  get canCaptureFrame(): boolean {
    return this.cameraReady && this.frameQualityUsable && this.currentAngle.status !== 'captured' && !this.isAutoCapturing;
  }

  get frameQualityReady(): boolean {
    const faceChecksPass = this.faceDetector
      ? this.faceCountState === 'good' && this.facePositionState === 'good' && this.faceSizeState === 'good'
      : true;
    return this.lightingState === 'good' && this.blurState === 'good' && faceChecksPass;
  }

  get frameQualityUsable(): boolean {
    const faceChecksPass = this.faceDetector
      ? this.faceCountState === 'good' && this.facePositionState !== 'bad' && this.faceSizeState !== 'bad'
      : true;
    return this.isUsableQuality(this.lightingState) && this.isUsableQuality(this.blurState) && faceChecksPass;
  }

  get faceDetectionLabel(): string {
    if (!this.faceDetector) return 'Browser unavailable';
    if (this.faceCount === null) return 'Scanning';
    if (this.faceCount === 1) return 'One face';
    if (this.faceCount === 0) return 'No face';
    return `${this.faceCount} faces`;
  }

  get lightingState(): FaceQualityState {
    if (!this.cameraReady || !this.lightingScore) return 'unknown';
    if (this.lightingScore >= 36 && this.lightingScore <= 88) return 'good';
    if (this.lightingScore >= 24 && this.lightingScore <= 94) return 'warning';
    return 'bad';
  }

  get blurState(): FaceQualityState {
    if (!this.cameraReady || !this.blurScore) return 'unknown';
    if (this.blurScore >= 24) return 'good';
    if (this.blurScore >= 12) return 'warning';
    return 'bad';
  }

  get faceCountState(): FaceQualityState {
    if (!this.faceDetector) return 'unknown';
    if (this.faceCount === 1) return 'good';
    if (this.faceCount === null) return 'unknown';
    return 'bad';
  }

  get facePositionState(): FaceQualityState {
    if (!this.faceDetector) return 'unknown';
    return this.faceCentered ? 'good' : 'bad';
  }

  get faceSizeState(): FaceQualityState {
    if (!this.faceDetector) return 'unknown';
    return this.faceLargeEnough ? 'good' : 'bad';
  }

  async captureCurrentFrame(source: 'manual' | 'auto' = 'manual'): Promise<void> {
    if (!this.cameraReady || !this.videoEl?.nativeElement || !this.canvasEl?.nativeElement) return;
    if (source === 'manual' && !this.canCaptureFrame) {
      this.errorMessage = 'Improve the camera frame until lighting and sharpness are at least usable.';
      return;
    }
    const video = this.videoEl.nativeElement;
    const canvas = this.canvasEl.nativeElement;
    const width = video.videoWidth || 1280;
    const height = video.videoHeight || 720;
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext('2d');
    if (!context) return;

    context.drawImage(video, 0, 0, width, height);
    this.updateImageQuality(context, width, height);
    const blob = await new Promise<Blob>((resolve) => {
      canvas.toBlob((value) => resolve(value as Blob), 'image/jpeg', 0.98);
    });

    const angle = this.currentAngle;
    if (angle.previewUrl) URL.revokeObjectURL(angle.previewUrl);
    angle.blob = blob;
    angle.previewUrl = URL.createObjectURL(blob);
    angle.status = 'captured';
    this.successMessage = source === 'auto' ? 'Best quality frame captured automatically.' : 'Front face captured.';
    this.qualityStableStartedAt = null;
    this.autoCaptureProgress = 0;

    this.currentAngleIndex = 0;
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
    this.blurScore = 0;
    this.qualityStableStartedAt = null;
    this.autoCaptureProgress = 0;
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

  checkLabel(state: FaceQualityState): string {
    if (state === 'good') return 'Good';
    if (state === 'warning') return 'Needs Improvement';
    if (state === 'bad') return 'Not Ready';
    return 'Scanning';
  }

  checkTone(state: FaceQualityState): V2StatusTone {
    if (state === 'good') return 'success';
    if (state === 'warning' || state === 'unknown') return 'warning';
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

  private setupFaceDetector(): void {
    if (!window.FaceDetector) {
      this.faceDetector = null;
      this.faceCount = null;
      return;
    }
    this.faceDetector = new window.FaceDetector({ fastMode: true, maxDetectedFaces: 2 });
  }

  private updateCameraAspectRatio(): void {
    const video = this.videoEl?.nativeElement;
    if (!video?.videoWidth || !video.videoHeight) {
      this.cameraAspectRatio = '16 / 9';
      this.cameraResolutionLabel = 'Camera resolution pending';
      return;
    }
    this.cameraAspectRatio = `${video.videoWidth} / ${video.videoHeight}`;
    this.cameraResolutionLabel = `${video.videoWidth} x ${video.videoHeight}`;
  }

  private async requestBestCameraStream(): Promise<MediaStream> {
    const highQualityConstraints: MediaStreamConstraints[] = [
      {
        video: {
          facingMode: 'user',
          width: { ideal: 1920 },
          height: { ideal: 1080 },
          frameRate: { ideal: 30 },
          resizeMode: 'none'
        } as MediaTrackConstraints,
        audio: false
      },
      {
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 }
        },
        audio: false
      },
      {
        video: {
          facingMode: 'user'
        },
        audio: false
      }
    ];

    let lastError: unknown;
    for (const constraints of highQualityConstraints) {
      try {
        return await navigator.mediaDevices.getUserMedia(constraints);
      } catch (error) {
        lastError = error;
      }
    }
    throw lastError;
  }

  private startQualityLoop(): void {
    this.stopQualityLoop();
    this.qualityTimer = setInterval(() => this.runQualityCheck(), 450);
  }

  private stopQualityLoop(): void {
    if (this.qualityTimer) {
      clearInterval(this.qualityTimer);
      this.qualityTimer = null;
    }
  }

  private async runQualityCheck(): Promise<void> {
    if (!this.cameraReady || !this.videoEl?.nativeElement || !this.canvasEl?.nativeElement || this.currentAngle.status === 'captured') {
      return;
    }

    const video = this.videoEl.nativeElement;
    const canvas = this.canvasEl.nativeElement;
    const width = Math.max(1, video.videoWidth || 640);
    const height = Math.max(1, video.videoHeight || 360);
    const context = canvas.getContext('2d', { willReadFrequently: true });
    if (!context) return;

    canvas.width = width;
    canvas.height = height;
    context.drawImage(video, 0, 0, width, height);
    this.updateImageQuality(context, width, height);
    await this.updateFaceQuality(canvas, width, height);
    this.updateQualityMessage();
    this.maybeAutoCapture();
  }

  private async updateFaceQuality(canvas: HTMLCanvasElement, width: number, height: number): Promise<void> {
    if (!this.faceDetector) {
      this.faceCount = null;
      this.faceCentered = false;
      this.faceLargeEnough = false;
      return;
    }

    try {
      const faces = await this.faceDetector.detect(canvas);
      this.faceCount = faces.length;
      const firstFace = faces[0]?.boundingBox;
      if (!firstFace || faces.length !== 1) {
        this.faceCentered = false;
        this.faceLargeEnough = false;
        return;
      }

      const centerX = firstFace.x + firstFace.width / 2;
      const centerY = firstFace.y + firstFace.height / 2;
      const xOffset = Math.abs(centerX - width / 2) / width;
      const yOffset = Math.abs(centerY - height / 2) / height;
      const faceAreaRatio = (firstFace.width * firstFace.height) / (width * height);
      this.faceCentered = xOffset <= 0.16 && yOffset <= 0.18;
      this.faceLargeEnough = faceAreaRatio >= 0.08 && faceAreaRatio <= 0.48;
    } catch {
      this.faceDetector = null;
      this.faceCount = null;
      this.faceCentered = false;
      this.faceLargeEnough = false;
    }
  }

  private updateQualityMessage(): void {
    if (!this.cameraReady) {
      this.qualityMessage = 'Start the camera and align the face inside the guide.';
    } else if (this.faceDetector && this.faceCount !== 1) {
      this.qualityMessage = this.faceCount && this.faceCount > 1
        ? 'Only one student should be visible in the frame.'
        : 'Align the student face inside the guide frame.';
    } else if (!this.isUsableQuality(this.lightingState)) {
      this.qualityMessage = 'Add light or reduce glare so the face is visible.';
    } else if (!this.isUsableQuality(this.blurState)) {
      this.qualityMessage = 'Hold still or move closer until the image is clearer.';
    } else if (this.faceDetector && !this.faceCentered) {
      this.qualityMessage = 'Center the face inside the guide frame.';
    } else if (this.faceDetector && !this.faceLargeEnough) {
      this.qualityMessage = 'Move closer or farther until the face fits the guide frame.';
    } else {
      this.qualityMessage = this.autoCaptureEnabled ? 'Good frame detected. Auto capture will start shortly.' : 'Good frame detected. Capture is ready.';
    }
  }

  private maybeAutoCapture(): void {
    if (!this.autoCaptureEnabled || !this.frameQualityReady || this.currentAngle.status === 'captured' || this.isAutoCapturing) {
      this.qualityStableStartedAt = null;
      this.autoCaptureProgress = 0;
      return;
    }

    const now = Date.now();
    this.qualityStableStartedAt = this.qualityStableStartedAt || now;
    const elapsed = now - this.qualityStableStartedAt;
    this.autoCaptureProgress = Math.min(100, Math.round((elapsed / 2500) * 100));
    if (elapsed >= 2500) {
      this.isAutoCapturing = true;
      this.captureCurrentFrame('auto').finally(() => {
        this.isAutoCapturing = false;
      });
    }
  }

  private updateImageQuality(context: CanvasRenderingContext2D, width: number, height: number): void {
    this.lightingScore = this.estimateLighting(context, width, height);
    this.blurScore = this.estimateSharpness(context, width, height);
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

  private estimateSharpness(context: CanvasRenderingContext2D, width: number, height: number): number {
    const sampleWidth = Math.min(180, width);
    const sampleHeight = Math.min(120, height);
    const imageData = context.getImageData(
      Math.floor((width - sampleWidth) / 2),
      Math.floor((height - sampleHeight) / 2),
      sampleWidth,
      sampleHeight
    );
    const gray: number[] = [];
    for (let index = 0; index < imageData.data.length; index += 4) {
      gray.push(
        (imageData.data[index] * 0.299) +
        (imageData.data[index + 1] * 0.587) +
        (imageData.data[index + 2] * 0.114)
      );
    }

    let totalEdge = 0;
    let count = 0;
    for (let y = 1; y < sampleHeight - 1; y += 1) {
      for (let x = 1; x < sampleWidth - 1; x += 1) {
        const center = gray[y * sampleWidth + x] * 4;
        const laplacian = Math.abs(
          center -
          gray[y * sampleWidth + x - 1] -
          gray[y * sampleWidth + x + 1] -
          gray[(y - 1) * sampleWidth + x] -
          gray[(y + 1) * sampleWidth + x]
        );
        totalEdge += laplacian;
        count += 1;
      }
    }

    return Math.max(0, Math.min(100, Math.round((totalEdge / Math.max(1, count)) * 4)));
  }

  private checkPassed(state: FaceQualityState): boolean {
    return state === 'good';
  }

  private isUsableQuality(state: FaceQualityState): boolean {
    return state === 'good' || state === 'warning';
  }

  private cameraErrorMessage(error: unknown): string {
    const name = error instanceof DOMException ? error.name : '';
    if (name === 'NotAllowedError' || name === 'SecurityError') {
      return 'Camera permission is blocked. Allow camera access in the browser, then retry.';
    }
    if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
      return 'No camera was found on this device.';
    }
    if (name === 'NotReadableError' || name === 'TrackStartError') {
      return 'The camera is already in use by another app or browser tab.';
    }
    return 'Camera permission is needed to capture face profile images.';
  }
}
