import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import { useMachines } from "./hooks/useMachines";
import type { Machine, MachineFilters } from "./types";
import "./App.css";

function StatusBadge({ status }: { status: Machine["status"] }) {
  return <span className={`status-pill status-pill--${status}`}>{status}</span>;
}

function MachineCard({ machine }: { machine: Machine }) {
  return (
    <article className="machine-card">
      <header>
        <h3>
          {machine.vendor} / {machine.model}
        </h3>
        <StatusBadge status={machine.status} />
      </header>
      <dl>
        <div>
          <dt>Version</dt>
          <dd>{machine.version}</dd>
        </div>
        <div>
          <dt>Serial</dt>
          <dd>{machine.serial}</dd>
        </div>
        <div>
          <dt>IP</dt>
          <dd>{machine.ip}</dd>
        </div>
        <div>
          <dt>Port</dt>
          <dd>{machine.port}</dd>
        </div>
      </dl>
    </article>
  );
}

export default function App() {
  const [filters, setFilters] = useState<MachineFilters>({ status: "all" });
  const { machines, loading, error, refresh } = useMachines(15000);

  const vendorTree = useMemo(() => {
    const map = new Map<string, Map<string, Set<string>>>();
    machines.forEach((machine) => {
      if (!map.has(machine.vendor)) {
        map.set(machine.vendor, new Map());
      }
      const modelMap = map.get(machine.vendor)!;
      if (!modelMap.has(machine.model)) {
        modelMap.set(machine.model, new Set());
      }
      modelMap.get(machine.model)!.add(machine.version);
    });
    return map;
  }, [machines]);

  const vendors = useMemo(() => Array.from(vendorTree.keys()), [vendorTree]);
  const models = useMemo(() => {
    if (!filters.vendor) {
      return [] as string[];
    }
    const modelMap = vendorTree.get(filters.vendor);
    if (!modelMap) {
      return [] as string[];
    }
    return Array.from(modelMap.keys());
  }, [vendorTree, filters.vendor]);
  const versions = useMemo(() => {
    if (!filters.vendor || !filters.model) {
      return [] as string[];
    }
    const modelMap = vendorTree.get(filters.vendor);
    const versionSet = modelMap?.get(filters.model);
    if (!versionSet) {
      return [] as string[];
    }
    return Array.from(versionSet.values());
  }, [vendorTree, filters.vendor, filters.model]);

  const filteredMachines = useMemo(() => {
    return machines.filter((machine) => {
      if (filters.vendor && machine.vendor !== filters.vendor) {
        return false;
      }
      if (filters.model && machine.model !== filters.model) {
        return false;
      }
      if (filters.version && machine.version !== filters.version) {
        return false;
      }
      if (filters.status && filters.status !== "all" && machine.status !== filters.status) {
        return false;
      }
      return true;
    });
  }, [machines, filters]);

  const hasActiveFilters = Boolean(
    filters.vendor || filters.model || filters.version || (filters.status && filters.status !== "all")
  );

  const { total, available } = useMemo(() => {
    const availableCount = filteredMachines.filter((machine) => machine.available).length;
    return {
      total: filteredMachines.length,
      available: availableCount,
    };
  }, [filteredMachines]);

  const handleVendorChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value || undefined;
    setFilters((prev) => ({
      ...prev,
      vendor: value,
      model: undefined,
      version: undefined,
    }));
  };

  const handleModelChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value || undefined;
    setFilters((prev) => ({
      ...prev,
      model: value,
      version: undefined,
    }));
  };

  const handleVersionChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value || undefined;
    setFilters((prev) => ({
      ...prev,
      version: value,
    }));
  };

  const handleStatusChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value as MachineFilters["status"];
    setFilters((prev) => ({
      ...prev,
      status: value,
    }));
  };

  const resetFilters = () => {
    setFilters({ status: "all" });
  };

  return (
    <div className="app-shell">
      <header className="masthead">
        <div>
          <h1>Switch Testbed Inventory</h1>
          <p>目前所有實驗機器的狀態與詳細資訊</p>
        </div>
        <div className="masthead__actions">
          <div className="count-group">
            <span className="count-group__item">
              <strong>{available}</strong>
              <span>可用</span>
            </span>
            <span className="count-group__item">
              <strong>{total}</strong>
              <span>總數</span>
            </span>
          </div>
          <button type="button" onClick={refresh} disabled={loading}>
            {loading ? "更新中..." : "立即更新"}
          </button>
        </div>
      </header>

      <section className="filter-bar">
        <form className="filter-form" onSubmit={(event) => event.preventDefault()}>
          <div className="filter-field">
            <label htmlFor="vendor-select">廠商</label>
            <select
              id="vendor-select"
              value={filters.vendor ?? ""}
              onChange={handleVendorChange}
              disabled={vendors.length === 0}
            >
              <option value="">全部廠商</option>
              {vendors.map((vendor) => (
                <option key={vendor} value={vendor}>
                  {vendor}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-field">
            <label htmlFor="model-select">Model</label>
            <select
              id="model-select"
              value={filters.model ?? ""}
              onChange={handleModelChange}
              disabled={!filters.vendor || models.length === 0}
            >
              <option value="">全部 Model</option>
              {models.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-field">
            <label htmlFor="version-select">Version</label>
            <select
              id="version-select"
              value={filters.version ?? ""}
              onChange={handleVersionChange}
              disabled={!filters.vendor || !filters.model || versions.length === 0}
            >
              <option value="">全部版本</option>
              {versions.map((version) => (
                <option key={version} value={version}>
                  {version}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-field">
            <label htmlFor="status-select">狀態</label>
            <select
              id="status-select"
              value={filters.status ?? "all"}
              onChange={handleStatusChange}
            >
              <option value="all">全部</option>
              <option value="available">可用</option>
              <option value="unavailable">使用中</option>
              <option value="unreachable">無法連線</option>
            </select>
          </div>

          <div className="filter-actions">
            <button
              type="button"
              onClick={resetFilters}
              disabled={!hasActiveFilters}
            >
              清除條件
            </button>
          </div>
        </form>
      </section>

      <main className="content">
        {error && <div className="alert">{error}</div>}

        {!error && total === 0 && !loading && (
          <p className="empty">
            {hasActiveFilters ? "找不到符合篩選條件的機器。" : "device.yaml 尚未定義任何可追蹤的機器。"}
          </p>
        )}

        {loading && <p className="loading">讀取中...</p>}

        <section className="machine-grid">
          {filteredMachines.map((machine) => (
            <MachineCard key={machine.serial_number} machine={machine} />
          ))}
        </section>
      </main>
    </div>
  );
}
