import type { Machine } from "../../types";
import { StatusBadge } from "../UI/StatusBadge";

interface Props {
  machine: Machine;
}

export function MachineCard({ machine }: Props) {
  return (
    <article className="machine-card">
      <header>
        <h3>{machine.vendor} / {machine.model}</h3>
        <StatusBadge status={machine.status} />
      </header>
      <dl>
        <div><dt>Hostname</dt><dd>{machine.hostname}</dd></div>
        <div><dt>Version</dt><dd>{machine.version}</dd></div>
        <div><dt>IP Address</dt><dd>{machine.mgmt_ip}:{machine.port}</dd></div>
        <div><dt>Serial</dt><dd>{machine.serial}</dd></div>
      </dl>
    </article>
  );
}