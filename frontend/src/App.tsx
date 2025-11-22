import "./App.css";
import { useMachineData } from "./hooks/useMachineData";
import { useMachineFilters } from "./hooks/useMachineFilters";
import { MachineCard } from "./components/Machine/MachineCard";
import { FilterBar } from "./components/UI/FilterBar";

export default function App() {
  // 1. 獲取資料
  const { machines, loading, error, refresh } = useMachineData();
  
  // 2. 處理過濾邏輯 (將 raw data 轉為 view model)
  const { 
    filters, 
    options, 
    filteredMachines, 
    stats, 
    actions 
  } = useMachineFilters(machines);

  return (
    <div className="app-shell">
      {/* Header Block */}
      <header className="masthead">
        <div>
          <h1>Switch Testbed Inventory</h1>
          <p>即時監控實驗網路設備狀態與資源</p>
        </div>
        <div className="masthead__actions">
          <div className="count-group">
            <span className="count-group__item">
              <strong>{stats.available}</strong>
              <span>Available</span>
            </span>
            <span className="count-group__item">
              <strong>{stats.total}</strong>
              <span>Total</span>
            </span>
          </div>
          <button 
            type="button" 
            onClick={refresh} 
            disabled={loading}
            className={loading ? "loading-btn" : ""}
          >
            {loading ? "Refreshing..." : "Refresh Now"}
          </button>
        </div>
      </header>

      {/* Filter Block */}
      <FilterBar 
        filters={filters} 
        options={options} 
        actions={actions} 
      />

      {/* Main Content Block */}
      <main className="content">
        {error && <div className="alert error">{error}</div>}

        {loading && filteredMachines.length === 0 && (
          <div className="loading-state">載入設備清單中...</div>
        )}

        {!loading && !error && filteredMachines.length === 0 && (
          <p className="empty-state">
            {machines.length === 0 
              ? "目前沒有任何設備資料 (device.yaml 為空或 API 異常)。" 
              : "沒有符合篩選條件的設備。"}
          </p>
        )}

        <section className="machine-grid">
          {filteredMachines.map((machine) => (
            <MachineCard key={machine.serial} machine={machine} />
          ))}
        </section>
      </main>
    </div>
  );
}