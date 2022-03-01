import json
import time

def handler(event, context):
    # Simulate that function take 1 second to finish processing
    time.sleep(1)

    # print('request: {}'.format(json.dumps(event)))

    for e in event['Records']:
        print('Message ID: {}'.format(e['messageId']))
        print('Message Body: {}'.format(e['body']))

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': 'DONE'
    }
