import { useState } from 'react'

function App() {
  const [data, setData] = useState(null)

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">
            GeoPark Automation System
          </h1>
        </div>
      </header>
      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          {/* Content will go here */}
          <div className="px-4 py-6 sm:px-0">
            <div className="border-4 border-dashed border-gray-200 rounded-lg h-96">
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-500">Sistema de Automatización GeoPark</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App 