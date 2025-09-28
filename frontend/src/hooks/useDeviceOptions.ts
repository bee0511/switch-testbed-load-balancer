import { useEffect, useMemo, useState } from "react";
import type {
  DeviceConfigResponse,
  DeviceModelEntry,
  DevicePortEntry,
  DeviceVendorEntry,
  DeviceVersionEntry,
} from "../types";

const API_PATH = "/devices/options";
const DEFAULT_BASE_URL = "http://localhost:8000";

type DeviceModelOption = {
  vendor: string;
  model: string;
};

type DeviceVersionOption = {
  vendor: string;
  model: string;
  version: string;
};

type DeviceDetailOption = {
  vendor: string;
  model: string;
  version: string;
  ip: string;
  port: number;
  serial: string;
};

export interface DeviceOptionSets {
  vendors: string[];
  models: DeviceModelOption[];
  versions: DeviceVersionOption[];
  details: DeviceDetailOption[];
}

function flattenModels(vendor: DeviceVendorEntry): DeviceModelOption[] {
  return (vendor.models ?? []).map((model) => ({
    vendor: vendor.vendor,
    model: model.model,
  }));
}

function flattenVersions(vendor: DeviceVendorEntry): DeviceVersionOption[] {
  const versions: DeviceVersionOption[] = [];
  (vendor.models ?? []).forEach((model: DeviceModelEntry) => {
    (model.versions ?? []).forEach((version: DeviceVersionEntry) => {
      versions.push({
        vendor: vendor.vendor,
        model: model.model,
        version: version.version,
      });
    });
  });
  return versions;
}

function flattenDetails(vendor: DeviceVendorEntry): DeviceDetailOption[] {
  const details: DeviceDetailOption[] = [];
  (vendor.models ?? []).forEach((model: DeviceModelEntry) => {
    (model.versions ?? []).forEach((version: DeviceVersionEntry) => {
      (version.devices ?? []).forEach((device: DevicePortEntry) => {
        details.push({
          vendor: vendor.vendor,
          model: model.model,
          version: version.version,
          ip: device.ip,
          port: device.port,
          serial: device.serial_number,
        });
      });
    });
  });
  return details;
}

function buildOptionSets(config: DeviceConfigResponse | null): DeviceOptionSets {
  if (!config) {
    return { vendors: [], models: [], versions: [], details: [] };
  }

  const vendorEntries = Array.isArray(config.vendors) ? config.vendors : [];

  const vendors = Array.from(new Set(vendorEntries.map((item) => item.vendor))).sort();
  const models: DeviceModelOption[] = [];
  const versions: DeviceVersionOption[] = [];
  const details: DeviceDetailOption[] = [];

  vendorEntries.forEach((vendor) => {
    models.push(...flattenModels(vendor));
    versions.push(...flattenVersions(vendor));
    details.push(...flattenDetails(vendor));
  });

  return {
    vendors,
    models,
    versions,
    details,
  };
}

export function useDeviceOptions() {
  const [config, setConfig] = useState<DeviceConfigResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE_URL;

    fetch(`${baseUrl}${API_PATH}`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Failed to fetch device options: ${response.status}`);
        }
        return (await response.json()) as DeviceConfigResponse;
      })
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setConfig(data);
      })
      .catch((err: unknown) => {
        console.error(err);
        if (isMounted) {
          setError("無法載入裝置選項");
          setConfig(null);
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const sets = useMemo(() => buildOptionSets(config), [config]);

  return { config, sets, loading, error };
}
