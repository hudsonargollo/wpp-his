import { useState, useEffect } from 'react'
import { createClient } from '@supabase/supabase-js'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell } from 'recharts'

const supabase = createClient(
  'https://sfvlpxgxjerujyfkvorc.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmdmxweGd4amVydWp5Zmt2b3JjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQyOTg0NzEsImV4cCI6MjA2OTg3NDQ3MX0.g_jJ6ysC4BdIQeasHDWNrhZK-EWaHKJWZkkiJPRQU9s'
)

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D']

export default function Dashboard() {
  const [analytics, setAnalytics] = useState(null)
  const [issues, setIssues] = useState([])
  const [conversations, setConversations] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      // Fetch conversations
      const { data: conversationsData } = await supabase
        .from('conversations')
        .select('*')
      
      // Fetch messages with category breakdown
      const { data: messagesData } = await supabase
        .from('messages')
        .select('category, sentiment')
      
      // Fetch issues
      const { data: issuesData } = await supabase
        .from('issues')
        .select('*')
      
      // Process analytics
      const categoryBreakdown = messagesData.reduce((acc, msg) => {
        acc[msg.category] = (acc[msg.category] || 0) + 1
        return acc
      }, {})
      
      const sentimentBreakdown = messagesData.reduce((acc, msg) => {
        acc[msg.sentiment] = (acc[msg.sentiment] || 0) + 1
        return acc
      }, {})
      
      const resolvedIssues = issuesData.filter(issue => issue.status === 'resolved').length
      
      setAnalytics({
        totalConversations: conversationsData.length,
        totalMessages: messagesData.length,
        totalIssues: issuesData.length,
        resolvedIssues,
        resolutionRate: (resolvedIssues / issuesData.length * 100).toFixed(1),
        categoryBreakdown: Object.entries(categoryBreakdown).map(([name, value]) => ({ name, value })),
        sentimentBreakdown: Object.entries(sentimentBreakdown).map(([name, value]) => ({ name, value }))
      })
      
      setIssues(issuesData)
      setConversations(conversationsData)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching data:', error)
      setLoading(false)
    }
  }

  const filteredIssues = selectedCategory === 'all' 
    ? issues 
    : issues.filter(issue => issue.issue_type === selectedCategory)

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">WhatsApp Support Analytics</h1>
        
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-700">Total Conversations</h3>
            <p className="text-3xl font-bold text-blue-600">{analytics?.totalConversations}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-700">Total Messages</h3>
            <p className="text-3xl font-bold text-green-600">{analytics?.totalMessages}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-700">Total Issues</h3>
            <p className="text-3xl font-bold text-yellow-600">{analytics?.totalIssues}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-700">Resolution Rate</h3>
            <p className="text-3xl font-bold text-purple-600">{analytics?.resolutionRate}%</p>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">Issues by Category</h3>
            <BarChart width={400} height={300} data={analytics?.categoryBreakdown}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#8884d8" />
            </BarChart>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">Sentiment Analysis</h3>
            <PieChart width={400} height={300}>
              <Pie
                data={analytics?.sentimentBreakdown}
                cx={200}
                cy={150}
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {analytics?.sentimentBreakdown?.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </div>
        </div>

        {/* Issues Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <div className="flex justify-between items-center">
              <h3 className="text-xl font-semibold">Issues Overview</h3>
              <select 
                value={selectedCategory} 
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="border rounded px-3 py-2"
              >
                <option value="all">All Categories</option>
                <option value="access_issues">Access Issues</option>
                <option value="refund_requests">Refund Requests</option>
                <option value="technical_issues">Technical Issues</option>
                <option value="product_confusion">Product Confusion</option>
                <option value="content_access">Content Access</option>
                <option value="affiliate_support">Affiliate Support</option>
                <option value="billing_issues">Billing Issues</option>
              </select>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issue Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredIssues.map((issue) => (
                  <tr key={issue.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {issue.issue_type.replace('_', ' ').toUpperCase()}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                      {issue.description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        issue.status === 'resolved' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {issue.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        issue.priority === 'high' 
                          ? 'bg-red-100 text-red-800' 
                          : issue.priority === 'medium'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {issue.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(issue.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}