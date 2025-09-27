import { useState } from "react";
import { FilterPanel } from "./components/FilterPanel";
import { TicketCard } from "./components/TicketCard";
import { TicketModal } from "./components/TicketModal";
import { useTickets } from "./hooks/useTickets";
import type { FilterState, Ticket } from "./types";
import "./App.css";

const initialFilters: FilterState = {
  activeFields: [],
  fieldValues: {},
  dateRanges: {
    enqueued_at: {},
    started_at: {},
    completed_at: {}
  },
  resultData: "",
  rawData: ""
};

export default function App() {
  const [filters, setFilters] = useState<FilterState>(initialFilters);
  const { tickets, loading, error } = useTickets(filters);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);

  return (
    <div className="layout">
      <FilterPanel filters={filters} onChange={setFilters} />

      <section className="results">
        <header className="results__header">
          <div>
            <h2>搜尋結果</h2>
            <p>共 {tickets.length} 筆符合條件的 ticket。</p>
          </div>
          {loading && <span className="pill">載入中...</span>}
        </header>

        {error && <div className="alert">{error}</div>}

        {!loading && tickets.length === 0 && (
          <p className="empty">找不到符合條件的 ticket，請調整搜尋條件。</p>
        )}

        <div className="card-grid">
          {tickets.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} onClick={setSelectedTicket} />
          ))}
        </div>
      </section>

      <TicketModal ticket={selectedTicket} onClose={() => setSelectedTicket(null)} />
    </div>
  );
}
