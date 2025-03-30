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
        # Zuerst lesen wir den gesamten Inhalt der Datei ein
        content = sales_file.read().decode('utf-8')
        
        # Wir teilen den Inhalt in Zeilen auf, um ihn besser zu analysieren
        lines = content.split('\n')
        
        # Datum extrahieren (sollte in Zeile 2 sein)
        date_str = "Unknown"
        if len(lines) > 1 and ";" in lines[1]:
            date_parts = lines[1].split(';')
            if len(date_parts) > 2:
                date_str = date_parts[2].strip()
        
        # Datum formatieren
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y")
            date_formatted = date_obj.strftime("%Y-%m-%d")
        except:
            date_formatted = date_str
        
        # Ergebnis-Dictionary initialisieren
        result = {
            'date': date_formatted,
            'total_sales': 0,
            'products': []
        }
        
        # Jetzt suchen wir die Produktdaten
        # Diese beginnen normalerweise mit einer Zeile, die "Produkte" in der ersten Spalte enthält
        products_section_start = -1
        for i, line in enumerate(lines):
            if "Produkte;Total" in line or (line.startswith("Produkte") and ";Total;" in line):
                products_section_start = i + 1  # Die nächste Zeile sollte die Header-Zeile sein
                break
        
        # Wenn wir die Produkte-Sektion nicht gefunden haben, suchen wir nach "Produkte" am Anfang
        if products_section_start == -1:
            for i, line in enumerate(lines):
                if line.startswith("Produkte;"):
                    products_section_start = i + 2  # +2 weil wir die Header-Zeile überspringen wollen
                    break
        
        # Als letzter Versuch suchen wir nach der Zeile, die mit "Produkte" beginnt
        if products_section_start == -1:
            for i, line in enumerate(lines):
                if line.strip() and line.split(';')[0].strip() == "Produkte":
                    products_section_start = i + 2  # +2 für die Header-Zeile
                    break
        
        # Wenn wir die Produkte-Sektion gefunden haben
        if products_section_start != -1 and products_section_start < len(lines):
            # Finde den Anfang der tatsächlichen Produktdaten (nach den Header-Zeilen)
            actual_products_start = products_section_start
            
            # Überspringen Sie die Zeilen, bis Sie zur konkreten Produktliste kommen
            # Dies ist normalerweise nach Zeile 80 im Bericht
            for i in range(products_section_start, len(lines)):
                if i >= 80 and i < len(lines) and lines[i].strip():
                    actual_products_start = i
                    break
            
            # Jetzt verarbeiten wir die tatsächlichen Produktdaten
            for i in range(actual_products_start, len(lines)):
                line = lines[i].strip()
                
                # Wenn wir eine leere Zeile erreichen oder eine, die nicht wie Produktdaten aussieht, brechen wir ab
                if not line or not ";" in line:
                    continue
                
                # Zeile in Teile zerlegen
                parts = line.split(';')
                
                # Produktname sollte das erste Feld sein, aber manchmal kann es leer sein oder eine Zahl
                product_name = parts[0].strip()
                
                # Wenn der Produktname nicht vorhanden ist oder nur eine Zahl ist, überspringen wir diese Zeile
                if not product_name or product_name.isdigit():
                    continue
                
                # Jetzt suchen wir die Mengen- und Gesamtpreis-Spalten
                # In den meisten Fällen sollten sie direkt nach dem Produktnamen kommen
                quantity_str = None
                total_str = None
                
                # Durchsuchen Sie die Teile nach Zahlen, um Menge und Preis zu finden
                for j in range(1, min(len(parts), 10)):  # Beschränke die Suche auf die ersten 10 Spalten
                    part = parts[j].strip()
                    
                    # Wenn der Teil eine Zahl ist, könnte es die Menge sein
                    if part.isdigit() and quantity_str is None:
                        quantity_str = part
                        # Der nächste Teil könnte der Preis sein
                        if j+1 < len(parts):
                            next_part = parts[j+1].strip()
                            # Preis könnte ein Dezimalwert mit Komma sein
                            if next_part and (next_part.replace(',', '.').replace('.', '').isdigit() or 
                                            (next_part.count(',') == 1 and next_part.replace(',', '').isdigit())):
                                total_str = next_part
                        break
                
                # Wenn wir Menge und Preis gefunden haben, verarbeiten wir die Daten
                if product_name and quantity_str and total_str:
                    try:
                        quantity = int(quantity_str)
                        # Preisformatierung für deutsche Zahlenformate (Komma als Dezimaltrennzeichen)
                        total = float(total_str.replace('.', '').replace(',', '.'))
                        
                        result['products'].append({
                            'product_name': product_name,
                            'quantity': quantity,
                            'total': total
                        })
                        
                        result['total_sales'] += total
                    except (ValueError, TypeError) as e:
                        print(f"Fehler beim Verarbeiten von Zeile {i}: {line} - {str(e)}")
                        # Fehlerhafte Zeilen überspringen
                        pass
            
            # Wenn wir keine Produkte gefunden haben, versuchen wir eine alternative Methode
            if not result['products']:
                print("Keine Produkte mit regulärem Parsing gefunden. Verwende alternative Methode.")
                # Alternative Methode: Suchen nach Zeilen, die nach dem Muster "Name;0;Menge;Preis;%" aussehen
                for i in range(actual_products_start, len(lines)):
                    line = lines[i].strip()
                    
                    if not line or not ";" in line:
                        continue
                    
                    parts = line.split(';')
                    
                    # Überprüfen, ob die Zeile dem erwarteten Format entspricht
                    if len(parts) >= 5 and parts[1].strip() == "0" and parts[4].strip().endswith("%"):
                        product_name = parts[0].strip()
                        quantity_str = parts[2].strip()
                        total_str = parts[3].strip()
                        
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
                                pass  # Fehlerhafte Zeilen überspringen
        
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
        
        # Add a column for the required amount to have at least 15 drinks of each cocktail
        # This should be at least the target stock level, which already accounts for the minimum needed
        needed_for_15_drinks = []
        
        for _, row in shopping_list.iterrows():
            ingredient_name = row['Zutat']
            current_stock = row['Aktueller Bestand (ml)']
            target_stock = row['Zielbestand (ml)']
            
            # The needed amount is max(target_stock, current_stock needed for 15 drinks)
            # Since target_stock should already account for this, use it as a baseline
            needed_amount = max(0, target_stock - current_stock)
            needed_for_15_drinks.append(needed_amount)
            
        shopping_list['Benötigte Menge (ml)'] = needed_for_15_drinks
        
        # Add a column for the amount to purchase in liters (not bottles)
        shopping_list['Benötigte Menge (Liter)'] = (shopping_list['Benötigte Menge (ml)'] / 1000).round(2)
        
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
        
        # Dictionary to track total needed amount for each ingredient to reach threshold
        ingredient_needed_for_threshold = {}
        
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
                    
                    # Calculate how much of this ingredient is needed for threshold drinks
                    amount_for_threshold = threshold * amount_needed
                    
                    # Add to the total needed for this ingredient
                    if ingredient_name in ingredient_needed_for_threshold:
                        ingredient_needed_for_threshold[ingredient_name] += amount_for_threshold
                    else:
                        ingredient_needed_for_threshold[ingredient_name] = amount_for_threshold
                    
                    # Update the minimum drinks possible for this ingredient
                    if ingredient_name not in ingredient_min_drinks or drinks_possible < ingredient_min_drinks[ingredient_name]['max_drinks_possible']:
                        ingredient_min_drinks[ingredient_name] = {
                            'max_drinks_possible': drinks_possible,
                            'current_stock_ml': current_stock,
                            'target_stock_ml': max(target_stock, ingredient_needed_for_threshold[ingredient_name]),
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
