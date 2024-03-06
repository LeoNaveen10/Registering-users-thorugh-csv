function generateRandomAlphaNumeric(length) {
	const characters =
		'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
	let result = '';
	for (let i = 0; i < length; i++) {
		result += characters.charAt(Math.floor(Math.random() * characters.length));
	}

	return result;
}

function generateNewPayloadVehicle(res, vehicle_type) {
	if (vehicle_type == 'trailers') {
		return {
			fleet_name: 'STR NEW-2',
			location: 'Hamburg',
			assets: {
				trailers: [
					{
						name: `${res.slice(0, 5)} ${res.slice(5)}`,
						reg_plate: `${res.slice(0, 5)} ${res.slice(5)}`,
						chassis_number: generateRandomAlphaNumeric(19),
						internal_grouping: 'STR NEW',
						axle_type: '3-axle',
						tire_size: '385/55R22.5',
					},
				],
			},
		};
	} else {
		return {
			fleet_name: 'STR NEW-2',
			location: 'Hamburg',
			assets: {
				trucks: [
					{
						name: `${res.slice(0, 5)} ${res.slice(5)}`,
						vin: generateRandomAlphaNumeric(19),
						reg_plate: `${res.slice(0, 5)} ${res.slice(5)}`,
						tank_capacity: 450,
						axle_type: '4x2',
						internal_grouping: 'STR NEW',
						steer_tire_size: '315/60R22.5',
						drive_tire_size: '315/60R22.5',
					},
				],
			},
		};
	}
}

function generateTiresPayload(
	fleet_id,
	tirePayload,
	vehicle_type,
	vehicleName
) {
	let returnValue = [];
	for (let tire of tirePayload) {
		returnValue.push({
			tire_id: tire.tire_id,
			brand: tire.brand,
			product_line: tire.product_line,
			size: tire.tire_size,
			tread_depth: tire?.td || 0,
			isRetread: false,
			axle_position: tire.axle_position,
			vehicle_name: vehicleName,
			mount_date: tire.date,
		});
	}
	return {
		fleet_id: fleet_id,
		tires: returnValue,
	};
}

function generateTruckBusPayload(vehicle_details) {
	return {
		name: vehicle_details.name,
		reg_plate: vehicle_details.reg_plate,
		internal_grouping: vehicle_details.internal_grouping,
		axle_type: '4x2',
		steer_tire_size: '315/60R22.5',
		drive_tire_size: '315/60R22.5',
		vin: vehicle_details.vin,
		tank_capacity: vehicle_details.tank_capacity
			? parseInt(vehicle_details.tank_capacity)
			: 0,
	};
}

function generateTrailerPayload(vehicle_details) {
	return {
		name: vehicle_details.name,
		reg_plate: vehicle_details.reg_plate,
		internal_grouping: vehicle_details.internal_grouping,
		axle_type: '3-axle',
		tire_size: '385/55R22.5',
		chassis_number: vehicle_details.chassis_number,
	};
}

function compareDates(payload, mounted_tires) {
	let result = [];
	for (var pay in payload) {
		for (var tire in mounted_tires) {
			if (pay.axle_position == tire.position) {
				const payloadDate = new Date(pay.date);
				const mountDate = new Date(tire.mount_date);
				if (payloadDate.getTime() > mountDate.getTime()) {
					// if (
					// 	pay.tire_id.toLowerCase() !== mounted_tires.tire_id.toLowerCase()
					// ) {
						result.push(pay.axle_position);
					// }
				}
			}
		}
	}
	return result;
}
module.exports = {
	generateNewPayloadVehicle,
	generateTiresPayload,
	generateTruckBusPayload,
	generateTrailerPayload,
	compareDates,
};
