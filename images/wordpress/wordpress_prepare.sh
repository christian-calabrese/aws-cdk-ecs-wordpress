#!/bin/sh
export TT=$PWD
cd /usr/src/wordpress/

if wp --allow-root core is-installed; then
  wp --allow-root core update
  wp --allow-root plugin install amazon-s3-and-cloudfront
  wp --allow-root plugin install hyperdb
fi

cd $TT