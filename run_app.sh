#!/bin/bash
# Startup script for Used Car Recommendation System

echo "========================================="
echo "Used Car Recommendation System"
echo "========================================="
echo ""

# Check if data exists
if [ ! -f "data/integrated_cars.csv" ]; then
    echo "⚠️  Integrated data not found. Running data integration..."
    python3 src/data_integration.py
    echo ""
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip3 install pandas numpy rdflib matplotlib streamlit scikit-learn --break-system-packages --quiet 2>/dev/null

echo "✅ Dependencies ready"
echo ""
echo "🚀 Starting Streamlit app..."
echo "   Open your browser to: http://localhost:8501"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""

streamlit run app.py
