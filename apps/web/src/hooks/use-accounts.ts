import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type {
  Account,
  AccountsResponse,
  CreateAccountRequest,
  UpdateAccountRequest,
} from '@/types';

/**
 * Hook to fetch accounts with pagination
 */
export const useAccounts = (page = 1, pageSize = 10) => {
  return useQuery({
    queryKey: ['accounts', page, pageSize],
    queryFn: async () => {
      const response = await api.get<AccountsResponse>('/api/accounts', {
        params: { page, page_size: pageSize },
      });
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

/**
 * Hook to fetch a single account by ID
 */
export const useAccount = (accountId: string) => {
  return useQuery({
    queryKey: ['account', accountId],
    queryFn: async () => {
      const response = await api.get<Account>(`/api/accounts/${accountId}`);
      return response.data;
    },
    enabled: !!accountId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

/**
 * Hook to create a new account
 */
export const useCreateAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateAccountRequest) => {
      const response = await api.post<Account>('/api/accounts', data);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate accounts query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
};

/**
 * Hook to update a account
 */
export const useUpdateAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ accountId, data }: { accountId: string; data: UpdateAccountRequest }) => {
      const response = await api.put<Account>(`/api/accounts/${accountId}`, data);
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate accounts queries
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['account', data.id] });
    },
  });
};

/**
 * Hook to delete a account
 */
export const useDeleteAccount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (accountId: string) => {
      await api.delete(`/api/accounts/${accountId}`);
    },
    onSuccess: () => {
      // Invalidate accounts query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
};
