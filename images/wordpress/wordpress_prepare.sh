#!/bin/sh

wp --allow-root core update
wp --allow-root plugin install amazon-s3-and-cloudfront
wp --allow-root plugin install hyperdb
