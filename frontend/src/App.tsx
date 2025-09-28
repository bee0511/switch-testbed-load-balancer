import { useMemo, useState } from "react";
import { FilterPanel } from "./components/FilterPanel";
import { TicketCard } from "./components/TicketCard";
import { TicketModal } from "./components/TicketModal";
import { useDeviceOptions } from "./hooks/useDeviceOptions";
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
  const [menuOpen, setMenuOpen] = useState<boolean>(false);
  const { options: deviceOptions, loading: deviceLoading, error: deviceError } = useDeviceOptions();

  const submitFilters = () => {
    setAppliedFilters(cloneFilters(pendingFilters));
    setMenuOpen(false);
  };

  const activeFilterCount = useMemo(() => {
    const fieldCount = pendingFilters.activeFields.length;
    const dateCount = Object.values(pendingFilters.dateRanges).filter(
      (range) => range.from || range.to
    ).length;
    const textCount = [pendingFilters.resultData, pendingFilters.rawData].filter((value) =>
      value.trim()
    ).length;
    return fieldCount + dateCount + textCount;
  }, [pendingFilters]);

  return (
    <div className="app-shell">
      <header className="top-bar">
        <button
          type="button"
          className="menu-button"
          onClick={() => setMenuOpen(true)}
          aria-label="開啟篩選條件"
        >
          <span />
          <span />
          <span />
        </button>
        <div className="brand">
          <h1>Switch Ticket Explorer</h1>
          <p>以台積電風格重新設計的搜尋控制台</p>
        </div>
        <div className="filter-status">
          <span className="status-label">篩選條件</span>
          <span className="status-count">{activeFilterCount}</span>
          <button type="button" onClick={submitFilters} disabled={loading}>
            {loading ? "搜尋中..." : "立即搜尋"}
          </button>
        </div>
      </header>

      <main className="results">
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
      </main>

      <FilterPanel
        filters={pendingFilters}
        onChange={setPendingFilters}
        onSubmit={submitFilters}
        submitting={loading}
        isOpen={menuOpen}
        onClose={() => setMenuOpen(false)}
        deviceConfig={deviceOptions}
        deviceLoading={deviceLoading}
        deviceError={deviceError}
      />

      <TicketModal ticket={selectedTicket} onClose={() => setSelectedTicket(null)} />
    </div>
  );
}
