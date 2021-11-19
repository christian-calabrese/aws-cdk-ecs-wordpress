FROM wordpress:php7.4-fpm-alpine@sha256:1c15976b6a2a03ad762883a57a3b78639aa6bdb21d2afc2ad9acecd06df2a226

COPY wp-config.php /usr/src/wordpress/
COPY db-config.php /usr/src/wordpress/
COPY wordpress_prepare.sh /

RUN  curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar && chmod +x wp-cli.phar && mv wp-cli.phar /usr/local/bin/wp

ENTRYPOINT ["/wordpress_prepare.sh"]
WORKDIR /var/www/html