import streamlit as st

st.title("Welkom bij Streamlit!")
st.write("Dit is een eenvoudige test om te controleren of Streamlit werkt.")

slider_value = st.slider("Verplaats de schuifregelaar:", 0, 100, 50)
st.write(f"De waarde van de schuifregelaar is: {slider_value}")
