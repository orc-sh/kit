import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import { useAuthStore } from '@/stores/auth-store';

/**
 * Hook to delete the current user's account
 */
export const useDeleteCurrentAccount = () => {
  const navigate = useNavigate();
  const clearAuth = useAuthStore((state) => state.clearAuth);

  return useMutation({
    mutationFn: async () => {
      await api.delete('/api/user/account');
    },
    onSuccess: () => {
      // Clear authentication state
      clearAuth();
      // Redirect to login page
      navigate('/login');
    },
  });
};
