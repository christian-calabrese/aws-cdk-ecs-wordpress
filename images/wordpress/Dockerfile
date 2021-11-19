FROM wordpress

COPY wp-config.php /usr/src/wordpress/
COPY db-config.php /usr/src/wordpress/
COPY wordpress_prepare.sh /usr/src/wordpress/

RUN  curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar && chmod +x wp-cli.phar && mv wp-cli.phar /usr/local/bin/wp

WORKDIR /usr/src/wordpress/

CMD wp --allow-root core update
CMD wp --allow-root plugin install amazon-s3-and-cloudfront --activate
CMD wp --allow-root plugin install hyperdb --activate

WORKDIR /var/www/html