import pandas as pd
import io
import csv
import re
import numpy as np
from datetime import datetime

def process_inventory_data(inventory_file):
    """
    Process the inventory data CSV file
    
    Args:
        inventory_file: The uploaded inventory CSV file
    
    Returns:
        pandas.DataFrame: Processed inventory data
    """
    try:
        # Read the CSV file
        df = pd.read_csv(inventory_file, encoding='utf-8', delimiter=',')
        
        # Fix column names and clean data
        df.columns = [col.strip() for col in df.columns]
        
        # Extract relevant columns and rename
        inventory_data = pd.DataFrame({
            'ingredient_name': df['Zutat'],
            'current_stock_ml': df['Lagerbestand (ml)'].replace('', 0).fillna(0),
            'price_per_liter': df['Einkaufspreis pro Liter (EUR)'].replace('', 0).fillna(0),
            'target_stock_ml': df['Soll-Lagerbestand in Flaschen für 50 Drinks'].replace('', 0).fillna(0)
        })
        
        # Convert columns to numeric, handling European number format
        for col in ['current_stock_ml', 'price_per_liter', 'target_stock_ml']:
            inventory_data[col] = inventory_data[col].astype(str).str.replace(',', '.').astype(float)
        
        # Remove rows with missing ingredient names
        inventory_data = inventory_data[inventory_data['ingredient_name'].notna() & 
                                        (inventory_data['ingredient_name'] != '')]
        
        return inventory_data
    
    except Exception as e:
        raise Exception(f"Error processing inventory data: {str(e)}")

def process_recipe_data(recipe_file):
    """
    Process the recipe data CSV file
    
    Args:
        recipe_file: The uploaded recipe CSV file
    
    Returns:
        pandas.DataFrame: Processed recipe data
    """
    try:
        # Read the CSV file
        df = pd.read_csv(recipe_file, encoding='utf-8', delimiter=',')
        
        # Fix column names and clean data
        df.columns = [col.strip() for col in df.columns]
        
        # Create a standardized dataframe
        recipe_data = pd.DataFrame({
            'drink_name': df['Getränkename'],
            'ingredient_name': df['Zutat'],
            'amount_ml': df['Menge pro Drink (ml/cl)']
        })
        
        # Convert amount column to numeric, handling different formats
        recipe_data['amount_ml'] = recipe_data['amount_ml'].astype(str).str.replace(',', '.').astype(float)
        
        return recipe_data
    
    except Exception as e:
        raise Exception(f"Error processing recipe data: {str(e)}")

def process_sales_data(sales_file):
    """
    Process the daily sales report CSV file
    
    Args:
        sales_file: The uploaded sales CSV file
    
    Returns:
        dict: Processed sales data with date, total, and products
    """
    try:
        # Read the content of the file
        content = sales_file.read().decode('utf-8')
        
        # Parse the CSV content using csv module with custom dialect
        reader = csv.reader(io.StringIO(content), delimiter=';')
        rows = list(reader)
        
        # Extract date from line 2
        date_row = rows[1] if len(rows) > 1 else []
        date_str = date_row[2] if len(date_row) > 2 else "Unknown"
        
        # Try to parse the date
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y")
            date_formatted = date_obj.strftime("%Y-%m-%d")
        except:
            date_formatted = date_str
        
        # Initialize result dictionary
        result = {
            'date': date_formatted,
            'total_sales': 0,
            'products': []
        }
        
        # Extract products from the "Produkte" section - should start around line 80
        products_section_start = None
        
        for i, row in enumerate(rows):
            if len(row) > 0 and row[0] == "Produkte":
                products_section_start = i + 2  # +2 to skip header row
                break
        
        if products_section_start is not None:
            # Read product data
            for i in range(products_section_start, len(rows)):
                row = rows[i]
                if len(row) < 6 or not row[0]:  # Stop when we reach an empty row
                    break
                
                # Extract product name, quantity, and total
                product_name = row[1]
                quantity_str = row[2]
                total_str = row[3]
                
                # Clean and convert values
                if product_name and quantity_str and total_str:
                    try:
                        quantity = int(quantity_str)
                        total = float(total_str.replace('.', '').replace(',', '.'))
                        
                        result['products'].append({
                            'product_name': product_name,
                            'quantity': quantity,
                            'total': total
                        })
                        
                        result['total_sales'] += total
                    except (ValueError, TypeError):
                        pass  # Skip rows with invalid data
        
        return result
    
    except Exception as e:
        raise Exception(f"Error processing sales data: {str(e)}")

def update_inventory_based_on_sales(inventory_data, recipe_data, sales_data):
    """
    Update inventory based on sales data
    
    Args:
        inventory_data: Current inventory DataFrame
        recipe_data: Recipe DataFrame
        sales_data: Sales data dictionary
    
    Returns:
        pandas.DataFrame: Updated inventory data
    """
    try:
        # Create a copy of the inventory data to avoid modifying the original
        updated_inventory = inventory_data.copy()
        
        # Get the products from sales data
        products = sales_data.get('products', [])
        
        # Track ingredients that couldn't be found
        missing_ingredients = []
        
        # Process each sold product
        for product in products:
            product_name = product['product_name']
            quantity_sold = product['quantity']
            
            # Find recipes for this product
            product_recipes = recipe_data[recipe_data['drink_name'] == product_name]
            
            if not product_recipes.empty:
                # Process each ingredient in the recipe
                for _, recipe_row in product_recipes.iterrows():
                    ingredient_name = recipe_row['ingredient_name']
                    amount_per_drink = recipe_row['amount_ml']
                    
                    # Find the ingredient in inventory
                    ingredient_idx = updated_inventory[updated_inventory['ingredient_name'] == ingredient_name].index
                    
                    if len(ingredient_idx) > 0:
                        # Calculate total amount used
                        total_amount_used = amount_per_drink * quantity_sold
                        
                        # Update inventory
                        current_stock = updated_inventory.at[ingredient_idx[0], 'current_stock_ml']
                        new_stock = max(0, current_stock - total_amount_used)
                        updated_inventory.at[ingredient_idx[0], 'current_stock_ml'] = new_stock
                    else:
                        missing_ingredients.append(ingredient_name)
            
        # Report if any ingredients were missing
        if missing_ingredients:
            missing_unique = list(set(missing_ingredients))
            print(f"Warning: Could not find these ingredients in inventory: {', '.join(missing_unique)}")
        
        return updated_inventory
    
    except Exception as e:
        print(f"Error updating inventory: {str(e)}")
        return None

def calculate_drink_costs(recipe_data, inventory_data):
    """
    Calculate the cost of each drink based on its ingredients
    
    Args:
        recipe_data: Recipe DataFrame
        inventory_data: Inventory DataFrame
    
    Returns:
        pandas.DataFrame: DataFrame with drink costs
    """
    try:
        # Create a dictionary to store drink costs
        drink_costs = {}
        
        # Get unique drink names
        unique_drinks = recipe_data['drink_name'].unique()
        
        # Calculate cost for each drink
        for drink_name in unique_drinks:
            # Get all ingredients for this drink
            drink_ingredients = recipe_data[recipe_data['drink_name'] == drink_name]
            
            total_cost = 0
            cost_breakdown = []
            
            # Calculate cost for each ingredient
            for _, ingredient_row in drink_ingredients.iterrows():
                ingredient_name = ingredient_row['ingredient_name']
                amount_ml = ingredient_row['amount_ml']
                
                # Find the ingredient in inventory
                ingredient_info = inventory_data[inventory_data['ingredient_name'] == ingredient_name]
                
                if not ingredient_info.empty:
                    # Get the price per liter and convert to price per ml
                    price_per_liter = ingredient_info['price_per_liter'].values[0]
                    price_per_ml = price_per_liter / 1000  # Convert to price per ml
                    
                    # Calculate cost for this ingredient
                    ingredient_cost = amount_ml * price_per_ml
                    total_cost += ingredient_cost
                    
                    cost_breakdown.append({
                        'ingredient_name': ingredient_name,
                        'amount_ml': amount_ml,
                        'cost': ingredient_cost
                    })
            
            # Store the total cost and breakdown
            drink_costs[drink_name] = {
                'total_cost': total_cost,
                'cost_breakdown': cost_breakdown
            }
        
        # Convert to DataFrame
        cost_df = pd.DataFrame([
            {'drink_name': drink_name, 'total_cost': data['total_cost']}
            for drink_name, data in drink_costs.items()
        ])
        
        return cost_df
    
    except Exception as e:
        print(f"Error calculating drink costs: {str(e)}")
        return None

def calculate_available_drinks(recipe_data, inventory_data):
    """
    Calculate how many of each drink can be made based on current inventory
    
    Args:
        recipe_data: Recipe DataFrame
        inventory_data: Inventory DataFrame
    
    Returns:
        pandas.DataFrame: DataFrame with available drink counts
    """
    try:
        # Create a dictionary to store available drink counts
        available_drinks = {}
        
        # Get unique drink names
        unique_drinks = recipe_data['drink_name'].unique()
        
        # Calculate available drinks for each drink type
        for drink_name in unique_drinks:
            # Get all ingredients for this drink
            drink_ingredients = recipe_data[recipe_data['drink_name'] == drink_name]
            
            max_drinks_possible = float('inf')  # Start with "infinite" drinks possible
            limiting_ingredient = None
            
            # Check each ingredient
            for _, ingredient_row in drink_ingredients.iterrows():
                ingredient_name = ingredient_row['ingredient_name']
                amount_needed = ingredient_row['amount_ml']
                
                # Find the ingredient in inventory
                ingredient_info = inventory_data[inventory_data['ingredient_name'] == ingredient_name]
                
                if not ingredient_info.empty:
                    # Get current stock
                    current_stock = ingredient_info['current_stock_ml'].values[0]
                    
                    # Calculate how many drinks can be made with this ingredient
                    if amount_needed > 0:  # Avoid division by zero
                        drinks_possible = current_stock / amount_needed
                        
                        # Update the maximum number of drinks if this ingredient is limiting
                        if drinks_possible < max_drinks_possible:
                            max_drinks_possible = drinks_possible
                            limiting_ingredient = ingredient_name
                else:
                    # If ingredient not found, we can't make any drinks
                    max_drinks_possible = 0
                    limiting_ingredient = f"{ingredient_name} (not in inventory)"
                    break
            
            # Store the results
            available_drinks[drink_name] = {
                'max_drinks_possible': int(max_drinks_possible),
                'limiting_ingredient': limiting_ingredient
            }
        
        # Convert to DataFrame
        available_df = pd.DataFrame([
            {
                'drink_name': drink_name, 
                'max_drinks_possible': data['max_drinks_possible'],
                'limiting_ingredient': data['limiting_ingredient']
            }
            for drink_name, data in available_drinks.items()
        ])
        
        return available_df
    
    except Exception as e:
        print(f"Error calculating available drinks: {str(e)}")
        return None

def export_low_stock_warnings_to_csv(warnings):
    """
    Export low stock warnings to a CSV file for creating a shopping list
    
    Args:
        warnings: List of dictionaries with warning information
    
    Returns:
        bytes: CSV file content as bytes
    """
    try:
        if not warnings or len(warnings) == 0:
            return None
            
        # Convert warnings to DataFrame
        warnings_df = pd.DataFrame(warnings)
        
        # Select and rename columns for the shopping list
        shopping_list = warnings_df[['ingredient_name', 'current_stock_ml', 'target_stock_ml']]
        shopping_list = shopping_list.rename(columns={
            'ingredient_name': 'Zutat',
            'current_stock_ml': 'Aktueller Bestand (ml)',
            'target_stock_ml': 'Zielbestand (ml)'
        })
        
        # Add a column for the amount to purchase
        shopping_list['Benötigte Menge (ml)'] = shopping_list['Zielbestand (ml)'] - shopping_list['Aktueller Bestand (ml)']
        shopping_list['Benötigte Menge (ml)'] = shopping_list['Benötigte Menge (ml)'].apply(lambda x: max(0, x))
        
        # Add a column for the amount to purchase in bottles (assume 700ml per bottle)
        shopping_list['Benötigte Flaschen (à 700ml)'] = (shopping_list['Benötigte Menge (ml)'] / 700).round(2)
        
        # Sort by needed amount (descending)
        shopping_list = shopping_list.sort_values('Benötigte Menge (ml)', ascending=False)
        
        # Convert to CSV
        csv_data = shopping_list.to_csv(index=False, encoding='utf-8-sig', sep=';')
        
        return csv_data.encode()
    
    except Exception as e:
        print(f"Error exporting low stock warnings: {str(e)}")
        return None

def get_low_stock_warnings(recipe_data, inventory_data, threshold=15):
    """
    Get warnings for ingredients with low stock (can make fewer than threshold drinks)
    
    Args:
        recipe_data: Recipe DataFrame
        inventory_data: Inventory DataFrame
        threshold: Warning threshold (default: 15 drinks)
    
    Returns:
        list: List of dictionaries with warning information
    """
    try:
        # Dictionary to track minimum drinks possible for each ingredient
        ingredient_min_drinks = {}
        
        # Get unique drink names
        unique_drinks = recipe_data['drink_name'].unique()
        
        # Analyze each drink
        for drink_name in unique_drinks:
            # Get all ingredients for this drink
            drink_ingredients = recipe_data[recipe_data['drink_name'] == drink_name]
            
            # Check each ingredient
            for _, ingredient_row in drink_ingredients.iterrows():
                ingredient_name = ingredient_row['ingredient_name']
                amount_needed = ingredient_row['amount_ml']
                
                # Find the ingredient in inventory
                ingredient_info = inventory_data[inventory_data['ingredient_name'] == ingredient_name]
                
                if not ingredient_info.empty and amount_needed > 0:
                    # Get current stock
                    current_stock = ingredient_info['current_stock_ml'].values[0]
                    target_stock = ingredient_info['target_stock_ml'].values[0]
                    
                    # Calculate how many drinks can be made with this ingredient
                    drinks_possible = int(current_stock / amount_needed)
                    
                    # Update the minimum drinks possible for this ingredient
                    if ingredient_name not in ingredient_min_drinks or drinks_possible < ingredient_min_drinks[ingredient_name]['max_drinks_possible']:
                        ingredient_min_drinks[ingredient_name] = {
                            'max_drinks_possible': drinks_possible,
                            'current_stock_ml': current_stock,
                            'target_stock_ml': target_stock,
                            'most_limiting_drink': drink_name
                        }
        
        # Filter for ingredients below threshold
        warnings = []
        for ingredient_name, data in ingredient_min_drinks.items():
            if data['max_drinks_possible'] < threshold:
                warnings.append({
                    'ingredient_name': ingredient_name,
                    'current_stock_ml': data['current_stock_ml'],
                    'target_stock_ml': data['target_stock_ml'],
                    'max_drinks_possible': data['max_drinks_possible'],
                    'most_limiting_drink': data['most_limiting_drink']
                })
        
        return warnings
    
    except Exception as e:
        print(f"Error generating low stock warnings: {str(e)}")
        return []

def update_recipe_data(edited_recipe):
    """
    Update recipe data from edited dataframe
    
    Args:
        edited_recipe: Edited recipe DataFrame from st.data_editor
    
    Returns:
        pandas.DataFrame: Updated recipe data
    """
    try:
        # Ensure all columns have the right data types
        updated_recipe = edited_recipe.copy()
        updated_recipe['amount_ml'] = pd.to_numeric(updated_recipe['amount_ml'], errors='coerce')
        updated_recipe['amount_ml'] = updated_recipe['amount_ml'].fillna(0)
        
        # Remove rows with empty drink or ingredient names
        updated_recipe = updated_recipe[
            updated_recipe['drink_name'].notna() & 
            (updated_recipe['drink_name'] != '') &
            updated_recipe['ingredient_name'].notna() & 
            (updated_recipe['ingredient_name'] != '')
        ]
        
        return updated_recipe
    
    except Exception as e:
        print(f"Error updating recipe data: {str(e)}")
        return edited_recipe

def update_inventory_data(edited_inventory):
    """
    Update inventory data from edited dataframe
    
    Args:
        edited_inventory: Edited inventory DataFrame from st.data_editor
    
    Returns:
        pandas.DataFrame: Updated inventory data
    """
    try:
        # Ensure all columns have the right data types
        updated_inventory = edited_inventory.copy()
        updated_inventory['current_stock_ml'] = pd.to_numeric(updated_inventory['current_stock_ml'], errors='coerce')
        updated_inventory['price_per_liter'] = pd.to_numeric(updated_inventory['price_per_liter'], errors='coerce')
        updated_inventory['target_stock_ml'] = pd.to_numeric(updated_inventory['target_stock_ml'], errors='coerce')
        
        # Fill NaN values with 0
        updated_inventory['current_stock_ml'] = updated_inventory['current_stock_ml'].fillna(0)
        updated_inventory['price_per_liter'] = updated_inventory['price_per_liter'].fillna(0)
        updated_inventory['target_stock_ml'] = updated_inventory['target_stock_ml'].fillna(0)
        
        # Remove rows with empty ingredient names
        updated_inventory = updated_inventory[
            updated_inventory['ingredient_name'].notna() & 
            (updated_inventory['ingredient_name'] != '')
        ]
        
        return updated_inventory
    
    except Exception as e:
        print(f"Error updating inventory data: {str(e)}")
        return edited_inventory

def calculate_sales_summary(sales_data):
    """
    Calculate summary statistics from sales data
    
    Args:
        sales_data: Sales data dictionary
    
    Returns:
        dict: Summary statistics
    """
    try:
        products = sales_data.get('products', [])
        
        if not products:
            return {
                'total_value': 0,
                'total_quantity': 0,
                'most_sold_drink': 'None',
                'most_sold_quantity': 0
            }
        
        # Calculate total value and quantity
        total_value = sum(product['total'] for product in products)
        total_quantity = sum(product['quantity'] for product in products)
        
        # Find most sold drink
        most_sold = max(products, key=lambda x: x['quantity'])
        
        return {
            'total_value': total_value,
            'total_quantity': total_quantity,
            'most_sold_drink': most_sold['product_name'],
            'most_sold_quantity': most_sold['quantity']
        }
    
    except Exception as e:
        print(f"Error calculating sales summary: {str(e)}")
        return {
            'total_value': 0,
            'total_quantity': 0,
            'most_sold_drink': 'Error',
            'most_sold_quantity': 0
        }
