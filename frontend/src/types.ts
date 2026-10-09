export interface User { id: number; name: string; paternal_surname?: string | null; maternal_surname?: string | null; phone?: string | null; email: string; roles: string[]; permissions: string[] }
export interface AuthResponse { access_token: string; refresh_token: string; token_type: string; expires_at: string; user: User }
