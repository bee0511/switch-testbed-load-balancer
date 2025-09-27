import type { FilterField, FilterState } from "../types";
import "./FilterPanel.css";

const FILTER_FIELDS: { key: FilterField; label: string }[] = [
  { key: "id", label: "Ticket ID" },
  { key: "status", label: "狀態" },
  { key: "vendor", label: "廠商" },
  { key: "model", label: "型號" },
  { key: "version", label: "版本" },
  { key: "machine.serial", label: "機器序號" },
  { key: "machine.ip", label: "機器 IP" },
  { key: "machine.port", label: "機器 Port" }
];

interface FilterPanelProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  onSubmit: () => void;
  submitting?: boolean;
}

export function FilterPanel({ filters, onChange, onSubmit, submitting = false }: FilterPanelProps) {
  const toggleField = (field: FilterField) => {
    const isActive = filters.activeFields.includes(field);
    const nextFields = isActive
      ? filters.activeFields.filter((item) => item !== field)
      : [...filters.activeFields, field];

    const nextValues = { ...filters.fieldValues };
    if (!isActive) {
      nextValues[field] = nextValues[field] ?? "";
    } else {
      delete nextValues[field];
    }

    onChange({
      ...filters,
      activeFields: nextFields,
      fieldValues: nextValues
    });
  };

  const updateFieldValue = (field: FilterField, value: string) => {
    onChange({
      ...filters,
      fieldValues: {
        ...filters.fieldValues,
        [field]: value
      }
    });
  };

  const updateDate = (field: "enqueued_at" | "started_at" | "completed_at", part: "from" | "to", value: string) => {
    onChange({
      ...filters,
      dateRanges: {
        ...filters.dateRanges,
        [field]: {
          ...filters.dateRanges[field],
          [part]: value
        }
      }
    });
  };

  return (
    <section className="filter-panel">
      <div className="filter-header">
        <h1>Switch Ticket Explorer</h1>
        <p>依照欄位與時間範圍快速篩選待處理與歷史 ticket。</p>
      </div>

      <div className="filter-section">
        <h2>選擇欄位</h2>
        <div className="field-grid">
          {FILTER_FIELDS.map(({ key, label }) => (
            <label key={key} className="field-option">
              <input
                type="checkbox"
                checked={filters.activeFields.includes(key)}
                onChange={() => toggleField(key)}
              />
              <span>{label}</span>
            </label>
          ))}
        </div>
      </div>

      {filters.activeFields.length > 0 && (
        <div className="filter-section">
          <h2>欄位內容</h2>
          <div className="field-inputs">
            {filters.activeFields.map((field) => (
              <label key={field} className="input-group">
                <span>{FILTER_FIELDS.find((item) => item.key === field)?.label ?? field}</span>
                <input
                  type="text"
                  value={filters.fieldValues[field] ?? ""}
                  onChange={(event) => updateFieldValue(field, event.target.value)}
                  placeholder="輸入關鍵字"
                />
              </label>
            ))}
          </div>
        </div>
      )}

      <div className="filter-section">
        <h2>時間範圍</h2>
        <div className="date-grid">
          {(["enqueued_at", "started_at", "completed_at"] as const).map((field) => (
            <div key={field} className="date-group">
              <span className="group-label">
                {field === "enqueued_at" && "排入佇列時間"}
                {field === "started_at" && "開始時間"}
                {field === "completed_at" && "完成時間"}
              </span>
              <div className="date-inputs">
                <input
                  type="datetime-local"
                  value={filters.dateRanges[field].from ?? ""}
                  onChange={(event) => updateDate(field, "from", event.target.value)}
                />
                <span className="delimiter">至</span>
                <input
                  type="datetime-local"
                  value={filters.dateRanges[field].to ?? ""}
                  onChange={(event) => updateDate(field, "to", event.target.value)}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="filter-section">
        <h2>內容搜尋</h2>
        <div className="text-grid">
          <label className="input-group">
            <span>Result Data</span>
            <input
              type="text"
              value={filters.resultData}
              onChange={(event) => onChange({ ...filters, resultData: event.target.value })}
              placeholder="輸入結果內容關鍵字"
            />
          </label>
          <label className="input-group">
            <span>Switch Config (raw_data)</span>
            <input
              type="text"
              value={filters.rawData}
              onChange={(event) => onChange({ ...filters, rawData: event.target.value })}
              placeholder="輸入設定內容關鍵字"
            />
          </label>
        </div>
      </div>

      <div className="filter-actions">
        <button type="button" onClick={onSubmit} disabled={submitting}>
          {submitting ? "搜尋中..." : "送出查詢"}
        </button>
      </div>
    </section>
  );
}
