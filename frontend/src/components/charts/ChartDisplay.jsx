export default function ChartDisplay({ charts, loading }) {
  if (!charts || Object.keys(charts).length === 0) {
    if (loading) {
      return (
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Data Visualizations</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[0,1].map(i => (
              <div key={i} className="bg-white rounded-lg shadow-md p-4">
                <div className="h-4 bg-gray-200 rounded animate-pulse w-40 mb-2" />
                <div className="h-3 bg-gray-200 rounded animate-pulse w-60 mb-3" />
                <div className="h-48 bg-gray-200 rounded-lg animate-pulse" />
              </div>
            ))}
          </div>
        </div>
      )
    }
    return null
  }
  const labels = {
    sales_by_region: { title: 'Sales by Region', desc: 'Bar chart showing total sales per region' },
    monthly_trend: { title: 'Monthly Sales Trend', desc: 'Line chart showing sales over time' },
    department_sales: { title: 'Department Sales Distribution', desc: 'Pie chart of department sales share' },
  }
  return (
    <div className="mb-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Data Visualizations</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(charts).map(([key, url]) => {
          if (!url) return null
          const cfg = labels[key] || { title: key }
          return (
            <div key={key} className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
              <h3 className="text-lg font-semibold text-gray-700 mb-1">{cfg.title}</h3>
              {cfg.desc && <p className="text-sm text-gray-500 mb-3">{cfg.desc}</p>}
              <div className="flex justify-center bg-gray-50 rounded-lg p-2">
                <img src={`http://localhost:5000${url}`} alt={cfg.title} className="max-w-full h-auto rounded" loading="lazy" />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
