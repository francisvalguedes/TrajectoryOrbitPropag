import pandas as pd

xls = pd.ExcelFile(r"SO1863_150921_ras_ilb.xls") #use r before absolute file path 

sheetX = xls.parse(0) #2 is the sheet number+1 thus if the file has only 1 sheet write 0 in paranthesis

var1 = sheetX["X_Rampa (km)"]

print(var1[10])