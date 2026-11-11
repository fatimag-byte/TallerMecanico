import api from './api'

export type LocationOption = { id: string; name: string }
export type SettlementOption = LocationOption & { postal_code: string; type: string }
export type PostalLookup = { state: LocationOption; municipality: LocationOption; settlements: SettlementOption[] }

export const getStates = async () => (await api.get<LocationOption[]>('/ubicaciones/estados')).data
export const getMunicipalities = async (stateId: string) => (await api.get<LocationOption[]>('/ubicaciones/municipios', { params: { estado_id: stateId } })).data
export const getSettlements = async (stateId: string, municipalityId: string) => (await api.get<SettlementOption[]>('/ubicaciones/localidades', { params: { estado_id: stateId, municipio_id: municipalityId } })).data
export const lookupPostalCode = async (postalCode: string) => (await api.get<PostalLookup>(`/ubicaciones/codigo-postal/${postalCode}`)).data
