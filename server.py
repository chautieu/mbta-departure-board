from flask import Flask, render_template
import requests
from mbta import MbtaStation
import datetime

app = Flask(__name__)


@app.route("/")
def home():
    north_station = MbtaStation("North Station", "place-north")
    north_station.initialize_data()
    stop_name = north_station.get_stop_name()
    departures = north_station.get_departures()
    arrivals = north_station.get_arrivals()
    current_time = datetime.datetime.now().strftime("%I:%M %p")

    return render_template('index.html', stop_name=stop_name, departures=departures, arrivals=arrivals, current_time=current_time)


if __name__ == "__main__":
    app.run()
