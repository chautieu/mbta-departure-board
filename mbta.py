import requests
import json
import datetime

class RouteType:
    COMMUTER_RAIL_TYPE = "2"

class MbtaStation:
    def __init__(self, stop_name, stop_id):
        self.stop_name = stop_name
        self.stop_id = stop_id
        self.departures = {}
        self.arrivals = {}
        self.predictions = {}
        self.start_time = ""

    def get_stop_name(self):
        return self.stop_name

    def get_departures(self):
        return self.departures

    def get_arrivals(self):
        return self.arrivals

    def get_start_time(self):
        return self.start_time

    def initialize_data(self):
        self.update_time()

        routes = self.get_commuter_rail_routes()
        self.extract_route_ids(routes)

        self.update_predictions()

        self.extract_departure_times()
        self.extract_arrival_times()

    def mbta_get(self, api_url, params):
        headers = {'user-agent': 'Dataquest'}
        try:
            response = requests.get(api_url, headers=headers, params=params)
            return response
        except Exception:
            raise Exception(f"Unable to get data from MBTA for url: {api_url}")

    def get_commuter_rail_routes(self):
        api_url = "https://api-v3.mbta.com/routes?"
        filter = "filter[stop]=" + self.stop_id
        filter += "&filter[type]=" + RouteType.COMMUTER_RAIL_TYPE
        commuter_rails = self.mbta_get(api_url + filter, {})
        return commuter_rails

    def get_next_departure_time(self, route_id):
        api_url = "https://api-v3.mbta.com/schedules?include=route"
        filter = "&filter[route]=" + route_id
        filter += "&filter[stop]=" + self.stop_id
        filter += "&filter[direction_id]=0"
        filter += "&filter[min_time]=" + self.start_time
        try:
            departure_time = self.mbta_get(api_url + filter, {}).json()
            return departure_time['data'][0]
        except Exception:
            raise Exception("Unable to get the next departure time")

    def get_arrival_times(self):
        api_url = "https://api-v3.mbta.com/schedules?"
        filter = "filter[stop]=" + self.stop_id
        filter += "&filter[direction_id]=1"
        filter += "&filter[min_time]=" + self.start_time
        try:
            arrival_times = self.mbta_get(api_url + filter, {})
            return arrival_times
        except Exception:
            raise Exception("Unable to get the arrival times")

    def update_predictions(self):
        api_url = "https://api-v3.mbta.com/predictions?"
        filter = "&filter[stop]=" + self.stop_id
        filter += "&filter[route_type]=" + RouteType.COMMUTER_RAIL_TYPE

        predictions = self.mbta_get(api_url + filter, {}).json()['data']
        for prediction in predictions:
            trip_id = prediction['relationships']['trip']['data']['id']
            status = prediction['attributes']['status']
            self.predictions[trip_id] = status

    def get_route_info(self, route_id):
        api_url = "https://api-v3.mbta.com/routes/"
        route_info = self.mbta_get(api_url + route_id, {}).json()['data']['attributes']
        result = {
            'destination': route_info['direction_destinations'][0],
            'direction': route_info['direction_names'][0],
            'long_name': route_info['long_name'],
            'color': route_info['color']
        }
        return result

    def extract_route_ids(self, routes_response):
        routes_data = routes_response.json()["data"]
        for route in routes_data:
            route_id = route["id"]
            self.departures[route_id] = {}
            route_info = self.get_route_info(route_id)
            self.departures[route_id] = route_info

    def update_time(self):
        current_time = datetime.datetime.now()
        self.start_time = current_time.strftime("%H:%M")

    def convert_to_readable_time(self, time_string):
        '''
        :params time_string in the format YYYY-MM-DDTHH:MM:SS-HH:MM
        ex: 2020-05-03T23:30:00-04:00
        '''
        utc_start_index = len(time_string) - 6
        time_string = time_string[:utc_start_index]
        time_obj = datetime.datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%S')
        return time_obj.strftime("%I:%M %p")

    def extract_departure_times(self):
        for route_id in self.departures.keys():
            # get the departure time
            schedule = self.get_next_departure_time(route_id)
            departure = self.convert_to_readable_time(schedule['attributes']['departure_time'])
            trip_id = schedule['relationships']['trip']['data']['id']
            trip_status = "Status Unavailable" if trip_id not in self.predictions else self.predictions[trip_id]

            # add it to the routes
            self.departures[route_id]['departure'] = departure if departure else "No departure for this route at this time"
            self.departures[route_id]['trip_status'] = trip_status

    def extract_arrival_times(self):
        arrivals = self.get_arrival_times().json()['data']
        for schedule in arrivals:
            route_id = schedule['relationships']['route']['data']['id']
            if route_id in self.departures.keys():
                # get the arrival time
                arrival_time = self.convert_to_readable_time(schedule['attributes']['arrival_time'])
                trip_id = schedule['relationships']['trip']['data']['id']
                trip_status = "Status Unavailable" if trip_id not in self.predictions else self.predictions[trip_id]
                arrival = {
                    'arrival': arrival_time,
                    'trip_status': trip_status,
                    'line_name': self.departures[route_id]['long_name']
                }

                # add it to the routes
                self.arrivals[route_id] = arrival
