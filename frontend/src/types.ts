export type TicketStatus = "queued" | "running" | "completed" | "failed";

export interface Ticket {
  id: string;
  status: TicketStatus;
  vendor: string;
  model: string;
  version: string;
  enqueued_at: string;
  started_at: string | null;
  completed_at: string | null;
  machine: MachineInfo | null;
  result_data?: string | null;
  raw_data?: string | null;
  message?: string;
}

export interface MachineInfo {
  serial: string;
  ip: string;
  port: number;
}

export type FilterField =
  | "id"
  | "status"
  | "vendor"
  | "model"
  | "version"
  | "machine.serial"
  | "machine.ip"
  | "machine.port";

export type DateField = "enqueued_at" | "started_at" | "completed_at";

export interface DateRange {
  from?: string;
  to?: string;
}

export interface FilterState {
  activeFields: FilterField[];
  fieldValues: Partial<Record<FilterField, string | string[]>>;
  dateRanges: Record<DateField, DateRange>;
  resultData: string;
  rawData: string;
}

export interface DevicePortEntry {
  ip: string;
  port: number;
  serial_number: string;
}

export interface DeviceVersionEntry {
  version: string;
  devices: DevicePortEntry[];
}

export interface DeviceModelEntry {
  model: string;
  versions: DeviceVersionEntry[];
}

export interface DeviceVendorEntry {
  vendor: string;
  models: DeviceModelEntry[];
}

export interface DeviceConfigResponse {
  vendors: DeviceVendorEntry[];
}
