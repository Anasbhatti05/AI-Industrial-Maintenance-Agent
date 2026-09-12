import pandas as pd

FILE_PATH = "data/AI_Industrial_Maintenance_Knowledge_Base_Final-1.xlsx"

try:
    excel_file = pd.ExcelFile(FILE_PATH)

    print("\nExcel loaded successfully!")
    print("\nSheets found:")

    for sheet in excel_file.sheet_names:
        print(f"- {sheet}")

    print("\nKnowledge Base preview:")

    df = pd.read_excel(FILE_PATH, sheet_name="Knowledge Base")

    print(f"\nTotal records: {len(df)}")
    print("\nColumns:")

    for column in df.columns:
        print(f"- {column}")

    print("\nFirst record:")
    print(df.iloc[0].to_dict())

except Exception as e:
    print("\nERROR:")
    print(e)
