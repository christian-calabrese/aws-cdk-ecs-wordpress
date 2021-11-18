define( 'AS3CF_SETTINGS', serialize( array(
    // Storage Provider ('aws', 'do', 'gcp')
    'provider' => 'aws',
    // Access Key ID for Storage Provider (aws and do only, replace '*')
    'access-key-id' => '********************',
    // Secret Access Key for Storage Providers (aws and do only, replace '*')
    'secret-access-key' => '**************************************',
    // GCP Key File Path (gcp only, absolute file path, not URL)
    // Make sure hidden from public website, i.e. outside site's document root.
    'key-file-path' => '/path/to/key/file.json',
    // Use IAM Roles on Amazon Elastic Compute Cloud (EC2) or Google Compute Engine (GCE)
    'use-server-roles' => true,
    // Bucket to upload files to
    'bucket' => getenv('MEDIA_S3_BUCKET'),
    // Bucket region (e.g. 'us-west-1' - leave blank for default region)
    'region' => '',
    // Automatically copy files to bucket on upload
    'copy-to-s3' => true,
    // Enable object prefix, useful if you use your bucket for other files
    'enable-object-prefix' => true,
    // Object prefix to use if 'enable-object-prefix' is 'true'
    'object-prefix' => 'wp-content/uploads/',
    // Organize bucket files into YYYY/MM directories matching Media Library upload date
    'use-yearmonth-folders' => true,
    // Append a timestamped folder to path of files offloaded to bucket to avoid filename clashes and bust CDN cache if updated
    'object-versioning' => true,
    // Delivery Provider ('storage', 'aws', 'do', 'gcp', 'cloudflare', 'keycdn', 'stackpath', 'other')
    'delivery-provider' => 'storage',
    // Custom name to display when using 'other' Delivery Provider
    'delivery-provider-name' => 'Akamai',
    // Rewrite file URLs to bucket
    'serve-from-s3' => true,
    // Use a custom domain (CNAME), not supported when using 'storage' Delivery Provider
    'enable-delivery-domain' => false,
    // Custom domain (CNAME), not supported when using 'storage' Delivery Provider
    // 'delivery-domain' => 'cdn.example.com',
    // Enable signed URLs for Delivery Provider that uses separate key pair (currently only 'aws' supported, a.k.a. CloudFront)
    'enable-signed-urls' => false,
    // Access Key ID for signed URLs (aws only, replace '*')
    // 'signed-urls-key-id' => '********************',
    // Key File Path for signed URLs (aws only, absolute file path, not URL)
    // Make sure hidden from public website, i.e. outside site's document root.
    // 'signed-urls-key-file-path' => '/path/to/key/file.pem',
    // Private Prefix for signed URLs (aws only, relative directory, no wildcards)
    // 'signed-urls-object-prefix' => 'private/',
    // Serve files over HTTPS
    'force-https' => false,
    // Remove the local file version once offloaded to bucket
    'remove-local-file' => false,
    // DEPRECATED (use enable-delivery-domain): Bucket URL format to use ('path', 'cloudfront')
    //'domain' => 'path',
    // DEPRECATED (use delivery-domain): Custom domain if 'domain' set to 'cloudfront'
    //'cloudfront' => 'cdn.exmple.com',
) ) );

/* That's all, stop editing! Happy blogging. */

/** Absolute path to the WordPress directory. */
if ( !defined('ABSPATH') )
    define('ABSPATH', dirname(__FILE__) . '/');

/** Sets up WordPress vars and included files. */
require_once(ABSPATH . 'wp-settings.php');