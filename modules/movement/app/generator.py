import datetime
import pytz
import os
import keymanager

# from googlegeocoder import GoogleGeocoder

assigned_device_id = keymanager.MODULE_DEVICE_ID
time_zone = keymanager.MODULE_TIME_ZONE
geo_api_key = keymanager.MODULE_GEO_API_KEY

## IdGenerator contains methods for generating various IDs used to identify transactions/videos
class IdGenerator(object):

    def __init__(self,
                address = "12280 NE District Way, Bellevue, WA 98005"):
        self.address = address
        self.device_id = assigned_device_id
        # self.geocoder = GoogleGeocoder(geo_api_key)

    ## Return current date and time (PST)
    def gen_date_time(self, time_delimiter=""):
        try:
            d = datetime.datetime.now()
            timezone = pytz.timezone(time_zone)
            d_aware = timezone.localize(d)
            date = d_aware.strftime("%Y-%m-%d")
            time = ""
            if time_delimiter == "-":
                time = d_aware.strftime('%H-%M-%S')
            else:
                time = d_aware.strftime('%H:%M:%S')
            return date, time
        except Exception as e:
            print(e)

    ## Return transaction id: device_id + date + time
    def gen_transaction_id(self):
        try:
            date, time = self.gen_date_time("-")
            transaction_id = self.device_id + date + "_" + time
            print("transaction_id : " + transaction_id)
            return transaction_id
        except Exception as e:
            print(e)

    ## Return latitude and longitude of device's address
    ## https://python-googlegeocoder.readthedocs.io/en/latest/
    # def gen_lat_lng(self):
    #     try:
    #         search = self.geocoder.get(self.address)
    #         lat = search[0].geometry.location.lat
    #         lng = search[0].geometry.location.lng
    #         print("lat: " + str(lat))
    #         print("lng: " + str(lng))
    #         return lat, lng
    #     except Exception as e:
    #         print(e)

    # ## This method would not be used in this device. It is just here to show to logic of generating member ids
    # def gen_member_id(self, first: str, last: str, email: str, phone: str):
    # 	try:
    # 		country_code = search[len(search)]
    # 		member_id = first[:1] + last[:1] + counter
    # 	except Exception as e:
    # 		print(e)

    # ## This method would not actually be applied on this device, especially not in production.
    # ## It is here to show the logic applied to generate unique device ids at a production facility.
    # ## Find pre-generated device ids as env variables in the manifest 
    # def gen_device_id(self):
    # 	try:
    # 		model_number = product_prefix_ZZZ + version_number_000 + building_code_ZZZ	# PAC100GIX 	 = PAC + 100 + GIX
    # 		device_id = model_number + production_run_ZZ + unit_counter_ZZZ				# PAC10GIX01001 = PAC100GIX + 01 + 001
    # 		return device_id
    # 	except Exception as e:
    # 		print(e)
