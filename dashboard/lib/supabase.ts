import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Data interfaces
export interface Conversation {
  id: string
  phone_number: string
  contact_name?: string
  created_at: string
  updated_at: string
  message_count: number
  has_issues: boolean
}

export interface Message {
  id: string
  conversation_id: string
  content: string
  timestamp: string
  sender_type: 'user' | 'support'
  category?: string
  sentiment?: 'positive' | 'negative' | 'neutral'
}

export interface Issue {
  id: string
  conversation_id: string
  message_id: string
  category: string
  description: string
  severity: 'low' | 'medium' | 'high'
  status: 'open' | 'resolved' | 'pending'
  created_at: string
  resolved_at?: string
}