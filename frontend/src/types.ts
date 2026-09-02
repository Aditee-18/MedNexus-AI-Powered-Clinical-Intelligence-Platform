export type ViewState = 'login' | 'signup' | 'chat' | 'account' | 'alerts';

export interface Message {
  role: 'user' | 'ai';
  content: string;
  timestamp?: string;
}

export interface Patient {
  patient_id: string;
  name: string;
  age: number;
}

export interface AlertItem {
  alert_id: string;
  patient_id: string;
  patient_name: string;
  age: number;
  severity_level: 'high' | 'medium' | 'low';
  risk_score: number;
  title: string;
  comparison_type: 'delta' | 'baseline';
  ai_summary: string;
  suggested_action: string;
  status: 'active' | 'acknowledged';
  created_at: string;
  acknowledgedAt?: string | null;
}

export interface UserSession {
  user_id: string;
  name: string;
  email: string;
  hospital_id: string;
  specialty: string;
  token: string;
}

export interface ChatSession {
  session_id: string;
  title: string;
  updated_at: string;
}
