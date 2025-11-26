export type NotificationType = 'email' | 'slack' | 'discord' | 'webhook';

export interface Notification {
  id: string;
  project_id: string;
  user_id: string;
  type: NotificationType;
  name: string;
  enabled: boolean;
  config: {
    email?: string;
    webhook_url?: string;
    channel?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface PaginationMetadata {
  current_page: number;
  total_pages: number;
  total_entries: number;
  page_size: number;
  next_page: number | null;
  previous_page: number | null;
  has_next: boolean;
  has_previous: boolean;
}

export interface NotificationsResponse {
  data: Notification[];
  pagination: PaginationMetadata;
}

export interface CreateNotificationRequest {
  type: NotificationType;
  name: string;
  enabled: boolean;
  config: {
    email?: string;
    webhook_url?: string;
    channel?: string;
  };
}

export interface UpdateNotificationRequest {
  name?: string;
  enabled?: boolean;
  config?: {
    email?: string;
    webhook_url?: string;
    channel?: string;
  };
}
