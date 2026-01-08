
import pandas as pd
import sys

# Set recursion limit just in case, though not needed here
sys.setrecursionlimit(2000)

try:
    df = pd.read_excel('data/univer_data.xlsx', sheet_name='이과', header=4)
    
    # Define columns of interest, try to match likely names
    interested_cols = [
        '대학교', '전공', '수능점수', '누백', 
        '국어구성비', '수학구성비', '탐구구성비', '영어구성비', 
        '국어배점', '수학배점', '탐구배점'
    ]
    
    # Filter only existing columns
    existing_cols = [c for c in interested_cols if c in df.columns]
    
    with open('value_debug.txt', 'w', encoding='utf-8') as f:
        f.write(f"Found Columns: {existing_cols}\n\n")
        
        # Print first 3 rows
        for i in range(3):
            row = df.iloc[i]
            f.write(f"--- Row {i} ---\n")
            for col in existing_cols:
                f.write(f"{col}: {row[col]}\n")
            f.write("\n")
            
except Exception as e:
    with open('value_debug.txt', 'w', encoding='utf-8') as f:
        f.write(f"Error: {e}")
