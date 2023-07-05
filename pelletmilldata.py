import tkinter as tk
from tkinter import ttk
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors



def generate_label(species):
    # Determine the nutrient requirements based on the selected species
    if species == "Horse":
        data = [
            ["Crude Protein (min)", "10%"],
            ["Crude Fat (min)", "3%"],
            ["Crude Fiber (max)", "15%"],
            ["Acid Detergent Fiber (ADF) (max)", "12%"],
            ["Neutral Detergent Fiber (NDF) (max)", "20%"],
            ["Calcium (min/max)", "0.8%/1.2%"],
            ["Phosphorus (min)", "0.5%"],
            ["Copper (min)", "20 ppm"],
            ["Selenium (min)", "0.3 ppm"],
            ["Zinc (min)", "100 ppm"],
            ["Vitamin A (min)", "3000 IU/lb"]
        ]
    elif species == "Cattle":
        data = [
            # Add nutrient requirements for cattle here
        ]
    elif species == "Sheep":
        data = [
            # Add nutrient requirements for sheep here
        ]
    else:
        data = []

    doc = SimpleDocTemplate(f"C:/Users/Public/{species}_Feed_Label.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    Story = []
    style = styles["Normal"]

    # Add the product code to the top left corner and change the font size to 14
    large_style = ParagraphStyle(name="large", fontSize=14, parent=styles["Normal"])
    Story.append(Paragraph("81114", large_style))
    Story.append(Spacer(1, 0.25 * inch))

    # Center justify the product name and change the font size to 16
    centered_style = ParagraphStyle(name="centered", alignment=1, parent=styles["Normal"])
    large_centered_style = ParagraphStyle(name="large_centered", alignment=1, fontSize=16, parent=styles["Normal"])
    Story.append(Paragraph("Eqceed 14", large_centered_style))
    Story.append(Spacer(1, 0.25 * inch))

    # Center the purpose statement and remove "Purpose Statement:"
    Story.append(Paragraph(f"For adult {species.lower()} in light to moderate work", centered_style))
    Story.append(Spacer(1, 0.25 * inch))

    # Center the guaranteed analysis section
    Story.append(Paragraph("Guaranteed Analysis", centered_style))

    # Create a table for the guaranteed analysis section
    table = Table(data, colWidths=[2.5 * inch, 1.5 * inch])
    table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2)
    ]))
    Story.append(table)

    Story.append(Spacer(1, 0.25 * inch))

    # Center the ingredient statement and fully justify the ingredient list
    Story.append(Paragraph("Ingredient Statement", centered_style))
    
    # Change the width of the ingredient list to 6 inches and remove line breaks
    justified_style = ParagraphStyle(name="justified", alignment=4,
                                     spaceBefore=6,
                                     spaceAfter=6,
                                     rightIndent=(doc.width-6*inch)/2,
                                     leftIndent=(doc.width-6*inch)/2,
                                     parent=styles["Normal"])
    
    Story.append(Paragraph("Wheat Middlings, Soybean Hulls,"
                           "Dehydrated Alfalfa Meal, Cane Molasses,"
                           "Calcium Carbonate, Salt",
                           justified_style))
    
    Story.append(Spacer(1, 0.25 * inch))

    # Center the directions for use
    Story.append(Paragraph("Directions for Use", centered_style))
    
     # Change the width of the directions for use to 6 inches
    directions_style = ParagraphStyle(name="directions",
                                      spaceBefore=6,
                                      spaceAfter=6,
                                      rightIndent=(doc.width-6*inch)/2,
                                      leftIndent=(doc.width-6*inch)/2,
                                      parent=styles["Normal"])
    
    Story.append(Paragraph(f"Feed at a rate of 0.5 to 1.0 pounds per 100 pounds of body weight per day", directions_style))
    Story.append(Spacer(1, 0.25 * inch))

    # Update manufacturer information
    Story.append(Paragraph("Manufactured by Tucker Milling LLC<br/>Guntersville, AL 35976", centered_style))
    Story.append(Spacer(1, 0.25 * inch))
    
    # Center the net quantity statement
    Story.append(Paragraph("Net Quantity Statement:<br/>Net Weight 50 lb (22.68 kg)", centered_style))

    doc.build(Story)

def on_select(event):
    species = species_var.get()
    generate_label(species)

root = tk.Tk()
root.geometry("300x200")

species_var = tk.StringVar(value="Select a species")
species_dropdown = ttk.Combobox(root, textvariable=species_var, state="readonly")
species_dropdown["values"] = ["Horse", "Cattle", "Sheep"]
species_dropdown.pack(pady=20)

species_dropdown.bind("<<ComboboxSelected>>", on_select)

root.mainloop()
