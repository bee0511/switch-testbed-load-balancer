import type { KeyboardEvent } from "react";
import type { Ticket } from "../types";
import "./TicketCard.css";

interface TicketCardProps {
  ticket: Ticket;
  onClick: (ticket: Ticket) => void;
}

export function TicketCard({ ticket, onClick }: TicketCardProps) {
  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onClick(ticket);
    }
  };

  return (
    <article
      className="ticket-card"
      onClick={() => onClick(ticket)}
      role="button"
      tabIndex={0}
      onKeyDown={handleKeyDown}
    >
      <header className="ticket-card__header">
        <span className={`status status--${ticket.status}`}>{ticket.status}</span>
        <h3>{ticket.id}</h3>
      </header>
      <dl className="ticket-card__grid">
        <div>
          <dt>廠商</dt>
          <dd>{ticket.vendor}</dd>
        </div>
        <div>
          <dt>型號</dt>
          <dd>{ticket.model}</dd>
        </div>
        <div>
          <dt>版本</dt>
          <dd>{ticket.version}</dd>
        </div>
        <div>
          <dt>排入佇列</dt>
          <dd>{ticket.enqueued_at || "-"}</dd>
        </div>
        <div>
          <dt>開始時間</dt>
          <dd>{ticket.started_at || "-"}</dd>
        </div>
        <div>
          <dt>完成時間</dt>
          <dd>{ticket.completed_at || "-"}</dd>
        </div>
      </dl>
      {ticket.machine && (
        <section className="machine">
          <h4>執行機器</h4>
          <div className="machine__grid">
            <div>
              <span className="label">Serial</span>
              <span>{ticket.machine.serial}</span>
            </div>
            <div>
              <span className="label">IP</span>
              <span>{ticket.machine.ip}</span>
            </div>
            <div>
              <span className="label">Port</span>
              <span>{ticket.machine.port}</span>
            </div>
          </div>
        </section>
      )}
    </article>
  );
}
