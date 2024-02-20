import json
import pandas as pd

# Load the JSON data
with open('./STR/duplicate.json') as f:
    data = json.load(f)

# Initialize an empty list to store the rows
rows = []

# Iterate through each key-value pair in the JSON data
for key, value in data.items():
    # Add the key to the row
    row = {'Key': key}
    
    # Iterate through each item in the value (list of dictionaries)
    for item in value:
        # Add each item to the row
        for k, v in item.items():
            row[k] = v
    
    # Append the row to the list of rows
    rows.append(row)

# Create a DataFrame from the list of rows
df = pd.DataFrame(rows)

# Write the DataFrame to a CSV file
df.to_csv('output.csv', index=False)

print('CSV file "output.csv" created successfully.')
