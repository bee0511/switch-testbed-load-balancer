import { useState } from "react";
import { FilterMenu } from "./components/FilterMenu";
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
  rawData: "",
};

function cloneFilters(filters: FilterState): FilterState {
  return {
    activeFields: [...filters.activeFields],
    fieldValues: { ...filters.fieldValues },
    dateRanges: Object.fromEntries(
      Object.entries(filters.dateRanges).map(([key, range]) => [key, { ...range }])
    ) as FilterState["dateRanges"],
    resultData: filters.resultData,
    rawData: filters.rawData,
  };
}

export default function App() {
  const [pendingFilters, setPendingFilters] = useState<FilterState>(initialFilters);
  const [appliedFilters, setAppliedFilters] = useState<FilterState>(initialFilters);
  const { tickets, loading, error } = useTickets(appliedFilters);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);

  const submitFilters = () => {
    setAppliedFilters(cloneFilters(pendingFilters));
  };

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero__overlay">
          <div className="hero__content">
            <div className="hero__branding">
              <span className="hero__badge">TSMC Network Lab</span>
              <h1>Switch Ticket Explorer</h1>
              <p>
                使用全新台積電色系介面，彈性配置廠商、型號、版本與裝置資訊，一次鎖定目標 ticket。
              </p>
            </div>
            <FilterMenu
              filters={pendingFilters}
              onChange={setPendingFilters}
              onSubmit={submitFilters}
              submitting={loading}
            />
          </div>
        </div>
      </header>

      <main className="content">
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
      </main>

      <TicketModal ticket={selectedTicket} onClose={() => setSelectedTicket(null)} />
    </div>
  );
}
