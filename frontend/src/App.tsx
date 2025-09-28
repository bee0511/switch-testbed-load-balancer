import { useMemo, useState, useRef, useEffect } from "react";
import { FilterPanel } from "./components/FilterPanel";
import { TicketCard } from "./components/TicketCard";
import { TicketModal } from "./components/TicketModal";
import { useDeviceOptions } from "./hooks/useDeviceOptions";
import { useTickets } from "./hooks/useTickets";
import type { FilterState, Ticket } from "./types";
import "./App.css";

// 動畫持續時間常數，確保 JS 和 CSS 同步
const ANIMATION_DURATION = 300;

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
  const [isClosingModal, setIsClosingModal] = useState<boolean>(false);
  const [isClosingFilter, setIsClosingFilter] = useState<boolean>(false);
  const { options: deviceOptions, loading: deviceLoading, error: deviceError } = useDeviceOptions();
  
  // 用於清理 timeout 的 refs
  const modalTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const filterTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 組件卸載時清理所有 timeout
  useEffect(() => {
    return () => {
      if (modalTimeoutRef.current) {
        clearTimeout(modalTimeoutRef.current);
      }
      if (filterTimeoutRef.current) {
        clearTimeout(filterTimeoutRef.current);
      }
    };
  }, []);

  const submitFilters = () => {
    setAppliedFilters(cloneFilters(pendingFilters));
    handleCloseFilter();
  };

  const clearFilters = () => {
    setPendingFilters(cloneFilters(initialFilters));
    setAppliedFilters(cloneFilters(initialFilters));
  };

  const handleCloseModal = () => {
    if (isClosingModal) return; // 防止重複觸發
    
    // 清理之前的 timeout
    if (modalTimeoutRef.current) {
      clearTimeout(modalTimeoutRef.current);
    }
    
    setIsClosingModal(true);
    modalTimeoutRef.current = setTimeout(() => {
      setSelectedTicket(null);
      setIsClosingModal(false);
      modalTimeoutRef.current = null;
    }, ANIMATION_DURATION);
  };

  const handleCloseFilter = () => {
    if (isClosingFilter) return; // 防止重複觸發
    
    // 清理之前的 timeout
    if (filterTimeoutRef.current) {
      clearTimeout(filterTimeoutRef.current);
    }
    
    setIsClosingFilter(true);
    filterTimeoutRef.current = setTimeout(() => {
      setMenuOpen(false);
      setIsClosingFilter(false);
      filterTimeoutRef.current = null;
    }, ANIMATION_DURATION);
  };

  const handleSelectTicket = (ticket: Ticket) => {
    // 如果正在關閉模態，先清理狀態
    if (isClosingModal && modalTimeoutRef.current) {
      clearTimeout(modalTimeoutRef.current);
      setIsClosingModal(false);
      modalTimeoutRef.current = null;
    }
    setSelectedTicket(ticket);
  };

  const handleOpenFilter = () => {
    // 如果正在關閉篩選面板，先清理狀態
    if (isClosingFilter && filterTimeoutRef.current) {
      clearTimeout(filterTimeoutRef.current);
      setIsClosingFilter(false);
      filterTimeoutRef.current = null;
    }
    setMenuOpen(true);
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
        <div className="brand">
          <h1>Testbed Ticket Explorer</h1>
        </div>
        <button 
          type="button"
          className="filter-status"
          onClick={handleOpenFilter}
          aria-label="開啟篩選條件"
        >
          <span className="status-label">篩選條件</span>
          <span className="status-count">{activeFilterCount}</span>
        </button>
        <div className="search-actions">
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
            <TicketCard key={ticket.id} ticket={ticket} onClick={handleSelectTicket} />
          ))}
        </div>
      </main>

      <FilterPanel
        filters={pendingFilters}
        onChange={setPendingFilters}
        onSubmit={submitFilters}
        onClear={clearFilters}
        submitting={loading}
        isOpen={menuOpen}
        onClose={handleCloseFilter}
        isClosing={isClosingFilter}
        deviceConfig={deviceOptions}
        deviceLoading={deviceLoading}
        deviceError={deviceError}
      />

      <TicketModal 
        ticket={selectedTicket} 
        onClose={handleCloseModal}
        isClosing={isClosingModal}
      />
    </div>
  );
}
