import pandas as pd
from sqlalchemy import create_engine, text, inspect
import clevercsv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

class DataProcessor:
    def __init__(self, file):
        try:
            # First ensure database exists
            self.create_database_if_not_exists()
            
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

    def create_database_if_not_exists(self):
        try:
            # Connect to default PostgreSQL database
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="samplepass",
                host="localhost",
                port="5432"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'retail_data'")
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute('CREATE DATABASE retail_data')
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            raise ValueError(f"Error creating database: {str(e)}")

    def create_table_if_not_exists(self):
        try:
            inspector = inspect(self.engine)
            if not inspector.has_table('retail_ingest_data'):
                # Create table with appropriate columns based on DataFrame
                create_table_query = """
                CREATE TABLE retail_ingest_data (
                    id SERIAL PRIMARY KEY
                """
                
                for column in self.df.columns:
                    if column.lower() in ['quantity', 'price', 'unit_price', 'total_amount', 'totalamount']:
                        create_table_query += f",\n    {column} NUMERIC"
                    else:
                        create_table_query += f",\n    {column} TEXT"
                
                create_table_query += "\n);"
                
                with self.engine.connect() as connection:
                    connection.execute(text(create_table_query))
                    connection.commit()
                
        except Exception as e:
            raise ValueError(f"Error creating table: {str(e)}")

    def process_data(self):
        try:
            # Ensure table exists
            self.create_table_if_not_exists()
            
            # Insert or replace data
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