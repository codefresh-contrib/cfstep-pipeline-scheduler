import json
import os
import requests
import sys
import urllib.parse


def test_success(endpoint, status_code, content):
    if status_code == 200:
        print('Call Successful')
    else:
        print('ERROR!!!')
        print(f'Endpoint: {endpoint}')
        print(f'Code: {status_code}')
        print(f'Message: {content}')
        sys.exit(1)

def get_pipeline_id(host, headers, build_id):
    endpoint = '{}/builds/{}'.format(host, build_id)
    r = requests.get(endpoint, headers=headers)
    test_success(endpoint, r.status_code, r.content)
    build_data = json.loads(r.text)
    pipeline_id = build_data['serviceId']
    return pipeline_id


def create_trigger_event(host, headers, expression, message):
    endpoint = '{}/hermes/events?public=false'.format(host)
    json = {'kind':'codefresh','type':'cron','values':{'expression':expression,'message':message}}
    r = requests.post(endpoint, json=json, headers=headers)
    test_success(endpoint, r.status_code, r.content)
    trigger_event = r.text.strip('\"')
    return trigger_event

def crud_trigger(action, host, headers, target_pipeline_id, event):
    endpoint = '{}/hermes/triggers/{}/{}'.format(host, urllib.parse.quote(urllib.parse.quote(event)), target_pipeline_id)
    if action == 'create':
        r = requests.post(endpoint, json={'event': event, 'pipeline':target_pipeline_id}, headers=headers)
    elif action == 'delete':
        r = requests.delete(endpoint, headers=headers)
    test_success(endpoint, r.status_code, r.content)

def delete_trigger_event(host, headers, event):
    event = urllib.parse.quote(urllib.parse.quote(event))
    endpoint = '{}/hermes/events/{}'.format(host, event)
    r = requests.delete(endpoint, headers=headers)
    test_success(endpoint, r.status_code, r.content)
    

def get_triggers(host, headers, target_pipeline_id):
    endpoint = '{}/hermes/triggers/pipeline/{}'.format(host, target_pipeline_id)
    r = requests.get(endpoint, headers=headers)
    test_success(endpoint, r.status_code, r.content)
    triggers_json = json.loads(r.text)
    return triggers_json

def main():

    action = os.getenv('ACTION', 'read')
    api_token = os.getenv('CF_API_KEY')
    headers = {"Authorization": "Bearer {}".format(api_token)}
    expression = os.getenv('CRON_EXPRESSION')
    host = os.getenv('CF_API_HOST', 'https://g.codefresh.io/api')
    scheduler = os.getenv('CF_BUILD_ID')
    pipeline_id = get_pipeline_id(host, headers, scheduler)
    target_pipeline_id = os.getenv('TARGET_PIPELINE_ID', pipeline_id)

    # Get listing of events for target pipeline
    triggers_json = get_triggers(host, headers, target_pipeline_id)

    if 'create' in action:
        print(f'Scheduling Deployment of: {target_pipeline_id} using CRON Expression: {expression}')
        message = scheduler
        if triggers_json:
            for event in triggers_json:
                event = event['event']
                previous_event = event.split(':')[3]
                print(f'Deleting existing scheduled event: {previous_event}')
                crud_trigger('delete', host, headers, target_pipeline_id, event)
                delete_trigger_event(host, headers, event)
                message = message + ' {}'.format(previous_event)
                print(f'Schedulers: {message}')
        else:
            print(f'Scheduler: {message}')
        print('Creating new trigger event...')
        event = create_trigger_event(host, headers, expression, message)     
        print(f'Created new trigger event: {event}')
        print('Creating new trigger...')
        crud_trigger('create', host, headers, target_pipeline_id, event)
        print(f'Added new event as trigger to {target_pipeline_id}')
    if 'read' in action:
        scheduler_list = triggers_json[0]['event'].split(':')[3]
        print(f'Starting..., scheduled by the following builds: {scheduler_list}')
    if 'delete' in action:
        event = urllib.parse.quote(triggers_json[0]['event'])
        print(f'Deleting Trigger: {triggers_json[0]} from pipeline')
        delete_trigger_status = crud_trigger('delete', host, headers, target_pipeline_id, event)
        print(f'Deleting Event Trigger: {event}')
        delete_trigger_event_status = delete_trigger_event(host, headers, event)
        

if __name__ == "__main__":
    main()