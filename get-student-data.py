import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('StudentTable')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,GET'
    }

    if 'httpMethod' in event:
        http_method = event['httpMethod']
    else:
        http_method = 'GET'

    if http_method == 'GET':
        if 'pathParameters' in event and event['pathParameters'] and 'rollNumber' in event['pathParameters']:
            roll_number = event['pathParameters']['rollNumber']
            response = table.get_item(Key={'roll': roll_number})
            if 'Item' in response:
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(response['Item'], cls=DecimalEncoder)
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'message': 'Student not found'})
                }
        else:
            response = table.scan()
            items = response.get('Items', [])
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(items, cls=DecimalEncoder)
            }

    return {
        'statusCode': 400,
        'headers': headers,
        'body': json.dumps({'message': 'Invalid request'})
    }
