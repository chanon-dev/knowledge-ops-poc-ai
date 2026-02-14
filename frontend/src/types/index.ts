// ==================== User ====================
export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  tenant_id: string;
  tenant_name: string;
  departments: string[];
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type UserRole = "super_admin" | "tenant_admin" | "department_admin" | "user";

// ==================== Tenant ====================
export interface Tenant {
  id: string;
  name: string;
  slug: string;
  logo_url?: string;
  is_active: boolean;
  settings: TenantSettings;
  created_at: string;
  updated_at: string;
}

export interface TenantSettings {
  max_users: number;
  max_departments: number;
  features: string[];
  ai_model?: string;
  custom_branding?: {
    primary_color?: string;
    logo_url?: string;
  };
}

// ==================== Department ====================
export interface Department {
  id: string;
  name: string;
  slug: string;
  description?: string;
  icon?: string;
  tenant_id: string;
  is_active: boolean;
  knowledge_base_count: number;
  created_at: string;
  updated_at: string;
}

// ==================== Conversation ====================
export interface Conversation {
  id: string;
  title: string;
  user_id: string;
  department_id: string;
  department_name: string;
  status: ConversationStatus;
  messages: Message[];
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export type ConversationStatus = "active" | "archived" | "pending_approval";

// ==================== Message ====================
export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  sources?: MessageSource[];
  confidence?: number;
  model_used?: string;
  latency_ms?: number;
  status?: string;
  approval_id?: string;
  approval_required?: boolean;
  approval_status?: ApprovalStatus;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export type MessageRole = "user" | "assistant" | "system";

export interface MessageSource {
  document_id: string;
  document_title: string;
  title: string;
  chunk_text: string;
  chunk: string;
  relevance_score: number;
  score: number;
}

// ==================== Knowledge Document ====================
export interface KnowledgeDoc {
  id: string;
  title: string;
  description?: string;
  department_id: string;
  department_name: string;
  file_type: string;
  source_type?: string;
  file_url: string;
  file_size: number;
  status: KnowledgeDocStatus;
  chunk_count: number;
  uploaded_by: string;
  uploaded_by_name: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export type KnowledgeDocStatus = "processing" | "ready" | "error" | "archived";

// ==================== Approval ====================
export interface Approval {
  id: string;
  message_id: string;
  conversation_id: string;
  conversation_title: string;
  department_id: string;
  department_name: string;
  requested_by: string;
  requested_by_name: string;
  reviewed_by?: string;
  reviewed_by_name?: string;
  status: ApprovalStatus;
  original_content: string;
  original_answer?: string;
  priority?: string;
  approved_content?: string;
  rejection_reason?: string;
  created_at: string;
  updated_at: string;
}

export type ApprovalStatus = "pending" | "approved" | "rejected" | "auto_approved";

// ==================== API Response Types ====================
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ==================== Analytics ====================
export interface AnalyticsSummary {
  total_conversations: number;
  total_messages: number;
  total_documents: number;
  pending_approvals: number;
  avg_response_time_ms: number;
  user_satisfaction_score: number;
  conversations_by_department: {
    department: string;
    count: number;
  }[];
  messages_over_time: {
    date: string;
    count: number;
  }[];
}
