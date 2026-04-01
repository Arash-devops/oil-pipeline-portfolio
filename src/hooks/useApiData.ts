'use client';

import { useState, useEffect } from 'react';
import type { ApiEnvelope } from '@/data/sample-api-data';

const API_BASE = 'http://localhost:8000/api/v1';
const TIMEOUT_MS = 3000;

type UseApiDataResult<T> = {
  data: T[] | null;
  loading: boolean;
  error: string | null;
  isLive: boolean;
};

export function useApiData<T>(
  path: string,
  fallback: ApiEnvelope<T>,
): UseApiDataResult<T> {
  const [data, setData] = useState<T[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

    async function fetchData() {
      try {
        const res = await fetch(`${API_BASE}${path}`, {
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json: ApiEnvelope<T> = await res.json();
        setData(json.data);
        setIsLive(true);
      } catch {
        setData(fallback.data);
        setIsLive(false);
        setError(null);
      } finally {
        clearTimeout(timer);
        setLoading(false);
      }
    }

    fetchData();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [path]); // eslint-disable-line react-hooks/exhaustive-deps

  return { data, loading, error, isLive };
}
