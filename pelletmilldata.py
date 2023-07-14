import os
import sys
import json
from io import BytesIO, StringIO
from datetime import datetime, timedelta

import re
import pandas as pd
import pyodbc
import subprocess
import qrcode
import barcode
from barcode.writer import ImageWriter
from PIL import Image
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Frame,
    Image,
    Table,
    Flowable,
    PageTemplate,
    TableStyle,
    KeepTogether,
    PageBreak,
    NextPageTemplate,
)
from reportlab.platypus import Image as PlatypusImage
import tempfile
import xml.dom
import ast
from io import BytesIO
from PIL import Image
from PyPDF2 import PdfReader, PdfMerger


pd.set_option('display.max_colwidth', 200)
pd.set_option('display.max_columns',20)

def generate_label(item, salesQC):
    
    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            """add page info to each page (page x of y)"""
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_number(num_pages)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)

        def draw_page_number(self, page_count):
            self.setFont("Helvetica", 10)
            page_number_text = "Page %d of %d" % (self._pageNumber, page_count)
            page_number_width = self.stringWidth(page_number_text, "Helvetica", 10)
            x = self._pagesize[0] - page_number_width - 1 * inch
            self.drawString(x, 20 * mm, page_number_text)
            self.draw_master_record_info(x, self._pagesize, page_number_width, self._pageNumber)
            self.draw_current_date_time()

        def draw_master_record_info(self, x, _pagesize, page_number_width, _pageNumber):
            self.setFont("Helvetica-Bold", 10)
            if salesQC == 0:
                self.drawString(1 * inch, 255 * mm, f"Master Record File")
            elif salesQC == 1:
                self.drawString(1 * inch, 255 * mm, f"Sales and QC Product File")

            folder_path = f"C:/Users/Public/{labelDict['item']}"
            pattern = re.compile(rf"{labelDict['description']}_Feed_Label_v(\d+)\.pdf$")
            max_version = 0
            for filename in os.listdir(folder_path):
                match = pattern.match(filename)
                if match:
                    version = int(match.group(1))
                    if version > max_version:
                        max_version = version + 1
            if self._pageNumber == 1:
                item_text = f"Version  {max_version}"
                space_width = self.stringWidth(" ", "Helvetica-Bold", 10)
                item_text_width = self.stringWidth(item_text, "Helvetica-Bold", 10)
                text_width = item_text_width
                x = self._pagesize[0] - text_width - 1 * inch

                # Draw the item text in bold
                self.setFont("Helvetica-Bold", 10)
                self.drawString(x, 255 * mm, item_text)
                x += item_text_width
            if self._pageNumber > 1:
                item_text = labelDict['item']
                description_text = labelDict['description']
                space_width = self.stringWidth(" ", "Helvetica-Bold", 10)
                item_text_width = self.stringWidth(item_text, "Helvetica-Bold", 10)
                description_text_width = self.stringWidth(description_text, "Helvetica", 10)
                text_width = item_text_width + space_width + description_text_width
                x = self._pagesize[0] - text_width - 1 * inch

                # Draw the item text in bold
                self.setFont("Helvetica-Bold", 10)
                self.drawString(x, 255 * mm, item_text)
                x += item_text_width + space_width

                # Draw the description text in a regular font
                self.setFont("Helvetica", 10)
                self.drawString(x, 255 * mm, description_text)
            self.setFont("Helvetica", 10)
            self.drawString(1 * inch, 20 * mm, "Tucker Milling, LLC")

        def draw_current_date_time(self):
            now = datetime.now()
            formatted_date = now.strftime("%B %d, %Y at %I:%M %p")
            self.setFont("Helvetica", 10)
            x = self._pagesize[0] / 2
            self.drawCentredString(x, 20 * mm, formatted_date)

    try:
        output = subprocess.check_output(['python', 'C:\\Users\\TM - Curran\\Documents\\Python Scripts\\Bagging Scripts\\getrecipes.py', item], stderr=subprocess.STDOUT)
        output_str = output.decode('utf-8').strip()
        recipes = json.loads(output_str)
    except subprocess.CalledProcessError as e:
        print(e.output.decode('utf-8'))

    # Update Recipe Compositions

    try:
        output = subprocess.check_output(['python', 'C:\\Users\\TM - Curran\\Documents\\Python Scripts\\Bagging Scripts\\MRFRecipeCompositions.py', json.dumps(recipes)], stderr=subprocess.STDOUT)
       
        # Convert the JSON string back into a DataFrame
        df5 = pd.read_json(output.decode('utf-8'), orient='records')
 
        
    except subprocess.CalledProcessError as e:
        print(e.output.decode('utf-8'))


    # Establish SQL connection
    server = r"TM-SQL1\BESTMIX" 
    database = r"Batching" 
    username = "curran" 
    password = "SuperLay22" 
    cnxn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER="+server+"; DATABASE="+database+";UID="+username+";PWD="+ password,autocommit=True)
    cursor = cnxn.cursor()



    cursor.execute("SELECT [Description], [Ingredient List] FROM [Bagging].[dbo].[RecipeLists] WHERE [Recipe] = ?", item)
    ingredientList = cursor.fetchall()

    cursor.execute("SELECT * FROM [Products].[dbo].[LabelInfo] WHERE [Item] = ?", item)
    datadict = cursor.fetchall()

    columns = [column[0] for column in cursor.description]

    labelDict = {
        "item": datadict[0][columns.index('Item')],
        "species": datadict[0][columns.index('Species')],
        "upc": datadict[0][columns.index('UPC')],
        "type": datadict[0][columns.index('Type')],
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
        "copperMin": datadict[0][columns.index('copperMin')],
        "copperMax": datadict[0][columns.index('copperMax')],
        "selenium": datadict[0][columns.index('selenium')],
        "zinc": datadict[0][columns.index('zinc')],
        "vitaminA": datadict[0][columns.index('vitaminA')],
        "ingredientList": ingredientList[0][1],
        "directions": datadict[0][columns.index('Directions')],
        "storage": datadict[0][columns.index('Storage')],
        "weight": datadict[0][columns.index('Weight')],
        "qr":datadict[0][columns.index('qr')],
        "bagIngredientList":datadict[0][columns.index('BagIngredients')],
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
    ["Crude Protein (min)", f"{labelDict['crudeProtein']}%" if labelDict['crudeProtein'] is not None else '', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
    ["Crude Fat (min)", f"{labelDict['crudeFat']}%" if labelDict['crudeFat'] is not None else '', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
    ["Crude Fiber (max)", f"{labelDict['crudeFiber']}%" if labelDict['crudeFiber'] is not None else '', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
    ["Acid Detergent Fiber (ADF) (max)", f"{labelDict['adf']}%" if labelDict['adf'] is not None else '', f" {round(nutrient_values['ADF (max)'], 1)} %"],
    ["Neutral Detergent Fiber (NDF) (max)", f"{labelDict['ndf']}%" if labelDict['ndf'] is not None else '', f" {round(nutrient_values['NDF (max)'], 1)} %"],
    ["Calcium (min/max)", f"{labelDict['calciumMin']}%/{labelDict['calciumMax']}%" if labelDict['calciumMin'] is not None and labelDict['calciumMax'] is not None else '', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
    ["Phosphorus (min)", f"{labelDict['phosphorus']}%" if labelDict['phosphorus'] is not None else '', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
    ["Copper (min)", f"{labelDict['copperMin']} ppm" if labelDict['copperMin'] is not None else '', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
    ["Selenium (min)", f"{labelDict['selenium']} ppm" if labelDict['selenium'] is not None else '', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"],
    ["Zinc (min)", f"{labelDict['zinc']} ppm" if labelDict['zinc'] is not None else '', f" {round(nutrient_values['Zinc (min)'], 1)} ppm"],
    ["Vitamin A (min)", f"{labelDict['vitaminA']:,} IU/lb" if labelDict['vitaminA'] is not None else '', f"{nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
                ]
    elif labelDict['species'] == "All Stock":
        data = [
    ["Crude Protein (min)", f"{labelDict['crudeProtein']}%" if labelDict['crudeProtein'] is not None else '', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
    ["Crude Fat (min)", f"{labelDict['crudeFat']}%" if labelDict['crudeFat'] is not None else '', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
    ["Crude Fiber (max)", f"{labelDict['crudeFiber']}%" if labelDict['crudeFiber'] is not None else '', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
    ["Acid Detergent Fiber (ADF) (max)", f"{labelDict['adf']}%" if labelDict['adf'] is not None else '', f" {round(nutrient_values['ADF (max)'], 1)} %"],
    ["Neutral Detergent Fiber (NDF) (max)", f"{labelDict['ndf']}%" if labelDict['ndf'] is not None else '', f" {round(nutrient_values['NDF (max)'], 1)} %"],
    ["Calcium (min/max)", f"{labelDict['calciumMin']}%/{labelDict['calciumMax']}%" if labelDict['calciumMin'] is not None and labelDict['calciumMax'] is not None else '', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
    ["Phosphorus (min)", f"{labelDict['phosphorus']}%" if labelDict['phosphorus'] is not None else '', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
    ["Salt (min/max)", f"{labelDict['saltMin']}%/{labelDict['saltMax']}%" if labelDict['saltMin'] is not None and labelDict['saltMax'] is not None else '', f" {round(nutrient_values['Salt (min)'], 1)} %"],
    ["Sodium (min/max)", f"{labelDict['sodiumMin']}%/{labelDict['sodiumMax']}%" if labelDict['sodiumMin'] is not None and labelDict['sodiumMax'] is not None else '', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
    ["Potassium (min)", f"{labelDict['potassium']}%" if labelDict['potassium'] is not None else '', f" {round(nutrient_values['Salt (min)'], 1)} %"],
    ["Copper (min)", f"{labelDict['copperMin']} ppm" if labelDict['copperMin'] is not None else '', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
    ["Selenium (min)", f"{labelDict['selenium']} ppm" if labelDict['selenium'] is not None else '', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"],
    ["Zinc (min)", f"{labelDict['zinc']} ppm" if labelDict['zinc'] is not None else '', f" {round(nutrient_values['Zinc (min)'], 1)} ppm"],
    ["Vitamin A (min)", f"{labelDict['vitaminA']:,} IU/lb" if labelDict['vitaminA'] is not None else '', f"{nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
            ]
    elif labelDict['species'] == "Swine":
        data = [
    ["Crude Protein (min)", f"{labelDict['crudeProtein']}%" if labelDict['crudeProtein'] is not None else '', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
    ["Lysine (min)", f"{labelDict['lysine']}%" if labelDict['lysine'] is not None else '', f" {round(nutrient_values['Lysine (min)'], 1)} %"],
    ["Crude Fat (min)", f"{labelDict['crudeFat']}%" if labelDict['crudeFat'] is not None else '', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
    ["Crude Fiber (max)", f"{labelDict['crudeFiber']}%" if labelDict['crudeFiber'] is not None else '', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
    ["Calcium (min/max)", f"{labelDict['calciumMin']}%/{labelDict['calciumMax']}%" if labelDict['calciumMin'] is not None and labelDict['calciumMax'] is not None else '', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
    ["Phosphorus (min)", f"{labelDict['phosphorus']}%" if labelDict['phosphorus'] is not None else '', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
    ["Salt (min/max)", f"{labelDict['saltMin']}%/{labelDict['saltMax']}%" if labelDict['saltMin'] is not None and labelDict['saltMax'] is not None else '', f" {round(nutrient_values['Salt (min)'], 1)} %"],
    ["Sodium (min/max)", f"{labelDict['sodiumMin']}%/{labelDict['sodiumMax']}%" if labelDict['sodiumMin'] is not None and labelDict['sodiumMax'] is not None else '', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
    ["Copper (min)", f"{labelDict['copperMin']} ppm" if labelDict['copperMin'] is not None else '', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
    ["Selenium (min)", f"{labelDict['selenium']} ppm" if labelDict['selenium'] is not None else '', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"]
]
    elif labelDict['species'] == "Poultry":
        data = [
    ["Crude Protein (min)", f"{labelDict['crudeProtein']}%" if labelDict['crudeProtein'] is not None else '', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
    ["Lysine (min)", f"{labelDict['lysine']}%" if labelDict['lysine'] is not None else '', f" {round(nutrient_values['Lysine (min)'], 1)} %"],
    ["Methionine (min)", f"{labelDict['methionine']}%" if labelDict['methionine'] is not None else '', f" {round(nutrient_values['Methionine (min)'], 1)} %"],
    ["Crude Fat (min)", f"{labelDict['crudeFat']}%" if labelDict['crudeFat'] is not None else '', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
    ["Crude Fiber (max)", f"{labelDict['crudeFiber']}%" if labelDict['crudeFiber'] is not None else '', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
    ["Calcium (min/max)", f"{labelDict['calciumMin']}%/{labelDict['calciumMax']}%" if labelDict['calciumMin'] is not None and labelDict['calciumMax'] is not None else '', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
    ["Phosphorus (min)", f"{labelDict['phosphorus']}%" if labelDict['phosphorus'] is not None else '', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
    ["Salt (min/max)", f"{labelDict['saltMin']}%/{labelDict['saltMax']}%" if labelDict['saltMin'] is not None and labelDict['saltMax'] is not None else '', f" {round(nutrient_values['Salt (min)'], 1)} %"],
    ["Sodium (min/max)", f"{labelDict['sodiumMin']}%/{labelDict['sodiumMax']}%" if labelDict['sodiumMin'] is not None and labelDict['sodiumMax'] is not None else '', f" {round(nutrient_values['Sodium (min)'], 1)} %"]
]
    elif labelDict['species'] == "Rabbits":
        data = [
    ["Crude Protein (min)", f"{labelDict['crudeProtein']}%" if labelDict['crudeProtein'] is not None else '', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
    ["Crude Fat (min)", f"{labelDict['crudeFat']}%" if labelDict['crudeFat'] is not None else '', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
    ["Crude Fiber (max)", f"{labelDict['crudeFiber']}%" if labelDict['crudeFiber'] is not None else '', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
    ["Calcium (min/max)", f"{labelDict['calciumMin']}%/{labelDict['calciumMax']}%" if labelDict['calciumMin'] is not None and labelDict['calciumMax'] is not None else '', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
    ["Phosphorus (min)", f"{labelDict['phosphorus']}%" if labelDict['phosphorus'] is not None else '', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
    ["Salt (min/max)", f"{labelDict['saltMin']}%/{labelDict['saltMax']}%" if labelDict['saltMin'] is not None and labelDict['saltMax'] is not None else '', f" {round(nutrient_values['Salt (min)'], 1)} %"],
    ["Sodium (min/max)", f"{labelDict['sodiumMin']}%/{labelDict['sodiumMax']}%" if labelDict['sodiumMin'] is not None and labelDict['sodiumMax'] is not None else '', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
    ["Vitamin A (min)", f"{labelDict['vitaminA']:,} IU/lb" if labelDict['vitaminA'] is not None else '', f"{nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
]

    elif labelDict['species'] == "Grains":
        data = [
    ["Crude Protein (min)", f"{labelDict['crudeProtein']}%" if labelDict['crudeProtein'] is not None else '', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
    ["Crude Fat (min)", f"{labelDict['crudeFat']}%" if labelDict['crudeFat'] is not None else '', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
    ["Crude Fiber (max)", f"{labelDict['crudeFiber']}%" if labelDict['crudeFiber'] is not None else '', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"]
        ]
    elif labelDict['species'] == "Cattle" and labelDict['equivalentCP'] is None:
        data = [
    ["Crude Protein (min)", f"{labelDict['crudeProtein']}%" if labelDict['crudeProtein'] is not None else '', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
    ["Crude Fat (min)", f"{labelDict['crudeFat']}%" if labelDict['crudeFat'] is not None else '', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
    ["Crude Fiber (max)", f"{labelDict['crudeFiber']}%" if labelDict['crudeFiber'] is not None else '', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
    ["Calcium (min/max)", f"{labelDict['calciumMin']}%/{labelDict['calciumMax']}%" if labelDict['calciumMin'] is not None and labelDict['calciumMax'] is not None else '', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
    ["Phosphorus (min)", f"{labelDict['phosphorus']}%" if labelDict['phosphorus'] is not None else '', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
    ["Salt (min/max)", f"{labelDict['saltMin']}%/{labelDict['saltMax']}%" if labelDict['saltMin'] is not None and labelDict['saltMax'] is not None else '', f" {round(nutrient_values['Salt (min)'], 1)} %"],
    ["Sodium (min/max)", f"{labelDict['sodiumMin']}%/{labelDict['sodiumMax']}%" if labelDict['sodiumMin'] is not None and labelDict['sodiumMax'] is not None else '', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
    ["Potassium (min)", f"{labelDict['potassium']}%" if labelDict['potassium'] is not None else '', f" {round(nutrient_values['Potassium (min)'], 1)} %"],
    ["Vitamin A (min)", f"{labelDict['vitaminA']:,} IU/lb" if labelDict['vitaminA'] is not None else '', f"{nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
]
    elif labelDict['species'] == "Cattle" and labelDict['equivalentCP'] is not None and labelDict['equivalentCP'] > 0:
        data = [
    ["Crude Protein (min)", f"{labelDict['crudeProtein']}%" if labelDict['crudeProtein'] is not None else '', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
    ["Equivalent Crude Protein from Non-Protein Nitrogen (NPN) (min)", f"{labelDict['equivalentCP']}%" if labelDict['equivalentCP'] is not None else '', f" {round(nutrient_values['NPN'], 1)} %"],
    ["Crude Fat (min)", f"{labelDict['crudeFat']}%" if labelDict['crudeFat'] is not None else '', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
    ["Crude Fiber (max)", f"{labelDict['crudeFiber']}%" if labelDict['crudeFiber'] is not None else '', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
    ["Calcium (min/max)", f"{labelDict['calciumMin']}%/{labelDict['calciumMax']}%" if labelDict['calciumMin'] is not None and labelDict['calciumMax'] is not None else '', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
    ["Phosphorus (min)", f"{labelDict['phosphorus']}%" if labelDict['phosphorus'] is not None else '', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
    ["Salt (min/max)", f"{labelDict['saltMin']}%/{labelDict['saltMax']}%" if labelDict['saltMin'] is not None and labelDict['saltMax'] is not None else '', f" {round(nutrient_values['Salt (min)'], 1)} %"],
    ["Sodium (min/max)", f"{labelDict['sodiumMin']}%/{labelDict['sodiumMax']}%" if labelDict['sodiumMin'] is not None and labelDict['sodiumMax'] is not None else '', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
    ["Potassium (min)", f"{labelDict['potassium']}%" if labelDict['potassium'] is not None else '', f" {round(nutrient_values['Potassium (min)'], 1)} %"],
    ["Vitamin A (min)", f"{labelDict['vitaminA']:,} IU/lb" if labelDict['vitaminA'] is not None else '', f"{nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
]
    elif labelDict['species'] == "Goats" and labelDict['equivalentCP'] is None:
        data = [
    ["Crude Protein (min)", f"{labelDict['crudeProtein']}%" if labelDict['crudeProtein'] is not None else '', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
    ["Crude Fat (min)", f"{labelDict['crudeFat']}%" if labelDict['crudeFat'] is not None else '', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
    ["Crude Fiber (max)", f"{labelDict['crudeFiber']}%" if labelDict['crudeFiber'] is not None else '', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
    ["Acid Detergent Fiber (max)", f"{labelDict['adf']}%" if labelDict['adf'] is not None else '', f" {round(nutrient_values['ADF (max)'], 1)} %"],
    ["Calcium (min/max)", f"{labelDict['calciumMin']}%/{labelDict['calciumMax']}%" if labelDict['calciumMin'] is not None and labelDict['calciumMax'] is not None else '', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
    ["Phosphorus (min)", f"{labelDict['phosphorus']}%" if labelDict['phosphorus'] is not None else '', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
    ["Salt (min/max)", f"{labelDict['saltMin']}%/{labelDict['saltMax']}%" if labelDict['saltMin'] is not None and labelDict['saltMax'] is not None else '', f" {round(nutrient_values['Salt (min)'], 1)} %"],
    ["Sodium (min/max)", f"{labelDict['sodiumMin']}%/{labelDict['sodiumMax']}%" if labelDict['sodiumMin'] is not None and labelDict['sodiumMax'] is not None else '', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
    ["Copper (min)", f"{labelDict['copperMin']} ppm" if labelDict['copperMin'] is not None else '', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
    ["Selenium (min)", f"{labelDict['selenium']} ppm" if labelDict['selenium'] is not None else '', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"],
    ["Vitamin A (min)", f"{labelDict['vitaminA']:,} IU/lb" if labelDict['vitaminA'] is not None else '', f"{nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
]
    elif labelDict['species'] == "Goats" and labelDict['equivalentCP'] is not None and labelDict['equivalentCP'] > 0:
        data = [
    ["Crude Protein (min)", f"{labelDict['crudeProtein']}%" if labelDict['crudeProtein'] is not None else '', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
    ["Equivalent Crude Protein from Non-Protein Nitrogen (NPN) (min)", f"{labelDict['equivalentCP']}%" if labelDict['equivalentCP'] is not None else '', f" {round(nutrient_values['NPN'], 1)} %"],
    ["Crude Fat (min)", f"{labelDict['crudeFat']}%" if labelDict['crudeFat'] is not None else '', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
    ["Crude Fiber (max)", f"{labelDict['crudeFiber']}%" if labelDict['crudeFiber'] is not None else '', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
    ["Acid Detergent Fiber (max)", f"{labelDict['adf']}%" if labelDict['adf'] is not None else '', f" {round(nutrient_values['ADF (max)'], 1)} %"],
    ["Calcium (min/max)", f"{labelDict['calciumMin']}%/{labelDict['calciumMax']}%" if labelDict['calciumMin'] is not None and labelDict['calciumMax'] is not None else '', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
    ["Phosphorus (min)", f"{labelDict['phosphorus']}%" if labelDict['phosphorus'] is not None else '', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
    ["Salt (min/max)", f"{labelDict['saltMin']}%/{labelDict['saltMax']}%" if labelDict['saltMin'] is not None and labelDict['saltMax'] is not None else '', f" {round(nutrient_values['Salt (min)'], 1)} %"],
    ["Sodium (min/max)", f"{labelDict['sodiumMin']}%/{labelDict['sodiumMax']}%" if labelDict['sodiumMin'] is not None and labelDict['sodiumMax'] is not None else '', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
    ["Copper (min)", f"{labelDict['copperMin']} ppm" if labelDict['copperMin'] is not None else '', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
    ["Selenium (min)", f"{labelDict['selenium']} ppm" if labelDict['selenium'] is not None else '', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"],
    ["Vitamin A (min)", f"{labelDict['vitaminA']:,} IU/lb" if labelDict['vitaminA'] is not None else '', f"{nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
]
    elif labelDict['species'] == "Sheep" and labelDict['equivalentCP'] is None:
        data = [
    ["Crude Protein (min)", f"{labelDict['crudeProtein']}%" if labelDict['crudeProtein'] is not None else '', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
    ["Crude Fat (min)", f"{labelDict['crudeFat']}%" if labelDict['crudeFat'] is not None else '', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
    ["Crude Fiber (max)", f"{labelDict['crudeFiber']}%" if labelDict['crudeFiber'] is not None else '', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
    ["Calcium (min/max)", f"{labelDict['calciumMin']}%/{labelDict['calciumMax']}%" if labelDict['calciumMin'] is not None and labelDict['calciumMax'] is not None else '', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
    ["Phosphorus (min)", f"{labelDict['phosphorus']}%" if labelDict['phosphorus'] is not None else '', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
    ["Salt (min/max)", f"{labelDict['saltMin']}%/{labelDict['saltMax']}%" if labelDict['saltMin'] is not None and labelDict['saltMax'] is not None else '', f" {round(nutrient_values['Salt (min)'], 1)} %"],
    ["Sodium (min/max)", f"{labelDict['sodiumMin']}%/{labelDict['sodiumMax']}%" if labelDict['sodiumMin'] is not None and labelDict['sodiumMax'] is not None else '', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
    ["Copper (min)", f"{labelDict['copperMin']} ppm" if labelDict['copperMin'] is not None else '', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
    ["Selenium (min)", f"{labelDict['selenium']} ppm" if labelDict['selenium'] is not None else '', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"],
    ["Vitamin A (min)", f"{labelDict['vitaminA']:,} IU/lb" if labelDict['vitaminA'] is not None else '', f"{nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
]
    elif labelDict['species'] == "Sheep" and labelDict['equivalentCP'] is not None and labelDict['equivalentCP'] > 0:
        data = [
    ["Crude Protein (min)", f"{labelDict['crudeProtein']}%" if labelDict['crudeProtein'] is not None else '', f" {round(nutrient_values['Crude Protein (min)'], 1)} %"],
    ["Equivalent Crude Protein from Non-Protein Nitrogen (NPN) (min)", f"{labelDict['equivalentCP']}%" if labelDict['equivalentCP'] is not None else '', f" {round(nutrient_values['NPN'], 1)} %"],
    ["Crude Fat (min)", f"{labelDict['crudeFat']}%" if labelDict['crudeFat'] is not None else '', f" {round(nutrient_values['Crude Fat (min)'], 1)} %"],
    ["Crude Fiber (max)", f"{labelDict['crudeFiber']}%" if labelDict['crudeFiber'] is not None else '', f" {round(nutrient_values['Crude Fiber (max)'], 1)} %"],
    ["Calcium (min/max)", f"{labelDict['calciumMin']}%/{labelDict['calciumMax']}%" if labelDict['calciumMin'] is not None and labelDict['calciumMax'] is not None else '', f" {round(nutrient_values['Calcium (min)'], 1)} %"],
    ["Phosphorus (min)", f"{labelDict['phosphorus']}%" if labelDict['phosphorus'] is not None else '', f" {round(nutrient_values['Phosphorus (min)'], 1)} %"],
    ["Salt (min/max)", f"{labelDict['saltMin']}%/{labelDict['saltMax']}%", f" {round(nutrient_values['Salt (min)'], 1)} %"],
    ["Sodium (min/max)", f"{labelDict['sodiumMin']}%/{labelDict['sodiumMax']}%" if labelDict['sodiumMin'] is not None and labelDict['sodiumMax'] is not None else '', f" {round(nutrient_values['Sodium (min)'], 1)} %"],
    ["Copper (min)", f"{labelDict['copperMin']} ppm" if labelDict['copperMin'] is not None else '', f" {round(nutrient_values['Copper (min)'], 1)} ppm"],
    ["Selenium (min)", f"{labelDict['selenium']} ppm" if labelDict['selenium'] is not None else '', f" {round(nutrient_values['Selenium (min)'], 1)} ppm"],
    ["Vitamin A (min)", f"{labelDict['vitaminA']:,} IU/lb" if labelDict['vitaminA'] is not None else '', f"{nutrient_values['Vitamin A (min)']:,.0f} IU/lb"]
]
    else:
        data = []

    if salesQC == 0:
        folder_name = labelDict['item']
    elif salesQC == 1:
        folder_name = f"{labelDict['item']} (QC)"
    folder_path = f"C:/Users/Public/{folder_name}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    version = 1
    while os.path.exists(f"{folder_path}/{labelDict['description']}_Feed_Label_v{version}.pdf"):
        version += 1

    # Create the document
    doc = SimpleDocTemplate(f"{folder_path}/{labelDict['description']}_Feed_Label_v{version}.pdf", pagesize=letter)


    # Create the styles
    styles = getSampleStyleSheet()

    # Create the story
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

    # Define a paragraph style for the "81114" text
    style = ParagraphStyle(name="Normal", fontName="Helvetica", fontSize=14)
    small_style = ParagraphStyle(name="Normal", fontName="Helvetica", fontSize=12)

    cursor.execute("SELECT [Type] FROM [Bagging].[dbo].[RecipeSizeandCost] WHERE [Recipe] = ?", labelDict['item'])
    results = cursor.fetchall()
    rectype = results[0][0]

    class BarcodeTableFlowable(Flowable):
        def __init__(self, barcode_text, barcode_image=None):
            Flowable.__init__(self)
            self.barcode_text = barcode_text.lstrip()
            self.barcode_image = barcode_image

        def draw(self):
            # Get the width of the page
            page_width = self.canv._pagesize[0]

            # Draw the barcode text
            self.canv.setFont("Helvetica", 10)
            x = -6
            y = 18
            self.canv.drawString(x, y, self.barcode_text)

            # Draw the barcode image if it exists
            if self.barcode_image:
                barcode_image_width = self.barcode_image.minWidth()
                x1 = page_width - barcode_image_width - 1.72*inch
                renderPDF.draw(self.barcode_image, self.canv, x1, y-55)

    try:
        upc = UPC(labelDict['upc'])
        # Create a temporary file for the SVG image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as f:
            temp_file_path = f.name

        # Save the SVG image to the temporary file
        upc.save(temp_file_path)

        # Convert the temporary SVG file to a ReportLab graphics object
        barcode_image = svg2rlg(temp_file_path)

        # Scale the drawing to half its size
        barcode_image.width, barcode_image.height = barcode_image.minWidth(), barcode_image.height
        barcode_image.scale(0.75, 0.75)
        
        # Set the value of barcode_text as a string
        barcode_text = f"{labelDict['item']} ({rectype})"

        Story.append(Spacer(1, 0.5 * inch))

        # Create a new BarcodeTableFlowable instance
        barcode_flowable = BarcodeTableFlowable(barcode_text, barcode_image)

    except Exception as e:
        print(f"The GTIN-12 (For U.P.C.) code is missing.")
        
        # Set the value of barcode_text as a string
        barcode_text = f"{labelDict['item']} ({rectype})"

        Story.append(Spacer(1, 0.5 * inch))

        # Create a new BarcodeTableFlowable instance without a barcode image
        barcode_flowable = BarcodeTableFlowable(barcode_text)

    # Add the BarcodeTableFlowable to the story
    Story.append(barcode_flowable)



    Story.append(Spacer(1, 0.75 * inch))
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

    try:
        # Center the purpose statement and remove "Purpose Statement:"
        Story.append(Paragraph(labelDict['purpose'], centered_style))
    except AttributeError as e:
        print(f"The purpose statement is missing")

    Story.append(Spacer(1, 0.25 * inch))

    # Center the guaranteed analysis section
    Story.append(Paragraph("Guaranteed Analysis", centered_bold_style))
    Story.append(Spacer(1, 0.15 * inch))

    if salesQC == 1:
        # Remove calculated values from data
        data = [row[:2] for row in data]
        data.insert(0, [""])
    else:
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
    
    if salesQC == 0:
        Story.append(Paragraph(labelDict['ingredientList'], justified_style))
    elif salesQC == 1:
        Story.append(Paragraph(labelDict['bagIngredientList'], justified_style))

    # Convert the ingredient lists to sets
    ingredientList_set = set(labelDict['ingredientList'].split(", "))
    bagIngredientList_set = set(labelDict['bagIngredientList'].split(", "))

    # Calculate the Jaccard similarity index
    jaccard_index = len(ingredientList_set & bagIngredientList_set) / len(ingredientList_set | bagIngredientList_set)

    # Convert the Jaccard similarity index to a percentage
    similarity_percentage = jaccard_index * 100

    print(f"The ingredient lists are {similarity_percentage:.2f}% similar")

    # Add a page break
    Story.append(PageBreak())

    # Add a spacer at the top of page 2
    Story.append(Spacer(1, 0.6 * inch))

    try:
        exec(labelDict['directions'])
    except TypeError as e:
        print(f"The feeding directions are missing.")
        # Create a list to hold all the elements in the block
        block_elements = []

        # Add the "Directions for Use" title to the block elements
        block_elements.append(Paragraph("Directions for Use", centered_bold_style))
        block_elements.append(Spacer(1, 0.25 * inch))
        # Wrap all the block elements in a KeepTogether container
        block = KeepTogether(block_elements)

        # Add the block to the story
        Story.append(block)

    Story.append(Spacer(1, 0.25 * inch))

    # Center the ingredient statement and fully justify the ingredient list
    Story.append(Paragraph("Storage", centered_bold_style))    

    try:
        # Add storage information
        Story.append(Paragraph(labelDict['storage'], justified_style))
    except AttributeError as e:
        print(f"The storage information is missing.")

    Story.append(Spacer(1, 0.25 * inch))

    # Update manufacturer information
    Story.append(Paragraph("Manufactured by Tucker Milling LLC<br/>Guntersville, AL 35976", centered_bold_style))
    Story.append(Spacer(1, 0.25 * inch))
    
    if labelDict['weight'] is None:
        labelDict['weight'] = 50
        print("The weight value is missing")

    # Center the net quantity statement
    Story.append(
    Paragraph(
        f"Net Weight {labelDict['weight']} lb ({round(float(labelDict['weight'])/2.2046,1)} kg)",
        centered_bold_style
    )
)
    if labelDict['qr'] is None:
        labelDict['qr'] = 'https://tuckermilling.com/'
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
 
    if salesQC == 0:
        # Get the distinct recipes from the DataFrame
        distinct_recipes = df5['Recipe'].unique()
        distinct_recipes = [str(x) for x in distinct_recipes.tolist()]
        print("distinct recipes: ", distinct_recipes)

        # List to store the tables
        table_list = []

            # Create a table for each distinct recipe
        for index, recipe in enumerate(distinct_recipes):
            # Retrieve the description for the current recipe from the RecipeLists table
            cursor.execute("SELECT * FROM [Bagging].[dbo].[RecipeSizeandCost] WHERE [Recipe] = ?", str(recipe))
            results = cursor.fetchall()
            if results:
                recipe_number = results[0][0]
                descriptions = results[0][1]
                batchSize = results[0][2]
                recipeCost = results[0][3]
                mixerRecipe = results[0][4]
                recipe_type = results[0][5]

            print(descriptions, f"${recipeCost:,.2f}")
            Story.append(Spacer(1, 0.25 * inch))
            Story.append(Spacer(1, 0.25 * inch))
        # Add the recipe number and type to the top of the page
            data = [[f"{recipe_number} ({recipe_type})", f""]]
            table = Table(data, colWidths=[3 * inch, 3 * inch])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                
                # Add other style options if needed
            ]))
            Story.append(table)

            df5['Recipe'] = df5['Recipe'].astype(str)

            # Filter the DataFrame for the current recipe
            recipe_data = df5[df5['Recipe'] == recipe][['Item', 'Description', 'lb_ton', 'Value']]
        
            # Filter the DataFrame for the current recipe and where the 'lb_ton' column is greater than zero
            recipe_data = df5[(df5['Recipe'] == recipe) & (df5['lb_ton'] > 0)][['Item', 'Description', 'lb_ton', 'Value']]

            # Sort the recipe data by 'lb_ton' column in descending order
            recipe_data = recipe_data.sort_values('lb_ton', ascending=False)

            lbs = recipe_data['lb_ton']

            # Round the values in the 'lb_ton' column to one decimal place
            recipe_data['lb_ton'] = recipe_data['lb_ton'].round(1)
            
            # Round the values in the 'Value' column to one decimal place
            recipe_data['Value'] = recipe_data['Value'].round(1)

            # Round the values in the 'Value' column to the nearest 0.05 if less than 1
            recipe_data['lb_ton'] = recipe_data['lb_ton'].apply(lambda x: round(x / 0.05) * 0.05 if x < 0.1 else round(x, 1))

            # Format the values in the 'lb_ton' column with a thousands separator
            recipe_data['lb_ton'] = recipe_data['lb_ton'].apply(lambda x: "{:,.1f}".format(x))

            # Round the values in the 'Value' column to 3 decimal places if less than 0.1
            recipe_data['Value'] = recipe_data['Value'].apply(lambda x: round(x, 3) if x < 0.1 else round(x, 1))

            # Convert the recipe data to a 2D list for the table
            data = [list(recipe_data.columns)] + recipe_data.values.tolist()

        

            # Add the total row
            total_lb_per_ton = lbs.sum()
            percent = total_lb_per_ton / batchSize * 100

            # Format total_lb_per_ton
            if isinstance(total_lb_per_ton, float):
                total_lb_per_ton = "{:,.1f}".format(total_lb_per_ton)
            else:
                total_lb_per_ton = "{:,.0f}".format(total_lb_per_ton)

            # Format percent
            if isinstance(percent, float):
                percent = "{:.1f}".format(percent)
            else:
                percent = "{:d}".format(int(percent))

            total_row = ['', 'Total', total_lb_per_ton, percent]
            data.append(total_row)

            # Change the 'lb_ton' header to 'lb/ton' and the 'Value' header to '%'
            data[0][data[0].index('lb_ton')] = 'lb/ton'
            data[0][data[0].index('Value')] = '%'

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

                # Bold the headers and total row
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),

                # Add other style options if needed
            ]))

            # Add the table to the story
            Story.append(table)
            Story.append(Spacer(1, 0.25 * inch))

            if mixerRecipe == 1:
                Story.append(Paragraph("Dry mix for 5 seconds and wet mix for an additional 80 seconds after any liquid addition.", justified_style))
                
            else:
                Story.append(Paragraph("This recipe is volumetrically blended and therefore does not have mixing steps or times.", justified_style))
                
            if index != len(distinct_recipes) - 1:
                # Check if the current page is not empty
                if Story[-1] is not PageBreak():
                    Story.append(PageBreak())

        try:
            os.unlink(temp_file_path)
        except UnboundLocalError as e:
            pass

        # Find the highest version number among the PDF files in the folder
        folder_path = f"C:/Users/Public/{labelDict['item']}"
        pattern = re.compile(rf"{labelDict['description']}_Feed_Label_v(\d+)\.pdf$")
        max_version = 0
        for filename in os.listdir(folder_path):
            match = pattern.match(filename)
            if match:
                version = int(match.group(1))
                if version > max_version:
                    max_version = version

        # Read the binary data of the PDF file with the highest version number
        pdf_path = f"{folder_path}/{labelDict['description']}_Feed_Label_v{max_version}.pdf"
        try:
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
                # Insert or replace the binary data into a BLOB column
                cursor.execute("""
                    IF EXISTS (SELECT * FROM [Products].[dbo].[LabelInfo] WHERE Item = ?)
                    UPDATE [Products].[dbo].[LabelInfo] SET [BlobColumn] = ? WHERE Item = ?
                    ELSE
                    INSERT INTO [Products].[dbo].[LabelInfo] (Item, BlobColumn) VALUES (?, ?)
                    """, (labelDict['item'], pyodbc.Binary(pdf_data), labelDict['item'], labelDict['item'], pyodbc.Binary(pdf_data)))
        except FileNotFoundError:
            # Handle the error here
            print(f"{pdf_path} not found")

    # Rebuild the document
    doc.build(Story, canvasmaker=NumberedCanvas)

item = '70112'
salesQC = 1

if salesQC == 0:
    print("Generating Master Record Files")
elif salesQC == 1:
    print("Generating Product Tags")

try:
        output = subprocess.check_output(['python', 'C:\\Users\\TM - Curran\\Documents\\Python Scripts\\Bagging Scripts\\getrecipes1.py', item], stderr=subprocess.STDOUT)
        output_str = output.decode('utf-8')
        recipes = json.loads(output_str)

except subprocess.CalledProcessError as e:
        print(e.output.decode('utf-8'))

print("Updated Recipes: ", recipes)

for item in recipes:
    generate_label(item, salesQC)

print("Finished with Individual Files")

# Establish SQL connection
server = r"TM-SQL1\BESTMIX" 
database = r"Batching" 
username = "curran" 
password = "SuperLay22" 
cnxn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER="+server+"; DATABASE="+database+";UID="+username+";PWD="+ password,autocommit=True)
cursor = cnxn.cursor()

# Execute the query
cursor.execute('SELECT [Item], [Species] FROM [Products].[dbo].[LabelInfo] ORDER BY [Species]')

# Fetch the results
results = cursor.fetchall()



# Create a dictionary of species and items
species_items = {}
for row in results:
    item, species = row
    if species not in species_items:
        species_items[species] = []
    species_items[species].append(item)



if salesQC == 1:
    folder_path = "C:/Users/Public/"
    output_folder = os.path.join(folder_path, "Sales_QC_Report")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Find the next version number for the output PDF file
    version = 1
    while True:
        output_file = os.path.join(output_folder, f"sales_QC_report_v{version}.pdf")
        if not os.path.exists(output_file):
            break
        version += 1

    output_pdf = PdfMerger()

    # Create a custom frame and page template for the species title page
    frame = Frame(
    inch, inch, letter[0] - 2 * inch, letter[1] - 2 * inch,
    showBoundary=0,
    topPadding=200,
    bottomPadding=0,
    leftPadding=0,
    rightPadding=0
    )

    styles = getSampleStyleSheet()
    style = styles["Heading1"]
    style.fontSize = 48
    style.alignment = TA_CENTER

    page_template = PageTemplate(id="species_title", frames=[frame])

    # Create a title page for the PDF
    title_text = "Tucker Milling, LLC<br/><br/><br/>Product Guide"
    title = Paragraph(title_text, style)
    spacer = Spacer(0, 2 * inch)
    temp_doc = SimpleDocTemplate("title_temp.pdf", pagesize=letter)
    temp_doc.addPageTemplates([page_template])
    temp_doc.build([title, spacer])
    output_pdf.append("title_temp.pdf")

    for species, items in species_items.items():
        # Remove any trailing "s" from the species name and add "Feeds" to the end
        if species != "Grains":
            species = species.rstrip("s") + " Feeds"
        # Create a temporary PDF with the species title page
        temp_filename = f"{species}_temp.pdf"
        temp_doc = SimpleDocTemplate(temp_filename, pagesize=letter)
        temp_doc.addPageTemplates([page_template])
        temp_doc.build([Paragraph(species, style)])
        output_pdf.append(temp_filename)
        print(species_items)
        # Find the PDF report with the highest version number for each item
        for item in items:
            item_folder_name = f"{item} (QC)"
            item_folder = os.path.join(folder_path, item_folder_name)
            if os.path.isdir(item_folder):
                pdf_files = [f for f in os.listdir(item_folder) if f.endswith(".pdf")]
                if pdf_files:
                    # Sort the PDF files by version number
                    pdf_files.sort(key=lambda f: int(f.split("v")[-1].split(".")[0]))
                    # Get the PDF file with the highest version number
                    pdf_file = pdf_files[-1]
                    pdf_path = os.path.join(item_folder, pdf_file)

                    # Merge the PDF file into the output PDF
                    output_pdf.append(pdf_path)


    # Save the output PDF as sales_QC_report_vX.pdf in the C:\Users\Public\Sales_QC_Report directory
    output_pdf.write(output_file)

elif salesQC == 0:
    folder_path = "C:/Users/Public/"
    output_folder = os.path.join(folder_path, "Master_Record_File")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Find the next version number for the output PDF file
    version = 1
    while True:
        output_file = os.path.join(output_folder, f"Master_Record_File_v{version}.pdf")
        if not os.path.exists(output_file):
            break
        version += 1

    output_pdf = PdfMerger()

    # Create a custom frame and page template for the species title page
    frame = Frame(
        inch, inch, letter[0] - 2 * inch, letter[1] - 2 * inch,
        showBoundary=0,
        topPadding=200,
        bottomPadding=0,
        leftPadding=0,
        rightPadding=0
    )

    styles = getSampleStyleSheet()
    style = styles["Heading1"]
    style.fontSize = 48
    style.alignment = TA_CENTER

    page_template = PageTemplate(id="species_title", frames=[frame])

    # Create a title page for the PDF
    title_text = "Tucker Milling, LLC<br/><br/><br/>Master Record File"
    title = Paragraph(title_text, style)
    spacer = Spacer(0, 2 * inch)
    temp_doc = SimpleDocTemplate("title_temp.pdf", pagesize=letter)
    temp_doc.addPageTemplates([page_template])
    temp_doc.build([title, spacer])
    output_pdf.append("title_temp.pdf")

    
    for species, items in species_items.items():
        # Remove any trailing "s" from the species name and add "Feeds" to the end
        if species != "Grains":
            species = species.rstrip("s") + " Feeds"
        # Create a temporary PDF with the species title page
        temp_filename = f"{species}_temp.pdf"
        temp_doc = SimpleDocTemplate(temp_filename, pagesize=letter)
        temp_doc.addPageTemplates([page_template])
        temp_doc.build([Paragraph(species, style)])
        output_pdf.append(temp_filename)
        
        # Find all PDF files for each item that have a creation date within 1 year of the current date
        for item in items:
            item_folder = os.path.join(folder_path, item)
            if os.path.isdir(item_folder):
                pdf_files = [f for f in os.listdir(item_folder) if f.endswith(".pdf")]
                if pdf_files:
                    # Get the current date and time
                    now = datetime.now()
                    # Get the cutoff date and time (1 year before the current date and time)
                    cutoff = now - timedelta(days=365)

                    # Filter the PDF files by creation date
                    pdf_files = [f for f in pdf_files if datetime.fromtimestamp(os.path.getctime(os.path.join(item_folder, f))) >= cutoff]

                    # Merge all remaining PDF files into the output PDF
                    for pdf_file in pdf_files:
                        pdf_path = os.path.join(item_folder, pdf_file)
                        output_pdf.append(pdf_path)

    # Save the output PDF as Master_Record_File_vX.pdf in the C:\Users\Public\Master_Record_File directory
    output_pdf.write(output_file)
