#!/usr/bin/env python3

class DeviceNotFoundException(Exception):
    status_code = 404

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def to_dict(self):
        return {'message': self.message}


class UpstreamApiException(Exception):
    status_code = 502

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def to_dict(self):
        return {'message': self.message}
