import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import sys

# Sicherstellen, dass das aktuelle Verzeichnis im Python-Pfad ist
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from helpers import display_header, display_footer, load_demo_data
from data_processor import (
    process_sales_data, process_recipe_data, process_inventory_data,
    update_inventory_based_on_sales, calculate_drink_costs,
    calculate_available_drinks, get_low_stock_warnings,
    update_recipe_data, update_inventory_data, calculate_sales_summary,
    export_low_stock_warnings_to_csv
)

# Set page config
st.set_page_config(
    page_title="Warenwirtschaft RumBar Falkensee",
    page_icon="🍹",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'inventory_data' not in st.session_state:
    st.session_state.inventory_data = None

if 'recipe_data' not in st.session_state:
    st.session_state.recipe_data = None

if 'sales_data' not in st.session_state:
    st.session_state.sales_data = None

if 'available_drinks' not in st.session_state:
    st.session_state.available_drinks = None

if 'drink_costs' not in st.session_state:
    st.session_state.drink_costs = None

if 'low_stock_warnings' not in st.session_state:
    st.session_state.low_stock_warnings = None

if 'sales_summary' not in st.session_state:
    st.session_state.sales_summary = None

# Display header
display_header()

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Seite auswählen", ["Dashboard", "Lagerbestand", "Rezepte", "Verkaufsdaten"])

# Load demo data option
if st.sidebar.button("Demo-Daten laden"):
    st.session_state.inventory_data, st.session_state.recipe_data = load_demo_data()
    
    if st.session_state.recipe_data is not None and st.session_state.inventory_data is not None:
        # Calculate derived data
        st.session_state.drink_costs = calculate_drink_costs(st.session_state.recipe_data, st.session_state.inventory_data)
        st.session_state.available_drinks = calculate_available_drinks(st.session_state.recipe_data, st.session_state.inventory_data)
        st.session_state.low_stock_warnings = get_low_stock_warnings(st.session_state.recipe_data, st.session_state.inventory_data)
        st.sidebar.success("Demo-Daten erfolgreich geladen!")
        st.rerun()
    else:
        st.sidebar.error("Fehler beim Laden der Demo-Daten.")

# Reset application data
if st.sidebar.button("Alle Daten zurücksetzen"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# Dashboard Page
if page == "Dashboard":
    st.title("Warenwirtschaft Dashboard")
    
    if (st.session_state.inventory_data is None or 
        st.session_state.recipe_data is None):
        st.info("Bitte laden Sie Daten, um das Dashboard anzuzeigen. Sie können entweder:")
        col1, col2 = st.columns(2)
        with col1:
            st.info("1. Klicken Sie auf 'Demo-Daten laden' in der Seitenleiste")
        with col2:
            st.info("2. Importieren Sie Ihre Lagerbestand- und Rezeptdaten in den entsprechenden Bereichen")
    else:
        # Display summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Lagerbestand Übersicht")
            st.metric("Anzahl Zutaten", len(st.session_state.inventory_data))
            
            # Display low stock warnings if any
            if st.session_state.low_stock_warnings and len(st.session_state.low_stock_warnings) > 0:
                st.warning(f"⚠️ {len(st.session_state.low_stock_warnings)} Zutaten mit niedrigem Bestand!")
            else:
                st.success("Alle Zutaten haben ausreichend Bestand")
        
        with col2:
            st.subheader("Rezepte Übersicht")
            st.metric("Anzahl Rezepte", len(st.session_state.recipe_data['drink_name'].unique()))
            
            # Most expensive drink
            if st.session_state.drink_costs is not None:
                most_expensive = st.session_state.drink_costs.sort_values('total_cost', ascending=False).iloc[0]
                st.metric("Teuerster Drink", 
                          f"{most_expensive['drink_name']} (€{most_expensive['total_cost']:.2f})")
        
        with col3:
            st.subheader("Verkaufsdaten Übersicht")
            if st.session_state.sales_summary is not None:
                st.metric("Gesamtumsatz", f"€{st.session_state.sales_summary['total_value']:.2f}")
                st.metric("Meistverkaufter Drink", st.session_state.sales_summary['most_sold_drink'])
            else:
                st.info("Noch keine Verkaufsdaten importiert")
        
        # Display low stock warnings
        st.subheader("Warnungen bei niedrigem Lagerbestand")
        if st.session_state.low_stock_warnings and len(st.session_state.low_stock_warnings) > 0:
            warning_df = pd.DataFrame(st.session_state.low_stock_warnings)
            warning_df = warning_df.sort_values('max_drinks_possible', ascending=True)
            st.dataframe(warning_df, use_container_width=True)
            
            # Export to CSV button
            csv_data = export_low_stock_warnings_to_csv(st.session_state.low_stock_warnings)
            if csv_data:
                col1, col2 = st.columns([1, 5])
                with col1:
                    current_date = pd.Timestamp.now().strftime('%Y-%m-%d')
                    st.download_button(
                        label="📥 Export Einkaufsliste",
                        data=csv_data,
                        file_name=f"RumBar_Einkaufsliste_{current_date}.csv",
                        mime="text/csv",
                        help="Exportiere die Zutatenliste mit niedrigem Bestand als CSV-Datei für den Einkauf"
                    )
        else:
            st.success("Keine Warnungen - alle Zutaten haben ausreichend Lagerbestand!")
        
        # Display available drinks
        st.subheader("Verfügbare Drinks")
        if st.session_state.available_drinks is not None:
            avail_df = st.session_state.available_drinks.sort_values('max_drinks_possible', ascending=True)
            st.dataframe(avail_df, use_container_width=True)
        
        # Display drink costs
        st.subheader("Drink Kosten")
        if st.session_state.drink_costs is not None:
            cost_df = st.session_state.drink_costs.sort_values('total_cost', ascending=False)
            st.dataframe(cost_df, use_container_width=True)

# Inventory Management Page
elif page == "Lagerbestand":
    st.title("Lagerbestand Management")
    
    # Upload inventory CSV
    st.subheader("Import Inventory Data")
    inventory_file = st.file_uploader("Upload Inventory CSV File", type=["csv"])
    
    if inventory_file is not None:
        try:
            st.session_state.inventory_data = process_inventory_data(inventory_file)
            st.success("Inventory data imported successfully!")
            
            # Recalculate derived data if recipe data is available
            if st.session_state.recipe_data is not None:
                st.session_state.drink_costs = calculate_drink_costs(st.session_state.recipe_data, st.session_state.inventory_data)
                st.session_state.available_drinks = calculate_available_drinks(st.session_state.recipe_data, st.session_state.inventory_data)
                st.session_state.low_stock_warnings = get_low_stock_warnings(st.session_state.recipe_data, st.session_state.inventory_data)
        except Exception as e:
            st.error(f"Error importing inventory data: {str(e)}")
    
    # Display and edit inventory data
    st.subheader("Current Inventory")
    
    if st.session_state.inventory_data is not None:
        # Allow editing inventory
        edited_inventory = st.data_editor(
            st.session_state.inventory_data,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "ingredient_name": st.column_config.TextColumn("Ingredient Name"),
                "current_stock_ml": st.column_config.NumberColumn("Current Stock (ml)", min_value=0),
                "price_per_liter": st.column_config.NumberColumn("Price per Liter (€)", min_value=0),
                "target_stock_ml": st.column_config.NumberColumn("Target Stock (ml)", min_value=0)
            }
        )
        
        # Update button
        if st.button("Update Inventory"):
            st.session_state.inventory_data = update_inventory_data(edited_inventory)
            
            # Recalculate derived data
            if st.session_state.recipe_data is not None:
                st.session_state.drink_costs = calculate_drink_costs(st.session_state.recipe_data, st.session_state.inventory_data)
                st.session_state.available_drinks = calculate_available_drinks(st.session_state.recipe_data, st.session_state.inventory_data)
                st.session_state.low_stock_warnings = get_low_stock_warnings(st.session_state.recipe_data, st.session_state.inventory_data)
            
            st.success("Inventory updated successfully!")
    else:
        st.info("Please upload inventory data or load demo data from the sidebar.")

# Recipe Management Page
elif page == "Rezepte":
    st.title("Rezepte Management")
    
    # Upload recipe CSV
    st.subheader("Import Recipe Data")
    recipe_file = st.file_uploader("Upload Recipe CSV File", type=["csv"])
    
    if recipe_file is not None:
        try:
            st.session_state.recipe_data = process_recipe_data(recipe_file)
            st.success("Recipe data imported successfully!")
            
            # Recalculate derived data if inventory data is available
            if st.session_state.inventory_data is not None:
                st.session_state.drink_costs = calculate_drink_costs(st.session_state.recipe_data, st.session_state.inventory_data)
                st.session_state.available_drinks = calculate_available_drinks(st.session_state.recipe_data, st.session_state.inventory_data)
                st.session_state.low_stock_warnings = get_low_stock_warnings(st.session_state.recipe_data, st.session_state.inventory_data)
        except Exception as e:
            st.error(f"Error importing recipe data: {str(e)}")
    
    # Display and edit recipe data
    st.subheader("Current Recipes")
    
    if st.session_state.recipe_data is not None:
        # Allow editing recipe data
        edited_recipe = st.data_editor(
            st.session_state.recipe_data,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "drink_name": st.column_config.TextColumn("Drink Name"),
                "ingredient_name": st.column_config.TextColumn("Ingredient Name"),
                "amount_ml": st.column_config.NumberColumn("Amount (ml)", min_value=0)
            }
        )
        
        # Update button
        if st.button("Update Recipes"):
            st.session_state.recipe_data = update_recipe_data(edited_recipe)
            
            # Recalculate derived data
            if st.session_state.inventory_data is not None:
                st.session_state.drink_costs = calculate_drink_costs(st.session_state.recipe_data, st.session_state.inventory_data)
                st.session_state.available_drinks = calculate_available_drinks(st.session_state.recipe_data, st.session_state.inventory_data)
                st.session_state.low_stock_warnings = get_low_stock_warnings(st.session_state.recipe_data, st.session_state.inventory_data)
            
            st.success("Recipes updated successfully!")
    else:
        st.info("Please upload recipe data or load demo data from the sidebar.")
    
    # Add new recipe form
    st.subheader("Add New Recipe")
    
    if st.session_state.recipe_data is not None and st.session_state.inventory_data is not None:
        with st.form("add_recipe_form"):
            new_drink_name = st.text_input("Drink Name")
            
            # Dynamic ingredient selection
            st.subheader("Ingredients")
            num_ingredients = st.number_input("Number of Ingredients", min_value=1, max_value=10, value=3)
            
            ingredients = []
            amounts = []
            
            for i in range(num_ingredients):
                col1, col2 = st.columns(2)
                with col1:
                    ingredient = st.selectbox(
                        f"Ingredient {i+1}",
                        options=st.session_state.inventory_data['ingredient_name'].unique(),
                        key=f"ingredient_{i}"
                    )
                    ingredients.append(ingredient)
                
                with col2:
                    amount = st.number_input(
                        f"Amount (ml) {i+1}",
                        min_value=0.0,
                        value=30.0,
                        step=5.0,
                        key=f"amount_{i}"
                    )
                    amounts.append(amount)
            
            submitted = st.form_submit_button("Add Recipe")
            
            if submitted:
                if not new_drink_name:
                    st.error("Please enter a drink name")
                else:
                    # Create new recipe entries
                    new_recipes = []
                    for i in range(num_ingredients):
                        if ingredients[i] and amounts[i] > 0:
                            new_recipes.append({
                                'drink_name': new_drink_name,
                                'ingredient_name': ingredients[i],
                                'amount_ml': amounts[i]
                            })
                    
                    # Add to existing recipes
                    if new_recipes:
                        new_recipe_df = pd.DataFrame(new_recipes)
                        st.session_state.recipe_data = pd.concat([st.session_state.recipe_data, new_recipe_df], ignore_index=True)
                        
                        # Recalculate derived data
                        st.session_state.drink_costs = calculate_drink_costs(st.session_state.recipe_data, st.session_state.inventory_data)
                        st.session_state.available_drinks = calculate_available_drinks(st.session_state.recipe_data, st.session_state.inventory_data)
                        st.session_state.low_stock_warnings = get_low_stock_warnings(st.session_state.recipe_data, st.session_state.inventory_data)
                        
                        st.success(f"Recipe for '{new_drink_name}' added successfully!")
                        st.rerun()
    else:
        st.info("Please make sure both inventory and recipe data are loaded before adding new recipes.")

# Sales Import Page
elif page == "Verkaufsdaten":
    st.title("Tägliche Verkaufsdaten importieren")
    
    # Check if recipe and inventory data are available
    if st.session_state.recipe_data is None or st.session_state.inventory_data is None:
        st.warning("Please load recipe and inventory data first before importing sales data!")
    else:
        # Upload sales CSV
        st.subheader("Import Daily Sales Report")
        sales_file = st.file_uploader("Upload Daily Sales Report CSV", type=["csv"])
        
        if sales_file is not None:
            try:
                # Process sales data
                st.session_state.sales_data = process_sales_data(sales_file)
                
                # Display sales data
                st.subheader("Sales Data Summary")
                
                # Find the unique sales date
                sales_date = "Unknown Date"
                if st.session_state.sales_data.get('date'):
                    sales_date = st.session_state.sales_data['date']
                
                st.write(f"Sales Date: {sales_date}")
                
                if 'products' in st.session_state.sales_data:
                    products_df = pd.DataFrame(st.session_state.sales_data['products'])
                    st.dataframe(products_df, use_container_width=True)
                    
                    # Calculate and store sales summary
                    st.session_state.sales_summary = calculate_sales_summary(st.session_state.sales_data)
                    
                    # Show update confirmation
                    st.subheader("Update Inventory")
                    st.write("Do you want to update your inventory based on these sales?")
                    
                    if st.button("Update Inventory"):
                        # Update inventory based on sales
                        updated_inventory = update_inventory_based_on_sales(
                            st.session_state.inventory_data, 
                            st.session_state.recipe_data, 
                            st.session_state.sales_data
                        )
                        
                        if updated_inventory is not None:
                            st.session_state.inventory_data = updated_inventory
                            
                            # Recalculate derived data
                            st.session_state.drink_costs = calculate_drink_costs(st.session_state.recipe_data, st.session_state.inventory_data)
                            st.session_state.available_drinks = calculate_available_drinks(st.session_state.recipe_data, st.session_state.inventory_data)
                            st.session_state.low_stock_warnings = get_low_stock_warnings(st.session_state.recipe_data, st.session_state.inventory_data)
                            
                            st.success("Inventory updated successfully based on sales data!")
                        else:
                            st.error("Failed to update inventory based on sales data.")
                else:
                    st.error("No product data found in the sales report.")
            except Exception as e:
                st.error(f"Error processing sales data: {str(e)}")
        else:
            st.info("Please upload a daily sales report CSV file.")

# Display footer
display_footer()
