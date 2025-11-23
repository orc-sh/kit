/**
 * Custom hook for webhook API operations
 */

import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import type { CreateCrownWebhookRequest, CrownWebhookResponse } from '@/types/webhook.types';

/**
 * Create a new webhook with job
 */
export const useCreateWebhook = () => {
  return useMutation<CrownWebhookResponse, Error, CreateCrownWebhookRequest>({
    mutationFn: async (data: CreateCrownWebhookRequest) => {
      const response = await api.post('/webhooks', data);
      return response.data;
    },
    onSuccess: (data) => {
      toast({
        title: 'Webhook Created Successfully! 🎉',
        description: `Job "${data.job.name}" and webhook have been created and scheduled.`,
      });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || error.message || 'Failed to create webhook';
      toast({
        title: 'Failed to Create Webhook',
        description: message,
        variant: 'destructive',
      });
    },
  });
};
