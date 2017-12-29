


ifndef version
$(error version is not set)
endif

# Shouldn't be overridden
AWS_LAMBDA_FUNCTION_PREFIX ?= image-extract-test-extract-images
AWS_TEMPLATE ?= cloudformation/keyframe-extract-Template.yaml
LAMBDA_PACKAGE ?= lambda-$(version).zip
manifest ?= cloudformation/pht-test-Manifest.yaml
AWS_LAMBDA_FUNCTION_NAME=image-extract-test-extract-images
DEPLOYBUCKET ?= pht-deploy
OBJECT_KEY=$(AWS_LAMBDA_FUNCTION_NAME)/$(LAMBDA_PACKAGE)


FFMPEG_URL=https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-64bit-static.tar.xz

# Static, not sure if needed??
PYTHON=python3
PIP=pip3

.PHONY: ffmpeg

# Run all tests
test: cfn-validate
	echo $(PATH)

deploy: package-upload cfn-deploy 

#
# Cloudformation Targets

# Validate the template
cfn-validate: $(AWS_TEMPLATE)
	aws cloudformation validate-template --region us-east-1 --template-body file://$(AWS_TEMPLATE)
	
# Deploy the stack
cfn-deploy: cfn-validate  $(manifest)
	deploy_stack.rb --force -m $(manifest) pLambdaZipFile=$(OBJECT_KEY) pDeployBucket=$(DEPLOYBUCKET) pVersion=$(version)


#
# Lambda function management
#

clean: 
	rm -rf __pycache__ *.zip

# Install Lambda modules
# ffmpeg:
# 	curl -o ffmpeg-release-64bit-static.tar.xz $(FFMPEG_URL)
# 	cd ffmpeg ; tar -xzvf ../ffmpeg-release-64bit-static.tar.xz
# 	# rm ffmpeg/ffprobe

# Create the package Zip. Assumes all tests were done
package.zip: index.py ffmpeg
	zip -r $(LAMBDA_PACKAGE) $^  

package: ffmpeg package.zip

package-upload: package.zip
	aws s3 cp $(LAMBDA_PACKAGE) s3://$(DEPLOYBUCKET)/$(OBJECT_KEY)

# Update the Lambda Code without modifying the CF Stack
update: package
	aws lambda update-function-code --function-name $(AWS_LAMBDA_FUNCTION_NAME) --zip-file fileb://$(LAMBDA_PACKAGE)

