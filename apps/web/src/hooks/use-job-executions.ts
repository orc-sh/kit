/**
 * Custom hook for job execution API operations
 */

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import type { PaginatedJobExecutionsResponse } from '@/types/webhook.types';

/**
 * Fetch job executions for a webhook with pagination
 */
export const useJobExecutions = (
  webhookId: string | undefined,
  limit: number = 20,
  offset: number | undefined = 0
) => {
  return useQuery<PaginatedJobExecutionsResponse, Error>({
    queryKey: ['job-executions', webhookId, limit, offset],
    queryFn: async () => {
      if (!webhookId) {
        throw new Error('Webhook ID is required');
      }
      const response = await api.get(`/api/schedules/${webhookId}/executions`, {
        params: { limit, offset: offset ?? 0 },
      });
      return response.data;
    },
    enabled: !!webhookId && offset !== undefined,
  });
};
