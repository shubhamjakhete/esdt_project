"""
Streamlit web interface for the car recommendation system
Run with: streamlit run app.py

CPSC 583 Project
Authors: Cameron Potvin, Shubham Jakhete, Jaiveer Kapadia
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / 'src'))

from recommendation_engine import CarRecommendationEngine

def format_prolog_explanation(pick):
    
    # get strengths that were computed by Prolog
    strengths = pick.get('prolog_strengths', [])

    if strengths:
        return "Prolog reasoning: " + ", ".join(strengths[:4]) + "."
    else:
        # fallback if Prolog not available
        cats = pick.get('prolog_categories', [])
        if cats and cats != ['uncategorized']:
            return f"Classified as: {', '.join(cats)}"
        return "Meets your search criteria."

st.set_page_config(
    page_title="Car Recommendation System",
    page_icon="🚗",
    layout="wide"
)

@st.cache_resource
def load_engine():
    """Cache the engine so we don't reload data every time"""
    return CarRecommendationEngine()


def main():
    st.title("Used Car Recommendation System")
    st.write("CPSC 583 Project - Potvin, Jakhete, Kapadia")
    
    # sidebar for user input
    st.sidebar.header("Search Preferences")
    
    max_price = st.sidebar.number_input(
        "Max Price ($)",
        min_value=5000,
        max_value=100000,
        value=25000,
        step=1000
    )
    
    min_year = st.sidebar.slider("Min Year", 2010, 2024, 2016)
    max_year = st.sidebar.slider("Max Year", 2010, 2024, 2024)
    
    min_safety = st.sidebar.slider(
        "Min Safety Rating",
        min_value=1.0,
        max_value=5.0,
        value=4.0,
        step=0.5
    )
    
    min_reliability = st.sidebar.slider(
        "Min Reliability",
        min_value=0.0,
        max_value=1.0,
        value=0.75,
        step=0.05
    )
    
    max_mileage = st.sidebar.number_input(
        "Max Mileage",
        min_value=0,
        max_value=200000,
        value=80000,
        step=5000
        
    )
    
    ownership_years = st.sidebar.slider(
        "Ownership Period (years)",
        min_value=1,
        max_value=10,
        value=5,
        step=1
    )

    
    top_n = st.sidebar.slider("Number of Results", 5, 20, 10)
    
    # main content 
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("About")
        st.write("""
        This system uses knowledge representation techniques to find you a good used car:

        1. **Prolog Logic Programming** - Expert rules classify cars into categories
        2. **RDF/OWL Ontology + SPARQL** - Semantic knowledge graph queries

        Plus propositional logic for filtering and probabilistic methods for reliability.
        """)
    
    with col2:
        st.subheader("Dataset Stats")
        try:
            engine = load_engine()
            if engine.df is not None and len(engine.df) > 0:
                st.metric("Total Vehicles", f"{len(engine.df):,}")
                st.metric("Makes", engine.df['make'].nunique())
            else:
                st.warning("No data loaded")
        except Exception as e:
            st.error(f"Error: {e}")
    
    # search button
    if st.button("Find Recommendations", type="primary"):
        
        preferences = {
            'max_price': max_price,
            'min_year': min_year,
            'max_year': max_year,
            'min_safety': min_safety,
            'min_reliability': min_reliability,
            'max_mileage': max_mileage,
            'year': ownership_years
        }
        
        with st.spinner("Running analysis..."):
            try:
                engine = load_engine()
                recs, explanations = engine.get_recommendations(preferences, top_n=top_n)
                
                if recs.empty:
                    st.warning(explanations.get('message', 'No results found - try relaxing your constraints'))
                else:
                    # show methodology (collapsed by default)
                    with st.expander("How it works"):
                        st.text(explanations['methodology'])
                        if 'ontology_stats' in explanations:
                            stats = explanations['ontology_stats']
                            st.info(f"Ontology: {stats.get('vehicles', 0)} vehicles, {stats.get('total_triples', 0)} triples")
                    
                    st.subheader(f"Top {len(explanations['top_picks'])} Recommendations")
                    
                    for i, pick in enumerate(explanations['top_picks'], 1):
                        st.markdown(f"### {i}. {pick['vehicle']}")

                        c1, c2, c3 = st.columns(3)
                        c1.metric("Score", pick['score'])
                        cats = pick.get('prolog_categories', ['uncategorized'])
                        c2.write(f"**Category:** {', '.join(cats)}")
                        
                        # get car data from dataframe
                        car_data = None
                        try:
                            parts = pick['vehicle'].split()
                            year = int(parts[0])
                            make = parts[1]
                            car_row = recs[(recs['year'] == year) & (recs['make'] == make)]
                            if len(car_row) > 0:
                                c3.metric("Price", f"${car_row.iloc[0]['price']:,.0f}")
                                car_data = car_row.iloc[0].to_dict()
                        except:
                            pass

                        col_a, col_b = st.columns(2)

                        with col_a:
                            st.write(f"**Safety:** {pick['safety']}")
                            st.write(f"**Reliability:** {pick['reliability']}")
                        
                        with col_b:
                            resale = pick.get('resale_value', "n/a")
                            if resale != "n/a":
                                st.write(f"**Est. resale after {preferences['year']} years:** {resale}")
                            else:
                                st.write("**Est. resale:** n/a")

                        # show explanation from Prolog reasoning
                        explanation = format_prolog_explanation(pick)
                        st.info(explanation)

                        st.divider()
                    
                    # full results table
                    st.subheader("All Results")
                    
                    cols_to_show = ['make', 'model', 'year', 'price', 'overall_rating', 
                                   'reliability_score', 'expected_resale_value', 'final_score']
                    display_df = recs[[c for c in cols_to_show if c in recs.columns]]
                    
                    st.dataframe(display_df, width='stretch', hide_index=True)
                    
                    # download button
                    csv = recs.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        "recommendations.csv",
                        "text/csv"
                    )
                    
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.exception(e)


if __name__ == '__main__':
    main()
