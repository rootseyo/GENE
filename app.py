# -- coding: utf-8 --

from flask import Flask, render_template, jsonify, request, Response
from config import EMAIL, TOKEN, URL
import requests
from requests.auth import HTTPBasicAuth
import json
import collections
from functools import wraps

app = Flask(__name__)


def get_payload(jql, startAt):
    return json.dumps({
        "expand": [
            "names",
            "schema",
            "operations"
        ],
        "jql": jql,
        "maxResults": 50,
        "fields": [
            "summary",
            "status",
            "assignee",
            "resolutiondate",
            "customfield_10023",

        ],
        "fieldsByKeys": False,
        "startAt": startAt
    })


def as_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        res = f(*args, **kwargs)
        res = json.dumps(res, ensure_ascii=False).encode('utf8')
        return Response(res, content_type='application/json; charset=utf-8')
    return decorated_function


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/point/report', methods=['POST'])
@as_json
def point_report():
    jql = request.form['jql']
    startAt = 50
    total = 0
    url = URL
    auth = HTTPBasicAuth(EMAIL, TOKEN)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8"
    }

    # jql = "project = GEN and issuetype = task and status in (Done,Closed) and resolutiondate > -3w ORDER BY resolutiondate asc"

    payload = get_payload(jql, startAt)

    response = requests.request(
        "POST", url, data=payload, headers=headers, auth=auth)
    kanban_json = json.loads(response.text)
    total = kanban_json['total']

    issues = dict()
    label = dict()
    data = []
    issue_list = []

    while(total > startAt):
        payload = get_payload(jql, startAt)

        response = requests.request(
            "POST", url, data=payload, headers=headers, auth=auth)
        kanban_json = json.loads(response.text)

        for aa in kanban_json['issues']:
            issues['summaray'] = aa['fields']['summary']

            if (aa['fields']['assignee']) is not None:
                issues['assignee'] = aa['fields']['assignee']['key']
            else:
                issues['assignee'] = 'Unassigned'

            if aa['fields']['customfield_10023'] is not None:
                issues['point'] = aa['fields']['customfield_10023']
            else:
                issues['point'] = 0

            issues['resolutiondate'] = aa['fields']['resolutiondate'][:10]

            # Gorup by story point
            dt = issues['resolutiondate']
            print(list(label.keys()))
            if dt in list(label.keys()):
                print(label[dt])
                label[dt]['point'] = label[dt]['point'] + issues['point']
                label[dt]['cnt'] = label[dt]['cnt'] + 1
            else:
                label[dt] = dict()
                label[dt]['point'] = issues['point']
                label[dt]['cnt'] = 1
            issue_list.append(dict(issues))

        startAt = startAt + 50

    data.append(dict(label))
    data.append(list(issue_list))

    return data


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
