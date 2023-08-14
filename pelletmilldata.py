import sys
from PySide6.QtWidgets import QMainWindow, QApplication, QSizePolicy, QCompleter, QTabWidget, QSpacerItem, QVBoxLayout, QMenu, QWidget, QLabel, QComboBox, QLineEdit, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,  QSplitter
from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtGui import QAction, QColor, QBrush
import pyodbc
import locale 
import pyomo.environ as pyomo
from pyomo.contrib import appsi
from pyomo.opt import TerminationCondition as tc
from pyomo.opt import SolutionStatus, SolverFactory
from pyomo.contrib.gdpopt.util import SuppressInfeasibleWarning, _DoNothing
import re

class CustomTableModel(QAbstractTableModel):
    def __init__(self, data, headers, parent=None):
        super().__init__(parent)
        self.data = data
        self.headers = headers

    def rowCount(self, parent=None):
        return len(self.data)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.data[index.row()][index.column()]

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        self.data = sorted(self.data, key=lambda x: x[column], reverse=order == Qt.DescendingOrder)
        self.layoutChanged.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.changed_value = None

        self.setWindowTitle("Tucker Mix")

        self.ingredient_scaling_factors = {}  # Initialize an empty dictionary for ingredient scaling factors
        self.nutrient_scaling_factors = {}  # Initialize an empty dictionary for nutrient constraints

        # Set the default window width with dynamic height
        self.resize(1700, 600)  # Adjust the initial width and height

        self.initUI()

    

    def on_item_changed(self, item):
            # Check if the changed item is in column 6 or 7
            if item.column() in [6, 7]:
                # Get the current text of the item
                text = item.text()
                # Remove any non-numeric characters from the text
                text = re.sub(r"[^\d.]", "", text)
                # Convert the text to a float
                value = float(text)
                # Format the value as a currency string
                formatted_value = "$" + locale.format_string("%.2f", value, grouping=True)
                # Set the text of the item to the formatted value
                item.setText(formatted_value)

    def handle_editing_finished(self, row, col):
        item = self.ingredients_table.item(row, col)
        if item is not None and item.text():
            item.setBackground(Qt.yellow)
        else:
            item.setBackground(Qt.white)

    def initUI(self):
        
        main_splitter = QSplitter(self)
        main_splitter.setHandleWidth(5)
        # Apply a stylesheet to the splitter handle to create a grey border
        handle_style = "QSplitter::handle { background-color: grey; }"
        main_splitter.setStyleSheet(handle_style)


        # Left pane for the main content
        content_widget = QWidget(main_splitter)
        layout = QVBoxLayout(content_widget)

        # Create a QLabel to display "Feasible Solution" text
        self.feasible_solution_label = QLabel("Feasible Solution")
        font = self.feasible_solution_label.font()  # Get the current font
        font.setPointSize(12)  # Increase font size
        font.setBold(True)    # Set the font to bold
        self.feasible_solution_label.setFont(font)  # Apply the updated font
        self.feasible_solution_label.setAlignment(Qt.AlignCenter)  # Center-align the text
        self.feasible_solution_label.setVisible(False)  # Initially invisible
        layout.addWidget(self.feasible_solution_label)

        label1 = QLabel("Batch Size:")
        layout.addWidget(label1)

        # Inside the initUI method
        batch_size_input = QLineEdit()
        batch_size_input.setPlaceholderText("2,000 lb")

        # Set the width of the batch size input box
        batch_size_input.setFixedWidth(100)  # Adjust the width as needed

        layout.addWidget(batch_size_input)

        # Create a vertical spacer
        vertical_spacer = QSpacerItem(1, 15, QSizePolicy.Minimum)
        layout.addItem(vertical_spacer)

        # Create a QLabel to display the ton cost
        self.ton_cost_label = QLabel("Ton Cost: N/A")
        layout.addWidget(self.ton_cost_label)

        horizontal_spacer = QSpacerItem(50,0, QSizePolicy.Minimum)
        layout.addItem(horizontal_spacer)

        

        # Create a QLabel to display the batch cost
        self.batch_cost_label = QLabel("Batch Cost: N/A")
        layout.addWidget(self.batch_cost_label)

        # Create a QLabel to display the bag cost
        self.bag_cost_label = QLabel("Bag Cost: N/A")
        layout.addWidget(self.bag_cost_label)


         # Create a vertical spacer
        vertical_spacer = QSpacerItem(1, 15, QSizePolicy.Minimum)
        layout.addItem(vertical_spacer)
       

        label = QLabel("Select an ingredient:")
        layout.addWidget(label)

        self.selected_ingredients = []  # Initialize the list to store selected items

        self.ingredient_combo = QComboBox()
        self.ingredient_combo.setEditable(True)

        # Add an empty item to the combo box
        self.ingredient_combo.addItem("")
       
        # Set the width of the combo box
        self.ingredient_combo.setFixedWidth(200)  # Adjust the width as needed

        # Fetch ingredient list from the database
        self.ingredient_list = self.fetch_ingredient_list()

        self.ingredient_combo.addItems([ingredient["Description"] for ingredient in self.ingredient_list])

        # Select the empty item
        self.ingredient_combo.setCurrentIndex(0)

        layout.addWidget(self.ingredient_combo)

        self.completer = QCompleter(self.ingredient_combo.model())
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ingredient_combo.setCompleter(self.completer)

        self.ingredients_table = QTableWidget()
        self.ingredients_table.setColumnCount(8)
        self.ingredients_table.setHorizontalHeaderLabels(["Code", "Description", "Min", "Max", "Batch", "Pct", "Price", "PriceLb"])
        
        # Set up the context menu for the ingredients_table
        self.ingredients_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ingredients_table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.ingredients_table)

        

        # Connect the on_item_changed slot function to the itemChanged signal of ingredients_table
        self.ingredients_table.itemChanged.connect(self.on_item_changed)

        # Set up the layout of the left pane
        content_layout = QVBoxLayout()
        content_layout.addWidget(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Create an empty widget for the right pane
        right_content_widget = QWidget(main_splitter)
        right_layout = QVBoxLayout(right_content_widget)
        # Add two blank lines here
        right_layout.addWidget(QLabel(""))  # First blank line
        optimize_button = QPushButton("Optimize Diet")  # Create the button
        right_layout.addWidget(optimize_button)  # Add the button to your layout

        # Connect the button's clicked signal to the optimize_diet method
        optimize_button.clicked.connect(lambda: self.optimize_diet(batch_size_input.text(), self.selected_ingredients, self.selected_nutrients, self.ingredient_scaling_factors, self.nutrient_scaling_factors))

        label = QLabel("Select a nutrient:")
        right_layout.addWidget(label)

        self.selected_nutrients = []  # Initialize the list to store selected nutrients

        self.nutrient_combo = QComboBox()
        self.nutrient_combo.setEditable(True)

        # Add an empty item to the combo box
        self.nutrient_combo.addItem("")
        self.nutrient_combo.setFixedWidth(200)

        # Fetch nutrient list from the database
        self.nutrient_list = self.fetch_nutrient_list()

        # Populate the combo box with nutrient descriptions
        self.nutrient_combo.addItems([nutrient["Description"] for nutrient in self.nutrient_list])

        # Select the empty item
        self.nutrient_combo.setCurrentIndex(0)

        right_layout.addWidget(self.nutrient_combo)

        self.completer = QCompleter(self.nutrient_combo.model())
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.nutrient_combo.setCompleter(self.completer)
        

        self.nutrients_table = QTableWidget()
        self.nutrients_table.setColumnCount(7)
        self.nutrients_table.setHorizontalHeaderLabels(["Code", "Nutrient", "Unit", "Min", "Max", "Value", "Target"])
        self.nutrients_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.nutrients_table.customContextMenuRequested.connect(self.show_nutrient_context_menu)

        right_layout.addWidget(self.nutrients_table)


        # Add the left and right panes to the splitter
        main_splitter.addWidget(content_widget)
        main_splitter.addWidget(right_content_widget)

        # Set the sizes of the panes equally
        main_splitter.setSizes([500, 500])

        self.setCentralWidget(main_splitter)

        # Connect the activated signal of the combo box to the slot
        self.ingredient_combo.activated.connect(self.add_to_selected)

    # Inside your MainWindow class
    def remove_row(self, row):
        # Get the ingredient item from the removed row
        removed_ingredient_item = self.ingredients_table.item(row, 0).text()

        # Remove the row from the table
        self.ingredients_table.removeRow(row)

        # Remove the ingredient from the selected_ingredients list
        if removed_ingredient_item in self.selected_ingredients:
            self.selected_ingredients.remove(removed_ingredient_item)

        # Remove the ingredient from the ingredient_scaling_factors dictionary
        if removed_ingredient_item in self.ingredient_scaling_factors:
            del self.ingredient_scaling_factors[removed_ingredient_item]

        # Update the batch and percentage columns in the table
        self.update_batch_and_percentage_columns()
    
    def show_context_menu(self, pos):
        row = self.ingredients_table.rowAt(pos.y())
        if row >= 0:
            context_menu = QMenu(self)

            remove_action = QAction("Remove Row", self)
            remove_action.triggered.connect(lambda: self.remove_row(row))

            context_menu.addAction(remove_action)
            context_menu.exec_(self.ingredients_table.mapToGlobal(pos))
    
    def remove_nutrient_row(self, row):
        # Get the nutrient item from the removed row
        removed_nutrient_item = self.nutrients_table.item(row, 0).text()

        # Remove the row from the table
        self.nutrients_table.removeRow(row)

        # Remove the nutrient from the selected_nutrients list
        if removed_nutrient_item in self.selected_nutrients:
            self.selected_nutrients.remove(removed_nutrient_item)

        # Remove the nutrient from the nutrient_scaling_factors dictionary
        if removed_nutrient_item in self.nutrient_scaling_factors:
            del self.nutrient_scaling_factors[removed_nutrient_item]

    def show_nutrient_context_menu(self, pos):
        row = self.nutrients_table.rowAt(pos.y())
        if row >= 0:
            context_menu = QMenu(self)

            remove_action = QAction("Remove Row", self)
            remove_action.triggered.connect(lambda: self.remove_nutrient_row(row))

            context_menu.addAction(remove_action)
            context_menu.exec_(self.nutrients_table.mapToGlobal(pos))

    def fetch_ingredient_list(self):
        # Connect to the SQL database
        server = 'TM-SQL1\BESTMIX'
        database = 'Bagging'
        username = 'curran'
        password = 'SuperLay22'
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password, autocommit=True)
        cursor = cnxn.cursor()

        # Define the SQL query to fetch ingredients
        query = f"""SELECT [Item], [Description], [Price] FROM [Bagging].[dbo].[ingredients]
        WHERE [FolderCode] NOT IN('Recipes', 'sub', 'AD_ING') ORDER BY [Item]"""

        cursor.execute(query)

        ingredient_list = [{"Item": row[0], "Description": row[1], "Price": row[2]} for row in cursor.fetchall()]

        return ingredient_list

    def fetch_nutrient_list(self):
        # Connect to the SQL database
        server = 'TM-SQL1\BESTMIX'
        database = 'Bagging'
        username = 'curran'
        password = 'SuperLay22'
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password, autocommit=True)
        cursor = cnxn.cursor()

        animal = 402
        query = f"SELECT [Nutrients] FROM [Bagging].[dbo].[animals] WHERE [Code] = {animal}"
        # Define the SQL query to fetch nutrients
        cursor.execute(query)

        nutrients_list = cursor.fetchone()[0]
        nutrients_list = nutrients_list.replace('[','(').replace(']',')')

        query = f"SELECT [Item], [Description], [UnitCode] FROM [Bagging].[dbo].[nutrients] WHERE [Item] IN {nutrients_list} ORDER BY [UnitCode]"

        cursor.execute(query)

        nutrient_list = [{"Item": row[0], "Description": row[1], "Units": row[2]} for row in cursor.fetchall()]

        return nutrient_list

    def add_to_selected(self, index):
        selected_description = self.ingredient_combo.currentText()  # Get the selected description
        selected_item = None

        for ingredient in self.ingredient_list:
            if ingredient["Description"] == selected_description:
                selected_item = ingredient["Item"]
                break

        if selected_item is not None and selected_item not in self.selected_ingredients:
            self.selected_ingredients.append(selected_item)
            
            # Initialize the ingredient scaling factors for the selected ingredient
            self.ingredient_scaling_factors[selected_item] = (0, float('inf'))

            # Add the selected ingredient to the table
            row_position = self.ingredients_table.rowCount()
            self.ingredients_table.insertRow(row_position)
            self.ingredients_table.setItem(row_position, 0, QTableWidgetItem(selected_item))
            self.ingredients_table.setItem(row_position, 1, QTableWidgetItem(selected_description))

             # Clear the text input in the combo box
            self.ingredient_combo.clearEditText()

            # Add input cells for min and max values
            min_item = QLineEdit()
            max_item = QLineEdit()
            pricelb_item = QLineEdit()  

            # Set stylesheet to remove border
            min_item.setStyleSheet("border: none;")
            max_item.setStyleSheet("border: none;")
            pricelb_item.setStyleSheet("border: none;")

            self.ingredients_table.setCellWidget(row_position, 2, min_item)
            self.ingredients_table.setCellWidget(row_position, 3, max_item)

            # Update the ingredient_scaling_factors dictionary with the default values
            self.ingredient_scaling_factors[selected_item] = (0, float('inf'))  # Default values

            # Connect the editingFinished signal of the min_item and max_item QLineEdit objects to update the dictionary
            min_item.editingFinished.connect(lambda: self.update_scaling_factors(selected_item, min_item, max_item))
            max_item.editingFinished.connect(lambda: self.update_scaling_factors(selected_item, min_item, max_item))
            pricelb_item.editingFinished.connect(lambda: self.update_price_values(selected_item, pricelb_item))  # Connect pricelb_item

            # Add Batch column
            batch_item = QTableWidgetItem("")  # Empty cell
            self.ingredients_table.setItem(row_position, 4, batch_item)  # Batch column

            percentage_item = QTableWidgetItem("")  # Empty cell
            self.ingredients_table.setItem(row_position, 5, percentage_item)  # Percentage column

            def calculate_percentage(batch_value, total_batch_size):
                if total_batch_size != 0:
                    return (batch_value / total_batch_size) * 100
                return 0

            # Get the Price value from the ingredient_list
            selected_price = None
            for ingredient in self.ingredient_list:
                if ingredient["Description"] == selected_description:
                    selected_price = ingredient["Price"]
                    break

            if selected_price is not None:
                # Add Price and PriceLb columns
                price_item = QTableWidgetItem("$"+locale.format_string("%.2f", selected_price, grouping=True))
                pricelb_item = QTableWidgetItem("$"+locale.format_string("%.2f", selected_price/2000, grouping=True))
   
                self.ingredients_table.setItem(row_position, 6, price_item)  # Price column
                self.ingredients_table.setItem(row_position, 7, pricelb_item)  # PriceLb column
                self.ingredients_table.item(row_position, 6).setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable)
                self.ingredients_table.item(row_position, 7).setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable)

    

                # Connect the itemChanged signal of the QTableWidget
                self.ingredients_table.itemChanged.connect(lambda item: self.handle_table_item_changed(item, selected_item))


    def handle_table_item_changed(self, item, selected_item):
        if item.column() == 7:  # Assuming PriceLb is column 7
            new_text = item.text()
            self.update_price_values(selected_item, new_text)
    
    
        
    def update_scaling_factors(self, ingredient_item, min_item, max_item):
        try:
            min_value = float(min_item.text())
        except ValueError:
            min_value = 0
        try:
            max_value = float(max_item.text())
        except ValueError:
            max_value = float('inf')
        
        self.ingredient_scaling_factors[ingredient_item] = (min_value, max_value)
    
    def update_nutrient_scaling_factors(self, nutrient_item, min_item, max_item):
        try:
            min_value = float(min_item.text())
        except ValueError:
            min_value = 0
        try:
            max_value = float(max_item.text())
        except ValueError:
            max_value = float('inf')
        
        self.nutrient_scaling_factors[nutrient_item] = (min_value, max_value)

    def add_empty_row(self):
        row_position = self.ingredients_table.rowCount()
        self.ingredients_table.insertRow(row_position)

        # Initialize cells with empty values
        for col in range(self.ingredients_table.columnCount()):
            empty_item = QTableWidgetItem("")
            self.ingredients_table.setItem(row_position, col, empty_item)

        # Set Price and PriceLb columns to show empty cells
        self.ingredients_table.setItem(row_position, 6, QTableWidgetItem(""))  # Price column
        self.ingredients_table.setItem(row_position, 7, QTableWidgetItem(""))  # PriceLb column
    
    def add_to_selected_nutrients(self, index):
        selected_description = self.nutrient_combo.currentText()  # Get the selected nutrient description
        selected_item = None
        selected_unit = None  # Initialize selected_unit

        for nutrient in self.nutrient_list:
            if nutrient["Description"] == selected_description:
                selected_item = nutrient["Item"]
                selected_unit = nutrient["Units"]  # Extract the unit
                break

        if selected_item is not None and selected_item not in self.selected_nutrients:
            self.selected_nutrients.append(selected_item)

            # Initialize the ingredient scaling factors for the selected ingredient
            self.nutrient_scaling_factors[selected_item] = (0, float('inf'))

            # Add the selected nutrient to the table
            row_position = self.nutrients_table.rowCount()
            self.nutrients_table.insertRow(row_position)
            self.nutrients_table.setItem(row_position, 0, QTableWidgetItem(selected_item))
            self.nutrients_table.setItem(row_position, 1, QTableWidgetItem(selected_description))
            self.nutrients_table.setItem(row_position, 2, QTableWidgetItem(selected_unit))  # Add unit to the table

            # Add input fields for min, max, and target values
            min_item = QLineEdit()
            max_item = QLineEdit()
            target_item = QLineEdit()

            # Set stylesheet to remove border    
            min_item.setStyleSheet("border: none;")
            max_item.setStyleSheet("border: none;")
            target_item.setStyleSheet("border: none;")

            self.nutrients_table.setCellWidget(row_position, 3, min_item)
            self.nutrients_table.setCellWidget(row_position, 4, max_item)
            self.nutrients_table.setCellWidget(row_position, 6, target_item)

            # Connect the editingFinished signal of the min_item and max_item QLineEdit objects to update the nutrient_scaling_factors dictionary
            min_item.editingFinished.connect(lambda: self.update_nutrient_scaling_factors(selected_item, min_item, max_item))
            max_item.editingFinished.connect(lambda: self.update_nutrient_scaling_factors(selected_item, min_item, max_item))

            # Initialize cells with empty values
            for col in range(3, self.nutrients_table.columnCount()):
                empty_item = QTableWidgetItem("")
                self.nutrients_table.setItem(row_position, col, empty_item)
        
            # Clear the text input in the combo box
            self.nutrient_combo.setCurrentText("")  # Clear the text input

    def resort_ingredients_table(self):
        # Sort the ingredients table by column 5 in descending order
        self.ingredients_table.sortItems(5, Qt.DescendingOrder)

    def optimize_diet(self, batch_size, selected_ingredients, selected_nutrients, ingredient_scaling_factors, nutrient_scaling_factors,  changed_value=None):
        # Connect to the SQL database
        server = 'TM-SQL1\BESTMIX' 
        database = 'Bagging' 
        username = 'curran' 
        password = 'SuperLay22' 
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password,autocommit=True)
        cursor = cnxn.cursor()

        # Define the ingredients and nutrients
        ingredients = selected_ingredients
        nutrients = selected_nutrients

        if not batch_size:
            batch_size = 2000  # Default batch size
        else:
            try:
                batch_size = float(batch_size)
            except ValueError:
                print("Invalid batch size value. Please enter a valid number.")
                return

        # Construct ingredient_constraints based on ingredient_scaling_factors
        ingredient_constraints = {
            ingredient: ((min_scaling_factor/2000) * batch_size, (max_scaling_factor/2000) * batch_size)
            for ingredient, (min_scaling_factor, max_scaling_factor) in ingredient_scaling_factors.items()
        }

      
        nutrient_constraints = nutrient_scaling_factors

        # Convert the lists to strings for use in the SQL query
        ingredients_str = ','.join([f"'{x}'" for x in ingredients])
        nutrients_str = ','.join([f"'{x}'" for x in nutrients])

        # Define the SQL query with a WHERE clause that uses the ingredients and nutrients
        query = f"""
        SELECT i.[Item], i.[Description], [Lb_Price], [Nutrient], n.[Description] AS 'NutrientDesc', [Value], [UnitCode]
        FROM [Bagging].[dbo].[ingredients] i
        JOIN [Bagging].[dbo].[ingredientvalues] iv
        ON i.Item = iv.Ingredient
        JOIN [Bagging].[dbo].[nutrients] n
        ON iv.Nutrient = n.[Item]
        WHERE i.Item IN ({ingredients_str}) AND iv.Nutrient IN ({nutrients_str})
        """

        cursor.execute(query)

        sqldata = {}

        # Iterate over the rows returned by the cursor
        for row in cursor:
            item, description, price, nutrient, nutrientdesc, value, unitcode = row
            # Create a new entry in the data dictionary for the current item if it doesn't already exist
            if item not in sqldata:
                sqldata[item] = {
                    'description': description,
                    'price': float(price),
                    'nutrients': {}
                }
                
            # Update the nutrient value for the current item and nutrient
            sqldata[item]['nutrients'][nutrient] = {
                'description': nutrientdesc,
                'value': float(value),
                'unitcode': unitcode
            }

        data = {}

        for ingredient in ingredients:
            data[ingredient] = {}
            
            for nutrient in nutrients:
                nutrient_value = sqldata.get(ingredient, {}).get('nutrients', {}).get(nutrient, {}).get('value', 0) / 100
                data[ingredient][nutrient] = nutrient_value
            
            data[ingredient]['cost'] = sqldata.get(ingredient, {}).get('price', 0)

        # Check and print a message if the ingredient cost is not available
        for ingredient in ingredients:
            if data[ingredient]['cost'] == 0:
                print(f"{ingredient} does not have a price")
                sys.exit()

        
        def calculate_nutrient_sum(nutrient, rounded_solution, C):
                return sum(rounded_solution[c] * data[c][nutrient] for c in C)/2/10
        
        def diet(batch_size, data, sqldata):
            C = data.keys()
            model = pyomo.ConcreteModel()
            model.x = pyomo.Var(C, domain=pyomo.NonNegativeReals)

            original_price = [data[c]['cost'] for c in C]
            print(original_price)


            model.cost = pyomo.Objective(expr = sum(model.x[c]*data[c]['cost'] for c in C))
            

            #nutrient constraints
            model.batch_size = pyomo.Constraint(expr = batch_size == sum(model.x[c] for c in C))
            
            # Define ingredient constraints dynamically
            for ingredient, (ingredient_min, ingredient_max) in ingredient_constraints.items():
                model.add_component(f'{ingredient}_min', pyomo.Constraint(
                    expr=model.x[ingredient] >= ingredient_min
                ))
                
                model.add_component(f'{ingredient}_max', pyomo.Constraint(
                    expr=model.x[ingredient] <= ingredient_max
                ))
        
            # Define the nutrient constraints dynamically
            for nutrient, (nutrient_min, nutrient_max) in nutrient_constraints.items():
                model.add_component(f'{nutrient}_min', pyomo.Constraint(
                    expr=sum(model.x[c] * data[c][nutrient] for c in C) >= nutrient_min/100 * batch_size
                ))
                
                model.add_component(f'{nutrient}_max', pyomo.Constraint(
                    expr=sum(model.x[c] * data[c][nutrient] for c in C) <= nutrient_max/100 * batch_size
                ))
                
            
            solver = pyomo.SolverFactory('appsi_highs')
            
            # Set a time limit of 30 seconds
            solver.config.time_limit = 30.0

            # Configure solver options
            solver.config.load_solution = False

            #solver.config.load_solution=False
            results = None
            try:
                results = solver.solve(model, tee=True)
            except RuntimeError:
                print("Infeasible")

    

            if results is not None:
                # Get the status of the solver's solution
                status = results.solver.status
                print("Solver Status:", status)
                
                

                # Update the text of the feasible_solution_label to show "Feasible Solution"
                self.feasible_solution_label.setText("No Feasible Solution Found")


            if results is not None and results.solver.termination_condition == tc.optimal:

                print("Solver found an optimal solution.")

                

                # Get the dual values
                dual_values = solver.get_duals()

                # Print the dual values
                for constraint, dual in dual_values.items():
                    print(f"Dual value for constraint {constraint}: {dual}")
                else:
                    print("Solver did not find an optimal solution.")
                # Get primal solution (variable values)
                primal_values = solver.get_primals()

                # Get reduced costs of variables
                reduced_costs = solver.get_reduced_costs()

                # Get slack values of constraints
                slack_values = solver.get_slacks()

                # Get solver options
                solver_options = solver.highs_options

                # Print the results
                print("Primal Solution:")
                for var, value in primal_values.items():
                    print(f"{var}: {value}")

                print("\nReduced Costs:")
                for var, cost in reduced_costs.items():
                    print(f"{var}: {cost}")

                print("\nSlack Values:")
                for constraint, slack in slack_values.items():
                    print(f"{constraint}: {slack}")

                print("\nSolver Options:")
                for option, value in solver_options.items():
                    print(f"{option}: {value}")
                rounded_solution = round_solution(model, C)
                
                rounded_cost = sum(rounded_solution[c]*data[c]['cost'] for c in C)
                bag_cost = rounded_cost/40

                print('Batch Size = ', batch_size, 'lbs')
                print('Ton Cost = $', format(rounded_cost/batch_size*2000, '.2f'))
                # Calculate and display the ton cost at the top
                ton_cost = sum(rounded_solution[c] * data[c]['cost'] for c in C)/batch_size*2000
                ton_cost_text = f"Ton Cost: ${ton_cost:.2f}"
                self.ton_cost_label.setText(ton_cost_text)

                print('Batch Cost = $', format(rounded_cost, '.2f'))
                batch_cost = sum(rounded_solution[c] * data[c]['cost'] for c in C)/2000*batch_size
                batch_cost_text = f"Batch Cost: ${batch_cost:.2f}"
                self.batch_cost_label.setText(batch_cost_text)
                print('Bag Cost = $', format(bag_cost/batch_size*2000, '.3f'))
                bag_cost = ton_cost/40
                bag_cost_text = f"Bag Cost: ${bag_cost:.2f}"
                self.bag_cost_label.setText(bag_cost_text)
                print()
                for c in sorted(sqldata.keys(), key=lambda c: rounded_solution[c], reverse=True):
                    print(sqldata[c]['description'], ':', round(rounded_solution[c], 1), 'lbs')

                # Sort the left pane table by the Batch column value in descending order
                sorted_ingredients = sorted(sqldata.keys(), key=lambda c: rounded_solution[c], reverse=True)
                for c in sorted_ingredients:
                    print(sqldata[c]['description'], ':', round(rounded_solution[c], 1), 'lbs')

                font_color = QColor("gray")

                # Update the Batch column values in the table
                for c in sorted_ingredients:
                    optimized_value = round(rounded_solution[c], 1)
                    for row in range(self.ingredients_table.rowCount()):
                        if self.ingredients_table.item(row, 0).text() == c:
                            # Create QTableWidgetItem objects if they don't exist already
                            for col in range(self.ingredients_table.columnCount()):
                                if not self.ingredients_table.item(row, col):
                                    self.ingredients_table.setItem(row, col, QTableWidgetItem())
                            
                            self.ingredients_table.item(row, 4).setText(str(optimized_value))
                            
                            # Check if the batch value is zero for the current row
                            if optimized_value == 0:
                                # Set font color to gray for all items in the row
                                for col in range(self.ingredients_table.columnCount()):
                                    self.ingredients_table.item(row, col).setForeground(QBrush(font_color))
                            else:
                                # Clear the font color for all items in the row
                                for col in range(self.ingredients_table.columnCount()):
                                    self.ingredients_table.item(row, col).setForeground(QBrush())
                            break

                # Update the Pct column values in the table
                for c in sorted_ingredients:
                    pct_value = round(rounded_solution[c]/batch_size*100, 1)
                    for row in range(self.ingredients_table.rowCount()):
                        if self.ingredients_table.item(row, 0).text() == c:
                            self.ingredients_table.item(row, 5).setText(str(pct_value))
                            break
                
                # Update the text of the feasible_solution_label to show "Feasible Solution"
                self.feasible_solution_label.setText("Feasible Solution")

                # Make the label visible
                self.feasible_solution_label.setVisible(True)

                # Update the position of the feasible_solution_label
                self.feasible_solution_label.setGeometry(80, 10, self.feasible_solution_label.width(), self.feasible_solution_label.height())


                # Sort the left pane table by the Batch column in descending order
                self.ingredients_table.sortItems(4, Qt.DescendingOrder)
                
                # Update the Value column values in the right pane table
                for nutrient in selected_nutrients:
                    nutrient_sum = calculate_nutrient_sum(nutrient, rounded_solution, C)
                    nutrient_desc = sqldata[selected_ingredients[0]]['nutrients'][nutrient]['description']
                    for row in range(self.nutrients_table.rowCount()):
                        if self.nutrients_table.item(row, 0).text() == nutrient:
                            self.nutrients_table.item(row, 5).setText(str(round(nutrient_sum, 2)))
                            break

                nutrient_sums = {}
                for nutrient in nutrients:
                    nutrient_sum = calculate_nutrient_sum(nutrient, rounded_solution, C)
                    nutrient_sums[nutrient] = nutrient_sum

                total_batch_size = sum(rounded_solution[c] for c in C)
                print()
                
                for nutrient in nutrients:
                    nutrient_sum_percent = sum(rounded_solution[c] * data[c][nutrient] for c in C) / total_batch_size * 100
                    nutrient_desc = sqldata[ingredients[0]]['nutrients'][nutrient]['description']
                    print(f'{nutrient_desc} = ', round(nutrient_sum_percent, 2), '%')

                # Call the resort_ingredients_table method to update the sorting after optimization
                self.resort_ingredients_table()

          
        def round_solution(model, C):
            rounded_solution = {}
            for c in C:
                if model.x[c]() >= 4:
                    rounded_solution[c] = round(model.x[c]() * 2) / 2
                else:
                    rounded_solution[c] = round(model.x[c]() * 20) / 20
            return rounded_solution
    
  
        diet(batch_size, data, sqldata)
        
        

def cleanup():
    # Close any open database connections
    if 'cnxn' in globals():
        cnxn.close()
        print("Database connection closed.")

class RecipesTab(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()  # Main layout with two panes

        # Top Pane
        top_pane = QWidget()
        top_layout = QVBoxLayout(top_pane)

        new_recipe_button = QPushButton("New Recipe")  # Create a button
        new_recipe_button.setFixedWidth(200)  # Set the button width to 200
        top_layout.addWidget(new_recipe_button)  # Add the button to the top pane

        # Left and Right Panes (side by side)
        middle_pane = QWidget()
        middle_layout = QHBoxLayout(middle_pane)
        
        # Left Pane
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)

        # Connect to the SQL database
        server = 'TM-SQL1\BESTMIX' 
        database = 'Bagging' 
        username = 'curran' 
        password = 'SuperLay22' 
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password,autocommit=True)
        cursor = cnxn.cursor()

        # Define the SQL query to fetch recipes
        query = "SELECT * FROM [Bagging].[dbo].[recipes]"
        cursor.execute(query)

        # Fetch the column names from the cursor description
        column_names = [column[0] for column in cursor.description]

        left_layout.addWidget(QLabel("Left Pane Content"))  # Add content to the left pane

        # Right Pane
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)

        # Create a QTableWidget and set its column count
        table = QTableWidget()
        table.setColumnCount(len(column_names))
        
        # Set the column headers
        table.setHorizontalHeaderLabels(column_names)

        # Fetch all rows from the query result
        rows = cursor.fetchall()

        # Populate the table with data from the query result
        for row_index, row_data in enumerate(rows):
            table.insertRow(row_index)  # Insert a new row
            for col_index, cell_value in enumerate(row_data):
                item = QTableWidgetItem(str(cell_value))
                table.setItem(row_index, col_index, item)

        right_layout.addWidget(table)  # Add the table to the right pane

        middle_layout.addWidget(left_pane)  # Add left pane to the middle layout
        middle_layout.addWidget(right_pane)  # Add right pane to the middle layout

        main_layout.addWidget(top_pane)  # Add the top pane to the main layout
        main_layout.addWidget(middle_pane)  # Add the middle pane (with left and right) to the main layout

        self.setLayout(main_layout)

class IngredientsTab(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()  # Main layout with two panes

        # Top Pane
        top_pane = QWidget()
        top_layout = QVBoxLayout(top_pane)

        new_recipe_button = QPushButton("New Ingredient")  # Create a button
        new_recipe_button.setFixedWidth(200)  # Set the button width to 200
        top_layout.addWidget(new_recipe_button)  # Add the button to the top pane

        # Left and Right Panes (side by side)
        middle_pane = QWidget()
        middle_layout = QHBoxLayout(middle_pane)
        
        # Left Pane
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)

        # Connect to the SQL database
        server = 'TM-SQL1\BESTMIX' 
        database = 'Bagging' 
        username = 'curran' 
        password = 'SuperLay22' 
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password,autocommit=True)
        cursor = cnxn.cursor()

        # Define the SQL query to fetch recipes
        query = "SELECT * FROM [Bagging].[dbo].[ingredients]"
        cursor.execute(query)

        # Fetch the column names from the cursor description
        column_names = [column[0] for column in cursor.description]

        left_layout.addWidget(QLabel("Left Pane Content"))  # Add content to the left pane

        # Right Pane
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)

        # Create a QTableWidget and set its column count
        table = QTableWidget()
        table.setColumnCount(len(column_names))
        
        # Set the column headers
        table.setHorizontalHeaderLabels(column_names)

        # Fetch all rows from the query result
        rows = cursor.fetchall()

        # Populate the table with data from the query result
        for row_index, row_data in enumerate(rows):
            table.insertRow(row_index)  # Insert a new row
            for col_index, cell_value in enumerate(row_data):
                item = QTableWidgetItem(str(cell_value))
                table.setItem(row_index, col_index, item)

        right_layout.addWidget(table)  # Add the table to the right pane

        middle_layout.addWidget(left_pane)  # Add left pane to the middle layout
        middle_layout.addWidget(right_pane)  # Add right pane to the middle layout

        main_layout.addWidget(top_pane)  # Add the top pane to the main layout
        main_layout.addWidget(middle_pane)  # Add the middle pane (with left and right) to the main layout

        self.setLayout(main_layout)

class NutrientsTab(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()  # Main layout with two panes

        # Top Pane
        top_pane = QWidget()
        top_layout = QVBoxLayout(top_pane)

        new_recipe_button = QPushButton("New Nutrient")  # Create a button
        new_recipe_button.setFixedWidth(200)  # Set the button width to 200
        top_layout.addWidget(new_recipe_button)  # Add the button to the top pane

        # Left and Right Panes (side by side)
        middle_pane = QWidget()
        middle_layout = QHBoxLayout(middle_pane)
        
        # Left Pane
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)

        # Connect to the SQL database
        server = 'TM-SQL1\BESTMIX' 
        database = 'Bagging' 
        username = 'curran' 
        password = 'SuperLay22' 
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password,autocommit=True)
        cursor = cnxn.cursor()

        # Define the SQL query to fetch recipes
        query = "SELECT * FROM [Bagging].[dbo].[nutrients]"
        cursor.execute(query)

        # Fetch the column names from the cursor description
        column_names = [column[0] for column in cursor.description]

        left_layout.addWidget(QLabel("Left Pane Content"))  # Add content to the left pane

        # Right Pane
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)

        # Create a QTableWidget and set its column count
        table = QTableWidget()
        table.setColumnCount(len(column_names))
        
        # Set the column headers
        table.setHorizontalHeaderLabels(column_names)

        # Fetch all rows from the query result
        rows = cursor.fetchall()

        # Populate the table with data from the query result
        for row_index, row_data in enumerate(rows):
            table.insertRow(row_index)  # Insert a new row
            for col_index, cell_value in enumerate(row_data):
                item = QTableWidgetItem(str(cell_value))
                table.setItem(row_index, col_index, item)

        right_layout.addWidget(table)  # Add the table to the right pane

        middle_layout.addWidget(left_pane)  # Add left pane to the middle layout
        middle_layout.addWidget(right_pane)  # Add right pane to the middle layout

        main_layout.addWidget(top_pane)  # Add the top pane to the main layout
        main_layout.addWidget(middle_pane)  # Add the middle pane (with left and right) to the main layout

        self.setLayout(main_layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()

    # Connect the activated signal of the nutrient combo box to the slot
    w.nutrient_combo.activated.connect(w.add_to_selected_nutrients)

    # Create a QTabWidget to hold the main window content in tabs
    tab_widget = QTabWidget()
    
    # Create an instance of MainWindow for each tab
    tab1 = RecipesTab()  # Create a blank QWidget for the "Recipes" tab
    tab2 = IngredientsTab() 
    tab3 = NutrientsTab() 
    tab4 = w  # You can create more tabs as needed
    
    # Add tabs to the tab widget and set their names
    tab_widget.addTab(tab1, "Recipes")  # Name the first tab as "Recipes"
    tab_widget.addTab(tab2, "Ingredients")  # Name the first tab as "Recipes"
    tab_widget.addTab(tab3, "Nutrients")  # Name the first tab as "Recipes"
    tab_widget.addTab(tab4, "Diet Formulation")    # You can set tab names as needed
    
    # Set the minimum size of the tab widget (adjust the values as needed)
    tab_widget.setMinimumSize(1700, 600)
    
    # Show the tab widget
    tab_widget.show()

    # Connect the aboutToQuit signal to a function that ensures proper cleanup
    app.aboutToQuit.connect(cleanup)

    sys.exit(app.exec())
