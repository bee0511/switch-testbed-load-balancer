export type TicketStatus = "queued" | "running" | "completed" | "failed";

export interface MachineInfo {
  serial: string;
  ip: string;
  port: number;
}

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
  fieldValues: Partial<Record<FilterField, string>>;
  dateRanges: Record<DateField, DateRange>;
  resultData: string;
  rawData: string;
}

export interface DeviceEntryOption {
  ip: string;
  port: number;
  serial_number: string;
}

export interface VersionOption {
  version: string;
  devices: DeviceEntryOption[];
}

export interface ModelOption {
  model: string;
  versions: VersionOption[];
}

export interface VendorOption {
  vendor: string;
  models: ModelOption[];
}

export interface DeviceConfig {
  vendors: VendorOption[];
}
