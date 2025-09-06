import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RoomScheduleEditorComponent } from './room-schedule-editor.component';

describe('RoomScheduleEditorComponent', () => {
  let component: RoomScheduleEditorComponent;
  let fixture: ComponentFixture<RoomScheduleEditorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RoomScheduleEditorComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RoomScheduleEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
