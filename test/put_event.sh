#!/bin/bash

if [ ! -f $1 ]; then
    echo "Usage: $0 <path-to-test-event>.json"
    echo "No file specified or cant read $1"
    exit -1
fi

if [ -z $TEST_ARN ]; then
	echo "export TEST_ARN=\"ARN of your stack's trigger topic\""
	exit 1
fi

aws sns publish --topic-arn $TEST_ARN --message file://${1}
