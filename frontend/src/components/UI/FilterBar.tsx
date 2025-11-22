import type { MachineFilters } from "../../types";

interface FilterOptions {
  vendors: string[];
  models: string[];
  versions: string[];
}

interface FilterActions {
  setVendor: (v: string) => void;
  setModel: (v: string) => void;
  setVersion: (v: string) => void;
  setStatus: (v: string) => void;
  reset: () => void;
}

interface Props {
  filters: MachineFilters;
  options: FilterOptions;
  actions: FilterActions;
}

export function FilterBar({ filters, options, actions }: Props) {
  const hasActiveFilters = Boolean(
    filters.vendor || filters.model || filters.version || filters.status !== "all"
  );

  return (
    <section className="filter-bar">
      <form className="filter-form" onSubmit={(e) => e.preventDefault()}>
        <div className="filter-field">
          <label htmlFor="vendor">廠商 (Vendor)</label>
          <select
            id="vendor"
            value={filters.vendor ?? ""}
            onChange={(e) => actions.setVendor(e.target.value)}
            disabled={options.vendors.length === 0}
          >
            <option value="">All Vendors</option>
            {options.vendors.map(v => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="model">型號 (Model)</label>
          <select
            id="model"
            value={filters.model ?? ""}
            onChange={(e) => actions.setModel(e.target.value)}
            disabled={!filters.vendor || options.models.length === 0}
          >
            <option value="">All Models</option>
            {options.models.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="version">版本 (Version)</label>
          <select
            id="version"
            value={filters.version ?? ""}
            onChange={(e) => actions.setVersion(e.target.value)}
            disabled={!filters.vendor || !filters.model || options.versions.length === 0}
          >
            <option value="">All Versions</option>
            {options.versions.map(v => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>

        <div className="filter-field">
          <label htmlFor="status">狀態 (Status)</label>
          <select
            id="status"
            value={filters.status}
            onChange={(e) => actions.setStatus(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="available">Available</option>
            <option value="unavailable">Unavailable</option>
            <option value="unreachable">Unreachable</option>
          </select>
        </div>

        <div className="filter-actions">
          <button type="button" onClick={actions.reset} disabled={!hasActiveFilters}>
            Reset Filters
          </button>
        </div>
      </form>
    </section>
  );
}