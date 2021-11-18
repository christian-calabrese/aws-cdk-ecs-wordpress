$wpdb->add_database(array(
 'host'	=> getenv('PRIMARY_DB_URI') != false ? getenv('PRIMARY_DB_URI') : "",
    'user'	=> getenv('DB_USER') != false  ? getenv('DB_USER') : "",
    'password'	=> getenv('DB_PWD') != false  ? getenv('DB_PWD') : "",
  'name' 	=> getenv('DB_NAME') != false ? getenv('DB_NAME') : "",
));

$sec_db_uri = getenv('SECONDARY_DB_URI') != false ? getenv('SECONDARY_DB_URI') : "";
if($sec_db_uri != "") {
    $wpdb->add_database(array(
     'host' 	=> $sec_db_uri,
     'user'	=> getenv('DB_USER') != false ? getenv('DB_USER') : "",
     'password'	=> getenv('DB_PWD') != false ? getenv('DB_PWD') : "",
      'name' 	=> getenv('DB_NAME') != false ? getenv('DB_NAME') : "",
     'write'	=> 0,
     'read'	=> 1,
    ));
}