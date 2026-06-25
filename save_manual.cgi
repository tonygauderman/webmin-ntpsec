#!/usr/bin/perl
# save_manual.cgi
# Handles saving raw config file manual edits.

use WebminCore;
require './ntpsec-lib.pl';

&ReadParse();
&error_setup($text{'manual_err'});

my $file = $config{'ntp_conf'} || '/etc/ntpsec/ntp.conf';
my $data = $in{'data'};

# Normalize line endings
$data =~ s/\r\n/\n/g;
$data =~ s/\r/\n/g;

# Force a trailing newline if missing
if ($data ne '' && $data !~ /\n$/) {
    $data .= "\n";
}

&lock_file($file);
if (!open(my $fh, ">", $file)) {
    &unlock_file($file);
    &error("Failed to write to $file: $!");
}
print $fh $data;
close($fh);
&unlock_file($file);

&redirect("");
