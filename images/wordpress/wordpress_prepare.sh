#!/bin/sh

wp --allow-root core update
wp --allow-root plugin install amazon-s3-and-cloudfront --activate
wp --allow-root plugin install hyperdb --activate
