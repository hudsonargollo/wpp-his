import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any
from supabase import create_client, Client
import pandas as pd
from pathlib import Path

# Supabase configuration
SUPABASE_URL = "https://sfvlpxgxjerujyfkvorc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmdmxweGd4amVydWp5Zmt2b3JjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDI5ODQ3MSwiZXhwIjoyMDY5ODc0NDcxfQ.a239NSy9ncxRsdEFFWpLl92lUWpHIZG2Cjb0WckQFOA"

class WhatsAppAnalyzer:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.categories = {
            'access_issues': ['acesso', 'login', 'senha', 'password', 'não consigo', 'problema para acessar'],
            'refund_requests': ['reembolso', 'cancelamento', 'estorno', 'devolver', 'quero cancelar'],
            'technical_issues': ['bug', 'erro', 'problema', 'não funciona', 'travando', 'carregando'],
            'product_confusion': ['modo caverna', 'central caverna', 'qual produto', 'diferença'],
            'content_access': ['não encontro', 'onde está', 'cadê', 'sumiu', 'material'],
            'affiliate_support': ['afiliado', 'comissão', 'link', 'divulgar', 'ganhar'],
            'general_support': ['ajuda', 'dúvida', 'suporte', 'atendimento'],
            'billing_issues': ['cobrança', 'cartão', 'pagamento', 'valor', 'preço']
        }
        
    def setup_database(self):
        """Create necessary tables in Supabase"""
        # This would typically be done via Supabase dashboard or SQL
        # Here's the schema for reference
        print("Setting up database tables...")
        print("Please create these tables in your Supabase dashboard:")
        print("""
        -- Conversations table
        CREATE TABLE conversations (
            id SERIAL PRIMARY KEY,
            contact_name VARCHAR(255),
            contact_number VARCHAR(50),
            file_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Messages table
        CREATE TABLE messages (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER REFERENCES conversations(id),
            message_text TEXT,
            message_type VARCHAR(50),
            position VARCHAR(10),
            timestamp TIMESTAMP,
            media_name VARCHAR(255),
            media_size VARCHAR(50),
            category VARCHAR(100),
            is_resolved BOOLEAN DEFAULT FALSE,
            sentiment VARCHAR(20),
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Issues table
        CREATE TABLE issues (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER REFERENCES conversations(id),
            issue_type VARCHAR(100),
            description TEXT,
            status VARCHAR(50) DEFAULT 'open',
            priority VARCHAR(20) DEFAULT 'medium',
            resolved_at TIMESTAMP,
            resolution_notes TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Categories table
        CREATE TABLE categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE,
            description TEXT,
            color VARCHAR(7),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        
    def categorize_message(self, message_text: str) -> str:
        """Categorize message based on content"""
        if not message_text:
            return 'uncategorized'
            
        message_lower = message_text.lower()
        
        for category, keywords in self.categories.items():
            if any(keyword in message_lower for keyword in keywords):
                return category
                
        return 'general_support'
    
    def detect_sentiment(self, message_text: str) -> str:
        """Simple sentiment analysis"""
        if not message_text:
            return 'neutral'
            
        positive_words = ['obrigado', 'ótimo', 'excelente', 'perfeito', 'adorei', 'parabéns']
        negative_words = ['problema', 'erro', 'ruim', 'péssimo', 'frustrado', 'irritado', 'cancelar']
        
        message_lower = message_text.lower()
        
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def is_issue_resolved(self, messages: List[Dict]) -> bool:
        """Determine if an issue was resolved based on conversation flow"""
        resolution_indicators = [
            'resolvido', 'solucionado', 'funcionando', 'consegui', 
            'obrigado', 'perfeito', 'tudo certo'
        ]
        
        # Check last few messages for resolution indicators
        last_messages = messages[-5:] if len(messages) >= 5 else messages
        
        for msg in last_messages:
            if msg.get('msg'):
                msg_lower = msg['msg'].lower()
                if any(indicator in msg_lower for indicator in resolution_indicators):
                    return True
                    
        return False
    
    def parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp from WhatsApp format"""
        try:
            return datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S")
        except:
            return datetime.now()
    
    def process_json_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Remove the contentCallbackFunc wrapper
        json_start = content.find('({')
        json_end = content.rfind('})')
        if json_start != -1 and json_end != -1:
            json_content = content[json_start+1:json_end+1]
            data = json.loads(json_content)
        else:
            data = json.loads(content)
        
        return data
    
    def store_conversation(self, data: Dict, file_name: str) -> int:
        """Store conversation in Supabase and return conversation ID"""
        conversation_data = {
            'contact_name': data['head']['name'],
            'contact_number': data['head'].get('member', ''),
            'file_name': file_name
        }
        
        result = self.supabase.table('conversations').insert(conversation_data).execute()
        return result.data[0]['id']
    
    def store_messages(self, conversation_id: int, messages: List[Dict]):
        """Store messages in Supabase"""
        message_batch = []
        
        for msg in messages:
            category = self.categorize_message(msg.get('msg', ''))
            sentiment = self.detect_sentiment(msg.get('msg', ''))
            
            message_data = {
                'conversation_id': conversation_id,
                'message_text': msg.get('msg', ''),
                'message_type': msg.get('type', 'unknown'),
                'position': msg.get('position', 'unknown'),
                'timestamp': self.parse_timestamp(msg.get('time', '')).isoformat(),
                'media_name': msg.get('mediaName', ''),
                'media_size': msg.get('mediaSize', ''),
                'category': category,
                'sentiment': sentiment
            }
            
            message_batch.append(message_data)
        
        # Insert in batches of 100
        for i in range(0, len(message_batch), 100):
            batch = message_batch[i:i+100]
            self.supabase.table('messages').insert(batch).execute()
    
    def extract_issues(self, conversation_id: int, messages: List[Dict]):
        """Extract and categorize issues from conversation"""
        issues = []
        current_issue = None
        
        for msg in messages:
            if not msg.get('msg'):
                continue
                
            category = self.categorize_message(msg['msg'])
            
            if category != 'general_support' and category != 'uncategorized':
                if current_issue and current_issue['issue_type'] != category:
                    # Save previous issue
                    issues.append(current_issue)
                    current_issue = None
                
                if not current_issue:
                    current_issue = {
                        'conversation_id': conversation_id,
                        'issue_type': category,
                        'description': msg['msg'][:500],  # Truncate long descriptions
                        'status': 'resolved' if self.is_issue_resolved(messages) else 'open',
                        'priority': 'high' if category in ['refund_requests', 'technical_issues'] else 'medium'
                    }
        
        if current_issue:
            issues.append(current_issue)
        
        # Insert issues
        if issues:
            self.supabase.table('issues').insert(issues).execute()
    
    def process_all_files(self, json_directory: str):
        """Process all JSON files in the directory"""
        json_files = list(Path(json_directory).glob('*.json'))
        total_files = len(json_files)
        
        print(f"Processing {total_files} JSON files...")
        
        for i, file_path in enumerate(json_files, 1):
            try:
                print(f"Processing {file_path.name} ({i}/{total_files})")
                
                data = self.process_json_file(str(file_path))
                conversation_id = self.store_conversation(data, file_path.name)
                
                if 'body' in data and data['body']:
                    self.store_messages(conversation_id, data['body'])
                    self.extract_issues(conversation_id, data['body'])
                    
            except Exception as e:
                print(f"Error processing {file_path.name}: {str(e)}")
                continue
        
        print("Processing complete!")
    
    def generate_analytics(self):
        """Generate analytics and insights"""
        # Get conversation statistics
        conversations = self.supabase.table('conversations').select('*').execute()
        messages = self.supabase.table('messages').select('*').execute()
        issues = self.supabase.table('issues').select('*').execute()
        
        analytics = {
            'total_conversations': len(conversations.data),
            'total_messages': len(messages.data),
            'total_issues': len(issues.data),
            'resolved_issues': len([i for i in issues.data if i['status'] == 'resolved']),
            'category_breakdown': {},
            'sentiment_breakdown': {}
        }
        
        # Category breakdown
        for msg in messages.data:
            category = msg['category']
            analytics['category_breakdown'][category] = analytics['category_breakdown'].get(category, 0) + 1
        
        # Sentiment breakdown
        for msg in messages.data:
            sentiment = msg['sentiment']
            analytics['sentiment_breakdown'][sentiment] = analytics['sentiment_breakdown'].get(sentiment, 0) + 1
        
        return analytics

def main():
    analyzer = WhatsAppAnalyzer()
    
    # Setup database (run once)
    analyzer.setup_database()
    
    # Process all JSON files
    json_directory = "/Users/hudsonargollo/wpp-his/Json"
    analyzer.process_all_files(json_directory)
    
    # Generate analytics
    analytics = analyzer.generate_analytics()
    print("\nAnalytics Summary:")
    print(f"Total Conversations: {analytics['total_conversations']}")
    print(f"Total Messages: {analytics['total_messages']}")
    print(f"Total Issues: {analytics['total_issues']}")
    print(f"Resolved Issues: {analytics['resolved_issues']}")
    print(f"Resolution Rate: {analytics['resolved_issues']/analytics['total_issues']*100:.1f}%")
    
if __name__ == "__main__":
    main()