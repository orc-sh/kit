export interface Project {
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

export interface ProjectsResponse {
  data: Project[];
  pagination: PaginationMetadata;
}

export interface CreateProjectRequest {
  name: string;
}

export interface UpdateProjectRequest {
  name: string;
}
