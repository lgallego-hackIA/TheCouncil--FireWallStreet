import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { fetchData } from '../services/api';

interface DashboardData {
  geopark: {
    production: number;
    revenue: number;
    wells: number;
    location: string;
    status: string;
  };
  market: {
    stock_price: number;
    market_cap: number;
    volume: number;
    currency: string;
  };
  brent: {
    price: number;
    volume: number;
    change: number;
  };
}

export const DataDashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const response = await fetchData<DashboardData>('/data/latest');
        setData(response.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error loading data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
    // Actualizar cada 5 minutos
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="flex justify-center items-center h-96">Loading...</div>;
  if (error) return <div className="text-red-500">Error: {error}</div>;
  if (!data) return null;

  const chartData = [
    {
      name: 'GeoPark',
      Producción: data.geopark.production,
      Ingresos: data.geopark.revenue / 1000, // Convertir a miles para mejor visualización
    },
  ];

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* GeoPark Card */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">GeoPark Operations</h3>
          <div className="space-y-2">
            <p>Production: {data.geopark.production.toLocaleString()} bbl/day</p>
            <p>Revenue: ${data.geopark.revenue.toLocaleString()}</p>
            <p>Active Wells: {data.geopark.wells}</p>
            <p>Location: {data.geopark.location}</p>
            <p>Status: <span className="text-green-500">{data.geopark.status}</span></p>
          </div>
        </div>

        {/* Market Data Card */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Market Data</h3>
          <div className="space-y-2">
            <p>Stock Price: ${data.market.stock_price}</p>
            <p>Market Cap: ${(data.market.market_cap / 1000000).toFixed(2)}M</p>
            <p>Volume: {data.market.volume.toLocaleString()}</p>
            <p>Currency: {data.market.currency}</p>
          </div>
        </div>

        {/* Brent Data Card */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Brent Oil</h3>
          <div className="space-y-2">
            <p>Price: ${data.brent.price}</p>
            <p>Volume: {data.brent.volume.toLocaleString()}</p>
            <p>Change: <span className={data.brent.change >= 0 ? 'text-green-500' : 'text-red-500'}>
              {data.brent.change > 0 ? '+' : ''}{data.brent.change}%
            </span></p>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Production & Revenue Overview</h3>
        <BarChart width={800} height={400} data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="Producción" fill="#4F46E5" />
          <Bar dataKey="Ingresos" fill="#10B981" />
        </BarChart>
      </div>
    </div>
  );
}; 