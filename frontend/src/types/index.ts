export type MachineStatus = "available" | "unavailable" | "unreachable";

export interface Machine {
  vendor: string;
  model: string;
  version: string;
  mgmt_ip: string;
  port: number;
  serial: string;
  status: MachineStatus;
  hostname: string;
  default_gateway?: string;
  netmask?: string;
}

export interface MachineListResponse {
  machines: Machine[];
}

export interface MachineFilters {
  vendor?: string;
  model?: string;
  version?: string;
  status: MachineStatus | "all";
}