import env
import requests
import traceback
import random
import string


def APiCalls(obj):
    try:
        for fleet_name, vehicle_types in obj.items():
            for vehicle_type, plate_nos in vehicle_types.items():
                for plate_no, tires_info in plate_nos.items():
                    if (
                        len(tires_info["tires"]) == 0
                    ):  # this condition is for invalid product line present we just skip it
                        continue
                    print("----------------------------------")
                    print(
                        "vehicle ",
                        vehicle_type.lower(),
                        "------",
                        tires_info["vehicle_name"],
                    )
                    # Generate a random 17-digit number for chassis/vin
                    RandomNumber = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(17))
                    payload = None
                    if vehicle_type.lower() == "rigid":
                        payload = {
                            "fleet_name": fleet_name,
                            "location": fleet_name,
                            "assets": {
                                "trucks": [
                                    {
                                        "name": tires_info["vehicle_name"],
                                        "reg_plate": str(plate_no).replace(" ","").strip(),
                                        "tank_capacity": 1000,  # setting default value as not available in csv
                                        "vin": RandomNumber,
                                        "internal_grouping": "trucks",
                                    }
                                ]
                            },
                        }
                    else:
                        # Prepare the payload
                        payload = {
                            "fleet_name": fleet_name,
                            "location": fleet_name,
                            "assets": {
                                "trailers": [
                                    {
                                        "name": tires_info["vehicle_name"],
                                        "reg_plate": str(plate_no).replace(" ","").strip(),
                                        "chassis_number": RandomNumber,
                                        "internal_grouping": "trailer"
                                        if vehicle_type.lower() == "trailer"
                                        else "semi-trailer",
                                    }
                                ]
                            },
                        }

                    # Make the API request
                    response = requests.post(
                        f"{env.base_url}/fleet",
                        json=payload,
                        headers={"Authorization": f"Bearer {env.bearer_token}"},
                    )

                    if response.status_code == 200:
                        print("vehicle created successfully")
                        created_fleet = response.json()["resp"]["fleet"]["fleet_id"]
                        # Check if all positions in tires_info['tires'] are None then it is an un-configured vehicle
                        nan_positions = False
                        for tire in tires_info["tires"]:
                            if str(tire["position"]) == "nan":
                                nan_positions =True
                                break
                        if nan_positions:
                            print('This vehicle is un-configured and no tires are present either, so proceeding to the next vehicle')
                            continue
                        
                        #get the fleet details of the created vehicle
                        response_vehicle = requests.get(
                            f"{env.base_url}/vehicles?fleet_id={created_fleet}",
                            headers={"Authorization": f"Bearer {env.bearer_token}"},
                        )
                        if response_vehicle.status_code == 200:
                            print('fleet details fetched successfully')
                            created_vehicle_detail = None
                            if vehicle_type.lower() != "rigid":
                                created_vehicle_detail = response_vehicle.json()[
                                    "resp"
                                ]["trailers"]
                            else:
                                created_vehicle_detail = response_vehicle.json()[
                                    "resp"
                                ]["trucks"]

                            # Retrieve the vehicle_id based on tires_info["vehicle_name"]
                            vehicle_details = None
                            for trailer in created_vehicle_detail:
                                if trailer["reg_plate"].replace(" ", "").lower() == plate_no.replace(" ", "").lower():
                                    vehicle_details = trailer
                                    print('Vehicle details fetched successfully!!')
                                    break
                            #in this case vehicle with the above reg_number is already present in different fleet
                            if vehicle_details is None:
                                #calling profile endpoint
                                print("started to search other fleets for the vehicle details based on reg_plate")
                                response_profile = requests.get(f"{env.base_url}/profile", headers= {
                                                "Authorization": f"Bearer {env.bearer_token}"
                                            })
                                fleet_ids = []
                                if response_profile.status_code == 200:
                                    if "fleets" in response_profile.json()["resp"]:
                                        for fleet in response_profile.json()["resp"]["fleets"]:
                                            fleet_ids.append(fleet["fleet_id"])
                                    for fleet_id in fleet_ids:
                                        response_separate_fleet = requests.get(f"{env.base_url}/vehicles?fleet_id={fleet_id}", headers={
                                                    "Authorization": f"Bearer {env.bearer_token}"
                                                })
                                        if "trucks" in response_separate_fleet.json()["resp"]:
                                            for truck in response_separate_fleet.json()["resp"]["trucks"]:
                                                if str(truck["reg_plate"]).replace(" ", "").strip() == str(plate_no).replace(" ", "").strip():
                                                    vehicle_details = truck
                                                    break

                                        if "trailers" in response_separate_fleet.json()["resp"]:
                                            for trailer in response_separate_fleet.json()["resp"]["trailers"]:
                                                if trailer["reg_plate"] == plate_no:
                                                    vehicle_details = trailer
                                                    break

                                        if vehicle_details is not None:
                                            break
                                    if vehicle_details is None:
                                        print("we cannot find the vehicle that is registered with the app")
                                        continue
                                    else:
                                        print("vehicle found in other fleet!!!!")
                                else:
                                     print(
                                    "API request failed with status code while getting the profile values: ",
                                    response_profile.status_code,
                                    response_profile.content,
                                )
                                if vehicle_details is None:
                                    print('vehicle with this registration plate is present already with the app But we cannot find the vehicle')
                                    continue
                            #add tire to inventory
                            system_tire_ids = []
                            mount_payloads = []
                            for tire_info in tires_info["tires"]:
                                # Create a new payload for each tire
                                tire_id = None
                                if tire_info.get("tire_id") is None or tire_info.get("tire_id") == 'nan' or (len(tire_info.get("tire_id")) < 9):
                                    tire_id=''.join(random.choice(string.ascii_letters + string.digits) for _ in range(9))
                                else:
                                    tire_id = tire_info.get("tire_id")
                                payload = {
                                    "fleet_id": created_fleet,
                                    "tires": [
                                        {
                                            "tire_id": str(tire_id),
                                            "brand": str(tire_info["brand"]),
                                            "product_line": str(tire_info["product_line"]),
                                            "size": str(tire_info["tire_size"]),
                                            "tread_depth": str(tire_info["TD"]),
                                            "isRetread": False,
                                        }
                                    ],
                                }
                                # Adding the tires to the tire inventory
                                response_tireInventory = requests.post(
                                    f"{env.base_url}/tire",
                                    json=payload,
                                    headers={
                                        "Authorization": f"Bearer {env.bearer_token}"
                                    },
                                )
                                if response_tireInventory.json()['resp']['tire_summary'][0]['upload_status'] == 'success':
                                    print(f'Tire has been created for tire_id = {tire_id}!')
                                    system_tire_ids.append(
                                        response_tireInventory.json()["resp"][
                                            "tire_summary"
                                        ][0].get("system_tire_id")
                                    )
                                    event = {
                                        "position": tire_info.get("position"),
                                        "axle_position_id": None,  # This will take the first element and remove it
                                        "event_type": "MOUNT",
                                        "event_date": tire_info.get("TD_date"),
                                    }
                                    mount_payloads.append(event)
                                else:
                                    print(
                                        f"API request failed with status code while creating a tire in inventory: {response_tireInventory.json()['resp']['tire_summary'][0]['upload_result']}"
                                    )   
                                                             
                            
                                
                            # Check if any position in tires_info['tires'] contains the character '3'
                            axle = None
                            if vehicle_type.lower() == "rigid":
                                if any(
                                    "2SR" in str(tire.get("position", ""))
                                    or "2SL" in str(tire.get("position", ""))
                                    for tire in tires_info["tires"]
                                ):
                                    axle = "6x2"
                                elif any(
                                    "D" in str(tire.get("position", ""))
                                    for tire in tires_info["tires"]
                                ):
                                    axle = "4x2"
                            else:
                                if any(
                                    "3" in str(tire.get("position", ""))
                                    for tire in tires_info["tires"]
                                ):
                                    axle = "3-axle"
                                elif any(
                                    "2" in str(tire.get("position", ""))
                                    for tire in tires_info["tires"]
                                ):
                                    axle = "2-axle"
                            if axle is None:
                                print(
                                    f"Cannot configure the vehicle {vehicle_type}-->{vehicle_details['name']} as necessary info is not present for the vehicle"
                                )
                                continue
                            endpoint = None
                            if vehicle_type.lower() == "rigid":
                                endpoint = f"{env.base_url}/truck?vehicle_id={vehicle_details['vehicle_id']}"
                                # check for the steer and drive tire sizes
                                steer_tire_size = None
                                drive_tire_size = None
                                for tire in tires_info["tires"]:
                                    position = str(tire["position"])
                                    if position == "1SL" or position == "1SR":
                                        if steer_tire_size is None:
                                            steer_tire_size = str(tire["tire_size"])
                                    elif position == "2SR" or position == "2SL" or position == "1DLI" or position == "1DRI" or position == "1DR" or position == "1DL":
                                        if drive_tire_size is None:
                                            drive_tire_size = str(tire["tire_size"])
                                    if steer_tire_size and drive_tire_size is not None:
                                        break
                                if steer_tire_size is None and drive_tire_size is not None: 
                                    steer_tire_size = drive_tire_size
                                if drive_tire_size is None and steer_tire_size is not None: 
                                    drive_tire_size = steer_tire_size   
                                payload = {
                                "name": str(vehicle_details["name"]),
                                "reg_plate":str(vehicle_details["reg_plate"]),
                                "internal_grouping": str(vehicle_details[
                                    "internal_grouping"
                                ]),
                                "axle_type": axle,
                                "steer_tire_size": steer_tire_size,
                                "drive_tire_size": drive_tire_size,
                                "vin": str(vehicle_details["vin"]),
                                "tank_capacity": 1000,
                                }
                            else:
                                endpoint = f"{env.base_url}/trailer?vehicle_id={vehicle_details['vehicle_id']}"
                                payload = {
                                    "name": vehicle_details["name"],
                                    "reg_plate": vehicle_details["reg_plate"],
                                    "internal_grouping": vehicle_details[
                                        "internal_grouping"
                                    ],
                                    "axle_type": axle,
                                    "tire_size": tires_info["tires"][0]["tire_size"],
                                    "chassis_number": vehicle_details["chassis_number"],
                                }
                            # API call to configure the tires
                            response_configure = requests.post(
                                endpoint,
                                json=payload,
                                headers={"Authorization": f"Bearer {env.bearer_token}"},
                            )
                            if response_configure.status_code == 200:
                                print(
                                    f'{vehicle_details["name"]} is successfully configured to {axle}'
                                )
                                # Get axle_position_id from the response
                                for i, mounted_tire in enumerate(response_configure.json()["resource"]["mounted_tires"]):
                                    if i >= len(mount_payloads):
                                        break
                                    mount_payloads[i]["axle_position_id"] = str(mounted_tire["axle_position_id"])
                                # Mounting the tires to the appropriate positions
                                for event, tire_id in zip(
                                    mount_payloads, system_tire_ids
                                ):
                                    payload = {"events": []}
                                    payload["events"].append(event)
                                    response_mounted_tire = requests.put(
                                        f"{env.base_url}/tire/{tire_id}",
                                        json=payload,
                                        headers={
                                            "Authorization": f"Bearer {env.bearer_token}"
                                        },
                                    )
                                    if response_mounted_tire.status_code == 200:
                                        print(
                                            f"API request successful for mounting tires: {tire_id}"
                                        )
                                    else:
                                        print(
                                            f"API request failed for mounting the tire_id: {tire_id} with status code {response_mounted_tire.status_code} and {response_mounted_tire.content}"
                                        )
                            else:
                                print(
                                    "API request failed with status code while configuring the vehicle: ",
                                    response_configure.status_code,
                                    response_configure.content,
                                )
                        else:
                            print(
                                "API request failed with status code while fetching the vehicle details: ",
                                response_vehicle.status_code,
                                response_vehicle.content,
                            )
                    else:
                        print(
                            "API request failed with status code for creating the vehicle: ",
                            response.status_code,
                            response.content,
                        )
    except Exception as e:
        error = traceback.format_exc()
        print(f"error in the implementation: {error}")
        

# APiCalls(env.obj2)
