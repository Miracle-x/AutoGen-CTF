<?php
if (isset($_GET['file'])) {
    echo '<pre>';
    echo htmlspecialchars(file_get_contents($_GET['file']));
    echo '</pre>';
} else {
    echo 'Usage: ?file=filename';
}
?>