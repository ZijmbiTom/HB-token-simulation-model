import streamlit as st
import pandas as pd
import numpy as np

st.title('My Enhanced Streamlit App')

# Adding a header and subheader
st.header('Introduction')
st.subheader('This app demonstrates advanced features of Streamlit.')

# Adding interactive widgets
option = st.selectbox(
    'Which number do you like best?',
    [1, 2, 3, 4, 5]
)

st.write('You selected:', option)

# Adding a slider
slider_value = st.slider('Select a range of values', 0.0, 100.0, (25.0, 75.0))
st.write('Slider range:', slider_value)

# Displaying a DataFrame
df = pd.DataFrame({
    'first column': list(range(1, 11)),
    'second column': np.random.randn(10)
})

st.write('DataFrame example:')
st.dataframe(df)

# Adding a chart
st.line_chart(df['second column'])

# Using markdown for documentation
st.markdown("""
    ## Usage
    - Select your favorite number from the dropdown.
    - Use the slider to select a range of values.
    - View the data in the DataFrame and the chart.
""")
