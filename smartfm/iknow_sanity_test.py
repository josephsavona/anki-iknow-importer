from iknow import SmartFMAPI

api = SmartFMAPI("debug.txt")
items = api.listItems(83026, True, True)
api._close()