import type { Ticket } from "./types";

export const sampleTickets: Ticket[] = [
  {
    id: "6b85e2c5-a33a-44ce-b6ea-9ca0d2aa9f4c",
    status: "completed",
    vendor: "cisco",
    model: "c8k",
    version: "1.0",
    enqueued_at: "2025-09-27 19:07:45.735329",
    started_at: "2025-09-27 19:07:45.736822",
    completed_at: "2025-09-27 19:07:51.748649",
    machine: {
      serial: "c8kSerial2",
      ip: "192.168.1.2",
      port: 6002
    },
    result_data: "Processed cisco - c8k",
    raw_data: "hostname c8k\ninterface Gi0/1\n description Sample config"
  },
  {
    id: "f2bf13b8-16b1-44bc-9d7c-112233445566",
    status: "running",
    vendor: "juniper",
    model: "mx480",
    version: "18.4",
    enqueued_at: "2025-10-01 09:12:00",
    started_at: "2025-10-01 09:13:10",
    completed_at: null,
    machine: {
      serial: "jnpr-mx480-01",
      ip: "192.168.2.10",
      port: 7001
    },
    result_data: null,
    raw_data: "set system host-name mx480\nset interfaces ge-0/0/0 description \"Uplink\""
  },
  {
    id: "70ea9d1f-5108-4b53-88c3-abcdef123456",
    status: "failed",
    vendor: "arista",
    model: "7050X3",
    version: "4.26",
    enqueued_at: "2025-08-18 12:00:00",
    started_at: "2025-08-18 12:05:00",
    completed_at: "2025-08-18 12:07:30",
    machine: {
      serial: "arista7050x3-07",
      ip: "10.10.10.7",
      port: 6020
    },
    result_data: "Interface error at Eth2",
    raw_data: "hostname spine-01\ninterface Ethernet2\n description Down"
  }
];
