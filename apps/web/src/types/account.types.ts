export interface Account {
  id: string;
  name: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface PaginationMetadata {
  current_page: number;
  total_pages: number;
  total_entries: number;
  next_page: number | null;
  previous_page: number | null;
  has_next: boolean;
  has_previous: boolean;
}

export interface AccountsResponse {
  data: Account[];
  pagination: PaginationMetadata;
}

export interface CreateAccountRequest {
  name: string;
}

export interface UpdateAccountRequest {
  name: string;
}
