export interface User { id: number; name: string; paternal_surname?: string | null; maternal_surname?: string | null; phone?: string | null; email: string; roles: string[]; permissions: string[] }
export interface AuthResponse { access_token: string; refresh_token: string; token_type: string; expires_at: string; user: User }
export interface Permission { id: number; code: string; description: string }
export interface Role { id: number; name: string; description: string; permissions: Permission[]; user_count: number; is_protected: boolean; is_active?: boolean; updated_at?: string }
export interface RoleUser { id: number; name: string; email: string; is_active: boolean }
export interface RoleUsers { role: Role; assigned: RoleUser[]; available: RoleUser[] }

export interface Workshop {
  id?: number
  name: string
  rfc: string
  contact_email: string
  street_and_number: string
  neighborhood: string
  postal_code: string
  state: string
  municipality: string
  photo_url?: string | null
  photo_name?: string | null
  is_active?: boolean
  created_at?: string
}

export interface Customer {
  id: number
  workshop_id: number
  workshop_name: string
  first_name: string
  paternal_surname: string
  maternal_surname?: string | null
  street_and_number: string
  neighborhood?: string | null
  postal_code?: string | null
  municipality: string
  state: string
  primary_email: string
  secondary_email?: string | null
  primary_phone: string
  secondary_phone?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CustomerPayload {
  first_name: string
  paternal_surname: string
  maternal_surname?: string | null
  street_and_number: string
  neighborhood: string
  postal_code: string
  municipality: string
  state: string
  primary_email: string
  secondary_email?: string | null
  primary_phone: string
  secondary_phone?: string | null
}

export interface VehiclePayload {
  vin: string
  make: string
  model: string
  year: number
  plate?: string | null
}

export interface VehicleUpdatePayload {
  make: string
  model: string
  year: number
  plate: string
  version?: string | null
  color?: string | null
  mileage?: number | null
}

export interface VehiclePhoto { id: number; filename: string; url: string }
export interface Vehicle {
  id: number; workshop_id: number; workshop_name: string; customer_id: number; customer_name: string
  vin: string; plate?: string | null; make: string; model: string; year: number; version?: string | null
  color?: string | null; mileage?: number | null; is_active: boolean; created_at: string; updated_at?: string; photo_count: number; photos?: VehiclePhoto[]
  owner?: { name: string; primary_email: string; secondary_email?: string | null; primary_phone: string; secondary_phone?: string | null; address: string }
}
