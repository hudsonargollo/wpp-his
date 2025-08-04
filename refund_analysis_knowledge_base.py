import json
import os
from pathlib import Path
from datetime import datetime
import re
from collections import defaultdict, Counter

class RefundAnalysisKnowledgeBase:
    def __init__(self):
        self.refund_conversations = []
        self.refund_reasons = defaultdict(list)
        self.retention_strategies = defaultdict(list)
        self.customer_journey_analysis = []
        
        # Refund reason categories with keywords
        self.refund_categories = {
            'content_quality': {
                'keywords': ['conteúdo ruim', 'não gostei', 'esperava mais', 'muito básico', 'superficial', 'não vale', 'decepcionante'],
                'reasons': [],
                'retention_rate': 0
            },
            'technical_issues': {
                'keywords': ['não funciona', 'erro', 'bug', 'travando', 'não carrega', 'problema técnico', 'não consigo acessar'],
                'reasons': [],
                'retention_rate': 0
            },
            'access_problems': {
                'keywords': ['não consigo entrar', 'bloqueado', 'senha', 'login', 'acesso negado', 'expirou'],
                'reasons': [],
                'retention_rate': 0
            },
            'financial_issues': {
                'keywords': ['sem dinheiro', 'situação financeira', 'desemprego', 'não posso pagar', 'crise'],
                'reasons': [],
                'retention_rate': 0
            },
            'expectation_mismatch': {
                'keywords': ['não era isso', 'diferente do prometido', 'propaganda enganosa', 'não é como falaram'],
                'reasons': [],
                'retention_rate': 0
            },
            'time_constraints': {
                'keywords': ['não tenho tempo', 'muito ocupado', 'não consigo estudar', 'sem tempo'],
                'reasons': [],
                'retention_rate': 0
            },
            'duplicate_purchase': {
                'keywords': ['comprei duas vezes', 'duplicado', 'erro na compra', 'compra acidental'],
                'reasons': [],
                'retention_rate': 0
            },
            'competitor_influence': {
                'keywords': ['encontrei mais barato', 'outro curso', 'melhor opção', 'concorrente'],
                'reasons': [],
                'retention_rate': 0
            }
        }
        
        # Retention strategies that work
        self.retention_strategies_patterns = {
            'technical_support': ['vamos resolver', 'suporte técnico', 'vou te ajudar', 'problema técnico'],
            'content_upgrade': ['material extra', 'bônus', 'conteúdo adicional', 'acesso premium'],
            'personal_assistance': ['acompanhamento', 'suporte personalizado', 'mentoria', 'ajuda individual'],
            'flexible_payment': ['parcelamento', 'desconto', 'condição especial', 'facilitar pagamento'],
            'guarantee_extension': ['garantia estendida', 'mais tempo', 'prazo maior'],
            'community_access': ['grupo vip', 'comunidade', 'networking', 'contatos'],
            'alternative_solution': ['outro produto', 'troca', 'migração', 'alternativa']
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
    
    def is_refund_conversation(self, messages):
        """Check if conversation contains refund requests"""
        refund_keywords = [
            'reembolso', 'devolver', 'estorno', 'cancelar', 'cancelamento',
            'dinheiro de volta', 'quero meu dinheiro', 'desfazer compra'
        ]
        
        for msg in messages:
            message_text = msg.get('body', '').lower()
            if any(keyword in message_text for keyword in refund_keywords):
                return True
        return False
    
    def identify_refund_reason(self, messages):
        """Identify the main reason for refund request"""
        customer_messages = [msg for msg in messages if not msg.get('fromMe', False)]
        
        reason_scores = {category: 0 for category in self.refund_categories.keys()}
        
        for msg in customer_messages:
            message_text = msg.get('body', '').lower()
            
            for category, data in self.refund_categories.items():
                for keyword in data['keywords']:
                    if keyword in message_text:
                        reason_scores[category] += 1
        
        # Return the category with highest score
        if max(reason_scores.values()) > 0:
            return max(reason_scores, key=reason_scores.get)
        return 'unspecified'
    
    def extract_customer_sentiment_journey(self, messages):
        """Track customer sentiment throughout the conversation"""
        customer_messages = [msg for msg in messages if not msg.get('fromMe', False)]
        
        sentiment_journey = []
        
        # Sentiment indicators
        negative_words = ['irritado', 'chateado', 'decepcionado', 'frustrado', 'raiva', 'péssimo']
        positive_words = ['obrigado', 'gostei', 'bom', 'satisfeito', 'resolvido', 'perfeito']
        neutral_words = ['ok', 'entendi', 'certo', 'tudo bem']
        
        for i, msg in enumerate(customer_messages):
            message_text = msg.get('body', '').lower()
            
            sentiment = 'neutral'
            if any(word in message_text for word in negative_words):
                sentiment = 'negative'
            elif any(word in message_text for word in positive_words):
                sentiment = 'positive'
            
            sentiment_journey.append({
                'message_index': i,
                'sentiment': sentiment,
                'message': msg.get('body', '')[:100],
                'timestamp': msg.get('timestamp', '')
            })
        
        return sentiment_journey
    
    def identify_retention_attempts(self, messages):
        """Identify what retention strategies were used"""
        support_messages = [msg for msg in messages if msg.get('fromMe', False)]
        
        strategies_used = []
        
        for msg in support_messages:
            message_text = msg.get('body', '').lower()
            
            for strategy, keywords in self.retention_strategies_patterns.items():
                if any(keyword in message_text for keyword in keywords):
                    strategies_used.append({
                        'strategy': strategy,
                        'message': msg.get('body', ''),
                        'timestamp': msg.get('timestamp', '')
                    })
        
        return strategies_used
    
    def was_customer_retained(self, messages):
        """Determine if customer was successfully retained"""
        customer_messages = [msg for msg in messages if not msg.get('fromMe', False)]
        
        retention_indicators = [
            'vou continuar', 'obrigado pela ajuda', 'resolvido', 'vou tentar',
            'entendi', 'vou usar', 'ok, vou fazer', 'muito obrigado'
        ]
        
        refund_insistence = [
            'ainda quero reembolso', 'mesmo assim quero cancelar', 'não mudei de ideia',
            'quero meu dinheiro', 'vou cancelar mesmo'
        ]
        
        # Check last few messages for retention indicators
        recent_messages = customer_messages[-3:] if len(customer_messages) >= 3 else customer_messages
        
        for msg in recent_messages:
            message_text = msg.get('body', '').lower()
            
            if any(indicator in message_text for indicator in retention_indicators):
                return True
            if any(insistence in message_text for insistence in refund_insistence):
                return False
        
        return False  # Default to not retained if unclear
    
    def process_all_conversations(self, json_directory):
        """Process all JSON files to find and analyze refund conversations"""
        json_files = list(Path(json_directory).glob('*.json'))
        
        print(f"Processing {len(json_files)} conversation files for refund analysis...")
        
        for json_file in json_files:
            conversation_data = self.extract_conversations_from_json(json_file)
            
            if not conversation_data:
                continue
                
            messages = conversation_data.get('messages', [])
            
            if not messages:
                continue
            
            # Check if this is a refund conversation
            if self.is_refund_conversation(messages):
                refund_reason = self.identify_refund_reason(messages)
                sentiment_journey = self.extract_customer_sentiment_journey(messages)
                retention_attempts = self.identify_retention_attempts(messages)
                was_retained = self.was_customer_retained(messages)
                
                refund_analysis = {
                    'file': json_file.name,
                    'reason_category': refund_reason,
                    'sentiment_journey': sentiment_journey,
                    'retention_attempts': retention_attempts,
                    'was_retained': was_retained,
                    'messages': messages,
                    'customer_final_sentiment': sentiment_journey[-1]['sentiment'] if sentiment_journey else 'neutral'
                }
                
                self.refund_conversations.append(refund_analysis)
                self.refund_reasons[refund_reason].append(refund_analysis)
                
                # Track successful retention strategies
                if was_retained and retention_attempts:
                    for attempt in retention_attempts:
                        self.retention_strategies[attempt['strategy']].append(refund_analysis)
    
    def generate_refund_analysis_report(self, output_file='refund_analysis_knowledge_base.md'):
        """Generate comprehensive refund analysis report"""
        
        total_refunds = len(self.refund_conversations)
        total_retained = sum(1 for conv in self.refund_conversations if conv['was_retained'])
        overall_retention_rate = (total_retained / total_refunds * 100) if total_refunds > 0 else 0
        
        report = f"""# Refund Analysis & Customer Retention Knowledge Base

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Total Refund Requests Analyzed:** {total_refunds}
- **Successfully Retained Customers:** {total_retained}
- **Overall Retention Rate:** {overall_retention_rate:.1f}%
- **Analysis Period:** Based on WhatsApp conversation data

---

## 📊 Refund Reasons Analysis

"""
        
        # Analyze each refund category
        for category, conversations in self.refund_reasons.items():
            if not conversations:
                continue
                
            category_name = category.replace('_', ' ').title()
            category_total = len(conversations)
            category_retained = sum(1 for conv in conversations if conv['was_retained'])
            category_retention_rate = (category_retained / category_total * 100) if category_total > 0 else 0
            
            report += f"""### {category_name}

**Frequency:** {category_total} cases ({(category_total/total_refunds*100):.1f}% of all refunds)
**Retention Rate:** {category_retention_rate:.1f}% ({category_retained}/{category_total})
**Risk Level:** {'🔴 High' if category_retention_rate < 30 else '🟡 Medium' if category_retention_rate < 60 else '🟢 Low'}

#### Common Customer Complaints:
"""
            
            # Extract common complaints
            complaints = []
            for conv in conversations[:5]:  # Top 5 examples
                customer_msgs = [msg for msg in conv['messages'] if not msg.get('fromMe', False)]
                if customer_msgs:
                    first_complaint = customer_msgs[0].get('body', '')[:150]
                    complaints.append(first_complaint)
            
            for i, complaint in enumerate(complaints, 1):
                report += f"{i}. \"{complaint}{'...' if len(complaint) >= 150 else ''}\"\n"
            
            # Successful retention strategies for this category
            successful_strategies = defaultdict(int)
            for conv in conversations:
                if conv['was_retained']:
                    for attempt in conv['retention_attempts']:
                        successful_strategies[attempt['strategy']] += 1
            
            if successful_strategies:
                report += "\n#### ✅ Successful Retention Strategies:\n\n"
                for strategy, count in sorted(successful_strategies.items(), key=lambda x: x[1], reverse=True):
                    strategy_name = strategy.replace('_', ' ').title()
                    report += f"- **{strategy_name}:** {count} successful cases\n"
            
            report += "\n---\n\n"
        
        # Top retention strategies across all categories
        report += """## 🎯 Most Effective Retention Strategies

"""
        
        strategy_success_rates = {}
        for strategy, conversations in self.retention_strategies.items():
            total_attempts = len(conversations)
            successful_attempts = sum(1 for conv in conversations if conv['was_retained'])
            success_rate = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0
            strategy_success_rates[strategy] = {
                'success_rate': success_rate,
                'total_attempts': total_attempts,
                'successful_attempts': successful_attempts
            }
        
        # Sort by success rate
        sorted_strategies = sorted(strategy_success_rates.items(), key=lambda x: x[1]['success_rate'], reverse=True)
        
        for strategy, data in sorted_strategies:
            if data['total_attempts'] >= 3:  # Only show strategies used at least 3 times
                strategy_name = strategy.replace('_', ' ').title()
                report += f"""### {strategy_name}
**Success Rate:** {data['success_rate']:.1f}% ({data['successful_attempts']}/{data['total_attempts']} attempts)
**Effectiveness:** {'🏆 Highly Effective' if data['success_rate'] >= 70 else '✅ Effective' if data['success_rate'] >= 50 else '⚠️ Needs Improvement'}

"""
                
                # Show example of successful use
                successful_examples = [conv for conv in self.retention_strategies[strategy] if conv['was_retained']]
                if successful_examples:
                    example = successful_examples[0]
                    for attempt in example['retention_attempts']:
                        if attempt['strategy'] == strategy:
                            report += f"**Example Response:** \"{attempt['message'][:200]}{'...' if len(attempt['message']) > 200 else ''}\"\n\n"
                            break
                
                report += "---\n\n"
        
        # Customer journey analysis
        report += """## 🛤️ Customer Sentiment Journey Analysis

### Typical Sentiment Progression:

"""
        
        # Analyze sentiment patterns
        sentiment_patterns = defaultdict(list)
        for conv in self.refund_conversations:
            journey = conv['sentiment_journey']
            if len(journey) >= 2:
                start_sentiment = journey[0]['sentiment']
                end_sentiment = journey[-1]['sentiment']
                pattern = f"{start_sentiment} → {end_sentiment}"
                sentiment_patterns[pattern].append(conv['was_retained'])
        
        for pattern, outcomes in sentiment_patterns.items():
            if len(outcomes) >= 3:  # Only show patterns with at least 3 cases
                retention_rate = (sum(outcomes) / len(outcomes) * 100)
                report += f"- **{pattern}:** {len(outcomes)} cases, {retention_rate:.1f}% retention rate\n"
        
        # Action plan
        report += f"""\n---\n\n## 🎯 Action Plan for Customer Retention

### Immediate Actions (High Priority):

1. **Focus on High-Risk Categories:**
   - Implement proactive support for categories with <50% retention rate
   - Create specific response templates for each refund reason

2. **Scale Successful Strategies:**
   - Train support team on top-performing retention techniques
   - Create standard operating procedures for each strategy

3. **Early Intervention:**
   - Identify customers at risk before they request refunds
   - Implement satisfaction check-ins at key journey points

### Long-term Improvements:

1. **Product/Service Enhancements:**
   - Address root causes of most common refund reasons
   - Improve onboarding process to set proper expectations

2. **Support Process Optimization:**
   - Reduce response time for technical issues
   - Implement escalation procedures for complex cases

3. **Customer Success Program:**
   - Proactive outreach to ensure customer success
   - Regular check-ins and value demonstration

---

## 📋 Retention Response Templates

### For Technical Issues:
\"Entendo sua frustração com o problema técnico. Vou resolver isso imediatamente para você. Nossa equipe técnica já está trabalhando nisso e vou garantir que você tenha acesso completo hoje mesmo. Posso também oferecer [specific solution/bonus] como forma de compensar o inconveniente.\"

### For Content Quality Concerns:
\"Agradeço seu feedback sobre o conteúdo. Quero entender melhor suas expectativas para garantir que você tenha a melhor experiência. Posso oferecer acesso a [additional content/mentoring] que pode ser mais alinhado com o que você está buscando.\"

### For Financial Difficulties:
\"Entendo sua situação e queremos ajudar. Posso oferecer um plano de pagamento mais flexível ou pausar temporariamente sua assinatura até que sua situação melhore. Nosso objetivo é que você tenha sucesso conosco.\"

---

*This analysis is based on real customer conversations and should be updated regularly to reflect current trends.*
"""
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Refund analysis report generated: {output_file}")
        
        # Generate JSON data for AI training
        training_data = {
            'refund_categories': {},
            'retention_strategies': {},
            'response_templates': {}
        }
        
        for category, conversations in self.refund_reasons.items():
            if conversations:
                training_data['refund_categories'][category] = {
                    'total_cases': len(conversations),
                    'retention_rate': sum(1 for conv in conversations if conv['was_retained']) / len(conversations),
                    'common_phrases': list(set([msg.get('body', '')[:100] for conv in conversations for msg in conv['messages'] if not msg.get('fromMe', False)]))[:10]
                }
        
        for strategy, data in strategy_success_rates.items():
            if data['total_attempts'] >= 3:
                training_data['retention_strategies'][strategy] = data
        
        with open('refund_analysis_training_data.json', 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)
        
        print("\nSummary Statistics:")
        print(f"Total refund conversations: {total_refunds}")
        print(f"Overall retention rate: {overall_retention_rate:.1f}%")
        print(f"Most common refund reason: {max(self.refund_reasons.keys(), key=lambda k: len(self.refund_reasons[k])) if self.refund_reasons else 'None'}")
        print(f"Most effective retention strategy: {max(strategy_success_rates.keys(), key=lambda k: strategy_success_rates[k]['success_rate']) if strategy_success_rates else 'None'}")

def main():
    analyzer = RefundAnalysisKnowledgeBase()
    
    # Process all JSON files in the Json directory
    json_directory = "Json"
    
    if not os.path.exists(json_directory):
        print(f"Error: {json_directory} directory not found!")
        return
    
    analyzer.process_all_conversations(json_directory)
    analyzer.generate_refund_analysis_report('refund_analysis_knowledge_base.md')

if __name__ == "__main__":
    main()