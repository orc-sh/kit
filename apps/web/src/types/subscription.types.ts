/**
 * Subscription types for plan management
 */

export interface Subscription {
  id: string;
  account_id: string;
  chargebee_subscription_id: string;
  chargebee_customer_id: string;
  plan_id: string;
  status: string;
  current_term_start: string | null;
  current_term_end: string | null;
  trial_end: string | null;
  cancelled_at: string | null;
  cancel_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface UpdateSubscriptionRequest {
  plan_id: string;
}

export interface CancelSubscriptionRequest {
  cancel_reason?: string;
}

export type PlanId = 'free-plan' | 'pro-plan';

export const PLAN_IDS = {
  FREE: 'free-plan' as const,
  PRO: 'pro-plan' as const,
} as const;
