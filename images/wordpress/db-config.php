$wpdb->add_database(array(
 'host'	=> getenv('PRIMARY_DB_URI') != false ? getenv('PRIMARY_DB_URI') : "",
    'user'	=> getenv('WORDPRESS_DB_USER') != false  ? getenv('WORDPRESS_DB_USER') : "",
    'password'	=> getenv('WORDPRESS_DB_PASSWORD') != false  ? getenv('WORDPRESS_DB_PASSWORD') : "",
  'name' 	=> getenv('DB_NAME') != false ? getenv('DB_NAME') : "",
));

$sec_db_uri = getenv('SECONDARY_DB_URI') != false ? getenv('SECONDARY_DB_URI') : "";
if($sec_db_uri != "") {
    $wpdb->add_database(array(
     'host' 	=> $sec_db_uri,
     'user'	=> getenv('WORDPRESS_DB_USER') != false ? getenv('WORDPRESS_DB_USER') : "",
     'password'	=> getenv('WORDPRESS_DB_PASSWORD') != false ? getenv('WORDPRESS_DB_PASSWORD') : "",
      'name' 	=> getenv('WORDPRESS_DB_NAME') != false ? getenv('WORDPRESS_DB_NAME') : "",
     'write'	=> 0,
     'read'	=> 1,
    ));
}