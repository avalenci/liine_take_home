from datetime import datetime
import csv
from flask import Flask, request, abort, jsonify, make_response
from flask_restful import Resource, Api, reqparse
import json
from marshmallow import Schema, fields

weekday_str_ary = ["Mon", "Tues", "Wed", "Thu", "Fri", "Sat", "Sun"]

def convertToDatetime(time):
    try: # try two ways to convert to datetime
        return datetime.strptime(time, "%I:%M%p")
    except ValueError:
        return datetime.strptime(time, "%I%p")

def testConvertToDateTime():
    time1a = "11:00am"
    time1b = "11am"
    time2 = "9pm"
    dateTime1 = datetime.strptime("1900-01-01 11:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")
    dateTime2 = datetime.strptime("1900-01-01 21:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")
    assert convertToDatetime(time1a) == dateTime1 # if time is in 00:00am/pm format
    assert convertToDatetime(time1b) == dateTime1 # if time in in 00am/pm format
    assert convertToDatetime(time2) == dateTime2 # if time is in 0am/pm format

def isOpen(row, day, time):
        sentences = row.split("/") # in case there are more dates
        for sentence in sentences:
            words = sentence.split()
            words.append("/") # add end character
            checking_time = False
            time_str = ""
            day_list = []
            for word in words:
                if not checking_time and word[0].isnumeric(): # check if word is a time, then enter time mode
                    if not (day in day_list):
                        break # day isn't right so foggettaboutit
                    day_list = []
                    checking_time = True
                if word == "/": # reached end character, know to check end time and break
                    end_time = convertToDatetime(time_str)
                    if (end_time > time):
                        return True # if we haven't breaked thus far, the dates and times must match
                    break # otherwise we're done
                if checking_time: # when checking times, this means we are checking the first time of a range
                    if word == "-":
                        start_time = convertToDatetime(time_str)
                        if (start_time > time):
                            break # start time isn't right so just forget it
                        time_str = ""
                    else:
                        time_str += word
                else: # not checking times, therefore checking days
                    day_range = word.replace(",", "").split("-")
                    if (len(day_range) == 2):
                        index1 = weekday_str_ary.index(day_range[0])
                        index2 = weekday_str_ary.index(day_range[1])
                        if (index1 > index2): # in case weekday range goes past Sun
                            weekdays_to_add = weekday_str_ary[index1:] + weekday_str_ary[:index2 + 1]
                        else:
                            weekdays_to_add = weekday_str_ary[index1 : index2 + 1]
                        day_list += weekdays_to_add
                    else:
                        day_list += day_range
        return False # if none of the dates and times match, return false

def testIsOpen():
    row1 = "Mon-Sat 11:00 am - 10 pm"
    row2 = "Mon-Sun 12pm - 9pm"
    row3 = "Mon-Sat, Sun 12pm - 9:00pm"
    row4 = "Mon-Sat 12pm - 9:00pm / Sun 12pm - 1pm"
    row5 = "Sat-Mon 12pm - 9:00pm"
    day1 = "Sun"
    day2 = "Sat"
    day3 = "Mon"
    time1 = datetime.strptime("1900-01-01 11:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")
    time2 = datetime.strptime("1900-01-01 21:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")
    time3 = datetime.strptime("1900-01-01 12:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")
    assert not isOpen(row1, day1, time1) # if day is not included, then return False
    assert not isOpen(row2, day1, time1) # if day is included but not time, then return False
    assert not isOpen(row2, day1, time2) # if day is included but time is equal to end time, return False
    assert isOpen(row1, day2, time1) # if day and time is included, return True
    assert isOpen(row3, day1, time3) # if day and time is included, when there is day separated by a comma, return True
    assert isOpen(row4, day1, time3) # if day and time is included, when there is another day/time separated by "/", return True
    assert isOpen(row5, day3, time3) # if day and time is included, when day range goes beyond weekday ary, then return True

class MyAPISchema(Schema):
    date = fields.Str(required=True)

class MyAPI(Resource):

    def get(self):
        errors = schema.validate(request.args)
        if errors: # if errors, send error message
            abort(400, str(errors))

        date_time_str = request.args["date"]
        try:
            date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError: # if wrong format, abort and send message
            abort(400, "Incorrect Date Format: Must be in %Y-%m-%d %H:%M:%S.%f, e.g. 2018-06-23 10:15:27.243860")
        date_time_time = datetime.strptime(str(date_time_obj.time()), "%H:%M:%S.%f")

        given_day = weekday_str_ary[date_time_obj.weekday()]

        with open("restaurants.csv") as csvfile:
            spamreader = csv.reader(csvfile, delimiter="\"")
            next(spamreader)
            ret_ary = []
            for row in spamreader:
                if isOpen(row[1], given_day, date_time_time):
                    ret_ary.append(row[0][0:-1]) # append restaurant name to list, cut off trailing comma
            response = make_response(
                jsonify(
                    {"restaurants": ret_ary}
                ),
                200,
            )
            response.headers["Content-Type"] = "application/json"
            return response

app = Flask(__name__)
api = Api(app)
api.add_resource(MyAPI, "/")
schema = MyAPISchema()

if __name__ == "__main__":
    testConvertToDateTime()
    testIsOpen()
    app.run()