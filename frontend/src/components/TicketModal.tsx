import { useEffect, useState } from "react";
import type { Ticket } from "../types";
import "./TicketModal.css";

interface TicketModalProps {
  ticket: Ticket | null;
  onClose: () => void;
  isClosing?: boolean;
}

type TabKey = "result" | "raw";

const TAB_LABELS: Record<TabKey, string> = {
  result: "Result Data",
  raw: "Switch Config"
};

export function TicketModal({ ticket, onClose, isClosing }: TicketModalProps) {
  const [activeTab, setActiveTab] = useState<TabKey>("result");

  useEffect(() => {
    setActiveTab("result");
  }, [ticket?.id]);

  useEffect(() => {
    const listener = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, [onClose]);

  if (!ticket) {
    return null;
  }

  const content = activeTab === "result" ? ticket.result_data : ticket.raw_data;

  return (
    <div className={`modal-backdrop ${isClosing ? 'closing' : ''}`} onClick={onClose}>
      <div className={`modal ${isClosing ? 'closing' : ''}`} role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
        <header className="modal__header">
          <div>
            <span className="modal__status">{ticket.status}</span>
            <h3>{ticket.id}</h3>
          </div>
          <button type="button" className="modal__close" onClick={onClose}>
            ×
          </button>
        </header>
        <nav className={`modal__tabs ${activeTab === "raw" ? "tab-1" : ""}`}>
          {(Object.keys(TAB_LABELS) as TabKey[]).map((key) => (
            <button
              key={key}
              type="button"
              className={key === activeTab ? "active" : ""}
              onClick={() => setActiveTab(key)}
            >
              {TAB_LABELS[key]}
            </button>
          ))}
        </nav>
        <section className="modal__content">
          {content ? (
            <pre>{content}</pre>
          ) : (
            <p className="empty">無內容</p>
          )}
        </section>
      </div>
    </div>
  );
}
