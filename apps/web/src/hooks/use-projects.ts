import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type {
  Project,
  ProjectsResponse,
  CreateProjectRequest,
  UpdateProjectRequest,
} from '@/types';

/**
 * Hook to fetch projects with pagination
 */
export const useProjects = (page = 1, pageSize = 10) => {
  return useQuery({
    queryKey: ['projects', page, pageSize],
    queryFn: async () => {
      const response = await api.get<ProjectsResponse>('/api/projects', {
        params: { page, page_size: pageSize },
      });
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

/**
 * Hook to fetch a single project by ID
 */
export const useProject = (projectId: string) => {
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      const response = await api.get<Project>(`/api/projects/${projectId}`);
      return response.data;
    },
    enabled: !!projectId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

/**
 * Hook to create a new project
 */
export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateProjectRequest) => {
      const response = await api.post<Project>('/api/projects', data);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate projects query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
};

/**
 * Hook to update a project
 */
export const useUpdateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: UpdateProjectRequest }) => {
      const response = await api.put<Project>(`/api/projects/${projectId}`, data);
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate projects queries
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['project', data.id] });
    },
  });
};

/**
 * Hook to delete a project
 */
export const useDeleteProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (projectId: string) => {
      await api.delete(`/api/projects/${projectId}`);
    },
    onSuccess: () => {
      // Invalidate projects query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
};
