from openpyxl import Workbook
from pathlib import Path

base = Path(__file__).resolve().parent.parent
excel_path = base / 'data' / 'sample_maintenance_issues.xlsx'
excel_path.parent.mkdir(parents=True, exist_ok=True)

wb = Workbook()
ws = wb.active
ws.title = 'Maintenance Issues'
ws.append(['equipment', 'issue', 'likely_cause'])
ws.append(['Conveyor Motor', 'Motor overheating and noise', 'Bearing failure or lubrication issue'])
ws.append(['Boiler', 'Pressure fluctuation', 'Control valve or sensor mismatch'])
ws.append(['Pump', 'Vibration after startup', 'Alignment or impeller imbalance'])
ws.append(['Compressor', 'Air leakage and reduced pressure', 'Damaged gasket or valve seal'])

wb.save(excel_path)
print(f'Created Excel file: {excel_path}')
