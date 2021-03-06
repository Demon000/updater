import json

from flask import Blueprint, jsonify, request

from api_common import get_oems, get_device_builds, get_device_data, get_device_versions, group_changes_by_build
from changelog import GerritServer, get_project_repo, get_paginated_changes, get_timestamp, get_device_dependencies
from config import Config
from custom_exceptions import InvalidValueException, UpstreamApiException, DeviceNotFoundException

api = Blueprint('api_v2', __name__)
extras_data = json.loads(open(Config.EXTRAS_BLOB, 'r').read())
gerrit = GerritServer(Config.GERRIT_URL)


@api.route('/oems')
def api_v2_oems():
    oems = get_oems()
    response = []

    for oem, devices_data in oems.items():
        response_oem = {
            'name': oem,
            'devices': []
        }

        for device_data in devices_data:
            response_oem['devices'].append({
                'model': device_data['model'],
                'name': device_data['name'],
            })

        response.append(response_oem)

    return jsonify(response)


@api.route('/devices/<string:device>')
def api_v2_device(device):
    device_data = get_device_data(device)

    return jsonify({
        'name': device_data['name'],
        'model': device_data['model'],
        'oem': device_data['oem'],
        'info_url': Config.WIKI_INFO_URL.format(device=device),
        'install_url': Config.WIKI_INSTALL_URL.format(device=device),
        'versions': get_device_versions(device),
        'dependencies': get_device_dependencies(device),
    })


@api.route('/devices/<string:device>/builds')
def api_v2_device_builds(device):
    builds = get_device_builds(device)

    def get_download_url(build):
        return Config.DOWNLOAD_BASE_URL + build['filepath']

    for build in builds:
        build['url'] = get_download_url(build)
        if 'recovery' in build:
            build['recovery']['url'] = get_download_url(build['recovery'])

    return jsonify(builds)


@api.route('/changes')
def api_v2_changes():
    args = request.args.to_dict()

    page = args.get('page')
    page = 0 if page is None else page
    try:
        page = int(page)
    except ValueError:
        pass
    if type(page) != int:
        raise InvalidValueException('Page is not an integer')

    changes = get_paginated_changes(gerrit, page=page)
    response = []

    for change in changes:
        response.append({
            'url': change.url,
            'repository': get_project_repo(change.project),
            'branch': change.branch,
            'subject': change.subject,
            'submitted': get_timestamp(change.submitted),
            'updated': get_timestamp(change.updated),
        })

    return jsonify(response)


@api.route('/extras')
def api_v2_extras():
    return jsonify(extras_data)


@api.errorhandler(DeviceNotFoundException)
@api.errorhandler(InvalidValueException)
@api.errorhandler(UpstreamApiException)
@api.errorhandler(UpstreamApiException)
def api_v2_handle_exception(e):
    return jsonify({
        'error': e.message
    }), 400


@api.errorhandler(ConnectionError)
def api_v2_handle_exception():
    return jsonify({
        'error': 'Connection failed'
    }), 400
