
import pandas as pd

# Load the Excel file
df = pd.read_excel('data/univer_data.xlsx', sheet_name='이과', header=4)

# Create a text file with the output
with open('data_debug_output.txt', 'w', encoding='utf-8') as f:
    f.write("=== Column Names ===\n")
    for col in df.columns:
        f.write(f"{col}\n")
    
    f.write("\n=== First Row Data ===\n")
    first_row = df.iloc[0]
    for col in df.columns:
        f.write(f"{col}: {first_row[col]}\n")
