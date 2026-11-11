import api from './api'
import type { Workshop } from '../types'

export const MEXICAN_STATES: Record<string, string[]> = {
  'Aguascalientes': ['Aguascalientes', 'Asientos', 'Calvillo', 'Jesús María', 'Rincón de Romos'],
  'Baja California': ['Ensenada', 'Mexicali', 'Playas de Rosarito', 'Tecate', 'Tijuana', 'San Quintín'],
  'Baja California Sur': ['Comondú', 'La Paz', 'Loreto', 'Los Cabos', 'Mulegé'],
  'Campeche': ['Campeche', 'Carmen', 'Champotón', 'Escárcega', 'Hecelchakán'],
  'Chiapas': ['Chiapa de Corzo', 'Comitán', 'Ocosingo', 'San Cristóbal de las Casas', 'Tapachula', 'Tuxtla Gutiérrez'],
  'Chihuahua': ['Chihuahua', 'Cuauhtémoc', 'Delicias', 'Hidalgo del Parral', 'Juárez', 'Nuevo Casas Grandes'],
  'Ciudad de México': [
    'Álvaro Obregón', 'Azcapotzalco', 'Benito Juárez', 'Coyoacán', 'Cuajimalpa', 'Cuauhtémoc',
    'Gustavo A. Madero', 'Iztacalco', 'Iztapalapa', 'Magdalena Contreras', 'Miguel Hidalgo',
    'Milpa Alta', 'Tláhuac', 'Tlalpan', 'Venustiano Carranza', 'Xochimilco'
  ],
  'Coahuila': ['Acuña', 'Monclova', 'Piedras Negras', 'Ramos Arizpe', 'Saltillo', 'Torreón'],
  'Colima': ['Armería', 'Colima', 'Manzanillo', 'Tecomán', 'Villa de Álvarez'],
  'Durango': ['Durango', 'Gómez Palacio', 'Lerdo', 'Santiago Papasquiaro'],
  'Estado de México': [
    'Atizapán de Zaragoza', 'Chalco', 'Chimalhuacán', 'Coacalco', 'Cuautitlán Izcalli', 'Ecatepec',
    'Huixquilucan', 'Naucalpan', 'Nezahualcóyotl', 'Tecámac', 'Tlalnepantla', 'Toluca'
  ],
  'Guanajuato': ['Celaya', 'Guanajuato', 'Irapuato', 'León', 'Salamanca', 'San Miguel de Allende'],
  'Guerrero': ['Acapulco', 'Chilpancingo', 'Iguala', 'Taxco', 'Zihuatanejo'],
  'Hidalgo': ['Actopan', 'Pachuca', 'Tepeji del Río', 'Tizayuca', 'Tula de Allende', 'Tulancingo'],
  'Jalisco': ['Guadalajara', 'Puerto Vallarta', 'Tlaquepaque', 'Tlajomulco', 'Tonalá', 'Zapopan'],
  'Michoacán': ['Apatzingán', 'Lázaro Cárdenas', 'Morelia', 'Uruapan', 'Zamora', 'Zitácuaro'],
  'Morelos': ['Cuautla', 'Cuernavaca', 'Jiutepec', 'Temixco', 'Yautepec'],
  'Nayarit': ['Bahía de Banderas', 'Compostela', 'Santiago Ixcuintla', 'Tepic', 'Xalisco'],
  'Nuevo León': ['Apodaca', 'García', 'General Escobedo', 'Guadalupe', 'Juárez', 'Monterrey', 'San Nicolás de los Garza', 'San Pedro Garza García', 'Santa Catarina'],
  'Oaxaca': ['Juchitán', 'Oaxaca de Juárez', 'Salina Cruz', 'San Juan Bautista Tuxtepec', 'Santa Cruz Xoxocotlán'],
  'Puebla': ['Atlixco', 'Cholula', 'Puebla', 'San Martín Texmelucan', 'Tehuacán'],
  'Querétaro': ['Corregidora', 'El Marqués', 'Querétaro', 'San Juan del Río'],
  'Quintana Roo': ['Benito Juárez (Cancún)', 'Cozumel', 'Othón P. Blanco (Chetumal)', 'Playa del Carmen', 'Tulum'],
  'San Luis Potosí': ['Ciudad Valles', 'Matehuala', 'Rioverde', 'San Luis Potosí', 'Soledad de Graciano Sánchez'],
  'Sinaloa': ['Ahome (Los Mochis)', 'Culiacán', 'Guasave', 'Mazatlán', 'Navolato'],
  'Sonora': ['Cajeme (Cd. Obregón)', 'Guaymas', 'Hermosillo', 'Navojoa', 'Nogales', 'San Luis Río Colorado'],
  'Tabasco': ['Cárdenas', 'Centro (Villahermosa)', 'Comalcalco', 'Huimanguillo', 'Macuspana'],
  'Tamaulipas': ['Ciudad Madero', 'Matamoros', 'Nuevo Laredo', 'Reynosa', 'Tampico', 'Victoria'],
  'Tlaxcala': ['Apizaco', 'Chiautempan', 'Huamantla', 'San Pablo del Monte', 'Tlaxcala'],
  'Veracruz': ['Boca del Río', 'Coatzacoalcos', 'Córdoba', 'Minatitlán', 'Orizaba', 'Poza Rica', 'Veracruz', 'Xalapa'],
  'Yucatán': ['Kanasín', 'Mérida', 'Progreso', 'Tizimín', 'Valladolid'],
  'Zacatecas': ['Fresnillo', 'Guadalupe', 'Jerez', 'Sombrerete', 'Zacatecas']
}

export const STATE_NAMES = Object.keys(MEXICAN_STATES)

export async function saveWorkshop(payload: Workshop): Promise<Workshop> {
  const { data } = await api.post<Workshop>('/workshops', payload)
  return data
}

export async function updateWorkshop(id: number, payload: Workshop): Promise<Workshop> {
  const { data } = await api.put<Workshop>(`/workshops/${id}`, payload)
  return data
}

export async function getWorkshop(): Promise<Workshop | null> {
  const { data } = await api.get<Workshop[]>('/workshops', { params: { status_filter: 'activos' } })
  return data[0] || null
}
