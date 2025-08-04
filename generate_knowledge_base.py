import json
import os
from pathlib import Path
from datetime import datetime
import re
from collections import defaultdict

class KnowledgeBaseGenerator:
    def __init__(self):
        self.issues_solutions = defaultdict(list)
        self.categories = {
            'access_issues': {
                'keywords': ['não consigo acessar', 'não consegue entrar', 'login', 'senha', 'bloqueado', 'acesso negado', 'modo caverna', 'central caverna'],
                'solutions': []
            },
            'refund_cancellation': {
                'keywords': ['reembolso', 'cancelamento', 'devolver', 'estorno', 'cancelar', 'dinheiro de volta'],
                'solutions': []
            },
            'technical_issues': {
                'keywords': ['erro', 'bug', 'não funciona', 'travando', 'carregando', 'tela preta', 'problema técnico'],
                'solutions': []
            },
            'content_access': {
                'keywords': ['ebook', 'material', 'download', 'link', 'conteúdo', 'curso', 'vídeo'],
                'solutions': []
            },
            'affiliate_issues': {
                'keywords': ['afiliado', 'comissão', 'link de afiliado', 'parceiro', 'indicação'],
                'solutions': []
            },
            'payment_issues': {
                'keywords': ['pagamento', 'cobrança', 'cartão', 'pix', 'boleto', 'fatura'],
                'solutions': []
            }
        }
        
    def extract_conversations_from_json(self, json_file_path):
        """Extract conversation data from JSON file"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data
        except Exception as e:
            print(f"Error reading {json_file_path}: {e}")
            return None
    
    def identify_issue_category(self, message_text):
        """Identify which category an issue belongs to"""
        message_lower = message_text.lower()
        
        for category, data in self.categories.items():
            for keyword in data['keywords']:
                if keyword in message_lower:
                    return category
        return 'general'
    
    def extract_solution_pattern(self, conversation_messages):
        """Extract solution patterns from conversation flow"""
        solutions = []
        
        # Look for support responses that contain solution indicators
        solution_indicators = [
            'para resolver', 'solução', 'tente', 'faça', 'acesse', 'clique',
            'vá em', 'entre em contato', 'envie', 'verifique', 'confirme',
            'procedimento', 'passo a passo', 'instruções'
        ]
        
        for msg in conversation_messages:
            if msg.get('fromMe', False):  # Support team message
                message_text = msg.get('body', '').lower()
                
                # Check if this message contains solution language
                if any(indicator in message_text for indicator in solution_indicators):
                    solutions.append({
                        'solution_text': msg.get('body', ''),
                        'timestamp': msg.get('timestamp', '')
                    })
        
        return solutions
    
    def is_issue_resolved(self, conversation_messages):
        """Determine if an issue was resolved based on conversation flow"""
        resolution_indicators = [
            'obrigado', 'obrigada', 'resolvido', 'funcionou', 'consegui',
            'deu certo', 'perfeito', 'muito obrigado', 'valeu', 'ok, obrigado'
        ]
        
        # Look for customer messages indicating resolution
        for msg in reversed(conversation_messages):  # Check recent messages first
            if not msg.get('fromMe', False):  # Customer message
                message_text = msg.get('body', '').lower()
                if any(indicator in message_text for indicator in resolution_indicators):
                    return True
        
        return False
    
    def process_all_conversations(self, json_directory):
        """Process all JSON files to extract issues and solutions"""
        json_files = list(Path(json_directory).glob('*.json'))
        
        print(f"Processing {len(json_files)} conversation files...")
        
        for json_file in json_files:
            conversation_data = self.extract_conversations_from_json(json_file)
            
            if not conversation_data:
                continue
                
            messages = conversation_data.get('messages', [])
            
            if not messages:
                continue
            
            # Extract customer issues (non-fromMe messages)
            customer_messages = [msg for msg in messages if not msg.get('fromMe', False)]
            support_messages = [msg for msg in messages if msg.get('fromMe', False)]
            
            # Look for issues in customer messages
            for msg in customer_messages:
                message_text = msg.get('body', '')
                
                if len(message_text) > 20:  # Filter out very short messages
                    category = self.identify_issue_category(message_text)
                    
                    # Extract solutions from support responses
                    solutions = self.extract_solution_pattern(messages)
                    
                    # Check if issue was resolved
                    resolved = self.is_issue_resolved(messages)
                    
                    if solutions:  # Only include if there are solutions
                        issue_entry = {
                            'issue': message_text,
                            'category': category,
                            'solutions': solutions,
                            'resolved': resolved,
                            'conversation_file': json_file.name,
                            'timestamp': msg.get('timestamp', '')
                        }
                        
                        self.issues_solutions[category].append(issue_entry)
    
    def generate_knowledge_base_document(self, output_file='knowledge_base.md'):
        """Generate a structured knowledge base document"""
        
        kb_content = f"""# Knowledge Base - Customer Support Issues & Solutions

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Purpose:** This document contains common customer issues and their proven solutions extracted from WhatsApp support conversations.

---

## Table of Contents

"""
        
        # Add table of contents
        for category in self.categories.keys():
            if category in self.issues_solutions:
                category_name = category.replace('_', ' ').title()
                kb_content += f"- [{category_name}](#{category.replace('_', '-')})\n"
        
        kb_content += "\n---\n\n"
        
        # Generate content for each category
        for category, issues in self.issues_solutions.items():
            if not issues:
                continue
                
            category_name = category.replace('_', ' ').title()
            kb_content += f"## {category_name}\n\n"
            
            # Group similar issues
            resolved_issues = [issue for issue in issues if issue['resolved']]
            unresolved_issues = [issue for issue in issues if not issue['resolved']]
            
            kb_content += f"**Total Issues:** {len(issues)} | **Resolved:** {len(resolved_issues)} | **Success Rate:** {(len(resolved_issues)/len(issues)*100):.1f}%\n\n"
            
            # Add resolved issues with solutions
            if resolved_issues:
                kb_content += "### ✅ Resolved Issues & Solutions\n\n"
                
                for i, issue in enumerate(resolved_issues[:10], 1):  # Limit to top 10
                    kb_content += f"#### Issue #{i}\n\n"
                    kb_content += f"**Problem:** {issue['issue'][:200]}{'...' if len(issue['issue']) > 200 else ''}\n\n"
                    
                    kb_content += "**Solutions Applied:**\n\n"
                    for j, solution in enumerate(issue['solutions'], 1):
                        solution_text = solution['solution_text'][:300]
                        kb_content += f"{j}. {solution_text}{'...' if len(solution['solution_text']) > 300 else ''}\n\n"
                    
                    kb_content += "---\n\n"
            
            # Add common unresolved issues for improvement
            if unresolved_issues:
                kb_content += "### ⚠️ Common Unresolved Issues (Needs Attention)\n\n"
                
                for i, issue in enumerate(unresolved_issues[:5], 1):  # Limit to top 5
                    kb_content += f"**{i}.** {issue['issue'][:150]}{'...' if len(issue['issue']) > 150 else ''}\n\n"
                
                kb_content += "---\n\n"
        
        # Add AI Training Section
        kb_content += """## 🤖 AI Training Guidelines

### How to Use This Knowledge Base:

1. **Issue Classification:** Use the categories above to classify incoming customer issues
2. **Solution Matching:** Match customer problems with similar resolved issues
3. **Response Templates:** Use the proven solutions as response templates
4. **Escalation Rules:** Unresolved issues may require human intervention

### Response Quality Indicators:
- Customer confirmation ("obrigado", "resolvido", "funcionou")
- No follow-up complaints
- Clear step-by-step instructions
- Relevant links or resources provided

### Common Solution Patterns:
- Access issues → Check credentials, reset password, verify account status
- Technical issues → Clear cache, update app, check internet connection
- Refund requests → Verify purchase, explain policy, process if eligible
- Content access → Verify purchase, provide direct links, check account permissions

---

*This knowledge base is automatically generated from real customer conversations and should be regularly updated.*
"""
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(kb_content)
        
        print(f"Knowledge base generated: {output_file}")
        
        # Generate summary statistics
        total_issues = sum(len(issues) for issues in self.issues_solutions.values())
        total_resolved = sum(len([i for i in issues if i['resolved']]) for issues in self.issues_solutions.values())
        
        print(f"\nSummary:")
        print(f"Total issues processed: {total_issues}")
        print(f"Total resolved issues: {total_resolved}")
        print(f"Overall resolution rate: {(total_resolved/total_issues*100):.1f}%" if total_issues > 0 else "No issues found")
        
        for category, issues in self.issues_solutions.items():
            if issues:
                resolved = len([i for i in issues if i['resolved']])
                print(f"{category.replace('_', ' ').title()}: {len(issues)} issues, {resolved} resolved ({(resolved/len(issues)*100):.1f}%)")

def main():
    generator = KnowledgeBaseGenerator()
    
    # Process all JSON files in the Json directory
    json_directory = "Json"
    
    if not os.path.exists(json_directory):
        print(f"Error: {json_directory} directory not found!")
        return
    
    generator.process_all_conversations(json_directory)
    generator.generate_knowledge_base_document('customer_support_knowledge_base.md')
    
    # Also generate a JSON version for AI training
    json_output = {}
    for category, issues in generator.issues_solutions.items():
        json_output[category] = [
            {
                'issue': issue['issue'],
                'solutions': [sol['solution_text'] for sol in issue['solutions']],
                'resolved': issue['resolved']
            }
            for issue in issues if issue['resolved']  # Only include resolved issues
        ]
    
    with open('knowledge_base_training_data.json', 'w', encoding='utf-8') as f:
        json.dump(json_output, f, ensure_ascii=False, indent=2)
    
    print("\nAlso generated: knowledge_base_training_data.json (for AI training)")

if __name__ == "__main__":
    main()