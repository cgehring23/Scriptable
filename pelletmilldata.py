def predict(target, recipe):       
    import pandas as pd
    import os
    os.environ['PYTHONHASHSEED'] = '0'
    import numpy as np
    import random as rn
    import tensorflow as tf
    # The below is necessary for starting Numpy generated random numbers
    # in a well-defined initial state.
    np.random.seed(0)
    rn.seed(0)
    import random as python_random
    from keras.models import Sequential
    from keras.layers import Dense
    from keras import regularizers
    from keras.callbacks import EarlyStopping
    from keras.layers import Dropout
    from sklearn.model_selection import train_test_split
    from sklearn.model_selection import cross_val_score
    from keras.wrappers.scikit_learn import KerasRegressor
    from sqlalchemy import create_engine
    import requests
    import nest_asyncio
    import random
    import warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    import asyncio
    nest_asyncio.apply()
    # Create an engine that connects to a Microsoft SQL Server database
    engine = create_engine('mssql+pyodbc://curran:SuperLay22@TM-BCSRV/BC130?driver=ODBC+Driver+17+for+SQL+Server')

    # Read data from a SQL table into a DataFrame
    data = pd.read_sql('EXECUTE [dbo].[sp_PelletingSettings]', engine)

    # Filter data where PelletMill != '3/4'
    data = data[data['PelletMill'] != '3/4']

  
   
   
    # Define your features and target variable
    features = ['00031', '511', '512', '44', '43', '68', '00035', '00033', '00043', '475', '00032', '55', '24', '86000225', '00036', '1093', '61', '62', '00034', '31', '88', '983', '63', '59', '70', '192', '1011', '548', '70126', '70423356', '129', '28', '51', '15', '018', '99A', '7', '40', '123A', '013', 'CSD-004', '96', '67', '128', '64', '142B']
    
    target = []
    target.append(target1)
    
    target_dict = {
        'ConditionerTemp': 'Conditioner Temperature',
        'DieSpeed': 'Die Speed',
        'FeederSpeed': 'Feeder Speed',
        'ConditionerSpeed': 'Conditioner Speed',
        'ConditionerLoad': 'Conditioner Load',
        'PelletMillLoad': 'Pellet Mill Load',
        'TPH': 'Tons per Hour'
    }

    # Split your data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(data[features], data[target1], test_size=0.2)

    # Print the number of items in the training set
    print(f'Number of items in training set: {X_train.shape[0]}')

    # Print the number of items in the testing set
    print(f'Number of items in testing set: {X_test.shape[0]}')

    # Calculate summary statistics
    summary = y_train.describe()

    # Define a custom formatting function
    def format_element(x):
        if x % 1 == 0:
            return f'{x:.0f}'
        else:
            return f'{x:.1f}'

    # Apply the formatting function to each element of the summary statistics
    formatted_summary = summary.apply(format_element)
    print()
    # Print the formatted summary statistics
    print(formatted_summary)

    #Early stopping: Monitor the validation loss during training and stop the training process early if the validation loss starts to increase. This prevents the model from overfitting by stopping the training when it starts to perform worse on unseen data. 
    early_stopping = EarlyStopping(monitor='val_loss', 
                                   mode="min", 
                                   patience=5,
                                   restore_best_weights=True)
    def build_model():
        model = Sequential()
        model.add(Dense(64, input_dim=len(features), activation='relu', kernel_regularizer=regularizers.l2(0.01))) #started with model.add(Dense(64, input_dim=len(features), activation='relu', kernel_regularizer=regularizers.l2(0.01)))
        model.add(Dropout(0.2))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(1))
        model.compile(loss='mean_squared_error', optimizer='adam', metrics=['mean_squared_error'])   #started with model.compile(loss='mean_squared_error', optimizer='adam', metrics=['mean_squared_error'])
        model.fit(X_train, y_train, 
          callbacks=[early_stopping], 
          epochs=100, batch_size=len(X_train), 
          validation_data=(X_test, y_test), 
          verbose=0, 
          shuffle = False)
        model.predict(X_train, verbose = 0)
        return model

    model = build_model()
    
    # Evaluate the performance of your model on the testing set using mean squared error
    mse = model.evaluate(X_test, y_test, verbose = 0)[1]
    print()
    print(f"Mean squared error: {mse:.2f}")

    estimator = KerasRegressor(build_fn=build_model, epochs=100, batch_size=128, verbose=0)


    # Use cross_val_score with the estimator
    scores = cross_val_score(estimator, X_train, y_train, cv=5, scoring='neg_mean_squared_error')
    mse_scores = -scores  # Convert negative MSE scores to positive
    print()
    print('Cross-validation scores:', mse_scores)


    features_dict = {feature: [0] for feature in features}

    print("recipe ", recipe)
    # Set the URL for the API endpoint
    url = f"https://bmpublicapi-prd.adifo.cloud/api/v1/Recipes/{recipe}/compositions?siteCode=TM_Site&version=1"

    # Set the headers for the API request
    headers = {
        'Tenant-Guid': '494f7b20-e66d-44d8-acb0-967ad674f17b',
        'X-API-KEY': 'S41ei9ahKE6guRpJ1XpW6Q=='
    }

    # Send a GET request to the API endpoint
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Get the JSON data from the response
        data = response.json()
        comp = data['Composition']
        
        # Create a dictionary where the keys are the MaterialCode values and the values are the corresponding Value values
        data_dict = {x['MaterialCode']: x['Value'] for x in comp}
        
        # Do something with the data
        #print(data_dict)
    else:
        # Handle the error
        print(f"An error occurred: {response.status_code}")
        data_dict = {}

    for key, value in data_dict.items():
        if key in features:
            features_dict[key] = [value/100*4000]


    # Sort the dictionary by value in descending order
    sorted_data = sorted(features_dict.items(), key=lambda x: x[1], reverse=True)

    # Find the maximum length of the keys and formatted values
    max_key_length = max([len(k) for k, v in sorted_data])
    max_value_length = max([len(format_element(v[0])) for k, v in sorted_data])

    print()
    print(f'              {recipe}')
    # Iterate over the sorted key-value pairs
    for key, value in sorted_data:
        # Remove the colon from the key
        key = key.replace(':', '')
        # Left-justify the key
        key = key.ljust(max_key_length)
        # Check if the value is a list
        if isinstance(value, list):
            # Loop through the elements in the list
            for element in value:
                # Check if the element is greater than 0
                if element > 0:
                    # Format the element using the format_element function
                    formatted_element = format_element(element)
                    # Right-justify the formatted element
                    formatted_element = formatted_element.rjust(max_value_length)
                    # Print the key-value pair on a new line without a colon separator
                    print(f"{key}       {formatted_element}")
        else:
            # Check if the value is greater than 0
            if value > 0:
                # Format the value using the format_element function
                formatted_value = format_element(value)
                # Right-justify the formatted value
                formatted_value = formatted_value.rjust(max_value_length)
                # Print the key-value pair on a new line without a colon separator
                print(f"{key}       {formatted_value}")

    # Use your trained model to make predictions on new data
    new_data = pd.DataFrame(features_dict)

    prediction = model.predict(new_data, verbose = 0)

    # Convert the prediction to a string and remove the brackets and quotation marks
    prediction_str = str(prediction).replace('[', '').replace(']', '').replace("'", "")

    print()

    return print(f"Predicted {target_dict[target1]}: {prediction_str}")

if __name__ == "__main__":
    # Set the target and recipe variables
    target1 = 'TPH'
    recipe = '70112'
    # Call the predict function with the desired target and recipe
    prediction_str = predict(target1, recipe)
    
