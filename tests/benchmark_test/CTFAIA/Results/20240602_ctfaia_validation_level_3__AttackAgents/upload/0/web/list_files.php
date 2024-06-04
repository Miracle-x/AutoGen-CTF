
<?php
    function list_dir($dir) {
        if ($handle = opendir($dir)) {
            echo "Listing files in $dir:<br><br>";
            while (false !== ($entry = readdir($handle))) {
                $path = $dir . '/' . $entry;
                echo "$path (" . (is_dir($path) ? 'directory' : 'file') . ", permissions: " . substr(sprintf('%o', fileperms($path)), -4) . ")<br>";
            }
            closedir($handle);
        } else {
            echo "Unable to open directory $dir";
        }
        echo "<br>";
    }

    list_dir('.');
    list_dir('/uploads');
    list_dir('/var/www/html');
?>
