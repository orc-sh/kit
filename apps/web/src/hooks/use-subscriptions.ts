import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type { Subscription, UpdateSubscriptionRequest, CancelSubscriptionRequest } from '@/types';

/**
 * Hook to fetch all subscriptions for the current user
 */
export const useSubscriptions = () => {
  return useQuery({
    queryKey: ['subscriptions'],
    queryFn: async () => {
      const response = await api.get<Subscription[]>('/api/subscriptions');
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

/**
 * Hook to update a subscription (change plan)
 */
export const useUpdateSubscription = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      subscriptionId,
      data,
    }: {
      subscriptionId: string;
      data: UpdateSubscriptionRequest;
    }) => {
      const response = await api.put<Subscription>(`/api/subscriptions/${subscriptionId}`, data);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate subscriptions query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });
};

/**
 * Hook to cancel a subscription
 */
export const useCancelSubscription = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      subscriptionId,
      data,
    }: {
      subscriptionId: string;
      data?: CancelSubscriptionRequest;
    }) => {
      const response = await api.post<Subscription>(
        `/api/subscriptions/${subscriptionId}/cancel`,
        data || {}
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalidate subscriptions query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });
};
