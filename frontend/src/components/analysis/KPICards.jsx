export default function KPICards({ kpis, loading }) {
  if (!kpis) {
    if (loading) {
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[0,1,2,3].map(i => (
            <div key={i} className="bg-white rounded-lg shadow-md overflow-hidden">
              <div className="h-2 bg-gray-200 animate-pulse" />
              <div className="p-4 space-y-3">
                <div className="h-3 bg-gray-200 rounded animate-pulse w-20" />
                <div className="h-6 bg-gray-200 rounded animate-pulse w-32" />
              </div>
            </div>
          ))}
        </div>
      )
    }
    return null
  }
  const cards = [
    { label: 'Total Sales', value: kpis.total_sales != null ? `$${kpis.total_sales.toLocaleString()}` : 'N/A', color: 'bg-blue-500' },
    { label: 'Top Region', value: kpis.top_region || 'N/A', subtext: kpis.top_region_sales != null ? `$${kpis.top_region_sales.toLocaleString()}` : '', color: 'bg-green-500' },
    { label: 'Top Department', value: kpis.top_department || 'N/A', subtext: kpis.top_department_sales != null ? `$${kpis.top_department_sales.toLocaleString()}` : '', color: 'bg-purple-500' },
    { label: 'Total Records', value: kpis.total_records?.toLocaleString() || '0', color: 'bg-orange-500' },
  ]
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((c, i) => (
        <div key={i} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
          <div className={`${c.color} h-2`} />
          <div className="p-4">
            <p className="text-sm text-gray-500 font-medium mb-2">{c.label}</p>
            <p className="text-2xl font-bold text-gray-800">{c.value}</p>
            {c.subtext && <p className="text-sm text-gray-500 mt-1">{c.subtext}</p>}
          </div>
        </div>
      ))}
    </div>
  )
}
