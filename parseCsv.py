import pandas as pd
from datetime import datetime
import Apicalls

mapProductLines = {
    "DURS2": "Durvais R-Steer 002",
    "DURD2": "Duravis R-Drive 002",
    "DURT2": "Duravis R-Trailer 002",
    "FS422+E": "FS422",
    "FT422+E": "FT422",
    "FT522+": "FT522 PLUS",
    "CONTIHY": "Conti Hybrid HD3",
    "HD3": "Conti Hybrid HD3",
    "HT3": "Conti Hybrid HT3",
    "ECOHS2": "Ecopia H-Steer 002",
    "ECOHD2": "Ecopia H-Drive 002",
    "ECOHT2": "Ecopia H-Trailer 002",
    "R168+": "R168 ",
    "R179": "R179",
}

# if 1 is only present, then we cannot configure it
## if only upto 2 is present map it to 4*2
#  if 3 is present then 6*2
truckAxleReplace = {
    "1L1": "1SL",
    "1R1": "1SR",
    "2L1": "1DL",
    "2L2": "1DLI",
    "2R1": "1DR",
    "2R2": "1DRI",
    "3R1": "2SR",
    "3L1": "2SL",
}

# if only 1 - then cannot configure
# upto 2 - only 2-axle
# upto 3 - 3 axle
trailerAxleReplace = {
    "1R1": "1TR",
    "1L1": "1TL",
    "2R1": "2TR",
    "2L1": "2TL",
    "3R1": "3TR",
    "3L1": "3TL",
}
df = pd.read_csv(
    "Martens_2507.csv",
    usecols=lambda col: col not in ["Name des Standortes", "Nummere des Standortes"], delimiter='\t',
    encoding="utf-16le"
)
obj = {}

last_fleet_name = None
last_vehicle_type = None
last_plate_no = None
last_vehicle_name = None
# Iterate over each row in the DataFrame
for _, row in df.iterrows():
    fleet_name = row["Flotten Stadt"]
    vehicle_type = row["VehicleType_Name"]
    plate_no = row["Kennzeichen"]
    position = row["Position"]
    tire_id = row["Seriennummer "]
    tire_size = row["Größe"]
    product_line = row["Reifenmuster"]
    brand = row["Marken"]
    td = row["RTD1"]
    td_date = row["RTD gemessenes Datum"]
    pressure = row["MeasuredPressure"]
    vehicle_name = row["Flotten Referenz"]
    # fleet_name = row.iloc[2]
    # vehicle_type = row.iloc[3]
    # plate_no = row.iloc[4]
    # position = row.iloc[8]
    # tire_id = row.iloc[9]
    # tire_size = row.iloc[11]
    # product_line = row.iloc[12]
    # brand = row.iloc[13]
    # td = row.iloc[16]
    # td_date = row.iloc[15]
    # pressure = row.iloc[18]
    # vehicle_name = row.iloc[5]

    if str(vehicle_name).lower() == 'tt067':
        print('continuing for the vehicle_name no TT067')
        continue
    # check if the latest values are null, if null then get the previous values in the fleet_name, vehicle_type and plate_no
    if pd.isnull(fleet_name):
        fleet_name = last_fleet_name
    else:
        last_fleet_name = fleet_name

    if pd.isnull(vehicle_type):
        vehicle_type = last_vehicle_type
    else:
        last_vehicle_type = vehicle_type

    if pd.isnull(plate_no):
        plate_no = last_plate_no
    else:
        last_plate_no = plate_no

    if pd.isnull(vehicle_name):
        vehicle_name = last_vehicle_name
    else:
        last_vehicle_name = vehicle_name

    if fleet_name not in obj:
        obj[fleet_name] = {}

    if vehicle_type not in obj[fleet_name]:
        obj[fleet_name][vehicle_type] = {}

    if plate_no not in obj[fleet_name][vehicle_type]:
        obj[fleet_name][vehicle_type][plate_no] = {"vehicle_name": vehicle_name, "tires": []}

    # check product line - if it is in the given array then ignoring that
    product_line = str(product_line).strip().replace("\n", "")
    if product_line is not None and str(product_line).upper() in [
        "TRAILER",
        "STEER",
        "DRIVE",
    ]:
        continue
    product_line = mapProductLines.get(product_line, "")

    # making tire size as per our app
    if tire_size is not None:
        tire_size = str(tire_size).strip().replace(",", ".").replace(" ", "")
    if position is not None and vehicle_type == "Rigid":
        position = truckAxleReplace.get(position, position)
    elif position is not None and vehicle_type in ["Semi Trailer", "Trailer"]:
        position = trailerAxleReplace.get(position, position)
    # setting time format as per our app
    if td_date is not None and str(td_date) != "nan":
        td_date = datetime.strptime(str(td_date), "%d.%m.%Y").strftime("%Y-%m-%d")

    tire = {
        "position": position,
        "tire_id": tire_id,
        "tire_size": tire_size,
        "product_line": product_line,
        "brand": brand,
        "TD": td,
        "TD_date": td_date,
        "pressure": pressure,
    }
    obj[fleet_name][vehicle_type][plate_no]["tires"].append(tire)

print(obj)
print("data successfully extracted from the given csv file")


# Apicalls.APiCalls(obj)
