import json
import time

def handler(event, context):
    # Simulate that function takes 1 sec to finish processing
    time.sleep(1)

    print('request: {}'.format(json.dumps(event)))

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': 'DONE'
    }
