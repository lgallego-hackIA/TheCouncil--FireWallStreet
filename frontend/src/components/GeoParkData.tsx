import { useEffect, useState } from 'react';
import { fetchGeoParkData, GeoDataPoint } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

const GeoParkData = () => {
  const [data, setData] = useState<GeoDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const result = await fetchGeoParkData();
        setData(result);
        setError(null);
      } catch (err) {
        setError('Error al cargar los datos de GeoPark');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-40">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-800"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        <p>{error}</p>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
        <p>No hay datos disponibles para mostrar.</p>
      </div>
    );
  }

  // Formatea los datos para el gráfico
  const chartData = data.slice(0, 30).map(item => ({
    ...item,
    fecha_formateada: format(parseISO(item.fecha), 'dd MMM', { locale: es })
  })).reverse();

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">Precio diario de GeoPark (GPRK)</h2>
      
      {/* Datos más recientes */}
      <div className="mb-6 bg-gray-50 p-4 rounded-md">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-gray-500 text-sm">Último precio</p>
            <p className="text-2xl font-bold">${data[0].precio_geo.toFixed(2)}</p>
            <p className="text-gray-500 text-sm">
              {format(parseISO(data[0].fecha), 'dd MMMM yyyy', { locale: es })}
            </p>
          </div>
          <div>
            <p className="text-gray-500 text-sm">Volumen</p>
            <p className="text-xl font-semibold">{data[0].volumen.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-gray-500 text-sm">Variación (1d)</p>
            {data.length > 1 && (
              <p className={`text-xl font-semibold ${data[0].precio_geo > data[1].precio_geo ? 'text-green-600' : 'text-red-600'}`}>
                {((data[0].precio_geo - data[1].precio_geo) / data[1].precio_geo * 100).toFixed(2)}%
              </p>
            )}
          </div>
        </div>
      </div>
      
      {/* Gráfico */}
      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="fecha_formateada" 
              tick={{ fontSize: 12 }}
            />
            <YAxis 
              domain={['auto', 'auto']} 
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip 
              formatter={(value) => [`$${Number(value).toFixed(2)}`, 'Precio']}
              labelFormatter={(label) => `Fecha: ${label}`}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="precio_geo" 
              name="Precio" 
              stroke="#3182ce" 
              activeDot={{ r: 8 }} 
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Tabla de datos */}
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border-collapse">
          <thead>
            <tr className="bg-gray-100">
              <th className="py-2 px-4 text-left border">Fecha</th>
              <th className="py-2 px-4 text-left border">Precio (USD)</th>
              <th className="py-2 px-4 text-left border">Volumen</th>
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 10).map((item, index) => (
              <tr key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                <td className="py-2 px-4 border">
                  {format(parseISO(item.fecha), 'dd/MM/yyyy')}
                </td>
                <td className="py-2 px-4 border">${item.precio_geo.toFixed(2)}</td>
                <td className="py-2 px-4 border">{item.volumen.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Estructura de documentos */}
      <div className="mt-6 p-4 bg-gray-50 rounded-md">
        <h3 className="text-lg font-semibold mb-2">Estructura de Documentos</h3>
        <pre className="bg-gray-800 text-white p-4 rounded overflow-x-auto">
          {`{
  fecha: "2023-06-10",
  precio_geo: 12.34,
  volumen: 567890,
  brent: 85.67,
  market_cap: 750000000
}`}
        </pre>
      </div>
    </div>
  );
};

export default GeoParkData; 