import { useMemo, useState } from "react";
import type { DeviceConfig, FilterField, FilterState } from "../types";
import { TextEntryModal } from "./TextEntryModal";
import "./FilterPanel.css";

const TEXT_FIELDS: { key: FilterField; label: string; placeholder: string }[] = [
  { key: "id", label: "Ticket ID", placeholder: "輸入 ticket ID" },
];

const STATUS_OPTIONS = [
  { value: "queued", label: "queued" },
  { value: "running", label: "running" },
  { value: "completed", label: "completed" },
  { value: "failed", label: "failed" },
];

const DEVICE_FIELDS: (keyof DeviceSelections)[] = [
  "vendor",
  "model",
  "version",
  "machine.ip",
  "machine.serial",
  "machine.port",
];

interface FilterPanelProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  onSubmit: () => void;
  onClear: () => void;
  submitting?: boolean;
  isOpen: boolean;
  onClose: () => void;
  isClosing?: boolean;
  deviceConfig: DeviceConfig | null;
  deviceLoading: boolean;
  deviceError: string | null;
}

type SectionId = "device" | "dates" | "advanced";

type DeviceSelections = {
  vendor: string[];
  model: string[];
  version: string[];
  "machine.ip": string[];
  "machine.serial": string[];
  "machine.port": string[];
};

function parseSelections(value: string | undefined): string[] {
  if (!value) {
    return [];
  }
  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function selectionToValue(values: string[]): string | undefined {
  if (values.length === 0) {
    return undefined;
  }
  return values.join(",");
}

function collectModelOptions(
  config: DeviceConfig | null,
  vendors: string[]
): { vendor: string; name: string }[] {
  if (!config || vendors.length === 0) {
    return [];
  }
  const results: { vendor: string; name: string }[] = [];
  config.vendors.forEach((vendorEntry) => {
    if (!vendors.includes(vendorEntry.vendor)) {
      return;
    }
    vendorEntry.models.forEach((model) => {
      results.push({ vendor: vendorEntry.vendor, name: model.model });
    });
  });
  return results;
}

function collectVersionOptions(
  config: DeviceConfig | null,
  vendors: string[],
  models: string[]
): { vendor: string; model: string; name: string }[] {
  if (!config || vendors.length === 0 || models.length === 0) {
    return [];
  }
  const results: { vendor: string; model: string; name: string }[] = [];
  config.vendors.forEach((vendorEntry) => {
    if (!vendors.includes(vendorEntry.vendor)) {
      return;
    }
    vendorEntry.models.forEach((modelEntry) => {
      if (!models.includes(modelEntry.model)) {
        return;
      }
      modelEntry.versions.forEach((versionEntry) => {
        results.push({
          vendor: vendorEntry.vendor,
          model: modelEntry.model,
          name: versionEntry.version,
        });
      });
    });
  });
  return results;
}

interface DeviceDetailOption {
  vendor: string;
  model: string;
  version: string;
  ip: string;
  serial: string;
  port: number;
}

function collectDeviceDetailOptions(
  config: DeviceConfig | null,
  vendors: string[],
  models: string[],
  versions: string[]
): DeviceDetailOption[] {
  if (!config || vendors.length === 0 || models.length === 0 || versions.length === 0) {
    return [];
  }
  const results: DeviceDetailOption[] = [];
  config.vendors.forEach((vendorEntry) => {
    if (!vendors.includes(vendorEntry.vendor)) {
      return;
    }
    vendorEntry.models.forEach((modelEntry) => {
      if (!models.includes(modelEntry.model)) {
        return;
      }
      modelEntry.versions.forEach((versionEntry) => {
        if (!versions.includes(versionEntry.version)) {
          return;
        }
        versionEntry.devices.forEach((device) => {
          results.push({
            vendor: vendorEntry.vendor,
            model: modelEntry.model,
            version: versionEntry.version,
            ip: device.ip,
            serial: device.serial_number,
            port: device.port,
          });
        });
      });
    });
  });
  return results;
}

function applyDeviceSelections(
  filters: FilterState,
  onChange: (filters: FilterState) => void,
  selections: DeviceSelections
) {
  const nextFieldValues: FilterState["fieldValues"] = { ...filters.fieldValues };
  let nextActiveFields = filters.activeFields.filter((field) => 
    !(DEVICE_FIELDS as readonly string[]).includes(field)
  );

  DEVICE_FIELDS.forEach((field) => {
    const values = selections[field];
    const value = selectionToValue(values);
    if (value) {
      nextFieldValues[field] = value;
      if (!nextActiveFields.includes(field)) {
        nextActiveFields = [...nextActiveFields, field];
      }
    } else {
      delete nextFieldValues[field];
    }
  });

  onChange({
    ...filters,
    activeFields: nextActiveFields,
    fieldValues: nextFieldValues,
  });
}

function sanitizeSelections(
  selections: DeviceSelections,
  available: Partial<DeviceSelections>
): DeviceSelections {
  return {
    vendor: selections.vendor.filter((item) => available.vendor?.includes(item) ?? true),
    model: selections.model.filter((item) => available.model?.includes(item) ?? true),
    version: selections.version.filter((item) => available.version?.includes(item) ?? true),
    "machine.ip": selections["machine.ip"].filter((item) =>
      available["machine.ip"]?.includes(item) ?? true
    ),
    "machine.serial": selections["machine.serial"].filter((item) =>
      available["machine.serial"]?.includes(item) ?? true
    ),
    "machine.port": selections["machine.port"].filter((item) =>
      available["machine.port"]?.includes(item) ?? true
    ),
  };
}

export function FilterPanel({
  filters,
  onChange,
  onSubmit,
  onClear,
  submitting = false,
  isOpen,
  onClose,
  isClosing = false,
  deviceConfig,
  deviceLoading,
  deviceError,
}: FilterPanelProps) {
  const [openSections, setOpenSections] = useState<SectionId[]>(["device"]);
  const [activeTextModal, setActiveTextModal] = useState<"result" | "raw" | null>(null);
  const [dateErrors, setDateErrors] = useState<Record<string, string>>({});

  const selections: DeviceSelections = useMemo(
    () => ({
      vendor: parseSelections(filters.fieldValues.vendor),
      model: parseSelections(filters.fieldValues.model),
      version: parseSelections(filters.fieldValues.version),
      "machine.ip": parseSelections(filters.fieldValues["machine.ip"]),
      "machine.serial": parseSelections(filters.fieldValues["machine.serial"]),
      "machine.port": parseSelections(filters.fieldValues["machine.port"]),
    }),
    [filters.fieldValues]
  );

  const vendorOptions = useMemo(() => deviceConfig?.vendors ?? [], [deviceConfig]);
  const availableVendors = useMemo(
    () => vendorOptions.map((vendor) => vendor.vendor),
    [vendorOptions]
  );
  const modelOptions = useMemo(
    () => collectModelOptions(deviceConfig, selections.vendor),
    [deviceConfig, selections.vendor]
  );
  const availableModels = useMemo(
    () => modelOptions.map((model) => model.name),
    [modelOptions]
  );
  const versionOptions = useMemo(
    () => collectVersionOptions(deviceConfig, selections.vendor, selections.model),
    [deviceConfig, selections.vendor, selections.model]
  );
  const availableVersions = useMemo(
    () => versionOptions.map((version) => version.name),
    [versionOptions]
  );
  const deviceDetails = useMemo(
    () => collectDeviceDetailOptions(deviceConfig, selections.vendor, selections.model, selections.version),
    [deviceConfig, selections.vendor, selections.model, selections.version]
  );
  const availableIps = useMemo(
    () => deviceDetails.map((device) => device.ip),
    [deviceDetails]
  );
  const availableSerials = useMemo(
    () => deviceDetails.map((device) => device.serial),
    [deviceDetails]
  );
  const availablePorts = useMemo(
    () => deviceDetails.map((device) => String(device.port)),
    [deviceDetails]
  );

  const updateSelections = (next: DeviceSelections) => {
    const sanitized = sanitizeSelections(next, {
      vendor: availableVendors,
      model: availableModels,
      version: availableVersions,
      "machine.ip": availableIps,
      "machine.serial": availableSerials,
      "machine.port": availablePorts,
    });
    applyDeviceSelections(filters, onChange, sanitized);
  };

  const toggleSection = (section: SectionId) => {
    setOpenSections((prev) =>
      prev.includes(section) ? prev.filter((item) => item !== section) : [...prev, section]
    );
  };

  const updateDate = (
    field: "enqueued_at" | "started_at" | "completed_at",
    part: "from" | "to",
    value: string
  ) => {
    const nextRanges = {
      ...filters.dateRanges,
      [field]: {
        ...filters.dateRanges[field],
        [part]: value,
      },
    } as FilterState["dateRanges"];

    const from = nextRanges[field].from;
    const to = nextRanges[field].to;
    const hasError = Boolean(from && to && new Date(to) < new Date(from));
    setDateErrors((prev) => ({
      ...prev,
      [field]: hasError ? "結束時間需晚於開始時間" : "",
    }));

    onChange({
      ...filters,
      dateRanges: nextRanges,
    });
  };

  const updateTextField = (field: FilterField, value: string) => {
    const trimmed = value.trim();
    const nextValues = { ...filters.fieldValues };
    let nextActive = filters.activeFields;

    if (trimmed.length > 0) {
      nextValues[field] = trimmed;
      if (!nextActive.includes(field)) {
        nextActive = [...nextActive, field];
      }
    } else {
      delete nextValues[field];
      nextActive = nextActive.filter((item) => item !== field);
    }

    onChange({
      ...filters,
      activeFields: nextActive,
      fieldValues: nextValues,
    });
  };

  const toggleStatusValue = (status: string) => {
    const currentStatusValues = parseSelections(filters.fieldValues.status);
    const nextValues = { ...filters.fieldValues };
    let nextActive = filters.activeFields;

    const exists = currentStatusValues.includes(status);
    const nextStatusValues = exists
      ? currentStatusValues.filter((item) => item !== status)
      : [...currentStatusValues, status];

    if (nextStatusValues.length > 0) {
      nextValues.status = nextStatusValues.join(",");
      if (!nextActive.includes("status")) {
        nextActive = [...nextActive, "status"];
      }
    } else {
      delete nextValues.status;
      nextActive = nextActive.filter((field) => field !== "status");
    }

    onChange({
      ...filters,
      activeFields: nextActive,
      fieldValues: nextValues,
    });
  };

  const toggleDeviceValue = (field: keyof DeviceSelections, value: string) => {
    const currentValues = selections[field].slice();
    const exists = currentValues.includes(value);
    const nextValues = exists
      ? currentValues.filter((item) => item !== value)
      : [...currentValues, value];

    updateSelections({
      ...selections,
      [field]: nextValues,
    });
  };

  const handleVendorToggle = (vendor: string) => {
    // 單選模式：如果點擊的是已選中的廠商，則取消選擇；否則只選擇這個廠商
    const nextVendors = selections.vendor.includes(vendor) ? [] : [vendor];

    const modelsAfterVendor = collectModelOptions(deviceConfig, nextVendors).map((model) => model.name);
    // 清空不相關的選擇
    const sanitizedModels: string[] = [];
    const versionsAfterVendor: string[] = [];
    const sanitizedVersions: string[] = [];

    updateSelections({
      vendor: nextVendors,
      model: sanitizedModels,
      version: sanitizedVersions,
      "machine.ip": [],
      "machine.serial": [],
      "machine.port": [],
    });
  };

  const handleModelToggle = (model: string) => {
    // 單選模式：如果點擊的是已選中的型號，則取消選擇；否則只選擇這個型號
    const nextModels = selections.model.includes(model) ? [] : [model];

    const versionsAfterModel = collectVersionOptions(deviceConfig, selections.vendor, nextModels).map(
      (version) => version.name
    );
    // 清空不相關的選擇
    const sanitizedVersions: string[] = [];

    updateSelections({
      vendor: selections.vendor,
      model: nextModels,
      version: sanitizedVersions,
      "machine.ip": [],
      "machine.serial": [],
      "machine.port": [],
    });
  };

  const handleVersionToggle = (version: string) => {
    const nextVersions = selections.version.includes(version)
      ? selections.version.filter((item) => item !== version)
      : [...selections.version, version];

    const devicesAfterVersion = collectDeviceDetailOptions(
      deviceConfig,
      selections.vendor,
      selections.model,
      nextVersions
    );

    updateSelections({
      vendor: selections.vendor,
      model: selections.model,
      version: nextVersions,
      "machine.ip": selections["machine.ip"].filter((ip) => devicesAfterVersion.some((d) => d.ip === ip)),
      "machine.serial": selections["machine.serial"].filter((serial) =>
        devicesAfterVersion.some((d) => d.serial === serial)
      ),
      "machine.port": selections["machine.port"].filter((port) =>
        devicesAfterVersion.some((d) => String(d.port) === port)
      ),
    });
  };

  const renderDeviceOptions = () => {
    return (
      <div className="filter-section__body">
        <div className="option-group">
          <p className="option-group__title">廠商 (Vendor)</p>
          <div className="option-grid">
            {vendorOptions.map((vendor) => {
              const checked = selections.vendor.includes(vendor.vendor);
              return (
                <label key={vendor.vendor} className="option-chip">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => handleVendorToggle(vendor.vendor)}
                  />
                  <span>{vendor.vendor}</span>
                </label>
              );
            })}
          </div>
        </div>

        <div className="option-group">
          <p className="option-group__title">型號 (Model)</p>
          {selections.vendor.length === 0 && (
            <p className="option-hint">請先選擇一個廠商。</p>
          )}
          <div className="option-grid" aria-disabled={selections.vendor.length === 0}>
            {modelOptions.map((model) => (
              <label key={`${model.vendor}-${model.name}`} className="option-chip">
                <input
                  type="checkbox"
                  checked={selections.model.includes(model.name)}
                  onChange={() => handleModelToggle(model.name)}
                  disabled={selections.vendor.length === 0}
                />
                <span>{model.name}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="option-group">
          <p className="option-group__title">版本 (Version)</p>
          {selections.model.length === 0 && (
            <p className="option-hint">請先選擇一個型號。</p>
          )}
          <div className="option-grid" aria-disabled={selections.model.length === 0}>
            {versionOptions.map((version) => (
              <label key={`${version.vendor}-${version.model}-${version.name}`} className="option-chip">
                <input
                  type="checkbox"
                  checked={selections.version.includes(version.name)}
                  onChange={() => handleVersionToggle(version.name)}
                  disabled={selections.model.length === 0}
                />
                <span>{version.name}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="option-group">
          <p className="option-group__title">設備細節</p>
          {selections.version.length === 0 && (
            <p className="option-hint">請先選擇版本後即可指定設備細節。</p>
          )}
          <div className="device-detail-grid" aria-disabled={selections.version.length === 0}>
            <div className="device-detail-column">
              <h4>IP 位址</h4>
              <div className="option-grid">
                {availableIps.map((ip) => (
                  <label key={ip} className="option-chip">
                    <input
                      type="checkbox"
                      checked={selections["machine.ip"].includes(ip)}
                      onChange={() => toggleDeviceValue("machine.ip", ip)}
                      disabled={selections.version.length === 0}
                    />
                    <span>{ip}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="device-detail-column">
              <h4>序號</h4>
              <div className="option-grid">
                {availableSerials.map((serial) => (
                  <label key={serial} className="option-chip">
                    <input
                      type="checkbox"
                      checked={selections["machine.serial"].includes(serial)}
                      onChange={() => toggleDeviceValue("machine.serial", serial)}
                      disabled={selections.version.length === 0}
                    />
                    <span>{serial}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="device-detail-column">
              <h4>Port</h4>
              <div className="option-grid">
                {availablePorts.map((port) => (
                  <label key={port} className="option-chip">
                    <input
                      type="checkbox"
                      checked={selections["machine.port"].includes(port)}
                      onChange={() => toggleDeviceValue("machine.port", port)}
                      disabled={selections.version.length === 0}
                    />
                    <span>{port}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderTextFieldOptions = () => (
    <div className="filter-section__body">
      {TEXT_FIELDS.map(({ key, label, placeholder }) => (
        <label key={key} className="input-row">
          <span>{label}</span>
          <input
            type="text"
            value={filters.fieldValues[key] ?? ""}
            onChange={(event) => updateTextField(key, event.target.value)}
            placeholder={placeholder}
          />
        </label>
      ))}
      
      <div className="option-group">
        <p className="option-group__title">狀態 (Status)</p>
        <div className="option-grid">
          {STATUS_OPTIONS.map((option) => {
            const selectedStatuses = parseSelections(filters.fieldValues.status);
            return (
              <label key={option.value} className="option-chip">
                <input
                  type="checkbox"
                  checked={selectedStatuses.includes(option.value)}
                  onChange={() => toggleStatusValue(option.value)}
                />
                <span>{option.label}</span>
              </label>
            );
          })}
        </div>
      </div>
    </div>
  );

  const renderDateOptions = () => (
    <div className="filter-section__body date-body">
      {(["enqueued_at", "started_at", "completed_at"] as const).map((field) => (
        <div key={field} className="date-row">
          <div className="date-label">
            {field === "enqueued_at" && "排入佇列時間"}
            {field === "started_at" && "開始時間"}
            {field === "completed_at" && "完成時間"}
          </div>
          <div className="date-inputs">
            <input
              type="datetime-local"
              value={filters.dateRanges[field].from ?? ""}
              onChange={(event) => updateDate(field, "from", event.target.value)}
              placeholder="開始時間"
            />
            <span className="delimiter">至</span>
            <input
              type="datetime-local"
              value={filters.dateRanges[field].to ?? ""}
              onChange={(event) => updateDate(field, "to", event.target.value)}
              placeholder="結束時間"
            />
          </div>
          {dateErrors[field] && <p className="error-text">{dateErrors[field]}</p>}
        </div>
      ))}
    </div>
  );

  const renderAdvancedOptions = () => (
    <div className="filter-section__body advanced-body">
      <p>大量文字貼上請使用下方按鈕開啟輸入視窗：</p>
      <div className="advanced-actions">
        <button type="button" onClick={() => setActiveTextModal("result")}>
          編輯 Result Data
        </button>
        <button type="button" onClick={() => setActiveTextModal("raw")}>
          編輯 Switch Config (raw data)
        </button>
      </div>
    </div>
  );

  if (!isOpen) {
    return null;
  }

  return (
    <div className={`filter-menu ${isClosing ? 'closing' : ''}`} role="dialog" aria-modal="true">
      <div className={`filter-menu__backdrop ${isClosing ? 'closing' : ''}`} onClick={onClose} aria-hidden="true" />
      <div className={`filter-menu__container ${isClosing ? 'closing' : ''}`}>
        <header className="filter-menu__header">
          <div>
            <h1>Switch Ticket Explorer</h1>
          </div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="關閉篩選選單">
            ×
          </button>
        </header>

        <div className="filter-menu__content">
          <div className="filter-section filter-section--static">
            <div className="static-section-header">
              <span>欄位搜尋</span>
            </div>
            <div className="section-panel open static">
              {renderTextFieldOptions()}
            </div>
          </div>

          <div className="filter-section">
            <button
              type="button"
              className={`section-toggle ${openSections.includes("device") ? "open" : ""}`}
              onClick={() => toggleSection("device")}
            >
              <span>設備條件</span>
              <span className="section-toggle__icon" aria-hidden="true" />
            </button>
            <div className={`section-panel ${openSections.includes("device") ? "open" : ""}`}>
              {deviceLoading && <p className="option-hint">載入設備資料中...</p>}
              {deviceError && <p className="error-text">{deviceError}</p>}
              {!deviceLoading && !deviceError && renderDeviceOptions()}
            </div>
          </div>

          <div className="filter-section">
            <button
              type="button"
              className={`section-toggle ${openSections.includes("dates") ? "open" : ""}`}
              onClick={() => toggleSection("dates")}
            >
              <span>時間範圍</span>
              <span className="section-toggle__icon" aria-hidden="true" />
            </button>
            <div className={`section-panel ${openSections.includes("dates") ? "open" : ""}`}>
              {renderDateOptions()}
            </div>
          </div>

          <div className="filter-section">
            <button
              type="button"
              className={`section-toggle ${openSections.includes("advanced") ? "open" : ""}`}
              onClick={() => toggleSection("advanced")}
            >
              <span>進階內容</span>
              <span className="section-toggle__icon" aria-hidden="true" />
            </button>
            <div className={`section-panel ${openSections.includes("advanced") ? "open" : ""}`}>
              {renderAdvancedOptions()}
            </div>
          </div>
        </div>

        <footer className="filter-menu__footer">
          <button type="button" className="clear-button" onClick={onClear}>
            清空篩選
          </button>
          <button type="button" className="apply-button" onClick={onSubmit} disabled={submitting}>
            {submitting ? "搜尋中..." : "套用條件"}
          </button>
        </footer>
      </div>

      <TextEntryModal
        open={activeTextModal === "result"}
        title="編輯 Result Data"
        value={filters.resultData}
        onClose={() => setActiveTextModal(null)}
        onSave={(value) => {
          onChange({ ...filters, resultData: value });
          setActiveTextModal(null);
        }}
      />
      <TextEntryModal
        open={activeTextModal === "raw"}
        title="編輯 Switch Config (raw data)"
        value={filters.rawData}
        onClose={() => setActiveTextModal(null)}
        onSave={(value) => {
          onChange({ ...filters, rawData: value });
          setActiveTextModal(null);
        }}
      />
    </div>
  );
}
