import "./App.css";
import { useEffect, useState } from "react";
import { useMachineData } from "./hooks/useMachineData";
import { useMachineFilters } from "./hooks/useMachineFilters";
import { MachineCard } from "./components/Machine/MachineCard";
import { FilterBar } from "./components/UI/FilterBar";
import { TokenPrompt } from "./components/UI/TokenPrompt";
import { useAuthToken } from "./hooks/useAuthToken";

export default function App() {
  const { token, setToken, clearToken } = useAuthToken();
  const [showTokenPrompt, setShowTokenPrompt] = useState(!token);

  // 1. 獲取資料
  const { machines, loading, error, refresh } = useMachineData(token);
  
  // 2. 處理過濾邏輯 (將 raw data 轉為 view model)
  const { 
    filters, 
    options, 
    filteredMachines, 
    stats, 
    actions 
  } = useMachineFilters(machines);

  useEffect(() => {
    if (!token) setShowTokenPrompt(true);
  }, [token]);

  const handleTokenSave = (value: string) => {
    setToken(value);
    setShowTokenPrompt(false);
  };

  const tokenMissing = !token;

  return (
    <div className="app-shell">
      <TokenPrompt
        open={showTokenPrompt}
        initialToken={token ?? ""}
        onSubmit={handleTokenSave}
        onCancel={token ? () => setShowTokenPrompt(false) : undefined}
      />

      {/* Header Block */}
      <header className="masthead">
        <div>
          <h1>Switch Testbed Inventory</h1>
          <p>即時監控實驗網路設備狀態與資源</p>
        </div>
        <div className="masthead__actions">
          <div className="token-chip">
            <span>Bearer Token</span>
            <div className="token-chip__actions">
              <button type="button" onClick={() => setShowTokenPrompt(true)}>
                {token ? "變更 Token" : "輸入 Token"}
              </button>
              {token && (
                <button type="button" className="ghost" onClick={clearToken}>
                  清除
                </button>
              )}
            </div>
          </div>
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
      {!tokenMissing && (
        <FilterBar 
          filters={filters} 
          options={options} 
          actions={actions} 
        />
      )}

      {/* Main Content Block */}
      <main className="content">
        {tokenMissing && (
          <div className="token-empty">
            <h3>需要 API Token 才能載入設備清單</h3>
            <p>請向管理員取得 token，並點擊「輸入 Token」。Token 會保存在本機瀏覽器，不會上傳。</p>
            <button type="button" onClick={() => setShowTokenPrompt(true)}>
              輸入 Token
            </button>
          </div>
        )}

        {!tokenMissing && error && <div className="alert error">{error}</div>}

        {!tokenMissing && loading && filteredMachines.length === 0 && (
          <div className="loading-state">載入設備清單中...</div>
        )}

        {!tokenMissing && !loading && !error && filteredMachines.length === 0 && (
          <p className="empty-state">
            {machines.length === 0 
              ? "目前沒有任何設備資料 (device.yaml 為空或 API 異常)。" 
              : "沒有符合篩選條件的設備。"}
          </p>
        )}

        {!tokenMissing && (
          <section className="machine-grid">
            {filteredMachines.map((machine) => (
              <MachineCard key={machine.serial} machine={machine} />
            ))}
          </section>
        )}
      </main>
    </div>
  );
}
