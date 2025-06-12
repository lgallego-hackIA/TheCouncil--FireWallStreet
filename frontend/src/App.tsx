import { useState } from 'react'
import { Bell, ChevronDown } from 'lucide-react'
import GeoParkData from './components/GeoParkData'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-blue-800 text-white p-4 shadow-md">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">GeoPark Automation System</h1>
          <div className="flex items-center space-x-4">
            <Bell className="h-5 w-5" />
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center">
                <span className="text-sm font-medium">US</span>
              </div>
              <ChevronDown className="h-4 w-4" />
            </div>
          </div>
        </div>
      </header>
      <div className="container mx-auto p-4">
        <main className="mt-4 space-y-6">
          {/* Sección de información de GeoPark */}
          <section>
            <GeoParkData />
          </section>

          {/* Sección de ejemplo con contador */}
          <section className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4">Ejemplo de Contador</h2>
            <p className="text-gray-600">
              Haz clic en el botón para incrementar el contador: {count}
            </p>
            <button
              onClick={() => setCount((count) => count + 1)}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Incrementar
            </button>
          </section>
        </main>
      </div>
    </div>
  )
}

export default App 