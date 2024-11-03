import g4f
import json
from json_repair import repair_json
from typing import Dict, Optional

class LLMHandler:
    def __init__(self):
        g4f.debug.logging = False
        g4f.check_version = False
        
    def generate_insights(self, question: str, schema_info: Dict, query_results: Optional[Dict] = None) -> Dict:
        columns_detail = schema_info.get('columns_detail', [])
        
        base_prompt = f"""You are a data analyst. Analyze this PostgreSQL database:

Table: retail_ingest_data
Available Columns with Types:
{chr(10).join(columns_detail)}

Sample Data:
{schema_info.get('sample_data', 'No sample data available')}

CRITICAL RULES:
1. ONLY use columns from the list above
2. If the available columns are insufficient to answer the question, clearly state that
3. Keep answers concise and focused
4. For numeric calculations, CAST string columns to NUMERIC using CAST(column_name AS NUMERIC)
5. Table name is exactly 'retail_ingest_data'

Question: {question}

Respond in this JSON format:
{{
    "sql_query": "Your PostgreSQL query here (or 'None' if columns are insufficient)",
    "answer": "Clear, concise answer or explanation why the question cannot be answered"
}}"""

        if query_results is not None:
            base_prompt += f"\n\nQuery Results:\n{query_results}"

        print("\nPrompt sent to LLM:")
        print(base_prompt)
            
        try:
            response = g4f.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": base_prompt}],
                temperature=0.4,
                stream=False
            )
            
            print("\nLLM Response:")
            print(response)
            
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                cleaned_response = repair_json(response)
                result = json.loads(cleaned_response)
            
            return result
            
        except Exception as e:
            raise ValueError(f"Error generating insights: {str(e)}")