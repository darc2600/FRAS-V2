import { Component, EventEmitter, Input, Output } from '@angular/core';

export type V2DataTableColumn = {
  key: string;
  label: string;
  align?: 'left' | 'right' | 'center';
  width?: string;
};

@Component({
  selector: 'app-v2-data-table',
  templateUrl: './v2-data-table.component.html',
  styleUrls: ['./v2-data-table.component.scss']
})
export class V2DataTableComponent {
  @Input() columns: V2DataTableColumn[] = [];
  @Input() rows: Record<string, any>[] = [];
  @Input() actionLabel = '';
  @Input() emptyText = 'No records found.';
  @Output() rowAction = new EventEmitter<Record<string, any>>();

  valueFor(row: Record<string, any>, key: string): any {
    return row[key] ?? '';
  }
}
