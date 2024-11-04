import streamlit as st
from data_processor import DataProcessor
from llm_handler import LLMHandler
from visualization_handler import VisualizationHandler

def main():
    st.set_page_config(page_title="Retail Insight Generator", layout="wide")
    
    # Minimal CSS just for spacing and layout
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("📊 Retail Insight Generator")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.header("📁 Data Upload")
        uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
        st.markdown("---")
        st.markdown("### 💡 Tips")
        st.markdown("""
        - Upload a retail CSV file
        - Ask questions about your data
        - Get insights with visualizations
        """)

    if uploaded_file is not None:
        try:
            data_processor = DataProcessor(uploaded_file)
            data_processor.process_data()
            llm_handler = LLMHandler()
            viz_handler = VisualizationHandler()
            
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if "visualization" in message:
                        st.plotly_chart(message["visualization"], use_container_width=True)
            
            if prompt := st.chat_input("💭 Ask a question about your data..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    try:
                        with st.spinner("🤔 Analyzing data..."):
                            schema_info = data_processor.get_schema()
                            insights = llm_handler.generate_insights(prompt, schema_info)
                            
                            if insights.get('sql_query') and insights.get('sql_query').lower() != 'none':
                                results = data_processor.execute_analysis_query(insights['sql_query'])
                                final_insights = llm_handler.generate_insights(
                                    prompt, schema_info, results.to_markdown()
                                )
                                
                                fig = None
                                if final_insights.get('visualization') and final_insights['visualization']['type'] != 'none':
                                    fig = viz_handler.create_visualization(results, final_insights['visualization'])
                                
                                answer = final_insights.get('answer', 'No insights generated.')
                                st.markdown(answer)
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                message_data = {
                                    "role": "assistant",
                                    "content": answer
                                }
                                if fig:
                                    message_data["visualization"] = fig
                                st.session_state.messages.append(message_data)
                            
                            else:
                                answer = insights.get('answer', 'Unable to generate insights.')
                                st.markdown(answer)
                                st.session_state.messages.append({"role": "assistant", "content": answer})
                                
                    except Exception as e:
                        st.error(f"❌ Analysis error: {str(e)}")

        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    else:
        st.info("👆 Please upload a CSV file to get started!")

if __name__ == "__main__":
    main()