import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AttendanceMonitorComponent } from './attendance-monitor.component';

describe('AttendanceMonitorComponent', () => {
  let component: AttendanceMonitorComponent;
  let fixture: ComponentFixture<AttendanceMonitorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AttendanceMonitorComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AttendanceMonitorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
