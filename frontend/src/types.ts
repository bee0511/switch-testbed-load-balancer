export type MachineStatus = "available" | "unavailable";

export interface Machine {
  vendor: string;
  model: string;
  version: string;
  ip: string;
  port: number;
  serial_number: string;
  available: boolean;
  status: MachineStatus;
}

export interface MachineListResponse {
  machines: Machine[];
}

export interface MachineFilters {
  vendor?: string;
  model?: string;
  version?: string;
  status?: "available" | "unavailable" | "all";
}
