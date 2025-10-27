export type MachineStatus = "available" | "unavailable" | "unreachable";

export interface Machine {
  vendor: string;
  model: string;
  version: string;
  ip: string;
  port: number;
  serial: string;
  status: MachineStatus;
}

export interface MachineListResponse {
  machines: Machine[];
}

export interface MachineFilters {
  vendor?: string;
  model?: string;
  version?: string;
  status?: "available" | "unavailable" | "unreachable" | "all";
}
