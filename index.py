from __future__ import print_function
import boto3
import json
import logging
import os
import subprocess
from botocore.exceptions import ClientError
from datetime import datetime
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lambda main routine
def handler(event, context):
    # logger.info("Received event: " + json.dumps(event, sort_keys=True))
    message = json.loads(event['Records'][0]['Sns']['Message'])
    logger.info("Received message: " + json.dumps(message, sort_keys=True))

    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    sns_client = boto3.client('sns')

    movie_bucket = message['Records'][0]['s3']['bucket']['name']
    movie_key = message['Records'][0]['s3']['object']['key']
    movie_filename = movie_key.split('/')[-1]
    movie_fileprefix = movie_filename.split('.')[0]

    logger.info("New Movie Object is s3://{}/{} - FilePrefix: {}".format(movie_bucket, movie_key, movie_fileprefix))


    # Create the Temp Dir for my stills
    base_dir = "/tmp/{}".format(movie_fileprefix)
    output_dir = base_dir + "/stills"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    logger.info("Using {} as my base dir and {} as my output_dir".format(base_dir, output_dir))

    movie_local_path = "{}/{}".format(base_dir, movie_filename)

    try:
        s3_resource.Bucket(movie_bucket).download_file(movie_key, movie_local_path)
        time.sleep(1)
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            logger.error("The object does not exist.")
        else:
            logger.error("Error downloading movie: {}".format(e))

    # If I'm in the lambda, I won't get the path via the event
    # Use the default lambda location
    ffmpeg_path = '/var/task/ffmpeg/ffmpeg'
    if ffmpeg_path in event:
        ffmpeg_path = event['ffmpeg_path']

    # Run ffmpeg to extract them
    command = "{} -i '{}' -r {} {}/{}_%04d.jpg".format(ffmpeg_path, movie_local_path, os.environ['FRAMERATE'], 
        output_dir, movie_fileprefix)
    logger.info("About to execute ffmpeg command: {}".format(command))
    try:
        cmd_status = subprocess.call(command, shell=True)
        logger.info("ffmpeg output: {}".format(cmd_status))
    except Exception as e:
        logger.info("ffmpeg Error: {}".format(e))

    # Get a list of the created files
    output_keys = []
    for f in os.listdir(output_dir):
        logger.info("Output file: {}".format(f))
        output_keys.append(f)

        # Push files to S3

    # Publish Event
    output_event = {}
    output_event['bucket'] = movie_bucket
    output_event['movie_key'] = movie_key
    output_event['num_images'] = len(output_keys)
    output_event['images'] = output_keys
    output_message = json.dumps(output_event, sort_keys=True)
    logger.info("Sending Message: {}".format(output_message))
    # sns_client.publish(TopicArn=os.environ['OUTPUT_TOPIC'], Message=output_message)
    return(output_event)



# Establish a method to test locally 
if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--movie_s3_key", help="S3 key for test video file")
    parser.add_argument("--movie_s3_bucket", help="S3 bucket for test video file")
    args = parser.parse_args()

    if args.movie_s3_key == None:
        print("Must specify --movie_s3_key")
        exit(-1)
    if args.movie_s3_bucket == None:
        print("Must specify --movie_s3_bucket")
        exit(-1)

    message = {}
    message['Records'] = []
    message['Records'].append({})
    message['Records'][0]['s3'] = {}
    message['Records'][0]['s3']['bucket'] = {}
    message['Records'][0]['s3']['object'] = {}
    message['Records'][0]['s3']['bucket']['name'] = args.movie_s3_bucket
    message['Records'][0]['s3']['object']['key'] = args.movie_s3_key

    event = {}
    event['Records'] = []
    event['Records'].append({})
    event['Records'][0]['Sns'] = {}
    event['Records'][0]['Sns']['Message'] = json.dumps(message, sort_keys=True)

    context = {}
    event['ffmpeg_path'] = "/Users/chrisfarris/bin/ffmpeg"
    
    rc = handler(event, context)
    print("Lambda executed with {}".format(rc))