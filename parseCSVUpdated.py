import pandas as pd
from datetime import datetime
import Apicalls
import uuid

import chardet

# Read a chunk of the file to detect encoding
with open("martens_latest.csv", 'rb') as f:
    result = chardet.detect(f.read())

print("Detected encoding:", result['encoding'])

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
    "martens_latest.csv",
    # usecols=lambda col: col not in ["Name des Standortes", "Nummere des Standortes"],
    delimiter="\t",
    encoding=result['encoding'],
    header=0  # Treat the first row as header
)
obj = {}

last_fleet_name = None
last_vehicle_type = None
last_plate_no = None
last_vehicle_name = None


# comparison_date = datetime(2023, 7, 24)
# comparison_date = datetime(2023, 9, 1)
comparison_date = datetime(2023, 11, 30)
print(comparison_date)

print(df.columns)

    
for index, row in df.iterrows():
    if index==0:
        continue 
    if str(row["Letzte Job datum"]) == "nan":
        continue
    elif str(row["Letzte Job datum"]) != "nan":
        check_date = datetime.strptime(str(row["Letzte Job datum"]), "%d.%m.%Y")
        print(check_date," ",comparison_date);
        if check_date <= comparison_date:
            continue
    # if row["MeasuredPressure"] is not None:
    #     row["MeasuredPressure"] = str(row["MeasuredPressure"]).replace(',', '.', regex=False).astype(float)
    # if row["RTD1"] is not None:
    #     row["RTD1"] = str(row["RTD1"]).replace(',', '.', regex=False).astype(float)

    fleet_name = row["Flotten Stadt"]
    vehicle_type = row["VehicleType_Name"]
    plate_no = row["Kennzeichen"]
    position = row["Position"]
    tire_id = row["Seriennummer "]
    size = row["Größe"]
    product_line = row["Reifenmuster"]
    brand = row["Marken"]
    tread_depth = row["RTD1"]
    td_date = row["RTD gemessenes Datum"]
    pressure = row["MeasuredPressure"]
    vehicle_name = row["Flotten Referenz"]

    if pd.isna(tire_id) or tire_id == "":
        tire_id = "".join(str(uuid.uuid4().hex)[:9])

    if str(vehicle_name).lower() == "tt067":
        print("continuing for the vehicle_name no TT067")
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
        obj[fleet_name][vehicle_type][plate_no] = {
            "vehicle_name": vehicle_name,
            "modified_date" : row["Letzte Job datum"],
            "tires": [],
        }

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
    if size is not None:
        size = str(size).strip().replace(",", ".").replace(" ", "")
    if position is not None and vehicle_type == "Rigid":
        position = truckAxleReplace.get(position, position)
    elif position is not None and vehicle_type in ["Semi Trailer", "Trailer"]:
        position = trailerAxleReplace.get(position, position)
    # setting time format as per our app
    if td_date is not None and str(td_date) != "nan":
        td_date = datetime.strptime(str(td_date), "%d.%m.%Y").strftime("%Y-%m-%d")

    tire = {
        "tire_id": tire_id,
        "size": size,
        "product_line": product_line,
        "brand": brand,
        "tread_depth": tread_depth,
        "pressure": pressure,
        "TD_date": td_date,
        "position": position,
    }
    obj[fleet_name][vehicle_type][plate_no]["tires"].append(tire)

print(obj)
print("data successfully extracted from the given csv file")


# Apicalls.APiCalls(obj)
