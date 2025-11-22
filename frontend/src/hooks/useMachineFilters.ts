import { useMemo, useState } from "react";
import type { Machine, MachineFilters } from "../types";

export function useMachineFilters(machines: Machine[]) {
  const [filters, setFilters] = useState<MachineFilters>({ status: "all" });

  // 1. 建立 Vendor -> Model -> Version 的關聯樹
  const hierarchy = useMemo(() => {
    const tree = new Map<string, Map<string, Set<string>>>();
    
    machines.forEach((m) => {
      if (!tree.has(m.vendor)) tree.set(m.vendor, new Map());
      const models = tree.get(m.vendor)!;
      
      if (!models.has(m.model)) models.set(m.model, new Set());
      models.get(m.model)!.add(m.version);
    });
    return tree;
  }, [machines]);

  // 2. 根據當前選擇，計算下拉選單的選項
  const options = useMemo(() => {
    const vendors = Array.from(hierarchy.keys());
    
    const models = filters.vendor 
      ? Array.from(hierarchy.get(filters.vendor)?.keys() || []) 
      : [];
      
    const versions = (filters.vendor && filters.model)
      ? Array.from(hierarchy.get(filters.vendor)?.get(filters.model) || [])
      : [];

    return { vendors, models, versions };
  }, [hierarchy, filters.vendor, filters.model]);

  // 3. 執行過濾
  const filteredMachines = useMemo(() => {
    return machines.filter((m) => {
      if (filters.vendor && m.vendor !== filters.vendor) return false;
      if (filters.model && m.model !== filters.model) return false;
      if (filters.version && m.version !== filters.version) return false;
      if (filters.status !== "all" && m.status !== filters.status) return false;
      return true;
    });
  }, [machines, filters]);

  // 4. 計算統計數據
  const stats = useMemo(() => ({
    total: filteredMachines.length,
    available: filteredMachines.filter(m => m.status === "available").length
  }), [filteredMachines]);

  // Helper functions to update filters safely
  const setVendor = (vendor: string) => setFilters(prev => ({ ...prev, vendor: vendor || undefined, model: undefined, version: undefined }));
  const setModel = (model: string) => setFilters(prev => ({ ...prev, model: model || undefined, version: undefined }));
  const setVersion = (version: string) => setFilters(prev => ({ ...prev, version: version || undefined }));
  const setStatus = (status: string) => setFilters(prev => ({ ...prev, status: status as MachineFilters["status"] }));
  const reset = () => setFilters({ status: "all" });

  return {
    filters,
    options,
    filteredMachines,
    stats,
    actions: { setVendor, setModel, setVersion, setStatus, reset }
  };
}