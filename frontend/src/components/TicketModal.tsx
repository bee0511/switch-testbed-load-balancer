import { useEffect, useRef, useState } from "react";
import type { Ticket } from "../types";
import "./TicketModal.css";

interface TicketModalProps {
  ticket: Ticket | null;
  onClose: () => void;
  isClosing?: boolean;
}

type TabKey = "result" | "raw" | "machine";

const TABS: { key: TabKey; label: string }[] = [
  { key: "result", label: "Result Data" },
  { key: "raw", label: "Switch Config" },
  { key: "machine", label: "機器資訊" }
];

export function TicketModal({ ticket, onClose, isClosing }: TicketModalProps) {
  const [activeTab, setActiveTab] = useState<TabKey>("result");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const copyTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    setActiveTab("result");
  }, [ticket?.id]);

  useEffect(() => {
    return () => {
      if (copyTimeoutRef.current !== null) {
        window.clearTimeout(copyTimeoutRef.current);
        copyTimeoutRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const listener = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, [onClose]);

  const handleCopy = async (key: string, value: string | number | null | undefined) => {
    if (value === null || value === undefined) {
      return;
    }

    const text = String(value);
    if (!text) {
      return;
    }

    try {
      if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else if (typeof document !== "undefined") {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }

      setCopiedKey(key);
      if (copyTimeoutRef.current !== null) {
        window.clearTimeout(copyTimeoutRef.current);
      }
      copyTimeoutRef.current = window.setTimeout(() => {
        setCopiedKey(null);
        copyTimeoutRef.current = null;
      }, 1500);
    } catch (error) {
      console.error("Failed to copy value", error);
    }
  };

  useEffect(() => {
    if (copyTimeoutRef.current !== null) {
      window.clearTimeout(copyTimeoutRef.current);
      copyTimeoutRef.current = null;
    }
    setCopiedKey(null);
  }, [activeTab]);

  const renderTextTab = (key: "result" | "raw", content: string | null | undefined) => {
    if (!content) {
      return <p className="empty">無內容</p>;
    }

    const copyKey = `text-${key}`;
    const tabLabel = TABS.find((tab) => tab.key === key)?.label ?? "";
    const isCopied = copiedKey === copyKey;

    return (
      <>
        <div className="text-tab__content">
          <pre>{content}</pre>
          <button
            type="button"
            className="copy-button copy-button--floating"
            onClick={() => handleCopy(copyKey, content)}
            aria-label={`複製 ${tabLabel}`}
          >
            {isCopied ? "已複製" : "複製"}
          </button>
        </div>
      </>
    );
  };

  if (!ticket) {
    return null;
  }

  const activeIndex = TABS.findIndex((tab) => tab.key === activeTab);
  const safeIndex = activeIndex < 0 ? 0 : activeIndex;
  const tabClassName = `modal__tabs tab-count-${TABS.length} tab-active-${safeIndex}`;

  const renderContent = () => {
    switch (activeTab) {
      case "result":
        return renderTextTab("result", ticket.result_data);
      case "raw":
        return renderTextTab("raw", ticket.raw_data);
      case "machine": {
        const machineEntries = [
          { key: "vendor", label: "Vendor", value: ticket.vendor },
          { key: "model", label: "Model", value: ticket.model },
          { key: "version", label: "Version", value: ticket.version },
          { key: "serial", label: "Serial", value: ticket.machine?.serial },
          { key: "ip", label: "IP", value: ticket.machine?.ip },
          {
            key: "port",
            label: "Port",
            value: ticket.machine?.port ?? null
          }
        ];

        return (
          <div className="machine-info">
            {machineEntries.map(({ key, label, value }) => {
              const copyKey = `machine-${key}`;
              const displayValue = value ?? "-";
              const isCopyDisabled = value === null || value === undefined;

              return (
                <div className="machine-info__row" key={key}>
                  <span className="label">{label}</span>
                  <span className="value">{displayValue}</span>
                  <button
                    type="button"
                    className="copy-button"
                    onClick={() => handleCopy(copyKey, value)}
                    disabled={isCopyDisabled}
                    aria-label={`複製 ${label}`}
                  >
                    {copiedKey === copyKey ? "已複製" : "複製"}
                  </button>
                </div>
              );
            })}
            {!ticket.machine && (
              <p className="machine-info__note">目前尚未指派機器，此區將在派發後顯示詳細資訊。</p>
            )}
          </div>
        );
      }
      default:
        return null;
    }
  };

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
        <nav className={tabClassName}>
          {TABS.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              className={key === activeTab ? "active" : ""}
              onClick={() => setActiveTab(key)}
            >
              {label}
            </button>
          ))}
        </nav>
        <section className="modal__content">
          {renderContent()}
        </section>
      </div>
    </div>
  );
}
