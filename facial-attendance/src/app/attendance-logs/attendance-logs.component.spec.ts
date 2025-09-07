import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AttendanceLogsComponent } from './attendance-logs.component';

describe('AttendanceLogsComponent', () => {
  let component: AttendanceLogsComponent;
  let fixture: ComponentFixture<AttendanceLogsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AttendanceLogsComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AttendanceLogsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
