import streamlit as st
import pandas as pd
import io
import os
import base64

def display_header():
    """Display the application header with logo and title"""
    # Header with logo and title
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Display RumBar logo
        st.image("static/images/20241003_Logo_Rumbar_negativ.jpg", width=150)
    
    with col2:
        st.title("Warenwirtschaft RumBar Falkensee")
        st.subheader("Getränke-Management-System")

def display_footer():
    """Display the application footer"""
    st.markdown("---")
    st.markdown("© 2024 RumBar Falkensee - Warenwirtschaft System")

def load_demo_data():
    """Load the demo data from the provided CSV files"""
    try:
        # Define the sample data content for inventory
        inventory_csv = """Zutat,Lagerbestand (ml),,Lagerbestand in Flaschen (à 700ml),Einkaufspreis pro Liter (EUR),Soll-Lagerbestand in Flaschen für 50 Drinks,,
Havana Club 3 Años Rum,3300,,"3,81",5,5500,"7,86",1
Limettensaft,6000,,"2,55",27,6000,"28,93",12
Sodawasser,300,,"2,07",16,12500,"17,86",12
Gosling's Black Seal Rum,2800,,"3,57",,2500,"3,57",1
Ingwerbier,12000,,"7,14",,5000,"7,14",6
Mount Gay Eclipse Rum,2700,,"1,86",2,2500,"3,57",1
Feigensirup,1500,,"1,37",1,1000,"1,43",2
Angostura,198,,"0,28",,50,"0,07",
Plantation Original Dark Rum,3100,,0,7,4500,"6,43",2
Bananenlikör,500,,"0,47",1,1000,"1,43",1
Passoa,900,,"2,26",,1000,"1,43",1
Maracujasaft,29480,,"42,11",,8000,"11,43",8
Kokoscreme,700,,"1,54",,1000,"1,43",1
Sahne,200,,"2,6",,1500,"2,14",10
Holunderblütenlikör,1200,,"1,23",1,1000,"1,43",1
Ahornsirup,0,,"0,19",2,1250,"1,79",1
Apfelsaft,10580,,"15,11",,7000,10,6
Rhubarb Gin von Whitley Neill,1400,,"1,64",2,2500,"3,57",3
Zuckersirup,3800,,"2,46",4,4500,"6,43",1
Eiweiß,600,,"3,56",,50,"0,07",
Hendrick's Gin,1900,,2,2,2500,"3,57",
Beefeater London Garden Gin,3500,,"0,79",3,2500,"3,57",
Cointreau,700,,"2,11",1,2000,"2,86",1
Ananassaft,8000,,"13,91",,4000,"5,71",6
The Botanist Gin,2100,,2,2,2500,"3,57",3
Matcha Green Tea Sirup,1500,,"1,21",1,1250,"1,79",1
Vanille Sirup,1000,,"0,57",1,500,"0,71",
Grüner Tee,200,,"0,29",6,4000,"5,71",
Plymouth Gin,500,,"0,89",1,1250,"1,79",1
Grüner Chartreuse,700,,"0,89",1,1250,"1,79",2
Maraschino-Likör,500,,"0,63",1,1250,"1,25",2
9 Mile Vodka,2100,,"6,64",1,2500,"3,57",2
Weissburgunder,2100,,"14,29",,10000,"14,29",
Dornfelder,2100,,"14,29",,10000,"14,29",
Cola,18000,,"24,65",21,45000,45,
Cola Zero,15000,,"23,1",2,25000,25,
Radeberger Pils,0,,"9,43",12,15000,"21,43",
Radeberger Pils Alkoholfrei,0,,"8,57",13,15000,"21,43",
Fanta,3000,,15,,15000,15,
Sprite,1000,,15,,27500,"27,5",
Appleton Estate Reserve Blend,1400,,"0,83",2,1500,"2,14",
Worthy Park Estate 109 (Overproof Rum),4900,,,,5500,"7,86",
Botocal,700,,,,0,0,
Ardbeg Ten Whisky,300,,"0,93",,500,"0,71",
Glenmorangie Whisky,900,,"0,71",3,2000,"2,86",
Amarula,1400,,,,0,0,
Beefeater London Garden,0,,,,0,0,
Erdbeer-Rum,500,,,,2500,"3,57",
Tequila,2500,,,,2500,"3,57",
Aperol,0,,,,3000,"4,29",
Kaluha,700,,,,0,0,
Rharbarbersirup,2000,,"1,81",,750,"1,07",
Käsekuchenlikör,1000,,"0,39",2,1500,"2,14",
Laori Aperol,3000,,,,3000,"4,29",
Freikopf Gin,250,,,,3000,"4,29",
Freikopf Pink Lillet,250,,,,3000,"4,29",
Curacao Orange,340,,"0,49",1,750,"1,07",
Don Papa rot,1300,,"0,87",2,1500,"2,14",
Don Papa grün,1300,,"0,96",2,1500,"2,14",
Pfirsichlikör,700,,,,0,0,
O Donnell Moonshine Hart Nuss,700,,,,3000,"4,29",
O Donnell Moonshine Toffee,700,,,,3000,"4,29",
Erdbeersirup,1365,,"1,95",1,2000,"2,86",
Pfirsichsirup,1000,,,,0,0,
Falernum,2000,,"2,46",,750,"1,07",
Grenadine,1700,,,,0,0,
Bitter,1000,,,,0,0,
Pitu,2300,,,,0,0,
Likör 43,300,,0,3,2000,2,
Jack Daniel's Tennessee Whiskey,2400,,0,4,2500,"3,57",
Buffalo Trace Bourbon,1000,,"0,43",4,2500,"3,57",
Bullet burbon,2800,,,,0,0,
Woodford Reserve Whiskey,2100,,,,2500,"3,57",
Smith and cross,1400,,,,0,0,
Scavi & Ray Prosecco,0,,,,4500,"6,43",
Pink Grapefruit limo,6000,,,,0,0,
Schweppes Wild Berry,11900,,17,,5000,"7,14",
Wild berry zero,6000,,,,10000,"14,29",
Schweppes Tonic Water,7000,,,,0,0,
Thomas Henry Tonic Zero,12000,,,,10000,"14,29",
Ginger Ale,11500,,"16,43",16,22500,"32,14",
Orangensaft,2000,,"11,26",,3000,"4,29",
Milch,0,,"6,51",,2000,"2,86",
Smith & Cross Traditional Jamaica Rum,1400,,"0,83",2,1500,"2,14",
Overproof Rum,460,,"0,66",1,500,"0,71",
Mandelsirup (Orgeat),460,,"0,66",1,500,"0,71",
Lillet Blanc,750,,"4,21",,2500,"3,57",
Pink Grapefruit Limonade,1000,,,,7500,"10,71",
Kölsch,0,,9,13,15000,"21,43",
Scheidgen Zero Sekt,0,,,,10000,"14,29",
Captain Morgan Zero Rum,1000,,,,3000,"4,29",
Triple Sec,1400,,,,,,"""
        
        # Define the sample data content for recipes
        recipe_csv = """Getränkename,Zutat,Menge pro Drink (ml/cl)
Mojito,Havana Club 3 Años Rum,50
Mojito,Minze,10
Mojito,Rohrzucker,2
Mojito,Limettensaft,25
Mojito,Sodawasser,150
Dark 'n' Stormy,Gosling's Black Seal Rum,50
Dark 'n' Stormy,Ingwerbier,100
Dark 'n' Stormy,Limettensaft,10
Adam küsste Eva,Mount Gay Eclipse Rum,50
Adam küsste Eva,Feigensirup,20
Adam küsste Eva,Limettensaft,20
Adam küsste Eva,Angostura,1
Tropical Sniki Tiki,Plantation Original Dark Rum,40
Tropical Sniki Tiki,Bananenlikör,20
Tropical Sniki Tiki,Passoa,20
Tropical Sniki Tiki,Maracujasaft,60
Tropical Sniki Tiki,Kokoscreme,20
Tropical Sniki Tiki,Sahne,30
Elder Rum Punch,Plantation Original Dark Rum,50
Elder Rum Punch,Holunderblütenlikör,20
Elder Rum Punch,Ahornsirup,10
Elder Rum Punch,Apfelsaft,60
Elder Rum Punch,Limettensaft,20
Rhabarber Gin Fizz,Rhubarb Gin von Whitley Neill,50
Rhabarber Gin Fizz,Zitronensaft,25
Rhabarber Gin Fizz,Rharbarbersirup,15
Rhabarber Gin Fizz,Zuckersirup,15
Rhabarber Gin Fizz,Eiweiß,1
Rhabarber Gin Fizz,Sodawasser,100
Basil Smash,Hendrick's Gin,50
Basil Smash,Zitronensaft,25
Basil Smash,Zuckersirup,15
BeGINning of Weekend,Beefeater London Garden Gin,50
BeGINning of Weekend,Cointreau,20
BeGINning of Weekend,Ananassaft,60
BeGINning of Weekend,Limettensaft,20
Ginspiriert Matcha,The Botanist Gin,50
Ginspiriert Matcha,Matcha Green Tea Sirup,25
Ginspiriert Matcha,Vanille Sirup,10
Ginspiriert Matcha,Limettensaft,20
Ginspiriert Matcha,Grüner Tee,80
The Last Word,Plymouth Gin,25
The Last Word,Grüner Chartreuse,25
The Last Word,Maraschino-Likör,25
The Last Word,Limettensaft,25
Moscow Mule,9 Mile Vodka,50
Moscow Mule,Limettensaft,20
Moscow Mule,Ginger Beer,100
Weissburgunder,Weissburgunder,200
Dornfelder,Dornfelder,200
Cola,Cola,300
Cola Zero,Cola Zero,300
Radeberger Pils,Radeberger Pils,300
Radeberger Pils Alkoholfrei,Radeberger Pils Alkoholfrei,300
Fanta,Fanta,300
Sprite,Sprite,300
Whiskey Sour,Buffalo Trace Bourbon,50
Whiskey Sour,Limettensaft,25
Whiskey Sour,Zuckersirup,15
Big Brother of Moscow Mule,Glenmorangie Whisky,40
Big Brother of Moscow Mule,Ardbeg Ten Whisky,10
Big Brother of Moscow Mule,Falernum,15
Big Brother of Moscow Mule,Limettensaft,20
Big Brother of Moscow Mule,Ginger Ale,100
Maple Apple Whiskey Sour,Woodford Reserve Whiskey,50
Maple Apple Whiskey Sour,Limettensaft,20
Maple Apple Whiskey Sour,Ahornsirup,15
Maple Apple Whiskey Sour,Apfelsaft,30
Tennessee Buck,Jack Daniel's Tennessee Whiskey,50
Tennessee Buck,Zitronensaft,20
Tennessee Buck,Erdbeersirup,15
Tennessee Buck,Ginger Beer,100
Old Fashioned,Woodford Reserve Bourbon,50
Old Fashioned,Zuckersirup,10
Old Fashioned,Angostura-Bitters,3
Cosmopolitan,White Oak Vodka,40
Cosmopolitan,Cointreau,20
Cosmopolitan,Cranberrysaft,50
Cosmopolitan,Limettensaft,10
Eastern Breeze,White Oak Vodka,50
Eastern Breeze,Maracujasaft,40
Eastern Breeze,Limettensaft,20
Eastern Breeze,Zuckersirup,10
Espresso Martini,White Oak Vodka,50
Espresso Martini,Espresso,30
Espresso Martini,Kaffeelikör,20
Espresso Martini,Zuckersirup,10
Lemon Drop Martini,8 Mile Vodka,50
Lemon Drop Martini,Limettensaft,25
Lemon Drop Martini,Zuckersirup,15
Summertime Cheesecake,Likör 43,40
Summertime Cheesecake,Milch,40
Summertime Cheesecake,Vanillesirup,20
Summertime Cheesecake,Käsekuchenlikör,30
Summertime Cheesecake,Limettensaft,10
Mai Tai Boxed,Smith & Cross Traditional Jamaica Rum,30
Mai Tai Boxed,Appleton Estate Reserve Blend,30
Mai Tai Boxed,Overproof Rum,10
Mai Tai Boxed,Curacao Orange,15
Mai Tai Boxed,Mandelsirup (Orgeat),10
Mai Tai Boxed,Limettensaft,20
Mai Tai Boxed,Ananassaft,20
Pink and very stormy,Erdbeer-Rum,50
Pink and very stormy,Limettensaft,20
Pink and very stormy,Ginger Beer,100
Cuba Libre,Worthy Park Estate 109 (Overproof Rum),50
Cuba Libre,Cola,100
Cuba Libre,Limettensaft,20
Wildberry Lillet,Lillet Blanc,50
Wildberry Lillet,Schweppes Wild Berry,100
Paloma,Tequila,50
Paloma,Pink Grapefruit Limonade,150
Aperol Sprizz,Aperol,60
Aperol Sprizz,Scavi & Ray Prosecco,90
Solero,Maracujasaft,60
Solero,Limettensaft,30
Solero,Orangensaft,60
Solero,Vanillesirup,30
Ipanema,Sprite,250
Moscito,Ginger Ale,250
Virgin Pink Stormy,Cranberrysaft,50
Virgin Pink Stormy,Erdbeersirup,25
Virgin Pink Stormy,Ginger Beer,150
Apple Ginger Fizz,Apfelsaft,50
Apple Ginger Fizz,Limettensaft,25
Apple Ginger Fizz,Ingwersirup,25
Apple Ginger Fizz,Ginger Ale,100
Kölsch,Kölsch,300
O Donnell Moonshine Hart Nuss,O Donnell Moonshine Hart Nuss,30
O Donnell Moonshine Toffee,O Donnell Moonshine Toffee,30
Aperolless Sprizz,Laori Aperol,60
Aperolless Sprizz,Scheidgen Zero Sekt,200
Lilletless Berry,Freikopf Pink Lillet,60
Lilletless Berry,Wild berry zero,200
Ginless Tonic,Freikopf Gin,60
Ginless Tonic,Thomas Henry Tonic Zero,200
Cuba no Libre,Captain Morgan Zero Rum,60
Cuba no Libre,Cola Zero,200
O Donnell Moonshine Hart Nuss,O Donnell Moonshine Hart Nuss,30
O Donnell Moonshine Toffee,O Donnell Moonshine Toffee,30
Don Papa rot,Don Papa rot,30
Don Papa grün,Don Papa grün,30
Cuba Libre Havana Club,Havana Club 3 Años Rum,60
Cuba Libre Havana Club,Cola,250
Cuba Libre Worthy Park,Worthy Park Estate 109 (Overproof Rum),60
Cuba Libre Worthy Park,Cola,250"""
        
        # Convert CSV strings to file-like objects
        inventory_file = io.StringIO(inventory_csv)
        recipe_file = io.StringIO(recipe_csv)
        
        # Process the data
        from data_processor import process_inventory_data, process_recipe_data
        inventory_data = process_inventory_data(inventory_file)
        recipe_data = process_recipe_data(recipe_file)
        
        return inventory_data, recipe_data
    except Exception as e:
        st.error(f"Error loading demo data: {str(e)}")
        return None, None
