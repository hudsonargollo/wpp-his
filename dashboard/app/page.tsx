'use client'

import { useState, useEffect } from 'react'
import { supabase, Conversation, Message, Issue } from '../lib/supabase'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { MessageSquare, Users, AlertTriangle, CheckCircle, TrendingUp, Filter } from 'lucide-react'

interface Stats {
  totalConversations: number
  totalMessages: number
  totalIssues: number
  resolvedIssues: number
  resolutionRate: number
}

interface CategoryData {
  name: string
  count: number
  resolved: number
}

interface SentimentData {
  name: string
  value: number
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({
    totalConversations: 0,
    totalMessages: 0,
    totalIssues: 0,
    resolvedIssues: 0,
    resolutionRate: 0
  })
  const [categoryData, setCategoryData] = useState<CategoryData[]>([])
  const [sentimentData, setSentimentData] = useState<SentimentData[]>([])
  const [issues, setIssues] = useState<Issue[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'open' | 'resolved'>('all')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      // Fetch conversations
      const { data: conversations } = await supabase
        .from('conversations')
        .select('*')

      // Fetch messages
      const { data: messages } = await supabase
        .from('messages')
        .select('*')

      // Fetch issues
      const { data: issuesData } = await supabase
        .from('issues')
        .select('*')
        .order('created_at', { ascending: false })

      if (conversations && messages && issuesData) {
        // Calculate stats
        const resolvedCount = issuesData.filter(issue => issue.status === 'resolved').length
        const resolutionRate = issuesData.length > 0 ? (resolvedCount / issuesData.length) * 100 : 0

        setStats({
          totalConversations: conversations.length,
          totalMessages: messages.length,
          totalIssues: issuesData.length,
          resolvedIssues: resolvedCount,
          resolutionRate: Math.round(resolutionRate)
        })

        // Process category data
        const categoryMap = new Map<string, { count: number; resolved: number }>()
        issuesData.forEach(issue => {
          const current = categoryMap.get(issue.category) || { count: 0, resolved: 0 }
          current.count++
          if (issue.status === 'resolved') current.resolved++
          categoryMap.set(issue.category, current)
        })

        const categoryArray = Array.from(categoryMap.entries()).map(([name, data]) => ({
          name,
          count: data.count,
          resolved: data.resolved
        }))
        setCategoryData(categoryArray)

        // Process sentiment data
        const sentimentMap = new Map<string, number>()
        messages.forEach(message => {
          if (message.sentiment) {
            sentimentMap.set(message.sentiment, (sentimentMap.get(message.sentiment) || 0) + 1)
          }
        })

        const sentimentArray = Array.from(sentimentMap.entries()).map(([name, value]) => ({
          name: name.charAt(0).toUpperCase() + name.slice(1),
          value
        }))
        setSentimentData(sentimentArray)

        setIssues(issuesData)
      }
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredIssues = issues.filter(issue => {
    if (filter === 'all') return true
    return issue.status === filter
  })

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">WhatsApp Analytics Dashboard</h1>
        
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <Users className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Conversations</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalConversations}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <MessageSquare className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Messages</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalMessages}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-red-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Issues</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalIssues}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Resolved</p>
                <p className="text-2xl font-bold text-gray-900">{stats.resolvedIssues}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-purple-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Resolution Rate</p>
                <p className="text-2xl font-bold text-gray-900">{stats.resolutionRate}%</p>
              </div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Category Distribution */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Issues by Category</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={categoryData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#8884d8" name="Total" />
                <Bar dataKey="resolved" fill="#82ca9d" name="Resolved" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Sentiment Analysis */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Sentiment Analysis</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Issues Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Issues Management</h2>
              <div className="flex items-center space-x-2">
                <Filter className="h-4 w-4" />
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value as 'all' | 'open' | 'resolved')}
                  className="border border-gray-300 rounded-md px-3 py-1"
                >
                  <option value="all">All Issues</option>
                  <option value="open">Open</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredIssues.map((issue) => (
                  <tr key={issue.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {issue.category}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {issue.description.length > 100 
                        ? `${issue.description.substring(0, 100)}...` 
                        : issue.description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        issue.severity === 'high' ? 'bg-red-100 text-red-800' :
                        issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {issue.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        issue.status === 'resolved' ? 'bg-green-100 text-green-800' :
                        issue.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {issue.status}
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
