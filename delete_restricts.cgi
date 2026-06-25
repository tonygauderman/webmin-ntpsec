#!/usr/bin/perl
# delete_restricts.cgi
# Deletes multiple selected access control rules.

use WebminCore;
require './ntpsec-lib.pl';

&ReadParse();
&error_setup($text{'restrict_err'});

my @d = split(/\0/, $in{'d'});
if (!@d) {
    &redirect("edit_restrict.cgi");
    exit;
}

my $conf = &get_ntp_config();

# Sort in descending order to avoid index shifts during splice
@d = sort { $b <=> $a } @d;

foreach my $idx (@d) {
    if ($idx >= 0 && $idx < @$conf) {
        splice(@$conf, $idx, 1);
    }
}

&lock_file($config{'ntp_conf'});
my $ok = &save_ntp_config($conf);
&unlock_file($config{'ntp_conf'});

if (!$ok) {
    &error("Failed to save changes to configuration file");
}

&redirect("edit_restrict.cgi");
