import { Component, EventEmitter, Input, Output } from '@angular/core';

export type V2FilterField = {
  label: string;
  type: 'search' | 'select' | 'date-range';
  value?: string;
  options?: string[];
};

@Component({
  selector: 'app-v2-search-filter-bar',
  templateUrl: './v2-search-filter-bar.component.html',
  styleUrls: ['./v2-search-filter-bar.component.scss']
})
export class V2SearchFilterBarComponent {
  @Input() fields: V2FilterField[] = [];
  @Output() apply = new EventEmitter<V2FilterField[]>();
  @Output() search = new EventEmitter<string>();
}
