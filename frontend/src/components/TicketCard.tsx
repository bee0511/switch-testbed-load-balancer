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
        <div className="vendor">
          <dt>廠商</dt>
          <dd>{ticket.vendor}</dd>
        </div>
        <div className="model">
          <dt>型號</dt>
          <dd>{ticket.model}</dd>
        </div>
        <div className="version">
          <dt>版本</dt>
          <dd>{ticket.version}</dd>
        </div>
        <div className="enqueued">
          <dt>排入佇列</dt>
          <dd>{ticket.enqueued_at || "-"}</dd>
        </div>
        <div className="started">
          <dt>開始時間</dt>
          <dd>{ticket.started_at || "-"}</dd>
        </div>
        <div className="completed">
          <dt>完成時間</dt>
          <dd>{ticket.completed_at || "-"}</dd>
        </div>
      </dl>
    </article>
  );
}
