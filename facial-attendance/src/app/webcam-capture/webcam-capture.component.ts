
import { Component } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { WebcamModule, WebcamImage, WebcamInitError } from 'ngx-webcam';
import { Subject, Observable } from 'rxjs';
import { ApiService } from '../api.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-webcam-capture',
  templateUrl: './webcam-capture.component.html',
  styleUrls: ['./webcam-capture.component.css']
})
export class WebcamCaptureComponent {
  courseCode = '';
  section = '';
  courseCodeSection = '';
  message = '';
  webcamImage: WebcamImage | null = null;
  private trigger: Subject<void> = new Subject<void>();

  availableRooms: any[] = [];
  selectedRoom: any = null;
  availableCourseSections: string[] = [];
  availableCourseSectionObjects: any[] = [];
  selectedClassId: number | null = null;

  constructor(private api: ApiService) {
    this.loadRooms();
  }

  loadRooms() {
    // Load all floors first
    this.api.getFloors().subscribe(
      (floors: number[]) => {
        // Load rooms from all floors
        const roomPromises = floors.map(floor => 
          this.api.getRoomsByFloor(floor).toPromise()
        );
        
        Promise.all(roomPromises).then(
          (roomArrays: (any[] | undefined)[]) => {
            this.availableRooms = roomArrays.filter(arr => arr !== undefined).flat();
            if (this.availableRooms.length > 0) {
              this.selectedRoom = this.availableRooms[0];
              this.onRoomChange();
            }
          },
          err => console.error('Error loading rooms:', err)
        );
      },
      err => console.error('Error loading floors:', err)
    );
  }

  onRoomChange() {
    if (!this.selectedRoom) {
      this.availableCourseSections = [];
      this.availableCourseSectionObjects = [];
      this.courseCodeSection = '';
      this.selectedClassId = null;
      return;
    }
    
    this.api.getCoursesSectionsByRoom(this.selectedRoom.room_id).subscribe(
      (coursesSections: any[]) => {
        this.availableCourseSectionObjects = coursesSections;
        this.availableCourseSections = coursesSections.map(cs => cs.course_section);
        // Reset selection if not in new list
        if (!this.availableCourseSections.includes(this.courseCodeSection)) {
          this.courseCodeSection = '';
          this.selectedClassId = null;
        }
        this.updateSelectedClassId();
      },
      err => {
        console.error('Error fetching course-sections:', err);
        this.availableCourseSections = [];
        this.availableCourseSectionObjects = [];
        this.courseCodeSection = '';
        this.selectedClassId = null;
      }
    );
  }

  updateSelectedClassId() {
    if (!this.courseCodeSection) {
      this.selectedClassId = null;
      return;
    }
    const selectedObject = this.availableCourseSectionObjects.find(cs => cs.course_section === this.courseCodeSection);
    this.selectedClassId = selectedObject ? selectedObject.class_id : null;
    console.log('Selected class_id:', this.selectedClassId);
  }

  onCourseSectionChange() {
    this.updateSelectedClassId();
  }

  public get triggerObservable(): Observable<void> {
    return this.trigger.asObservable();
  }

  public triggerSnapshot(): void {
    this.trigger.next();
  }

  public handleImage(webcamImage: WebcamImage): void {
    this.webcamImage = webcamImage;
  }

  markAttendance() {
    if (!this.webcamImage) {
      this.message = 'Please capture an image first.';
      return;
    }
    if (!this.selectedClassId) {
      this.message = 'Please select a course section.';
      return;
    }
    const blob = this.dataURLtoBlob(this.webcamImage.imageAsDataUrl);
    const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
    this.api.recognizeFace(file, this.selectedClassId).subscribe(
      res => this.message = res.status === 'success'
        ? `Attendance marked for ${res.student_id}`
        : res.message,
      err => this.message = 'Error connecting to backend.'
    );
  }

  dataURLtoBlob(dataurl: string) {
    const arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)![1],
      bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
    for (let i = 0; i < n; i++) u8arr[i] = bstr.charCodeAt(i);
    return new Blob([u8arr], { type: mime });
  }
}
