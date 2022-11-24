import ee
import eemont
import math
from datetime import datetime, date, timedelta
import dateutil

class GFS_MAP:
    #We are using NOAA/NASA Global Forecast System from Google Earth Engine to
    #calculate Fire Weather Index (FWI)
    #The input for calculation is:
    ### timezone  : 'Continent/City'
    ###   The time zone (e.g. 'America/Los_Angeles'); defaults to UTC
    ### date_time : datetime
    ###   the date and time in noon local time for the observation
    ### boundary : ee.Geometry
    ###   the boundary used to limit the ee.Image file
    ### temp : ee.Image
    ###   temperature in degree Celsius observed in noon
    ### humidity : ee.Image
    ###   relative humidity in percent observed in noon
    ### wind : ee.Image
    ###   wind speed in kph observed in noon
    ### precipitation : ee.Image
    ###   total precipitation in mm in the past 24 hours, observed in noon

    def __init__(self, date, timezone, boundary):
        self.date = date
        self.boundary = boundary
        self.timezone = timezone

        self.__inputs_fwi()

    def __calculate_temperature(self):
        temperature = 'temperature_2m_above_ground'
        self.temp = self.gfs.select(temperature) \
            .rename('Temp')

    def __calculate_humidity(self):
        humidity = 'relative_humidity_2m_above_ground'
        self.hum = self.gfs.select(humidity) \
            .rename('Hum')

    def __calculate_wind(self):
        u_comp_wind = 'u_component_of_wind_10m_above_ground'
        v_comp_wind = 'v_component_of_wind_10m_above_ground'
        u_wind = self.gfs.select(u_comp_wind)
        v_wind = self.gfs.select(v_comp_wind)

        wind = ((u_wind ** 2 + v_wind ** 2) ** 0.5) * 3.6
        self.wind = wind.rename('Wind')

    def __calculate_precipitation(self):
        precipitation = 'total_precipitation_surface'
        #NOAA precipitation data is in kg/m2 and it's same to mm
        self.prec = self.gfs.select(precipitation) \
                        .rename('Prec')

    def __inputs_fwi(self):
        # Create noon local standard datetime
        local_noon = datetime(self.date.year, self.date.month, \
            self.date.day, hour = 12, tzinfo = dateutil.tz.gettz( \
            self.timezone))
        utc_datetime = local_noon.astimezone(dateutil.tz.UTC)
        forecast_time = int(utc_datetime.timestamp() * 1000)

        start_datetime = utc_datetime - timedelta(days = 1)

        self.gfs = ee.ImageCollection(f'NOAA/GFS0P25') \
            .filterMetadata('forecast_time', 'equals', forecast_time) \
            .closest(start_datetime.isoformat()).first()

        self.__calculate_temperature()
        self.__calculate_humidity()
        self.__calculate_wind()
        self.__calculate_precipitation()

    def preprocess(self, interpolation, crs, scale):
        self.temp = self.temp.resample(interpolation) \
            .reproject(crs = crs, scale = scale)

        self.hum = self.hum.resample(interpolation) \
            .reproject(crs = crs, scale = scale)

        self.wind = self.wind.resample(interpolation) \
            .reproject(crs = crs, scale = scale)

        self.prec = self.prec.resample(interpolation) \
            .reproject(crs = crs, scale = scale)

    def fwi_data_input(self):
        return ee.Image([self.temp, self.hum, self.wind, self.prec])