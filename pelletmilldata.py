import barcode
from barcode.writer import ImageWriter
from io import BytesIO, StringIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, SimpleDocTemplate, Paragraph, Spacer, Frame, Image, Table, PageTemplate, TableStyle, KeepTogether, PageBreak, NextPageTemplate
from reportlab.platypus import Image as PlatypusImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT,TA_CENTER
import qrcode
import pyodbc
import xml.dom
import os
from PIL import Image
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
from reportlab.graphics.shapes import Drawing
import subprocess
import sys
import json
import ast
import pandas as pd
from datetime import datetime


pd.set_option('display.max_colwidth', 200)
pd.set_option('display.max_columns',20)

def generate_label(item):

    

    try:
        output = subprocess.check_output(['python', 'C:\\Users\\TM - Curran\\Documents\\Python Scripts\\Bagging Scripts\\getrecipes.py', item], stderr=subprocess.STDOUT)
        output_str = output.decode('utf-8').strip()
        print(repr(output_str))
        recipes = json.loads(output_str)
        print(recipes)
    except subprocess.CalledProcessError as e:
        print(e.output.decode('utf-8'))

    # Update Recipe Compositions

    try:
        output = subprocess.check_output(['python', 'C:\\Users\\TM - Curran\\Documents\\Python Scripts\\Bagging Scripts\\MRFRecipeCompositions.py', json.dumps(recipes)], stderr=subprocess.STDOUT)
       
        # Convert the JSON string back into a DataFrame
        df5 = pd.read_json(output.decode('utf-8'), orient='records')
        
        
    except subprocess.CalledProcessError as e:
        print(e.output.decode('utf-8'))

    # Get the current date and time
    now = datetime.now()

    # Format the date and time
    formatted_date = now.strftime("%B %d, %Y at %I:%M %p")

    # Print the formatted date and time
    print(formatted_date)

    # Establish SQL connection
    server = r"TM-SQL1\BESTMIX" 
    database = r"Batching" 
    username = "curran" 
    password = "SuperLay22" 
    cnxn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER="+server+"; DATABASE="+database+";UID="+username+";PWD="+ password,autocommit=True)
    cursor = cnxn.cursor()



    cursor.execute("SELECT [Description], [Ingredient List] FROM [Bagging].[dbo].[RecipeLists] WHERE [Recipe] = ?", item)
    ingredientList = cursor.fetchall()
    print(ingredientList[0][0])

    cursor.execute("SELECT * FROM [Products].[dbo].[LabelInfo] WHERE [Item] = ?", item)
    datadict = cursor.fetchall()

    columns = [column[0] for column in cursor.description]

    labelDict = {
        "item": datadict[0][columns.index('Item')],
        "species": datadict[0][columns.index('Species')],
        "upc": datadict[0][columns.index('UPC')],
        "description": ingredientList[0][0],
        "purpose": datadict[0][columns.index('Purpose')],
        "crudeProtein": datadict[0][columns.index('crudeProtein')],
        "equivalentCP": datadict[0][columns.index('equivalentCP')],
        "lysine": datadict[0][columns.index('lysine')],
        "methionine": datadict[0][columns.index('methionine')],
        "crudeFat": datadict[0][columns.index('crudeFat')],
        "crudeFiber": datadict[0][columns.index('crudeFiber')],
        "adf": datadict[0][columns.index('adf')],
        "ndf": datadict[0][columns.index('ndf')],
        "calciumMin": datadict[0][columns.index('calciumMin')],
        "calciumMax": datadict[0][columns.index('calciumMax')],
        "phosphorus": datadict[0][columns.index('phosphorus')],
        "saltMin": datadict[0][columns.index('saltMin')],
        "saltMax": datadict[0][columns.index('saltMax')],
        "sodiumMin": datadict[0][columns.index('sodiumMin')],
        "sodiumMax": datadict[0][columns.index('sodiumMax')],
        "magnesium": datadict[0][columns.index('magnesium')],
        "potassium": datadict[0][columns.index('potassium')], 
        "copper": datadict[0][columns.index('copper')],
        "selenium": datadict[0][columns.index('selenium')],
        "zinc": datadict[0][columns.index('zinc')],
        "vitaminA": datadict[0][columns.index('vitaminA')],
        "ingredientList": ingredientList[0][1],
        "directions": datadict[0][columns.index('Directions')],
        "storage": datadict[0][columns.index('Storage')],
        "weight": datadict[0][columns.index('Weight')],
        "qr":datadict[0][columns.index('qr')]
    }

    


    # Query the nutrientvalues table to get the actual values for each nutrient
    cursor.execute("""SELECT [Description], [Value] 
    FROM 
    [Bagging].[dbo].[nutrientvalues] JOIN [Bagging].[dbo].[nutrients] 
    ON [Bagging].[dbo].[nutrientvalues].[Nutrient] = [Bagging].[dbo].[nutrients].[Item]
    WHERE 
    [Description] IN('Crude Protein (min)', 'Crude Fat (min)', 'Crude Fiber (max)', 'NPN', 'ADF (max)',
    'NDF (max)', 'Lysine (min)', 'Methionine (min)', 'Calcium (min)', 'Phosphorus (min)', 'Salt (min)', 
    'Sodium (min)', 'Mg', 'Potassium (min)', 'Copper (min)', 'Selenium (min)', 'Zinc (min)', 'Vitamin A (min)')
    AND Recipe = ?""", item)
    nutrient_values = {row.Description: row.Value for row in cursor.fetchall()}

    # Add missing nutrient descriptions to the dictionary with a value of None
    for description in ['Crude Protein (min)', 'Crude Fat (min)', 'Crude Fiber (max)', 'NPN', 'ADF (max)',
        'NDF (max)', 'Lysine (min)', 'Methionine (min)', 'Calcium (min)', 'Phosphorus (min)', 'Salt (min)', 
        'Sodium (min)', 'Mg', 'Potassium (min)', 'Copper (min)', 'Selenium (min)', 'Zinc (min)', 'Vitamin A (min)']:
        if description not in nutrient_values:
            nutrient_values[description] = None


    # Determine the nutrient requirements based on the selected species
    if labelDict['species'] == "Horses":
        data = [
            ["Crude Protein (min)", str(labelDict['crudeProtein'])+'%', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
            ["Crude Fat (min)", str(labelDict['crudeFat'])+'%', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
            ["Crude Fiber (max)", str(labelDict['crudeFiber'])+'%', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
            ["Acid Detergent Fiber (ADF) (max)", str(labelDict['adf'])+'%', f" {round(nutrient_values['ADF (max)'], 1)} %"],
            ["Neutral Detergent Fiber (NDF) (max)", str(labelDict['ndf'])+'%', f" {round(nutrient_values['NDF (max)'], 1)} %"],
            ["Calcium (min/max)", str(labelDict['calciumMin'])+'%/'+str(labelDict['calciumMax'])+'%', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
            ["Phosphorus (min)", str(labelDict['phosphorus'])+'%', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
            ["Copper (min)", str(labelDict['copper'])+' ppm', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
            ["Selenium (min)", str(labelDict['selenium'])+' ppm', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"],
            ["Zinc (min)", str(labelDict['zinc'])+' ppm', f" {round(nutrient_values['Zinc (min)'], 1)} ppm"],
            ["Vitamin A (min)", "{:,.0f}".format(labelDict['vitaminA'])+' IU/lb', f"{nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
        ]
    elif labelDict['species'] == "AllStock":
        data = [
            ["Crude Protein (min)", str(labelDict['crudeProtein'])+'%', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
            ["Crude Fat (min)", str(labelDict['crudeFat'])+'%', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
            ["Crude Fiber (max)", str(labelDict['crudeFiber'])+'%', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
            ["Acid Detergent Fiber (ADF) (max)", str(labelDict['adf'])+'%', f" {round(nutrient_values['ADF (max)'], 1)} %"],
            ["Neutral Detergent Fiber (NDF) (max)", str(labelDict['ndf'])+'%', f" {round(nutrient_values['NDF (max)'], 1)} %"],
            ["Calcium (min/max)", str(labelDict['calciumMin'])+'%/'+str(labelDict['calciumMax'])+'%', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
            ["Phosphorus (min)", str(labelDict['phosphorus'])+'%', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
            ["Salt (min/max)", str(labelDict['saltMin'])+'%/'+str(labelDict['saltMax'])+'%', f" {round(nutrient_values['Salt (min)'], 1)} %"],
            ["Sodium (min/max)", str(labelDict['sodiumMin'])+'%/'+str(labelDict['sodiumMax'])+'%', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
            ["Potassium (min)", str(labelDict['potassium'])+'%', f" {round(nutrient_values['Salt (min)'], 1)} %"],
            ["Copper (min)", str(labelDict['copper'])+' ppm', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
            ["Selenium (min)", str(labelDict['selenium'])+' ppm', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"],
            ["Zinc (min)", str(labelDict['zinc'])+' ppm', f" ({round(nutrient_values['Zinc (min)'], 1)} ppm"],
            ["Vitamin A (min)", "{:,.0f}".format(labelDict['vitaminA'])+' IU/lb', f" {nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
        ]
    elif labelDict['species'] == "Swine":
        data = [
            ["Crude Protein (min)", str(labelDict['crudeProtein'])+'%', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
            ["Lysine (min)", str(labelDict['lysine'])+'%', f" {round(nutrient_values['Lysine (min)'], 1)} %"],
            ["Crude Fat (min)", str(labelDict['crudeFat'])+'%', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
            ["Crude Fiber (max)", str(labelDict['crudeFiber'])+'%', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
            ["Calcium (min/max)", str(labelDict['calciumMin'])+'%/'+str(labelDict['calciumMax'])+'%', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
            ["Phosphorus (min)", str(labelDict['phosphorus'])+'%', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
            ["Salt (min/max)", str(labelDict['saltMin'])+'%/'+str(labelDict['saltMax'])+'%', f" {round(nutrient_values['Salt (min)'], 1)} %"],
            ["Sodium (min/max)", str(labelDict['sodiumMin'])+'%/'+str(labelDict['sodiumMax'])+'%', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
            ["Copper (min)", str(labelDict['copper'])+' ppm', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
            ["Selenium (min)", str(labelDict['selenium'])+' ppm', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"]
        ]
    elif labelDict['species'] == "Poultry":
        data = [
            ["Crude Protein (min)", str(labelDict['crudeProtein'])+'%', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
            ["Lysine (min)", str(labelDict['lysine'])+'%', f" {round(nutrient_values['Lysine (min)'], 1)} %"],
            ["Methionine (min)", str(labelDict['methionine'])+'%', f" {round(nutrient_values['Methionine (min)'], 1)} %"],
            ["Crude Fat (min)", str(labelDict['crudeFat'])+'%', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
            ["Crude Fiber (max)", str(labelDict['crudeFiber'])+'%', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
            ["Calcium (min/max)", str(labelDict['calciumMin'])+'%/'+str(labelDict['calciumMax'])+'%', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
            ["Phosphorus (min)", str(labelDict['phosphorus'])+'%', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
            ["Salt (min/max)", str(labelDict['saltMin'])+'%/'+str(labelDict['saltMax'])+'%', f" {round(nutrient_values['Salt (min)'], 1)} %"],
            ["Sodium (min/max)", str(labelDict['sodiumMin'])+'%/'+str(labelDict['sodiumMax'])+'%', f" {round(nutrient_values['Sodium (min)'], 1)} %"]
        ]
    elif labelDict['species'] == "Rabbits":
        data = [
            ["Crude Protein (min)", str(labelDict['crudeProtein'])+'%', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
            ["Crude Fat (min)", str(labelDict['crudeFat'])+'%', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
            ["Crude Fiber (max)", str(labelDict['crudeFiber'])+'%', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
            ["Calcium (min/max)", str(labelDict['calciumMin'])+'%/'+str(labelDict['calciumMax'])+'%', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
            ["Phosphorus (min)", str(labelDict['phosphorus'])+'%', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
            ["Salt (min/max)", str(labelDict['saltMin'])+'%/'+str(labelDict['saltMax'])+'%', f" {round(nutrient_values['Salt (min)'], 1)} %"],
            ["Sodium (min/max)", str(labelDict['sodiumMin'])+'%/'+str(labelDict['sodiumMax'])+'%', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
            ["Vitamin A (min)", "{:,.0f}".format(labelDict['vitaminA'])+' IU/lb', f" {nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
        ]
    elif labelDict['species'] == "Grains":
        data = [
            ["Crude Protein (min)", str(labelDict['crudeProtein'])+'%', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
            ["Crude Fat (min)", str(labelDict['crudeFat'])+'%', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
            ["Crude Fiber (max)", str(labelDict['crudeFiber'])+'%', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
        ]
    elif labelDict['species'] == "Cattle" and labelDict['equivalentCP'] != None:
        data = [
            ["Crude Protein (min)", str(labelDict['crudeProtein'])+'%', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
            ["Crude Fat (min)", str(labelDict['crudeFat'])+'%', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
            ["Crude Fiber (max)", str(labelDict['crudeFiber'])+'%', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
            ["Calcium (min/max)", str(labelDict['calciumMin'])+'%/'+str(labelDict['calciumMax'])+'%', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
            ["Phosphorus (min)", str(labelDict['phosphorus'])+'%', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
            ["Salt (min/max)", str(labelDict['saltMin'])+'%/'+str(labelDict['saltMax'])+'%', f" {round(nutrient_values['Salt (min)'], 1)} %"],
            ["Sodium (min/max)", str(labelDict['sodiumMin'])+'%/'+str(labelDict['sodiumMax'])+'%', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
            ["Potassium (min)", str(labelDict['potassium'])+'%', f" {round(nutrient_values['Potassium (min)'], 1)} %"],
            ["Vitamin A (min)", "{:,.0f}".format(labelDict['vitaminA'])+' IU/lb', f"{nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
        ]
    elif labelDict['species'] == "Cattle" and labelDict['equivalentCP'] > 0:
        data = [
            ["Crude Protein (min)", str(labelDict['crudeProtein'])+'%', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
            ["Equivalent Crude Protein from Non-Protein Nitrogen (NPN) (min)", str(labelDict['equivalentCP'])+'%', f" {round(nutrient_values['NPN'], 1)} %"],
            ["Crude Fat (min)", str(labelDict['crudeFat'])+'%', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
            ["Crude Fiber (max)", str(labelDict['crudeFiber'])+'%', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
            ["Calcium (min/max)", str(labelDict['calciumMin'])+'%/'+str(labelDict['calciumMax'])+'%', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
            ["Phosphorus (min)", str(labelDict['phosphorus'])+'%', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
            ["Salt (min/max)", str(labelDict['saltMin'])+'%/'+str(labelDict['saltMax'])+'%', f" {round(nutrient_values['Salt (min)'], 1)} %"],
            ["Sodium (min/max)", str(labelDict['sodiumMin'])+'%/'+str(labelDict['sodiumMax'])+'%', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
            ["Potassium (min)", str(labelDict['potassium'])+'%', f" {round(nutrient_values['Potassium (min)'], 1)} %"],
            ["Vitamin A (min)", "{:,.0f}".format(labelDict['vitaminA'])+' IU/lb', f"{nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
        ]
    elif labelDict['species'] == "Goats" and labelDict['equivalentCP'] != None:
        data = [
            ["Crude Protein (min)", str(labelDict['crudeProtein'])+'%', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
            ["Crude Fat (min)", str(labelDict['crudeFat'])+'%', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
            ["Crude Fiber (max)", str(labelDict['crudeFiber'])+'%', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
            ["Acid Detergent Fiber (max)", str(labelDict['adf'])+'%', f" {round(nutrient_values['ADF (max)'], 1)} %"],
            ["Calcium (min/max)", str(labelDict['calciumMin'])+'%/'+str(labelDict['calciumMax'])+'%', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
            ["Phosphorus (min)", str(labelDict['phosphorus'])+'%', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
            ["Salt (min/max)", str(labelDict['saltMin'])+'%/'+str(labelDict['saltMax'])+'%', f" {round(nutrient_values['Salt (min)'], 1)} %"],
            ["Sodium (min/max)", str(labelDict['sodiumMin'])+'%/'+str(labelDict['sodiumMax'])+'%', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
            ["Copper (min)", str(labelDict['copper'])+'%', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
            ["Selenium (min)", str(labelDict['selenium'])+'%', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"],
            ["Vitamin A (min)", "{:,.0f}".format(labelDict['vitaminA'])+' IU/lb', f" {nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
        ]
    elif labelDict['species'] == "Goats" and labelDict['equivalentCP'] > 0:
        data = [
            ["Crude Protein (min)", str(labelDict['crudeProtein'])+'%', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
            ["Equivalent Crude Protein from Non-Protein Nitrogen (NPN) (min)", str(labelDict['equivalentCP'])+'%', f" {round(nutrient_values['NPN'], 1)} %"],
            ["Crude Fat (min)", str(labelDict['crudeFat'])+'%', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
            ["Crude Fiber (max)", str(labelDict['crudeFiber'])+'%', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
            ["Acid Detergent Fiber (max)", str(labelDict['adf'])+'%', f" {round(nutrient_values['ADF (max)'], 1)} %"],
            ["Calcium (min/max)", str(labelDict['calciumMin'])+'%/'+str(labelDict['calciumMax'])+'%', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
            ["Phosphorus (min)", str(labelDict['phosphorus'])+'%', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
            ["Salt (min/max)", str(labelDict['saltMin'])+'%/'+str(labelDict['saltMax'])+'%', f" {round(nutrient_values['Salt (min)'], 1)} %"],
            ["Sodium (min/max)", str(labelDict['sodiumMin'])+'%/'+str(labelDict['sodiumMax'])+'%', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
            ["Copper (min)", str(labelDict['copper'])+'%', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
            ["Selenium (min)", str(labelDict['selenium'])+'%', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"],
            ["Vitamin A (min)", "{:,.0f}".format(labelDict['vitaminA'])+' IU/lb', f"{nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
        ]
    elif labelDict['species'] == "Sheep" and labelDict['equivalentCP'] != None:
        data = [
            ["Crude Protein (min)", str(labelDict['crudeProtein'])+'%', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
            ["Crude Fat (min)", str(labelDict['crudeFat'])+'%', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
            ["Crude Fiber (max)", str(labelDict['crudeFiber'])+'%', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
            ["Calcium (min/max)", str(labelDict['calciumMin'])+'%/'+str(labelDict['calciumMax'])+'%', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
            ["Phosphorus (min)", str(labelDict['phosphorus'])+'%', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
            ["Salt (min/max)", str(labelDict['saltMin'])+'%/'+str(labelDict['saltMax'])+'%', f" {round(nutrient_values['Salt (min)'], 1)} %"],
            ["Sodium (min/max)", str(labelDict['sodiumMin'])+'%/'+str(labelDict['sodiumMax'])+'%', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
            ["Copper (min)", str(labelDict['copper'])+'%', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
            ["Selenium (min)", str(labelDict['selenium'])+'%', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"],
            ["Vitamin A (min)", "{:,.0f}".format(labelDict['vitaminA'])+' IU/lb', f" {nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
        ]
    elif labelDict['species'] == "Sheep" and labelDict['equivalentCP'] > 0:
        data = [
            ["Crude Protein (min)", str(labelDict['crudeProtein'])+'%', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
            ["Equivalent Crude Protein from Non-Protein Nitrogen (NPN) (min)", str(labelDict['equivalentCP'])+'%', f" {round(nutrient_values['NPN'], 1)} %"],
            ["Crude Fat (min)", str(labelDict['crudeFat'])+'%', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
            ["Crude Fiber (max)", str(labelDict['crudeFiber'])+'%', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
            ["Calcium (min/max)", str(labelDict['calciumMin'])+'%/'+str(labelDict['calciumMax'])+'%', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
            ["Phosphorus (min)", str(labelDict['phosphorus'])+'%', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
            ["Salt (min/max)", str(labelDict['saltMin'])+'%/'+str(labelDict['saltMax'])+'%', f" {round(nutrient_values['Salt (min)'], 1)} %"],
            ["Sodium (min/max)", str(labelDict['sodiumMin'])+'%/'+str(labelDict['sodiumMax'])+'%', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
            ["Copper (min)", str(labelDict['copper'])+'%', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
            ["Selenium (min)", str(labelDict['selenium'])+'%', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"],
            ["Vitamin A (min)", "{:,.0f}".format(labelDict['vitaminA'])+' IU/lb', f" {nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
        ]

    else:
        data = []

    folder_name = labelDict['item']
    folder_path = f"C:/Users/Public/{folder_name}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    version = 1
    while os.path.exists(f"{folder_path}/{labelDict['description']}_Feed_Label_v{version}.pdf"):
        version += 1


    doc = SimpleDocTemplate(f"{folder_path}/{labelDict['description']}_Feed_Label_v{version}.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    Story = []
    style = styles["Normal"]
   
    # Change the width of the ingredient list to 6 inches and remove line breaks
    justified_style = ParagraphStyle(name="justified", alignment=4,
                                     spaceBefore=6,
                                     spaceAfter=6,
                                     rightIndent=(doc.width-6*inch)/2,
                                     leftIndent=(doc.width-6*inch)/2,
                                     parent=styles["Normal"])
    
    class UPC:
        """
        The all-in-one class that represents the UPC-A
        barcode.
        """

        QUIET = "000000000"
        EDGE = "101"
        MIDDLE = "01010"
        CODES = {
            "L": (
                "0001101",
                "0011001",
                "0010011",
                "0111101",
                "0100011",
                "0110001",
                "0101111",
                "0111011",
                "0110111",
                "0001011",
            ),
            "R": (
                "1110010",
                "1100110",
                "1101100",
                "1000010",
                "1011100",
                "1001110",
                "1010000",
                "1000100",
                "1001000",
                "1110100",
            ),
        }
        SIZE = "{0:.3f}mm"
        MODULE_WIDTH = 0.33
        MODULE_HEIGHT = 25.9
        EXTENDED_MODULE_HEIGHT = MODULE_HEIGHT + 5*MODULE_WIDTH
        BARCODE_HEIGHT = EXTENDED_MODULE_HEIGHT
        TOTAL_MODULES = 113

        def __init__(self, upc):
            self.upc = list(str(upc))[:11]
            if len(self.upc) < 11:
                raise Exception(f"The UPC has to be of length 11 or 12 (with check digit)")
            self.upc = self.upc + self.calculate_check_digit()
            encoded_code = self.encode()
            self.create_barcode()
            self.save("upc_custom.svg")

        def calculate_check_digit(self):
            """
            Calculate the check digit
            """
            upc = [int(digit) for digit in self.upc[:11]]
            oddsum = sum(upc[::2])
            evensum = sum(upc[1::2])

            check = (evensum + oddsum * 3) % 10
            if check == 0:
                return [0]
            else:
                return [10 - check]

        def encode(self):
            """
            Encode the UPC based on the mapping defined above
            """
            code = self.EDGE[:]
            for _i, number in enumerate(self.upc[0:6]):
                code += self.CODES["L"][int(number)]
            code += self.MIDDLE
            for number in self.upc[6:]:
                code += self.CODES["R"][int(number)]
            code += self.EDGE
            self.encoded_upc = code

        def create_text(self, text, xpos, ypos):
            """
            Create a text element and append it to the SVG group
            """
            element = self._document.createElement("text")
            element.setAttribute("x", self.SIZE.format(xpos))
            element.setAttribute("y", self.SIZE.format(ypos))
            element.setAttribute("font-size", "3mm")
            element.appendChild(self._document.createTextNode(str(text)))
            self._group.appendChild(element)

        def create_barcode(self):
            self.prepare_svg()

            # Quiet zone is automatically added as the background is white We will
            # simply skip the space for 9 modules and start the guard from there

            x_position = 9 * self.MODULE_WIDTH
            for count, extended in self.packed(self.encoded_upc):
                if count < 0:
                    color = "white"
                else:
                    color = "black"

                config = {
                    "xpos": x_position,
                    "ypos": -1.5,
                    "color": color,
                    "width": abs(count) * self.MODULE_WIDTH,
                    "height": self.EXTENDED_MODULE_HEIGHT if extended else self.MODULE_HEIGHT,
                }
                self.create_module(**config)
                x_position += abs(count) * self.MODULE_WIDTH

            # Add text elements for each digit of the UPC number
            x_position = 9 * self.MODULE_WIDTH
            for i, digit in enumerate(self.upc):
                if i == 0:
                    x_offset = -7 * self.MODULE_WIDTH
                elif i > 0 and i < 6:
                    x_offset = 6 * self.MODULE_WIDTH
                elif i >= 6 and i < 11:
                    x_offset = 11 * self.MODULE_WIDTH
                elif i == 11:
                    x_offset = 8

                self.create_text(digit, x_position + x_offset, self.BARCODE_HEIGHT)
                if i == 5:
                    x_position += 4.2 * self.MODULE_WIDTH
                x_position += 6.2 * self.MODULE_WIDTH

        def packed(self, encoded_upc):
            """
            Pack the encoded UPC to a list. Ex:
                "001101" -> [-2, 2, -1, 1]
            """
            encoded_upc += " "
            extended_bars = [1,2,3, 4,5,6,7, 28,29,30,31,32, 53,54,55,56, 57,58,59]
            count = 1
            bar_count = 1
            for i in range(0, len(encoded_upc) - 1):
                if encoded_upc[i] == encoded_upc[i + 1]:
                    count += 1
                else:
                    if encoded_upc[i] == "1":
                        yield count, bar_count in extended_bars
                    else:
                        yield -count, bar_count in extended_bars
                    bar_count += 1
                    count = 1

        def prepare_svg(self):
            """
            Create the complete boilerplate SVG for the barcode
            """
            self._document = self.create_svg_object()
            self._root = self._document.documentElement

            group = self._document.createElement("g")
            group.setAttribute("id", "barcode_group")
            self._group = self._root.appendChild(group)

            background = self._document.createElement("rect")
            background.setAttribute("width", "100%")
            background.setAttribute("height", "100%")
            background.setAttribute("style", "fill: white")
            self._group.appendChild(background)

        def create_svg_object(self):
            """
            Create an SVG object
            """
            imp = xml.dom.getDOMImplementation()
            doctype = imp.createDocumentType(
                "svg",
                "-//W3C//DTD SVG 1.1//EN",
                "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd",
            )
            document = imp.createDocument(None, "svg", doctype)
            document.documentElement.setAttribute("version", "1.1")
            document.documentElement.setAttribute("xmlns", "http://www.w3.org/2000/svg")
            document.documentElement.setAttribute(
                "width", self.SIZE.format(self.TOTAL_MODULES * self.MODULE_WIDTH)
            )
            document.documentElement.setAttribute(
                "height", self.SIZE.format(self.BARCODE_HEIGHT)
            )
            return document

        def create_module(self, xpos, ypos, width, height, color):
            """
            Create a module and append a corresponding rect to the SVG group
            """
            element = self._document.createElement("rect")
            element.setAttribute("x", self.SIZE.format(xpos))
            element.setAttribute("y", self.SIZE.format(ypos))
            element.setAttribute("width", self.SIZE.format(width))
            element.setAttribute("height", self.SIZE.format(height))
            element.setAttribute("style", "fill:{};".format(color))
            self._group.appendChild(element)

        def save(self, filename):
            """
            Dump the final SVG XML code to a file
            """
            output = self._document.toprettyxml(
                indent=4 * " ", newl=os.linesep, encoding="UTF-8"
            )
            with open(filename, "wb") as f:
                f.write(output)

        def to_memory(self):
            """
            Return the final SVG XML code as a string
            """
            output = self._document.toprettyxml(
                indent=4 * " ", newl=os.linesep, encoding="UTF-8"
            )
            return output.decode("UTF-8")
    
    upc = UPC(labelDict['upc'])
    upc.save('C:/Users/Public/my_file.svg') 
   
    barcode_image = svg2rlg('C:/Users/Public/my_file.svg')

    # Scale the drawing to half its size
    barcode_image.width, barcode_image.height = barcode_image.minWidth(), barcode_image.height
    barcode_image.scale(0.75, 0.75)

    # Create a container to hold the barcode and product code
    barcode_container = []
    barcode_container.append(barcode_image)
    barcode_container.append(Spacer(1, 0.1 * inch))
    barcode_container.append(Paragraph(labelDict['item'], style))
    

    # Define a paragraph style for the "81114" text
    style = ParagraphStyle(name="Normal", fontName="Helvetica", fontSize=14)
    small_style = ParagraphStyle(name="Normal", fontName="Helvetica", fontSize=12)

    # Create the "81114" text using the defined style
    barcode_text = Paragraph(labelDict['item'], small_style)

    # Create a table with two cells
    barcode_table = Table([[barcode_text, barcode_image]], colWidths=[3 * inch, 3 * inch])

    # Set the alignment of the first cell to left and the second cell to right
    # Set the vertical alignment of the first cell to top and the second cell to bottom
    barcode_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (0, 0), "CENTER"),
        ("VALIGN", (1, 0), (1, 0), "TOP")
    ]))

    # Add the table to the story
    Story.append(barcode_table)

    Story.append(Spacer(1, 0.25 * inch))
    
    # Center justify the product name and change the font size to 16
    centered_style = ParagraphStyle(
        name="centered", 
        alignment=1, 
        parent=styles["Normal"])
    
    centered_bold_style = ParagraphStyle(
        name='CenteredBold',
        alignment=1,
        fontSize=12,
        leading=14,
        textColor=colors.black,
        fontName='Helvetica-Bold'
)
    large_centered_style = ParagraphStyle(name="large_centered", alignment=1, fontSize=16, fontName='Helvetica-Bold', parent=styles["Normal"])
    Story.append(Paragraph(labelDict['description'], large_centered_style))
    Story.append(Spacer(1, 0.25 * inch))

    # Center the purpose statement and remove "Purpose Statement:"
    Story.append(Paragraph(labelDict['purpose'], centered_style))
    Story.append(Spacer(1, 0.25 * inch))

    # Center the guaranteed analysis section
    Story.append(Paragraph("Guaranteed Analysis", centered_bold_style))
    Story.append(Spacer(1, 0.25 * inch))

    # Add headers to the data
    data.insert(0, ["", "Guaranteed", "Calculated"])

    # Create a table for the guaranteed analysis section
    table = Table(data, colWidths=[2.5 * inch, 1.5 * inch])
    table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), # Set font to bold for first row
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2)
    ]))
    
    Story.append(table)


    Story.append(Spacer(1, 0.25 * inch))

    # Center the ingredient statement and fully justify the ingredient list
    Story.append(Paragraph("Ingredient Statement", centered_bold_style))
    
    
    Story.append(Paragraph(labelDict['ingredientList'],
                           justified_style))
    
    Story.append(Spacer(1, 0.25 * inch))

    exec(labelDict['directions'])

    Story.append(Spacer(1, 0.25 * inch))

    # Center the ingredient statement and fully justify the ingredient list
    Story.append(Paragraph("Storage", centered_bold_style))    

    # Add storage information
    Story.append(Paragraph(labelDict['storage'],
                           justified_style))
    Story.append(Spacer(1, 0.25 * inch))

    # Update manufacturer information
    Story.append(Paragraph("Manufactured by Tucker Milling LLC<br/>Guntersville, AL 35976", centered_bold_style))
    Story.append(Spacer(1, 0.25 * inch))
    
    # Center the net quantity statement
    Story.append(
    Paragraph(
        f"Net Weight {labelDict['weight']} lb ({round(float(labelDict['weight'])/2.2046,1)} kg)",
        centered_bold_style
    )
)

    # Generate a QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(labelDict['qr'])
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Save the QR code image in memory
    qr_image = BytesIO()
    qr_img.save(qr_image)

    # Create an Image object from the QR code image
    qr_image.seek(0)
    qr_image = PlatypusImage(qr_image)

    # Set the size of the QR code image to 1 inch by 1 inch
    qr_image.drawWidth = 1 * inch
    qr_image.drawHeight = 1 * inch

    # Add the QR code image to the bottom of the document
    Story.append(Spacer(1, 0.25 * inch))
    Story.append(qr_image)

    # Insert a page break
    Story.append(PageBreak())
  
    print(type(df5))
    print(f'df5 = {df5}')
 
    # Get the distinct recipes from the DataFrame
    distinct_recipes = df5['Recipe'].unique()
    # List to store the tables
    table_list = []


        # Create a table for each distinct recipe
    for index, recipe in enumerate(distinct_recipes):
        # Retrieve the description for the current recipe from the RecipeLists table
        cursor.execute("SELECT [Description], [Ingredient List] FROM [Bagging].[dbo].[RecipeLists] WHERE [Recipe] = ?", recipe)
        results = cursor.fetchall()
        descriptions = results[0][0]

        # Filter the DataFrame for the current recipe
        recipe_data = df5[df5['Recipe'] == recipe][['Item', 'Description', 'lb_ton', 'Value']]
        
        # Filter the DataFrame for the current recipe and where the 'lb_ton' column is greater than zero
        recipe_data = df5[(df5['Recipe'] == recipe) & (df5['lb_ton'] > 0)][['Item', 'Description', 'lb_ton', 'Value']]

        # Round the values in the 'lb_ton' column to one decimal place
        recipe_data['lb_ton'] = recipe_data['lb_ton'].round(1)

        # Round the values in the 'Value' column to one decimal place
        recipe_data['Value'] = recipe_data['Value'].round(1)

        # Round the values in the 'Value' column to the nearest 0.05 if less than 1
        recipe_data['lb_ton'] = recipe_data['lb_ton'].apply(lambda x: round(x / 0.05) * 0.05 if x < 0.1 else round(x, 1))

        # Round the values in the 'Value' column to 3 decimal places if less than 0.1
        recipe_data['Value'] = recipe_data['Value'].apply(lambda x: round(x, 3) if x < 0.1 else round(x, 1))

        # Sort the recipe data by 'lb_ton' column in descending order
        recipe_data = recipe_data.sort_values('lb_ton', ascending=False)

        # Convert the recipe data to a 2D list for the table
        data = [list(recipe_data.columns)] + recipe_data.values.tolist()

         # Change the 'lb_ton' header to 'lb/ton' and the 'Value' header to '%'
        data[0][data[0].index('lb_ton')] = 'lb/ton'
        data[0][data[0].index('Value')] = '%'

        # Add the recipe number to the top left of the page
        text = "<font size='12'>{}</font>".format(recipe)
        style = getSampleStyleSheet()['Normal']
        style.alignment = TA_LEFT
        recipe_paragraph = Paragraph(text, style)
        Story.append(recipe_paragraph) # Appending recipe

        Story.append(Spacer(1, 0.25 * inch))

        # Add the recipe description to the top center of the page
        text2 = "<font size='16'>{}</font>".format(descriptions)
        style2 = getSampleStyleSheet()['Heading1']
        style2.alignment = TA_CENTER
        recipe_paragraph2 = Paragraph(text2, style2)
        Story.append(recipe_paragraph2) # Appending description

        Story.append(Spacer(1, 0.25 * inch))

        # Create a table using the data
        table = Table(data)
        

        # Apply table styles
        table.setStyle(TableStyle([
            # Right-justify 'lb_ton' and 'Value' columns
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        
            # Bold the headers
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        
            # Add other style options if needed
        ]))

        # Add the table to the story
        Story.append(table)
        Story.append(Spacer(1, 0.25 * inch))

         # Center the ingredient statement and fully justify the ingredient list
        Story.append(Paragraph("Mixing Directions", centered_bold_style))    

        # Add storage information
        Story.append(Paragraph("Dry mix for 5 seconds and and wet mix for an additional 80 seconds after any liquid addition.", justified_style))
        Story.append(Spacer(1, 0.25 * inch))

        # Add a page break after each table, except for the last one
        if index != len(distinct_recipes) - 1:
            Story.append(PageBreak())


    doc.build(Story)



item = '81114'

try:
        output = subprocess.check_output(['python', 'C:\\Users\\TM - Curran\\Documents\\Python Scripts\\Bagging Scripts\\getrecipes1.py', item], stderr=subprocess.STDOUT)
        output_str = output.decode('utf-8')
        recipes = json.loads(output_str)

except subprocess.CalledProcessError as e:
        print(e.output.decode('utf-8'))

print(recipes)


for item in recipes:
    generate_label(item)


