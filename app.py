import streamlit as st
from data_processor import DataProcessor
from llm_handler import LLMHandler

def main():
    st.title("Retail Insight Generator")
    
    # Add custom CSS for better message formatting
    st.markdown("""
        <style>
        .stChatMessage {
            padding: 1rem;
            line-height: 1.5;
            white-space: pre-wrap;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            data_processor = DataProcessor(uploaded_file)
            data_processor.process_data()
            llm_handler = LLMHandler()
            
            # Display chat history
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            if prompt := st.chat_input("Ask a question about your data"):
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                with st.chat_message("assistant"):
                    try:
                        with st.spinner("Analyzing data..."):
                            schema_info = data_processor.get_schema()
                            insights = llm_handler.generate_insights(prompt, schema_info)
                            
                            if insights.get('sql_query') and insights.get('sql_query').lower() != 'none':
                                results = data_processor.execute_analysis_query(insights['sql_query'])
                                final_insights = llm_handler.generate_insights(
                                    prompt, schema_info, results.to_markdown()
                                )
                                answer = final_insights.get('answer', 'No insights generated.')
                                st.markdown(answer)
                                # Add assistant response to chat history
                                st.session_state.messages.append({"role": "assistant", "content": answer})
                            else:
                                answer = insights.get('answer', 'Unable to generate insights.')
                                st.markdown(answer)
                                # Add assistant response to chat history
                                st.session_state.messages.append({"role": "assistant", "content": answer})
                                
                    except Exception as e:
                        st.error(f"Analysis error: {str(e)}")
                        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()