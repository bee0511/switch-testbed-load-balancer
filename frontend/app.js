const { useMemo, useState } = React;
const { createRoot } = ReactDOM;

const tickets = [
  {
    id: '6b85e2c5-a33a-44ce-b6ea-9ca0d2aa9f4c',
    status: 'completed',
    vendor: 'cisco',
    model: 'c8k',
    version: '1.0',
    enqueued_at: '2025-09-27 19:07:45.735329',
    started_at: '2025-09-27 19:07:45.736822',
    completed_at: '2025-09-27 19:07:51.748649',
    machine: { serial: 'c8kSerial2', ip: '192.168.1.2', port: 6002 },
    completed: true,
    message: 'Ticket completed successfully',
    result_data: 'Processed cisco - c8k',
    raw_data: 'hostname core-switch\ninterface Gig0/0\n switchport access vlan 10\n spanning-tree portfast',
  },
  {
    id: '1ec5ef1b-8287-406f-9810-a7a4360e71ef',
    status: 'failed',
    vendor: 'juniper',
    model: 'qfx',
    version: '4.2',
    enqueued_at: '2025-09-21 08:12:01.101010',
    started_at: '2025-09-21 08:12:05.221010',
    completed_at: '2025-09-21 08:12:45.991010',
    machine: { serial: 'jnpr-qfx-008', ip: '192.168.10.45', port: 7001 },
    completed: false,
    message: 'Rollback applied: invalid VLAN configuration',
    result_data: 'VLAN validation failed on qfx',
    raw_data: 'set vlans vlan-100 description "Edge VLAN"\nset vlans vlan-100 vlan-id 100\nset interfaces ge-0/0/1 unit 0 family ethernet-switching vlan members 100',
  },
  {
    id: 'b7f4dc28-6d55-4ac0-8da0-b5e3461afcb9',
    status: 'completed',
    vendor: 'arista',
    model: '7050X',
    version: '2.6',
    enqueued_at: '2025-08-11 13:02:22.000145',
    started_at: '2025-08-11 13:02:24.000145',
    completed_at: '2025-08-11 13:05:30.000145',
    machine: { serial: 'ar7050x-21', ip: '10.10.10.21', port: 7002 },
    completed: true,
    message: 'Pushed QoS template to all uplinks',
    result_data: 'QoS profile applied to arista 7050X',
    raw_data: 'interface Ethernet1\n service-policy input QOS-IN\n service-policy output QOS-OUT',
  },
  {
    id: '9d27c1b5-53dc-4a5c-9312-b4222a2769f8',
    status: 'running',
    vendor: 'cisco',
    model: 'n9k',
    version: '3.1',
    enqueued_at: '2025-09-29 02:45:00.000010',
    started_at: '2025-09-29 02:45:05.000010',
    completed_at: '',
    machine: { serial: 'n9k-core-44', ip: '172.16.0.12', port: 6005 },
    completed: false,
    message: 'Ticket is currently executing',
    result_data: 'Executing maintenance workflow',
    raw_data: 'feature interface-vlan\ninterface Vlan200\n ip address 172.16.200.1/24',
  },
  {
    id: '3a12bc48-b7c2-4f92-9f6e-17e140987654',
    status: 'completed',
    vendor: 'hpe',
    model: 'aruba-8400',
    version: '10.3',
    enqueued_at: '2025-09-18 11:55:45.444321',
    started_at: '2025-09-18 11:55:47.444321',
    completed_at: '2025-09-18 11:57:12.444321',
    machine: { serial: 'aruba-8400-07', ip: '10.0.50.7', port: 7011 },
    completed: true,
    message: 'Updated wireless controller routes',
    result_data: 'Aruba routing policy synced',
    raw_data: 'router ospf 1\n network 10.0.50.0 0.0.0.255 area 0\n passive-interface default\n no passive-interface vlan 10',
  },
];

const nestedValue = (object, path) =>
  path.split('.').reduce((acc, key) => (acc && acc[key] !== undefined ? acc[key] : undefined), object);

const toDate = (value) => (value ? new Date(value.replace(' ', 'T')) : null);

const uniqueValues = (key) => {
  const seen = new Set();
  tickets.forEach((ticket) => {
    const value = nestedValue(ticket, key);
    if (value !== undefined && value !== null && value !== '') {
      seen.add(String(value));
    }
  });
  return Array.from(seen).sort((a, b) => a.localeCompare(b, 'zh-Hant'));
};

const fieldConfigs = [
  { key: 'id', label: 'Ticket ID', type: 'text' },
  { key: 'status', label: '狀態', type: 'select', options: uniqueValues('status') },
  { key: 'vendor', label: '廠商', type: 'select', options: uniqueValues('vendor') },
  { key: 'model', label: '型號', type: 'text' },
  { key: 'version', label: '版本', type: 'text' },
  { key: 'machine.serial', label: '設備序號', type: 'text' },
  { key: 'machine.ip', label: '設備 IP', type: 'text' },
  { key: 'machine.port', label: '設備連接埠', type: 'number' },
];

const dateFields = [
  { key: 'enqueued_at', label: '加入佇列時間' },
  { key: 'started_at', label: '開始時間' },
  { key: 'completed_at', label: '完成時間' },
];

const TicketFilters = ({
  activeFields,
  onToggleField,
  criteria,
  onCriteriaChange,
  dateRanges,
  onDateChange,
  resultQuery,
  rawQuery,
  onResultQueryChange,
  onRawQueryChange,
  onReset,
}) => (
  <div className="filter-card">
    <div className="app-header">
      <h1>Ticket 智慧篩選</h1>
      <p>選取條件、輸入內容，即可即時收斂符合條件的票單。</p>
    </div>

    <section>
      <h2 className="section-title" style={{ fontSize: '1rem', marginBottom: '14px' }}>
        選擇篩選欄位
      </h2>
      <div className="field-selector">
        {fieldConfigs.map((field) => {
          const isActive = activeFields.includes(field.key);
          return (
            <label key={field.key} className={`field-toggle${isActive ? ' active' : ''}`}>
              <input
                type="checkbox"
                checked={isActive}
                onChange={() => onToggleField(field.key)}
              />
              <span>{field.label}</span>
            </label>
          );
        })}
      </div>
    </section>

    <section className="field-inputs">
      {activeFields.map((key) => {
        const field = fieldConfigs.find((item) => item.key === key);
        if (!field) return null;
        const value = criteria[key] ?? '';
        return (
          <div key={key} className="input-group">
            <label htmlFor={`input-${key}`}>{field.label}</label>
            {field.type === 'select' ? (
              <select
                id={`input-${key}`}
                value={value}
                onChange={(event) => onCriteriaChange(key, event.target.value)}
              >
                <option value="">全部</option>
                {field.options.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            ) : (
              <input
                id={`input-${key}`}
                type={field.type}
                value={value}
                onChange={(event) => onCriteriaChange(key, event.target.value)}
                placeholder={`輸入${field.label}`}
              />
            )}
          </div>
        );
      })}

      {dateFields.map(({ key, label }) => (
        <div key={key} className="input-group">
          <label>{label}</label>
          <div style={{ display: 'flex', gap: '12px' }}>
            <input
              type="datetime-local"
              value={dateRanges[key]?.from ?? ''}
              onChange={(event) => onDateChange(key, 'from', event.target.value)}
            />
            <input
              type="datetime-local"
              value={dateRanges[key]?.to ?? ''}
              onChange={(event) => onDateChange(key, 'to', event.target.value)}
            />
          </div>
        </div>
      ))}

      <div className="input-group" style={{ gridColumn: '1 / -1' }}>
        <label htmlFor="result-query">Result Data</label>
        <textarea
          id="result-query"
          rows={3}
          placeholder="輸入結果文字片段"
          value={resultQuery}
          onChange={(event) => onResultQueryChange(event.target.value)}
        />
      </div>

      <div className="input-group" style={{ gridColumn: '1 / -1' }}>
        <label htmlFor="raw-query">Switch Config (Raw Data)</label>
        <textarea
          id="raw-query"
          rows={3}
          placeholder="輸入設定文字片段"
          value={rawQuery}
          onChange={(event) => onRawQueryChange(event.target.value)}
        />
      </div>
    </section>

    <div className="action-row">
      <button className="button secondary" type="button" onClick={onReset}>
        清除條件
      </button>
    </div>
  </div>
);

const TicketCard = ({ ticket, onSelect }) => (
  <article className="ticket-card" onClick={() => onSelect(ticket)}>
    <h2>{ticket.vendor.toUpperCase()} · {ticket.model}</h2>
    <div className="ticket-meta">
      <span>ID：{ticket.id}</span>
      <span>狀態：{ticket.status}</span>
      <span>版本：{ticket.version}</span>
      <span>加入佇列：{ticket.enqueued_at || '—'}</span>
      <span>開始時間：{ticket.started_at || '—'}</span>
      <span>完成時間：{ticket.completed_at || '—'}</span>
      <span>設備序號：{ticket.machine.serial}</span>
      <span>設備位址：{ticket.machine.ip}:{ticket.machine.port}</span>
    </div>
  </article>
);

const TicketModal = ({ ticket, onClose }) => {
  const [activeTab, setActiveTab] = useState('raw');

  if (!ticket) return null;

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="ticket-modal-title">
      <div className="modal">
        <div className="modal-header">
          <h3 id="ticket-modal-title">{ticket.vendor.toUpperCase()} · {ticket.model}</h3>
          <button className="modal-close" onClick={onClose} aria-label="關閉">
            ×
          </button>
        </div>
        <div className="modal-tabs">
          <button
            className={`tab-button${activeTab === 'raw' ? ' active' : ''}`}
            onClick={() => setActiveTab('raw')}
            type="button"
          >
            Switch Config
          </button>
          <button
            className={`tab-button${activeTab === 'result' ? ' active' : ''}`}
            onClick={() => setActiveTab('result')}
            type="button"
          >
            Result Data
          </button>
        </div>
        <div className="modal-content">
          {activeTab === 'raw' ? ticket.raw_data : ticket.result_data}
        </div>
      </div>
    </div>
  );
};

const App = () => {
  const [activeFields, setActiveFields] = useState(['status', 'vendor']);
  const [criteria, setCriteria] = useState({});
  const [dateRanges, setDateRanges] = useState({
    enqueued_at: { from: '', to: '' },
    started_at: { from: '', to: '' },
    completed_at: { from: '', to: '' },
  });
  const [resultQuery, setResultQuery] = useState('');
  const [rawQuery, setRawQuery] = useState('');
  const [selectedTicket, setSelectedTicket] = useState(null);

  const toggleField = (key) => {
    setActiveFields((prev) =>
      prev.includes(key) ? prev.filter((item) => item !== key) : [...prev, key]
    );
  };

  const handleCriteriaChange = (key, value) => {
    setCriteria((prev) => ({ ...prev, [key]: value }));
  };

  const handleDateChange = (key, bound, value) => {
    setDateRanges((prev) => ({
      ...prev,
      [key]: { ...prev[key], [bound]: value },
    }));
  };

  const resetFilters = () => {
    setActiveFields([]);
    setCriteria({});
    setDateRanges({
      enqueued_at: { from: '', to: '' },
      started_at: { from: '', to: '' },
      completed_at: { from: '', to: '' },
    });
    setResultQuery('');
    setRawQuery('');
  };

  const filteredTickets = useMemo(() => {
    return tickets.filter((ticket) => {
      for (const key of activeFields) {
        const query = (criteria[key] ?? '').trim();
        if (!query) continue;
        const value = nestedValue(ticket, key);
        if (value === undefined || value === null) {
          return false;
        }
        if (typeof value === 'number') {
          if (Number(query) !== value) {
            return false;
          }
        } else {
          if (!String(value).toLowerCase().includes(query.toLowerCase())) {
            return false;
          }
        }
      }

      for (const { key } of dateFields) {
        const range = dateRanges[key];
        if (!range) continue;
        const { from, to } = range;
        if (!from && !to) continue;
        const value = nestedValue(ticket, key);
        const dateValue = toDate(value);
        if (!dateValue) return false;
        if (from) {
          const fromDate = new Date(from);
          if (dateValue < fromDate) return false;
        }
        if (to) {
          const toDateValue = new Date(to);
          if (dateValue > toDateValue) return false;
        }
      }

      if (resultQuery.trim()) {
        if (!ticket.result_data || !ticket.result_data.toLowerCase().includes(resultQuery.trim().toLowerCase())) {
          return false;
        }
      }

      if (rawQuery.trim()) {
        if (!ticket.raw_data || !ticket.raw_data.toLowerCase().includes(rawQuery.trim().toLowerCase())) {
          return false;
        }
      }

      return true;
    });
  }, [activeFields, criteria, dateRanges, resultQuery, rawQuery]);

  return (
    <div>
      <TicketFilters
        activeFields={activeFields}
        onToggleField={toggleField}
        criteria={criteria}
        onCriteriaChange={handleCriteriaChange}
        dateRanges={dateRanges}
        onDateChange={handleDateChange}
        resultQuery={resultQuery}
        rawQuery={rawQuery}
        onResultQueryChange={setResultQuery}
        onRawQueryChange={setRawQuery}
        onReset={resetFilters}
      />

      {filteredTickets.length > 0 ? (
        <div className="ticket-grid">
          {filteredTickets.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} onSelect={setSelectedTicket} />
          ))}
        </div>
      ) : (
        <div className="empty-state">沒有符合條件的票單，請調整篩選條件。</div>
      )}

      {selectedTicket && (
        <TicketModal ticket={selectedTicket} onClose={() => setSelectedTicket(null)} />
      )}
    </div>
  );
};

const root = createRoot(document.getElementById('root'));
root.render(<App />);
