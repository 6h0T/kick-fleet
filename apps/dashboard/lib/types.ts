export type Worker = {
  id: string;
  name: string;
  status: string;
  cpu_percent: number;
  ram_mb: number;
  ram_limit_mb: number | null;
  novnc_url: string | null;
  last_heartbeat_at: string | null;
  labels: Record<string, string>;
  has_snapshot: boolean;
};

export type Account = {
  id: string;
  username: string;
  platform: string;
  status: string;
  health_score: number;
  last_login_at: string | null;
  assigned_worker_id: string | null;
  notes: string | null;
  created_at: string;
};

export type Task = {
  id: string;
  type: string;
  status: string;
  worker_id: string | null;
  account_id: string | null;
  payload: Record<string, unknown>;
  error: string | null;
  created_at: string;
};

export type Script = {
  id: string;
  name: string;
  platform: string;
  enabled: boolean;
  steps: unknown[];
  trigger: Record<string, unknown> | null;
};
