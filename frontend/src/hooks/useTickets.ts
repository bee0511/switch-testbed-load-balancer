import { useEffect, useState } from "react";
import type { FilterState, Ticket } from "../types";

const API_PATH = "/tickets/search";
const DEFAULT_BASE_URL = "http://localhost:8000";

function sanitizeFieldValues(filters: FilterState): Partial<Record<string, string>> {
  const values: Partial<Record<string, string>> = {};

  filters.activeFields.forEach((field) => {
    const rawValue = filters.fieldValues[field];
    const trimmed = rawValue?.trim();
    if (trimmed) {
      values[field] = trimmed;
    }
  });

  return values;
}

function sanitizeDateRanges(filters: FilterState): Record<string, { from?: string; to?: string }> {
  const ranges: Record<string, { from?: string; to?: string }> = {};

  (Object.entries(filters.dateRanges) as [string, { from?: string; to?: string }][]).forEach(
    ([key, range]) => {
      const from = range.from?.trim();
      const to = range.to?.trim();

      if (from || to) {
        ranges[key] = {
          ...(from ? { from } : {}),
          ...(to ? { to } : {}),
        };
      }
    }
  );

  return ranges;
}

function buildPayload(filters: FilterState) {
  return {
    activeFields: filters.activeFields,
    fieldValues: sanitizeFieldValues(filters),
    dateRanges: sanitizeDateRanges(filters),
    resultData: filters.resultData.trim(),
    rawData: filters.rawData.trim(),
  };
}

async function requestTickets(filters: FilterState): Promise<Ticket[]> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE_URL;

  try {
    const response = await fetch(`${baseUrl}${API_PATH}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload(filters))
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = (await response.json()) as { tickets?: Ticket[] } | Ticket[];
    if (Array.isArray(data)) {
      return data;
    }
    return data.tickets ?? [];
  } catch (error) {
    throw error;
  }
}

export function useTickets(filters: FilterState) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    requestTickets(filters)
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setTickets(data);
      })
      .catch((err: unknown) => {
        if (!isMounted) {
          return;
        }
        console.error(err);
        setError("無法從伺服器取得資料，請稍後再試。");
        setTickets([]);
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [filters]);

  return { tickets, loading, error };
}
