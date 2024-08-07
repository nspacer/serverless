import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('StudentTable')

def lambda_handler(event, context):
    try:
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,GET,PUT'
        }
        print(event)
        try:
            roll_number = event['roll']
        except KeyError as e:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': f'Missing required parameter: {str(e)}'})
            }
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid JSON in request body'})
            }

        # Ensure roll number is a string
        event['roll'] = str(roll_number)

        try:
            # Try to update the item
            update_expression = "set " + ", ".join(f"{k}=:{k}" for k in event if k != 'roll')
            expression_attribute_values = {f":{k}": v for k, v in event.items() if k != 'roll'}
            
            response = table.update_item(
                Key={'roll': event['roll']},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW"
            )
            
            result = response['Attributes']
            message = "Student data updated successfully"
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationException':
                # Item doesn't exist, create a new one
                table.put_item(Item=event)
                result = event
                message = "New student data created successfully"
            else:
                raise

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': message, 'data': result})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
