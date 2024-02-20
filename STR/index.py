import pandas as pd
from datetime import datetime
import uuid
import json
import chardet
import re
import string
import random


def generate_alphanumeric(length):
    alphanumeric_chars = string.ascii_letters + string.digits
    return "".join(random.choices(alphanumeric_chars, k=length))


df = pd.read_excel("str.xlsx", header=3)

tire_positions = {
    "außenlinks": "L",
    "außenrechts": "R",
    "innenlinks": "IL",
    "innenrechts": "IR",
}


axles = {
    "lenkachse1": "1S",
    "lenkachse2": "2S",
    "anhängerachse1": "1T",
    "anhängerachse2": "2T",
    "anhängerachse3": "3T",
    "antriebsachse1": "1D",
    "antriebsachse2": "1D",
}

obj = {}
duplicate = {}
row_no = []


for index, row in df.iterrows():
    if index <= 353: #skipping untill 353 rows as it is already done by sales team
        continue
    # print(row["Note"])
    if (row["Note"] != "nan" or row["Note"] != "NAN") and row[
        "Note"
    ] == "geringe Profiltiefe":
        continue
    date = row["Date of Service"]
    formatted_date = date.strftime("%Y-%m-%d")
    plate_no_temp = str(row["License Plate"])
    plate_no = f"{plate_no_temp[0:2]}-{plate_no_temp[2:]}"

    if str(row["Axle"]) != "nan":
        axle_temp = axles[row["Axle"].replace(" ", "").lower()]
        wheel_pos_temp = tire_positions[row["Wheel Position"].replace(" ", "").lower()]
        axle_position = f"{axle_temp}{wheel_pos_temp}"
    else:
        continue

    brand = str(row["Brand"]).upper()
    tire_size = str(row["Tire Size"])[0:11]
    row_no.append({"no": index, "plate_no": row["License Plate"]})

    if str(tire_size) == "nan":
        if axle_temp.find("T"):
            tire_size = "385/65R22.5"
        else:
            tire_size = "315/70R22.5"

    parts = str(row["Tire Size"]).split(" ")
    td = float(row["Lowest Measured Tread Depth"])
    pressure = float(row["Measured Tire Pressure"])
    product_line = ""
    tire_id = ""
    tire_id_temp = str(row["ID"])

    if (
        tire_id_temp is None
        or tire_id_temp[0:3] == "000"
        or tire_id_temp == "nan"
        or len(tire_id_temp) < 10
    ):
        tire_id = generate_alphanumeric(9)
    else:
        tire_id = tire_id_temp
        
        
    if str(brand) == "nan" or str(brand) == "NAN":
        brand = "STEINKUHLER"
        if axle_temp.find("T"):
            product_line = "TRAILER"
        elif axle_temp.find("S"):
            product_line = "STEER"
        else:
            product_line = "DRIVE"
    elif (
        brand == "FULDA"
        or brand == "DUNLOP"
        or brand == "GOODYEAR"
        or brand == "FIRESTONE"
    ):
        product_line = parts[1]
    elif brand == "MICHELIN":
        if parts[2] is not None and parts[2] == "XTE3":
            product_line = parts[2]
        else:
            product_line = f"{parts[2]} {parts[3]} {parts[4]}"
    elif brand == "CONTINENTAL" or brand == "BF GOODRICH" or brand == "NEXT TREAD":
        product_line = f"{parts[2]} {parts[3]}"
    elif (
        brand == "PIRELLI"
        or brand == "BRIDGESTONE"
        or brand == "HANKOOK"
        or brand == "APOLLO"
    ):
        product_line = f"{parts[2]}"
    elif brand == "FALKEN":
        product_line = parts[3]
    elif brand == "LAURENT":
        product_line = parts[11]
    elif brand == "OTHER COMPETITORS":
        if parts[2] == "NEO":
            product_line = f"{parts[2]} {parts[3]}"
        else:
            product_line = parts[2]

    if plate_no in obj:
        if axle_position in obj[plate_no]:
            if (
                obj[plate_no][axle_position]["date"] is not None
                and obj[plate_no][axle_position]["date"] == formatted_date
            ):
                if plate_no in duplicate:
                    duplicate[plate_no].append(
                        {
                            "row_number": index + 5,
                            "date": formatted_date,
                            "axle_position": axle_position,
                            "tire_id": tire_id,
                            "td": td,
                            "pressure": pressure,
                            "tire_size": tire_size,
                            "brand": brand,
                            "product_line": product_line,
                            "parts": parts,
                        }
                    )
                else:
                    duplicate[plate_no] = [
                        {
                            "row_number": index + 5,
                            "date": formatted_date,
                            "axle_position": axle_position,
                            "tire_id": tire_id,
                            "td": td,
                            "pressure": pressure,
                            "tire_size": tire_size,
                            "brand": brand,
                            "product_line": product_line,
                            "parts": parts,
                        }
                    ]

            elif obj[plate_no][axle_position]["date"] < formatted_date:
                if duplicate is not None and plate_no in duplicate:
                    for value in duplicate[plate_no]:
                        if value["axle_position"] == axle_position:
                            duplicate[plate_no].remove(value)

                obj[plate_no][axle_position] = {
                    "date": formatted_date,
                    "axle_position": axle_position,
                    "tire_id": tire_id,
                    "td": td,
                    "pressure": pressure,
                    "tire_size": tire_size,
                    "brand": brand,
                    "product_line": product_line,
                    "parts": parts,
                }
            elif obj[plate_no][axle_position]["date"] > formatted_date:
                del obj[plate_no][axle_position]
                print("value removed")
                
                if duplicate is not None and plate_no in duplicate:
                    for value in duplicate[plate_no]:
                        if value["axle_position"] == axle_position:
                            print('duplicate removed')
                            duplicate[plate_no].remove(value)
                            
                obj[plate_no][axle_position] = {
                    "date": formatted_date,
                    "axle_position": axle_position,
                    "tire_id": tire_id,
                    "td": td,
                    "pressure": pressure,
                    "tire_size": tire_size,
                    "brand": brand,
                    "product_line": product_line,
                    "parts": parts,
                }         

        else:
            obj[plate_no][axle_position] = {
                "date": formatted_date,
                "axle_position": axle_position,
                "tire_id": tire_id,
                "td": td,
                "pressure": pressure,
                "tire_size": tire_size,
                "brand": brand,
                "product_line": product_line,
                "parts": parts,
            }

    else:
        obj[plate_no] = {}
        obj[plate_no][axle_position] = {
            "date": formatted_date,
            "axle_position": axle_position,
            "tire_id": tire_id,
            "td": td,
            "pressure": pressure,
            "tire_size": tire_size,
            "brand": brand,
            "product_line": product_line,
            "parts": parts,
        }


with open("initial_2.json", "w") as f:
    json.dump(obj, f)

with open("duplicate.json", "w") as f:
    json.dump(duplicate, f)
