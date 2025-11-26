import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type {
  Notification,
  NotificationsResponse,
  CreateNotificationRequest,
  UpdateNotificationRequest,
} from '@/types';

/**
 * Hook to fetch notifications with pagination
 */
export const useNotifications = (page = 1, pageSize = 10, projectId?: string) => {
  return useQuery({
    queryKey: ['notifications', page, pageSize, projectId],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (projectId) {
        params.project_id = projectId;
      }
      const response = await api.get<NotificationsResponse>('/api/notifications', {
        params,
      });
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

/**
 * Hook to fetch a single notification by ID
 */
export const useNotification = (notificationId: string) => {
  return useQuery({
    queryKey: ['notification', notificationId],
    queryFn: async () => {
      const response = await api.get<Notification>(`/api/notifications/${notificationId}`);
      return response.data;
    },
    enabled: !!notificationId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

/**
 * Hook to create a new notification
 */
export const useCreateNotification = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateNotificationRequest) => {
      const response = await api.post<Notification>('/api/notifications', data);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate notifications query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
};

/**
 * Hook to update a notification
 */
export const useUpdateNotification = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      notificationId,
      data,
    }: {
      notificationId: string;
      data: UpdateNotificationRequest;
    }) => {
      const response = await api.put<Notification>(`/api/notifications/${notificationId}`, data);
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate notifications queries
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notification', data.id] });
    },
  });
};

/**
 * Hook to delete a notification
 */
export const useDeleteNotification = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (notificationId: string) => {
      await api.delete(`/api/notifications/${notificationId}`);
    },
    onSuccess: () => {
      // Invalidate notifications query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
};
