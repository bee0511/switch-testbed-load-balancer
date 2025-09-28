import { useEffect, useMemo, useState } from "react";
import { useDeviceOptions } from "../hooks/useDeviceOptions";
import type { DateField, FilterField, FilterState } from "../types";
import { TextModal } from "./TextModal";
import "./FilterMenu.css";

interface FilterMenuProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  onSubmit: () => void;
  submitting?: boolean;
}

type DateErrorState = Partial<Record<DateField, string>>;

const SECTION_IDS = {
  device: "device",
  ticket: "ticket",
  date: "date",
  content: "content",
} as const;

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "queued", label: "排隊中" },
  { value: "running", label: "執行中" },
  { value: "completed", label: "已完成" },
  { value: "failed", label: "失敗" },
];

const TEXT_FIELDS: { field: FilterField; label: string; placeholder?: string }[] = [
  { field: "id", label: "Ticket ID", placeholder: "輸入 ticket 編號" },
];

type TextModalKind = "result" | "raw";

function getFieldArray(filters: FilterState, field: FilterField): string[] {
  const value = filters.fieldValues[field];
  if (!value) {
    return [];
  }
  if (Array.isArray(value)) {
    return value;
  }
  return value ? [value] : [];
}

function uniqueBy<T>(items: T[], getKey: (item: T) => string): T[] {
  const seen = new Set<string>();
  const result: T[] = [];
  items.forEach((item) => {
    const key = getKey(item);
    if (!seen.has(key)) {
      seen.add(key);
      result.push(item);
    }
  });
  return result;
}

export function FilterMenu({ filters, onChange, onSubmit, submitting = false }: FilterMenuProps) {
  const { sets, loading: deviceLoading, error: deviceError } = useDeviceOptions();
  const [menuOpen, setMenuOpen] = useState<boolean>(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set([SECTION_IDS.device]));
  const [modal, setModal] = useState<TextModalKind | null>(null);
  const [dateErrors, setDateErrors] = useState<DateErrorState>({});

  useEffect(() => {
    document.body.classList.toggle("has-filter-menu", menuOpen);
    return () => {
      document.body.classList.remove("has-filter-menu");
    };
  }, [menuOpen]);

  const toggleMenu = () => {
    setMenuOpen((prev) => !prev);
  };

  const toggleSection = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const updateFilters = (nextFieldValues: Partial<Record<FilterField, string | string[]>>) => {
    const fieldValues = { ...filters.fieldValues };
    const active = new Set<FilterField>(filters.activeFields);

    (Object.entries(nextFieldValues) as [FilterField, string | string[] | undefined][]).forEach(
      ([field, value]) => {
        if (!value || (Array.isArray(value) && value.length === 0)) {
          delete fieldValues[field];
          active.delete(field);
        } else {
          fieldValues[field] = Array.isArray(value) ? [...value] : value;
          if (!active.has(field)) {
            active.add(field);
          }
        }
      }
    );

    onChange({
      ...filters,
      fieldValues,
      activeFields: Array.from(active),
    });
  };

  const toggleMultiValue = (field: FilterField, option: string) => {
    const current = getFieldArray(filters, field);
    const exists = current.includes(option);
    const next = exists ? current.filter((item) => item !== option) : [...current, option];
    updateFilters({ [field]: next });
  };

  const updateTextField = (field: FilterField, value: string) => {
    const trimmed = value;
    updateFilters({ [field]: trimmed });
  };

  const selectedVendors = useMemo(() => new Set(getFieldArray(filters, "vendor")), [filters]);
  const selectedModels = useMemo(() => new Set(getFieldArray(filters, "model")), [filters]);
  const selectedVersions = useMemo(() => new Set(getFieldArray(filters, "version")), [filters]);

  const modelOptions = useMemo(
    () =>
      sets.models.filter((item) =>
        selectedVendors.size === 0 ? true : selectedVendors.has(item.vendor)
      ),
    [sets.models, selectedVendors]
  );

  const versionOptions = useMemo(
    () =>
      sets.versions.filter((item) => {
        if (selectedVendors.size > 0 && !selectedVendors.has(item.vendor)) {
          return false;
        }
        if (selectedModels.size > 0 && !selectedModels.has(item.model)) {
          return false;
        }
        return true;
      }),
    [sets.versions, selectedModels, selectedVendors]
  );

  const detailOptions = useMemo(() => {
    return sets.details.filter((detail) => {
      if (selectedVendors.size > 0 && !selectedVendors.has(detail.vendor)) {
        return false;
      }
      if (selectedModels.size > 0 && !selectedModels.has(detail.model)) {
        return false;
      }
      if (selectedVersions.size > 0 && !selectedVersions.has(detail.version)) {
        return false;
      }
      return true;
    });
  }, [sets.details, selectedModels, selectedVendors, selectedVersions]);

  const ipOptions = useMemo(
    () =>
      uniqueBy(
        detailOptions.map((detail) => ({
          value: detail.ip,
          label: `${detail.ip} ・ ${detail.vendor}/${detail.model}/${detail.version}`,
        })),
        (item) => item.value
      ),
    [detailOptions]
  );

  const portOptions = useMemo(
    () =>
      uniqueBy(
        detailOptions.map((detail) => ({
          value: String(detail.port),
          label: `${detail.port} ・ ${detail.ip}`,
        })),
        (item) => item.value
      ),
    [detailOptions]
  );

  const serialOptions = useMemo(
    () =>
      uniqueBy(
        detailOptions.map((detail) => ({
          value: detail.serial,
          label: `${detail.serial} ・ ${detail.vendor}/${detail.model}`,
        })),
        (item) => item.value
      ),
    [detailOptions]
  );

  const updateDate = (field: DateField, part: "from" | "to", value: string) => {
    const normalized = value === "" ? undefined : value;
    const nextRanges = {
      ...filters.dateRanges,
      [field]: {
        ...filters.dateRanges[field],
        [part]: normalized,
      },
    };

    const fromValue = nextRanges[field].from;
    const toValue = nextRanges[field].to;
    let error = "";
    if (fromValue && toValue && fromValue > toValue) {
      error = "結束時間需晚於開始時間";
    }
    setDateErrors((prev) => ({
      ...prev,
      [field]: error,
    }));

    onChange({
      ...filters,
      dateRanges: nextRanges,
    });
  };

  const hasDateError = Object.values(dateErrors).some((message) => message);
  const hasBlockingError = hasDateError;

  const openModal = (kind: TextModalKind) => {
    setModal(kind);
  };

  const closeModal = () => {
    setModal(null);
  };

  const handleModalSave = (kind: TextModalKind, value: string) => {
    if (kind === "result") {
      onChange({ ...filters, resultData: value });
    } else {
      onChange({ ...filters, rawData: value });
    }
    setModal(null);
  };

  const selectedStatusValues = getFieldArray(filters, "status");

  const isSectionExpanded = (id: string) => expanded.has(id);

  return (
    <div className={`filter-menu ${menuOpen ? "filter-menu--open" : ""}`}>
      <button
        type="button"
        className="filter-menu__trigger"
        onClick={toggleMenu}
        aria-expanded={menuOpen}
        aria-controls="filter-menu-panel"
      >
        <span className="filter-menu__icon" aria-hidden="true">
          <span></span>
          <span></span>
          <span></span>
        </span>
        <span className="filter-menu__label">條件搜尋</span>
      </button>

      <div className="filter-menu__overlay" hidden={!menuOpen}>
        <div className="filter-menu__panel" id="filter-menu-panel">
          <header className="filter-menu__header">
            <div>
              <h1>Switch Ticket Explorer</h1>
              <p>運用台積電色系的全新搜尋介面，快速鎖定需要的測試紀錄。</p>
            </div>
            <button type="button" className="filter-menu__close" onClick={toggleMenu}>
              ×
            </button>
          </header>

          <div className="filter-menu__sections">
            <section className={`filter-menu__section ${isSectionExpanded(SECTION_IDS.device) ? "is-expanded" : ""}`}>
              <button
                type="button"
                className="filter-menu__section-toggle"
                onClick={() => toggleSection(SECTION_IDS.device)}
                aria-expanded={isSectionExpanded(SECTION_IDS.device)}
              >
                裝置資訊
              </button>
              <div className="filter-menu__section-body">
                {deviceLoading && <p className="filter-menu__hint">載入裝置選項中...</p>}
                {deviceError && <p className="filter-menu__error">{deviceError}</p>}
                {!deviceLoading && !deviceError && (
                  <div className="filter-menu__grid">
                    <div>
                      <h3>廠商</h3>
                      <div className="filter-menu__options">
                        {sets.vendors.map((vendor) => (
                          <label key={vendor} className="filter-menu__option">
                            <input
                              type="checkbox"
                              checked={getFieldArray(filters, "vendor").includes(vendor)}
                              onChange={() => toggleMultiValue("vendor", vendor)}
                            />
                            <span>{vendor}</span>
                          </label>
                        ))}
                        {sets.vendors.length === 0 && (
                          <p className="filter-menu__hint">device.yaml 尚未設定廠商資訊。</p>
                        )}
                      </div>
                    </div>
                    <div>
                      <h3>型號</h3>
                      <div className="filter-menu__options">
                        {modelOptions.map((option) => (
                          <label key={`${option.vendor}-${option.model}`} className="filter-menu__option">
                            <input
                              type="checkbox"
                              checked={getFieldArray(filters, "model").includes(option.model)}
                              onChange={() => toggleMultiValue("model", option.model)}
                            />
                            <span>
                              <strong>{option.model}</strong>
                              <small>{option.vendor}</small>
                            </span>
                          </label>
                        ))}
                        {modelOptions.length === 0 && (
                          <p className="filter-menu__hint">請先選擇廠商以顯示對應的型號。</p>
                        )}
                      </div>
                    </div>
                    <div>
                      <h3>版本</h3>
                      <div className="filter-menu__options">
                        {versionOptions.map((option) => (
                          <label
                            key={`${option.vendor}-${option.model}-${option.version}`}
                            className="filter-menu__option"
                          >
                            <input
                              type="checkbox"
                              checked={getFieldArray(filters, "version").includes(option.version)}
                              onChange={() => toggleMultiValue("version", option.version)}
                            />
                            <span>
                              <strong>{option.version}</strong>
                              <small>
                                {option.vendor} / {option.model}
                              </small>
                            </span>
                          </label>
                        ))}
                        {versionOptions.length === 0 && (
                          <p className="filter-menu__hint">請先選擇廠商或型號以顯示版本。</p>
                        )}
                      </div>
                    </div>
                    <div>
                      <h3>IP 位址</h3>
                      <div className="filter-menu__options">
                        {ipOptions.map((option) => (
                          <label key={option.value} className="filter-menu__option">
                            <input
                              type="checkbox"
                              checked={getFieldArray(filters, "machine.ip").includes(option.value)}
                              onChange={() => toggleMultiValue("machine.ip", option.value)}
                            />
                            <span>{option.label}</span>
                          </label>
                        ))}
                        {ipOptions.length === 0 && (
                          <p className="filter-menu__hint">選擇廠商 / 型號 / 版本後即可顯示 IP。</p>
                        )}
                      </div>
                    </div>
                    <div>
                      <h3>Port</h3>
                      <div className="filter-menu__options">
                        {portOptions.map((option) => (
                          <label key={option.value} className="filter-menu__option">
                            <input
                              type="checkbox"
                              checked={getFieldArray(filters, "machine.port").includes(option.value)}
                              onChange={() => toggleMultiValue("machine.port", option.value)}
                            />
                            <span>{option.label}</span>
                          </label>
                        ))}
                        {portOptions.length === 0 && (
                          <p className="filter-menu__hint">目前沒有符合條件的 port。</p>
                        )}
                      </div>
                    </div>
                    <div>
                      <h3>序號</h3>
                      <div className="filter-menu__options">
                        {serialOptions.map((option) => (
                          <label key={option.value} className="filter-menu__option">
                            <input
                              type="checkbox"
                              checked={getFieldArray(filters, "machine.serial").includes(option.value)}
                              onChange={() => toggleMultiValue("machine.serial", option.value)}
                            />
                            <span>{option.label}</span>
                          </label>
                        ))}
                        {serialOptions.length === 0 && (
                          <p className="filter-menu__hint">尚無符合條件的序號。</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </section>

            <section className={`filter-menu__section ${isSectionExpanded(SECTION_IDS.ticket) ? "is-expanded" : ""}`}>
              <button
                type="button"
                className="filter-menu__section-toggle"
                onClick={() => toggleSection(SECTION_IDS.ticket)}
                aria-expanded={isSectionExpanded(SECTION_IDS.ticket)}
              >
                票據欄位
              </button>
              <div className="filter-menu__section-body">
                <div className="filter-menu__grid">
                  <div>
                    <h3>基本資訊</h3>
                    <div className="filter-menu__inputs">
                      {TEXT_FIELDS.map(({ field, label, placeholder }) => (
                        <label key={field} className="filter-menu__input">
                          <span>{label}</span>
                          <input
                            type="text"
                            value={typeof filters.fieldValues[field] === "string" ? (filters.fieldValues[field] as string) : ""}
                            placeholder={placeholder}
                            onChange={(event) => updateTextField(field, event.target.value)}
                          />
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3>狀態</h3>
                    <div className="filter-menu__options">
                      {STATUS_OPTIONS.map((status) => (
                        <label key={status.value} className="filter-menu__option">
                          <input
                            type="checkbox"
                            checked={selectedStatusValues.includes(status.value)}
                            onChange={() => toggleMultiValue("status", status.value)}
                          />
                          <span>{status.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section className={`filter-menu__section ${isSectionExpanded(SECTION_IDS.date) ? "is-expanded" : ""}`}>
              <button
                type="button"
                className="filter-menu__section-toggle"
                onClick={() => toggleSection(SECTION_IDS.date)}
                aria-expanded={isSectionExpanded(SECTION_IDS.date)}
              >
                時間篩選
              </button>
              <div className="filter-menu__section-body">
                <div className="filter-menu__dates">
                  {(["enqueued_at", "started_at", "completed_at"] as DateField[]).map((field) => (
                    <div key={field} className="filter-menu__date-group">
                      <span className="filter-menu__date-label">
                        {field === "enqueued_at" && "排程時間"}
                        {field === "started_at" && "開始時間"}
                        {field === "completed_at" && "完成時間"}
                      </span>
                      <div className="filter-menu__date-inputs">
                        <label>
                          <span>從</span>
                          <input
                            type="datetime-local"
                            value={filters.dateRanges[field].from ?? ""}
                            onChange={(event) => updateDate(field, "from", event.target.value)}
                          />
                        </label>
                        <label>
                          <span>到</span>
                          <input
                            type="datetime-local"
                            value={filters.dateRanges[field].to ?? ""}
                            onChange={(event) => updateDate(field, "to", event.target.value)}
                          />
                        </label>
                      </div>
                      {dateErrors[field] && <p className="filter-menu__error">{dateErrors[field]}</p>}
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className={`filter-menu__section ${isSectionExpanded(SECTION_IDS.content) ? "is-expanded" : ""}`}>
              <button
                type="button"
                className="filter-menu__section-toggle"
                onClick={() => toggleSection(SECTION_IDS.content)}
                aria-expanded={isSectionExpanded(SECTION_IDS.content)}
              >
                內容搜尋
              </button>
              <div className="filter-menu__section-body">
                <div className="filter-menu__actions">
                  <button type="button" onClick={() => openModal("result")}>
                    編輯 Result Data
                  </button>
                  <button type="button" onClick={() => openModal("raw")}>
                    編輯 Switch Config
                  </button>
                </div>
                <p className="filter-menu__hint">
                  需要大量貼上內容時，請使用上方按鈕開啟彈出視窗進行編輯。
                </p>
              </div>
            </section>
          </div>

          <footer className="filter-menu__footer">
            <button
              type="button"
              className="filter-menu__submit"
              onClick={() => {
                onSubmit();
                setMenuOpen(false);
              }}
              disabled={submitting || hasBlockingError}
            >
              {submitting ? "搜尋中..." : "套用條件"}
            </button>
          </footer>
        </div>
      </div>

      {modal && (
        <TextModal
          title={modal === "result" ? "Result Data" : "Switch Config (raw_data)"}
          initialValue={modal === "result" ? filters.resultData : filters.rawData}
          onClose={closeModal}
          onSave={(value) => handleModalSave(modal, value)}
        />
      )}
    </div>
  );
}
