FROM wordpress

COPY wp-config.php /usr/src/wordpress/

RUN  curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar && chmod +x wp-cli.phar && mv wp-cli.phar /usr/local/bin/wp

WORKDIR /usr/src/wordpress/

RUN wp --allow-root core update
RUN wp --allow-root plugin install amazon-s3-and-cloudfront

WORKDIR /var/www/html