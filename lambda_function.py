import json
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = "WishList"
table = dynamodb.Table(TABLE_NAME)

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,GET',
        'Content-Type': 'application/json'
    }
    print(f"Received event: {json.dumps(event)}")
    if 'httpMethod' in event:
        http_method = event['httpMethod']
    else:
        http_method = 'GET'
    
    if http_method == 'GET':
        print("GET request received")
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
            print("GET request received inside else")
            response = table.scan()
            items = response.get('Items', [])
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(items, cls=DecimalEncoder)
            }
    elif http_method == "PUT":
        try:
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,GET,PUT'
            }
            print("Full event:", event)
            
            # Parse the request body
            try:
                body = json.loads(event['body'])
                print("Request body:", body)
                roll_number = body.get('roll')
                
                if not roll_number:
                    return {
                        'statusCode': 400,
                        'headers': headers,
                        'body': json.dumps({'error': 'Missing required parameter: roll'})
                    }

                # Ensure roll number is a string
                body['roll'] = str(roll_number)

                try:
                    # Try to update the item
                    update_expression = "set " + ", ".join(f"#{k}=:{k}" for k in body if k != 'roll')
                    expression_attribute_values = {f":{k}": v for k, v in body.items() if k != 'roll'}
                    expression_attribute_names = {f"#{k}": k for k in body if k != 'roll'}
                    
                    response = table.update_item(
                        Key={'roll': body['roll']},
                        UpdateExpression=update_expression,
                        ExpressionAttributeValues=expression_attribute_values,
                        ExpressionAttributeNames=expression_attribute_names,
                        ReturnValues="ALL_NEW"
                    )
                    
                    result = response.get('Attributes', {})
                    message = "Student data updated successfully"
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ValidationException':
                        # Item doesn't exist, create a new one
                        table.put_item(Item=body)
                        result = body
                        message = "New student data created successfully"
                    else:
                        raise

                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'message': message,
                        'data': result
                    }, cls=DecimalEncoder)
                }
                
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Invalid JSON in request body'})
                }
                
        except Exception as e:
            print("Error:", str(e))
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': str(e)})
            }

    
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Unsupported HTTP method'}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
