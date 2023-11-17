import openai
import re
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from textwrap import wrap

from prompts import get_system_prompt

st.title("🤿 Retail Data Diver")

def wrap_labels(labels, max_length=10):
    """Wrap labels if they exceed a maximum length."""
    wrapped_labels = [label if len(label) <= max_length else '\n'.join(wrap(label, max_length)) for label in labels]
    return wrapped_labels




# Initialize the chat messages history
openai.api_key = st.secrets.OPENAI_API_KEY
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": get_system_prompt()}]


# Prompt for user input and save
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

with st.expander("Chat History"):
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            # Display icon based on the role
            st.write(f"{(message['role'])} {message['content']}")
            if "results" in message:
                st.dataframe(message["results"])

# If the last message is not from the assistant, we need to generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        response = ""
        resp_container = st.empty()
        for delta in openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        ):
            response += delta.choices[0].delta.get("content", "")
            resp_container.markdown(response)

        message = {"role": "assistant", "content": response}
        sql_match = re.search(r"```sql\n(.*)\n```", response, re.DOTALL)
        if sql_match:
            sql = sql_match.group(1)
            conn = st.experimental_connection("snowpark")
            message["results"] = conn.query(sql)

            st.dataframe(message["results"])
            df = message["results"]
            st.download_button(
                "Download Results",
                df.to_csv().encode('utf-8'),
                "BigSupplyCo.csv",
                "text/csv",
                key='download-csv'
            )

            

    

            # Plotting section
            if (
                message["results"] is not None and
                message["results"].shape[0] >= 3 and
                message["results"].shape[0] <= 7 and
                message["results"].shape[1] >= 2 and
                all(isinstance(value, (int, float)) for value in message["results"].iloc[:, 1])
            ):
                # Sort the DataFrame in descending order based on the second column
                sorted_df = message["results"].sort_values(by=message["results"].columns[1], ascending=False)

                category_column = sorted_df.columns[0]
                value_column = sorted_df.columns[1]

                fig, ax = plt.subplots(figsize=(8, 6))
                bars = ax.bar(sorted_df.iloc[:, 0], sorted_df.iloc[:, 1], color='turquoise')
                ax.set_xticklabels(wrap_labels(sorted_df.iloc[:, 0]), rotation=5, ha='right')

                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{int(height)}',  # Rounded to zero decimal places
                                xy=(bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3),
                                textcoords="offset points", ha='center', va='bottom')

                ax.yaxis.set_visible(False)

                plt.xlabel(category_column)  # Set x-axis label dynamically
                chart_title = f"Bar Chart of {value_column} by {category_column}"  # Dynamic title
                plt.title(chart_title)  # Set title dynamically
                plt.xticks(rotation=5, ha='right')
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.write("No valid data available for plotting or too many rows for a bar chart.")

          
            st.session_state.messages.append(message)
