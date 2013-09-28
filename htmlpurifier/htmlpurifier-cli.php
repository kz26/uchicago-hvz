<?

/*
    basic HTML Purifier STDIN/STDOUT interface
    Make configuration changes as necessary: http://htmlpurifier.org/live/configdoc/plain.html
*/

require_once('HTMLPurifier.auto.php');

error_reporting(0);

$config = HTMLPurifier_Config::createDefault();
//$config->set('Core.DefinitionCache', null);


$purifier = new HTMLPurifier($config);

while(!feof(STDIN)) {
    $text .= fread(STDIN, 1024);
}

$clean_html = $purifier->purify($text);
fwrite(STDOUT, $clean_html);

exit();
?>

