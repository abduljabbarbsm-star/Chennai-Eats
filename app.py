from flask import Flask, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Load the dataset
CSV_PATH = os.path.join('data', 'restaurants.csv')

def load_data():
    df = pd.read_csv(CSV_PATH)
    # Ensure numeric columns are handled
    df['price'] = pd.to_numeric(df['price'])
    df['rating'] = pd.to_numeric(df['rating'])
    df['popularity_score'] = pd.to_numeric(df['popularity_score'])
    return df

@app.route('/')
def index():
    df = load_data()
    # Get distinct restaurants with their overall rating and location
    restaurants = df.groupby('restaurant_name').agg({
        'rating': 'mean',
        'location': 'first',
        'category': lambda x: 'Veg/Non-Veg' if ('veg' in x.values and 'non-veg' in x.values) else ('Veg' if 'veg' in x.values else 'Non-Veg')
    }).reset_index()
    restaurants['rating'] = restaurants['rating'].round(1)
    
    # Sort for the "Top 5" but show all on homepage if needed, 
    # Swiggy usually shows a list of all active top restaurants.
    top_restaurants = restaurants.sort_values(by='rating', ascending=False).to_dict('records')
    
    return render_template('index.html', restaurants=top_restaurants)

@app.route('/restaurant/<name>')
def restaurant_details(name):
    df = load_data()
    restaurant_items = df[df['restaurant_name'] == name].to_dict('records')
    details = {
        'name': name,
        'location': restaurant_items[0]['location'],
        'rating': round(sum(i['rating'] for i in restaurant_items) / len(restaurant_items), 1),
        'category': 'Veg/Non-Veg' if any(i['category'] == 'veg' for i in restaurant_items) and any(i['category'] == 'non-veg' for i in restaurant_items) else ('Veg' if any(i['category'] == 'veg' for i in restaurant_items) else 'Non-Veg')
    }
    return render_template('restaurant.html', details=details, items=restaurant_items)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/analytics')
def analytics_data():
    df = load_data()
    
    # 1. Top 5 Restaurants based on Rating and Popularity
    df['composite_score'] = (df['rating'] * 0.6) + (df['popularity_score'] * 0.04)
    top_5 = df.groupby('restaurant_name')['composite_score'].mean().sort_values(ascending=False).head(5).reset_index()
    
    # 2. Top Selling Dishes (Top items by popularity score)
    top_dishes = df.sort_values(by='popularity_score', ascending=False).head(5)[['food_item', 'popularity_score']].to_dict('records')
    
    # 3. Veg vs Non-Veg Distribution
    veg_dist = df['category'].value_counts().to_dict()
    
    # 4. Average Price Comparison
    avg_price = df.groupby('restaurant_name')['price'].mean().round(2).to_dict()
    
    return jsonify({
        'top_restaurants': top_5.to_dict('records'),
        'top_dishes': top_dishes,
        'veg_dist': veg_dist,
        'avg_price': avg_price
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
