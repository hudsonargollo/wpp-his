import json
import os
from pathlib import Path
from datetime import datetime
import re
from collections import defaultdict

class KnowledgeBaseGenerator:
    def __init__(self):
        self.issues_solutions = defaultdict(list)
        
        # Issue categories with Portuguese keywords
        self.categories = {
            'access_issues': {
                'keywords': ['não consigo acessar', 'problema para acessar', 'não entra', 'bloqueado', 'senha', 'login'],
                'description': 'Problems with account access, login, passwords'
            },
            'technical_issues': {
                'keywords': ['não funciona', 'erro', 'bug', 'travando', 'não carrega', 'problema técnico'],
                'description': 'Technical problems with the application or platform'
            },
            'content_issues': {
                'keywords': ['conteúdo', 'material', 'vídeo', 'aula', 'curso'],
                'description': 'Issues related to course content or materials'
            },
            'payment_issues': {
                'keywords': ['pagamento', 'cobrança', 'fatura', 'cartão', 'pix'],
                'description': 'Payment and billing related issues'
            },
            'refund_requests': {
                'keywords': ['reembolso', 'devolver', 'estorno', 'cancelar', 'dinheiro de volta'],
                'description': 'Refund and cancellation requests'
            },
            'general_support': {
                'keywords': ['ajuda', 'suporte', 'dúvida', 'como', 'onde'],
                'description': 'General support and how-to questions'
            }
        }
    
    def extract_conversations_from_json(self, json_file_path):
        """Extract conversation data from the specific JSON format"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Remove the JavaScript wrapper
                if content.startswith('contentCallbackFunc('):
                    content = content[len('contentCallbackFunc('):-1]
                
                data = json.loads(content)
                return data
        except Exception as e:
            print(f"Error reading {json_file_path}: {e}")
            return None
    
    def identify_issue_category(self, message_text):
        """Identify the category of the customer issue"""
        message_lower = message_text.lower()
        
        category_scores = {}
        for category, data in self.categories.items():
            score = 0
            for keyword in data['keywords']:
                if keyword in message_lower:
                    score += 1
            category_scores[category] = score
        
        # Return category with highest score, or 'general_support' if no matches
        if max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        return 'general_support'
    
    def extract_solution_pattern(self, messages):
        """Extract solution patterns from support responses"""
        solutions = []
        
        for i, msg in enumerate(messages):
            if msg.get('position') == 'right' and msg.get('type') == 'text':  # Support message
                message_text = msg.get('msg', '')
                
                if len(message_text) > 20:  # Filter out very short messages
                    solutions.append({
                        'solution_text': message_text,
                        'timestamp': msg.get('time', ''),
                        'message_index': i
                    })
        
        return solutions
    
    def is_issue_resolved(self, messages):
        """Check if the issue was resolved based on customer responses"""
        resolution_indicators = [
            'obrigado', 'obrigada', 'resolvido', 'funcionou', 'consegui',
            'deu certo', 'perfeito', 'muito obrigado', 'valeu', 'ok, obrigado'
        ]
        
        # Look for customer messages indicating resolution
        customer_messages = [msg for msg in messages if msg.get('position') == 'left']
        
        for msg in reversed(customer_messages):  # Check recent messages first
            message_text = msg.get('msg', '').lower()
            if any(indicator in message_text for indicator in resolution_indicators):
                return True
        
        return False
    
    def process_all_conversations(self, json_directory):
        """Process all JSON files to extract issues and solutions"""
        json_files = list(Path(json_directory).glob('*.json'))
        
        print(f"Processing {len(json_files)} conversation files...")
        
        processed_count = 0
        
        for json_file in json_files:
            conversation_data = self.extract_conversations_from_json(json_file)
            
            if not conversation_data:
                continue
                
            messages = conversation_data.get('body', [])
            
            if not messages:
                continue
            
            processed_count += 1
            
            # Extract customer issues (position: left)
            customer_messages = [msg for msg in messages if msg.get('position') == 'left' and msg.get('type') == 'text']
            
            # Look for issues in customer messages
            for msg in customer_messages:
                message_text = msg.get('msg', '')
                
                if len(message_text) > 10:  # Filter out very short messages
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
                            'timestamp': msg.get('time', ''),
                            'phone_number': conversation_data.get('head', {}).get('name', 'Unknown')
                        }
                        
                        self.issues_solutions[category].append(issue_entry)
        
        print(f"Successfully processed {processed_count} files")
        return processed_count
    
    def generate_knowledge_base_document(self, output_file='customer_support_knowledge_base.md'):
        """Generate a structured knowledge base document"""
        
        kb_content = f"""# Knowledge Base - Customer Support Issues & Solutions

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Purpose:** This document contains common customer issues and their proven solutions extracted from WhatsApp support conversations.

---

## Table of Contents

"""
        
        # Add table of contents
        for category in self.categories.keys():
            if category in self.issues_solutions and self.issues_solutions[category]:
                category_name = category.replace('_', ' ').title()
                kb_content += f"- [{category_name}](#{category.replace('_', '-')})\n"
        
        kb_content += "\n---\n\n"
        
        # Generate content for each category
        for category, issues in self.issues_solutions.items():
            if not issues:
                continue
                
            category_name = category.replace('_', ' ').title()
            category_description = self.categories[category]['description']
            
            kb_content += f"## {category_name}\n\n"
            kb_content += f"**Description:** {category_description}\n\n"
            
            # Group similar issues
            resolved_issues = [issue for issue in issues if issue['resolved']]
            unresolved_issues = [issue for issue in issues if not issue['resolved']]
            
            kb_content += f"**Total Issues:** {len(issues)} | **Resolved:** {len(resolved_issues)} | **Success Rate:** {(len(resolved_issues)/len(issues)*100):.1f}%\n\n"
            
            # Add resolved issues with solutions
            if resolved_issues:
                kb_content += "### ✅ Resolved Issues & Solutions\n\n"
                
                for i, issue in enumerate(resolved_issues[:5], 1):  # Limit to top 5
                    kb_content += f"#### Issue #{i}\n\n"
                    kb_content += f"**Problem:** {issue['issue'][:200]}{'...' if len(issue['issue']) > 200 else ''}\n\n"
                    
                    kb_content += "**Solutions Applied:**\n\n"
                    for j, solution in enumerate(issue['solutions'][:3], 1):  # Limit to 3 solutions
                        solution_text = solution['solution_text'][:300]
                        kb_content += f"{j}. {solution_text}{'...' if len(solution['solution_text']) > 300 else ''}\n\n"
                    
                    kb_content += "---\n\n"
            
            # Add common unresolved issues for improvement
            if unresolved_issues:
                kb_content += "### ⚠️ Common Unresolved Issues (Needs Attention)\n\n"
                
                for i, issue in enumerate(unresolved_issues[:3], 1):  # Limit to top 3
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
    
    processed_count = generator.process_all_conversations(json_directory)
    
    if processed_count == 0:
        print("No valid conversation files found!")
        return
    
    generator.generate_knowledge_base_document('customer_support_knowledge_base.md')
    
    # Also generate a JSON version for AI training
    json_output = {}
    for category, issues in generator.issues_solutions.items():
        if issues:
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