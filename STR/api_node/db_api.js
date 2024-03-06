const { Pool } = require('pg');
const jsonTireResult = require('./initial_2.json');
// const jsonTireResult = require('./initialTest.json');
const { default: axios } = require('axios');
const {
	generateNewPayloadVehicle,
	generateTiresPayload,
	generateTrailerPayload,
	generateTruckBusPayload,
	compareDates,
} = require('./db_api_helpers');
require('dotenv').config();

// Create a new pool instance
const pool = new Pool({
	user: process.env.PGUSER,
	host: process.env.PGHOST,
	database: process.env.PGDB,
	password: process.env.PGPASSWORD,
	port: process.env.PGPORT,
});

const fs = require('fs');
const path = require('path');

// Specify the file path for the log file
const logFilePath = path.join(__dirname, process.env.LOG_FILE_NAME);

// Create a writable stream connected to the log file
const logStream = fs.createWriteStream(logFilePath, { flags: 'a' });

// Redirect console.log to the log stream
console.log = function(message) {
  logStream.write(`${new Date().toISOString()} - ${message}\n`);
}


async function queries() {
	try {
		const headers = {
			'Content-Type': 'multipart/form-data',
		};
		const loginToken = await axios.post(
			`${process.env.LOGIN_URL}`,
			{
				email: 'steinkuehler-bot@co2opt.com',
				password: 'Password.123',
			},
			{ headers }
		);

		const access_token = loginToken.data.access_token;

		const customer_id = process.env.CUSTOMER_ID;
		const fleets = await pool.query(
			`select fleet_id,fleet_name from fleet_data where customer_id= $1;`,
			[customer_id]
		);
		let fleetIdNameMap = {};
		let fleetIdArray = fleets.rows.map((id) => id.fleet_id);
		fleets.rows.map((fleet) => {
			fleetIdNameMap[fleet.fleet_id] = fleet.fleet_name;
		});
		const placeholders = fleetIdArray
			.map((_, index) => `$${index + 1}`)
			.join(',');

		const trailer_vehicles = await pool.query(
			`select *, 'trailer' AS vehicle_type from trailer_metadata where fleet_id in (${placeholders});`,
			fleetIdArray
		);
		const truck_vehicles = await pool.query(
			`select *, 'truck' AS vehicle_type from truck_metadata where fleet_id in (${placeholders});`,
			fleetIdArray
		);

		const result = [...trailer_vehicles.rows, ...truck_vehicles.rows];
		
		const count = {
			vehiclenotPresent : 0,
			unconfig : 0,
			configTiresMounted : 0,
			configTiresNotPresent : 0,
			configChangeDateYes :0,
			configChangeDateNo : 0,
		}
		for (let res in jsonTireResult) {
			let flag = false,
				foundVehicle,
				vehicleType;
			result.map(async (vehicle, index) => {
				if (vehicle.name.replace(' ', '') == res.replace(' ', '')) {
					foundVehicle = vehicle;
					flag = !flag;
				}
			});
			for (let index in jsonTireResult[res]) {
				if (
					index == '1TL' ||
					index == '1TR' ||
					index == '2TL' ||
					index == '2TR' ||
					index == '2TL' ||
					index == '2TR'
				) {
					vehicleType = 'trailers';
					break;
				} else {
					vehicleType = 'trucks';
					break;
				}
			}

			if (!flag) {
				console.log(`vehicle not found, creating  new  vehicles : ${res}`);
				count.vehiclenotPresent++;
				continue;
				let vehicleAddPayload = generateNewPayloadVehicle(res, vehicleType);
				try {
					const vehiclesAddResponse = await axios.post(
						`${process.env.BASE_URL}/fleet`,
						vehicleAddPayload,
						{ headers: { Authorization: `Bearer ${access_token}` } }
					);

					if (vehiclesAddResponse.status == 200) {
						console.log(JSON.stringify(vehiclesAddResponse.data));
						console.log(
							`---------------Vehicles successfully created---------------------`
						);
						const fleetId = vehiclesAddResponse.data.resp.fleet.fleet_id;
						let tempPayload = [];
						let innerObj = jsonTireResult[res];
						for (const innerKey in innerObj) {
							tempPayload.push(innerObj[innerKey]);
						}
						let tirePayload = generateTiresPayload(
							fleetId,
							tempPayload,
							vehicleType,
							`${res.slice(0, 5)} ${res.slice(5)}`
						);

						//add tires and mount it
						try {
							let TiresAddedAndMount = await axios.post(
								`${process.env.BASE_URL}/tire`,
								tirePayload,
								{ headers: { Authorization: `Bearer ${access_token}` } }
							);

							if (TiresAddedAndMount.status == 200) {
								console.log(`Tires are successfully created and mounted`);
								console.log('--------DONE----------');
							}
						} catch (error) {
							console.log(error);
							console.log(`error while creating and mounting the tires`);
						}
					}
				} catch (error) {
					console.log(error);
					console.log(`error while creating the vehicles`);
				}
			} else {
				/**
				 * configured or unconfigured
				 * if unconfigured - directly start to configure and mount the tires
				 * if configured - mounted tire values needed to compare and then mount the tires
				 */
				foundVehicle.fleet_name = fleetIdNameMap[foundVehicle.fleet_id];
				if (foundVehicle && foundVehicle.axle_type == null) {
					console.log(
						`vehicle found - unconfigured - ${res}  - ${vehicleType}`
					);
					count.unconfig++;
					continue;
					//configure the vehicle
					try {
						if (foundVehicle.vehicle_type == 'trailer') {
							const configureTrailerPayload =
								generateTrailerPayload(foundVehicle);

							configure_vehicle = await axios.post(
								`${process.env.BASE_URL}/trailer?vehicle_id=${foundVehicle.vehicle_id}`,
								configureTrailerPayload,
								{ headers: { Authorization: `Bearer ${access_token}` } }
							);
						} else {
							const configureTruckPayload =
								generateTruckBusPayload(foundVehicle);
							configure_vehicle = await axios.post(
								`${process.env.BASE_URL}/truck?vehicle_id=${foundVehicle.vehicle_id}`,
								configureTruckPayload,
								{ headers: { Authorization: `Bearer ${access_token}` } }
							);
						}

						if (configure_vehicle.status === 200) {
							console.log(
								`Vehicle is successfully configured -- proceeding to mount`
							);
							let tempPayload = [];
							let innerObj = jsonTireResult[res];
							for (const innerKey in innerObj) {
								tempPayload.push(innerObj[innerKey]);
							}

							let tirePayload = generateTiresPayload(
								foundVehicle.fleet_id,
								tempPayload,
								vehicleType,
								foundVehicle.name
							);
							//add tires and mount it
							try {
								let TiresAddedAndMount = await axios.post(
									`${process.env.BASE_URL}/tire`,
									tirePayload,
									{ headers: { Authorization: `Bearer ${access_token}` } }
								);

								if (TiresAddedAndMount.status == 200) {
									console.log(`Tires are successfully created and mounted`);
									console.log('--------DONE----------');
								}
							} catch (error) {
								console.log(error);
								console.log(`error while creating and mounting the tires`);
							}
						}
					} catch (error) {
						console.log(`Error in configuring vehicle`);
						console.log(error);
					}
				} else {
					//already configured vehicles so fetch the mounted tires and compare them
					console.log(
						`Vehicle is already configured - ${res} - ${vehicleType}`
					);
					const mountedTires = await pool.query(
						`select mt.system_tire_id,mt.vehicle_id,mt.position, mt.vehicle_type,ti.system_tire_id,ti.mount_date, ti.last_event_date, ti.tire_id,
						ti.last_tread_depth, ti.last_pressure
						from mounted_tires mt 
						Inner join tire_inventory ti on ti.system_tire_id=mt.system_tire_id
						where mt.vehicle_id=$1;`,
						[foundVehicle.vehicle_id]
					);

					let tempPayload = [];
					let innerObj = jsonTireResult[res];
					for (const innerKey in innerObj) {
						tempPayload.push(innerObj[innerKey]);
					}

					if (mountedTires.rows.length == 0) {
						console.log(`configured but no tires are mounted case - manual entry suggested`);
						count.configTiresNotPresent++;
						console.log(`------------------DONE-------------`);
					} else {
						console.log(`configured and tires are mounted case`);

						console.log(tempPayload);
						console.log(mountedTires.rows);
						const dateResult = compareDates(tempPayload, mountedTires.rows);

						if (dateResult.length == 0) {
							console.log(
								`no changes are needed already latest tires are mounted`
							);
							count.configChangeDateNo++;
							console.log(`---------------DONE------------`);
						} else {
							console.log(`changes are needed on ${dateResult}`);
							count.configChangeDateYes++
							console.log(`---------------DONE------------`);
						}
					}
				}
			}
		}
		pool.end();
		console.log(JSON.stringify(count));
	} catch (error) {
		console.log(error);
		pool.end();
		console.log(`outer error: ${error.stack}`);
	}
}

queries();
