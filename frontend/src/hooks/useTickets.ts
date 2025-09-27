import { useEffect, useMemo, useState } from "react";
import type { FilterState, Ticket } from "../types";
import { sampleTickets } from "../sample-data";

const API_PATH = "/tickets/search";
const DEFAULT_BASE_URL = "http://localhost:8000";

async function requestTickets(filters: FilterState): Promise<Ticket[]> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE_URL;

  try {
    const response = await fetch(`${baseUrl}${API_PATH}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(filters)
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
    console.warn("Falling back to sample tickets:", error);
    return filterTickets(sampleTickets, filters);
  }
}

function includesIgnoreCase(value: string | null | undefined, search: string): boolean {
  if (!search.trim()) {
    return true;
  }
  return (value ?? "").toLowerCase().includes(search.trim().toLowerCase());
}

function fieldValue(ticket: Ticket, field: string): string {
  switch (field) {
    case "id":
      return ticket.id;
    case "status":
      return ticket.status;
    case "vendor":
      return ticket.vendor;
    case "model":
      return ticket.model;
    case "version":
      return ticket.version;
    case "machine.serial":
      return ticket.machine?.serial ?? "";
    case "machine.ip":
      return ticket.machine?.ip ?? "";
    case "machine.port":
      return ticket.machine ? String(ticket.machine.port) : "";
    default:
      return "";
  }
}

function normalizeDateString(value: string | null): string | null {
  if (!value) {
    return null;
  }
  if (value.includes("T")) {
    return value;
  }
  return value.replace(" ", "T");
}

function isWithinRange(dateValue: string | null, from?: string, to?: string): boolean {
  if (!from && !to) {
    return true;
  }

  const normalized = normalizeDateString(dateValue);
  const target = normalized ? new Date(normalized).getTime() : null;
  const fromTime = from ? new Date(from).getTime() : null;
  const toTime = to ? new Date(to).getTime() : null;

  if (!target) {
    return false;
  }

  if (fromTime && target < fromTime) {
    return false;
  }
  if (toTime && target > toTime) {
    return false;
  }
  return true;
}

export function filterTickets(tickets: Ticket[], filters: FilterState): Ticket[] {
  const { activeFields, fieldValues, dateRanges, resultData, rawData } = filters;

  return tickets.filter((ticket) => {
    const fieldMatches = activeFields.every((field) => {
      const expected = fieldValues[field]?.trim();
      if (!expected) {
        return true;
      }
      return includesIgnoreCase(fieldValue(ticket, field), expected);
    });

    if (!fieldMatches) {
      return false;
    }

    const dateMatches = (Object.entries(dateRanges) as [keyof typeof dateRanges, { from?: string; to?: string }][]).every(
      ([field, range]) => {
        if (!range.from && !range.to) {
          return true;
        }
        return isWithinRange((ticket as Record<string, string | null>)[field] ?? null, range.from, range.to);
      }
    );

    if (!dateMatches) {
      return false;
    }

    if (!includesIgnoreCase(ticket.result_data ?? null, resultData)) {
      return false;
    }

    if (!includesIgnoreCase(ticket.raw_data ?? null, rawData)) {
      return false;
    }

    return true;
  });
}

export function useTickets(filters: FilterState) {
  const [tickets, setTickets] = useState<Ticket[]>(sampleTickets);
  const [loading, setLoading] = useState<boolean>(true);
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
        setError("無法從伺服器取得資料，已顯示範例資料。");
        setTickets(filterTickets(sampleTickets, filters));
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

  const filteredTickets = useMemo(() => filterTickets(tickets, filters), [tickets, filters]);

  return { tickets: filteredTickets, loading, error };
}
