FROM wordpress
COPY wp-config.php /usr/src/wordpress/
COPY db-config.php /usr/src/wordpress/
COPY wordpress_prepare.sh /usr/src/wordpress/

RUN  curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar && chmod +x wp-cli.phar && mv wp-cli.phar /usr/local/bin/wp

WORKDIR /usr/src/wordpress/

#CMD sh /usr/src/wordpress/wordpress_prepare.sh

WORKDIR /var/www/html