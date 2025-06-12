const API_BASE_URL = '/api'

export interface APIResponse<T> {
  data: T
  error?: string
}

export const fetchData = async <T>(endpoint: string): Promise<APIResponse<T>> => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`)
    const data = await response.json()
    return { data }
  } catch (error) {
    return { 
      data: {} as T,
      error: error instanceof Error ? error.message : 'An error occurred' 
    }
  }
}

export const postData = async <T>(endpoint: string, data: any): Promise<APIResponse<T>> => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    const responseData = await response.json()
    return { data: responseData }
  } catch (error) {
    return {
      data: {} as T,
      error: error instanceof Error ? error.message : 'An error occurred'
    }
  }
}

// Define interfaces para los datos
export interface GeoDataPoint {
  fecha: string;
  precio_geo: number;
  volumen: number;
  brent?: number;
  market_cap?: number;
}

// Interfaz para la respuesta de Alpha Vantage
interface AlphaVantageResponse {
  'Meta Data': {
    '1. Information': string;
    '2. Symbol': string;
    '3. Last Refreshed': string;
    '4. Output Size': string;
    '5. Time Zone': string;
  };
  'Time Series (Daily)': {
    [date: string]: {
      '1. open': string;
      '2. high': string;
      '3. low': string;
      '4. close': string;
      '5. volume': string;
    };
  };
}

// URL base de la API
const ALPHA_VANTAGE_API_KEY = 'BCCMWJX0WL7IQYVE';
const ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co/query';

/**
 * Obtiene los datos diarios de GeoPark desde Alpha Vantage
 * @returns Promise con los datos formateados
 */
export async function fetchGeoParkData(): Promise<GeoDataPoint[]> {
  try {
    const url = `${ALPHA_VANTAGE_BASE_URL}?function=TIME_SERIES_DAILY&symbol=GPRK&apikey=${ALPHA_VANTAGE_API_KEY}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error('Error fetching GeoPark data');
    }
    
    const data = await response.json() as AlphaVantageResponse;
    
    // Verifica si los datos están en el formato esperado
    if (!data || !data['Time Series (Daily)']) {
      throw new Error('Invalid data format from Alpha Vantage');
    }
    
    // Transforma los datos al formato requerido
    const timeSeriesData = data['Time Series (Daily)'];
    const formattedData: GeoDataPoint[] = Object.keys(timeSeriesData).map(date => {
      const dailyData = timeSeriesData[date];
      return {
        fecha: date,
        precio_geo: parseFloat(dailyData['4. close']),
        volumen: parseFloat(dailyData['5. volume']),
        // Brent y Market Cap no están disponibles directamente desde esta API
      };
    });
    
    // Ordenar por fecha, más reciente primero
    return formattedData.sort((a, b) => 
      new Date(b.fecha).getTime() - new Date(a.fecha).getTime()
    );
  } catch (error) {
    console.error('Error fetching GeoPark data:', error);
    return [];
  }
} 