import pandas as pd
from sqlalchemy import create_engine, text
import clevercsv

class DataProcessor:
    def __init__(self, file):
        try:
            # Read file content
            content = file.read().decode('utf-8')
            file.seek(0)  # Reset file pointer
            
            # Use CleverCSV to detect dialect
            dialect = clevercsv.Sniffer().sniff(content)
            reader = clevercsv.reader(content.splitlines(), dialect)
            
            # Skip header
            headers = next(reader)
            data = list(reader)
            
            # Remove any header-like rows from data
            data = [row for row in data if not any(cell.lower() in ['order_id', 'date', 'product_name', 'total_amount'] for cell in row)]
            
            # Convert to DataFrame
            self.df = pd.DataFrame(data, columns=headers)
            
            # Clean column names
            self.df.columns = [str(col).strip().lower().replace(' ', '_') for col in self.df.columns]
            
            # Convert numeric columns
            numeric_columns = ['quantity', 'price', 'unit_price', 'total_amount', 'totalamount']
            for col in self.df.columns:
                if col in numeric_columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            
            # Initialize PostgreSQL database connection
            self.engine = create_engine('postgresql://postgres:samplepass@localhost:5432/retail_data')
            
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")

    def process_data(self):
        try:
            self.df.to_sql('retail_ingest_data', self.engine, if_exists='replace', index=False)
            self.column_types = {col: str(dtype) for col, dtype in self.df.dtypes.items()}
        except Exception as e:
            raise ValueError(f"Error processing data: {str(e)}")

    def get_schema(self):
        try:
            # Get actual data types
            self.column_types = {
                col: ('numeric' if pd.api.types.is_numeric_dtype(dtype) else 'text') 
                for col, dtype in self.df.dtypes.items()
            }
            
            return {
                "columns": list(self.df.columns),
                "column_types": self.column_types,
                "sample_data": self.df.head(3).to_markdown(index=False),
                "columns_detail": [f"{col} ({dtype})" for col, dtype in self.column_types.items()]
            }
        except Exception as e:
            raise ValueError(f"Error getting schema: {str(e)}")

    def execute_analysis_query(self, query):
        try:
            return pd.read_sql(text(query), self.engine)
        except Exception as e:
            raise ValueError(f"Error executing SQL query: {str(e)}")