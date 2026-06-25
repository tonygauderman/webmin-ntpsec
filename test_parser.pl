#!/usr/bin/perl
# test_parser.pl
# Unit test for NTPsec configuration parser/serializer.

use strict;
use warnings;
use File::Basename;
use File::Spec;

# Create mock web-lib.pl in parent directory
my $script_dir = dirname(File::Spec->rel2abs(__FILE__));
my $parent_dir = dirname($script_dir);
my $mock_web_lib = File::Spec->catfile($parent_dir, 'web-lib.pl');
my $mock_core_lib = File::Spec->catfile($parent_dir, 'WebminCore.pm');

open(my $fh, ">", $mock_web_lib) or die "Failed to create mock web-lib.pl: $!";
print $fh <<'EOF';
# Mock web-lib.pl for testing
package main;

our %config = (
    'ntp_conf' => 'test_ntp.conf',
    'ntpq_path' => 'mock_ntpq',
    'ntpdig_path' => 'mock_ntpdig',
    'ntp_service' => 'ntpsec'
);
our %text = (
    'servers_err' => 'Failed to save time source',
    'servers_eaddress' => 'Missing address',
    'servers_eminpoll' => 'Invalid minpoll',
    'servers_emaxpoll' => 'Invalid maxpoll'
);

sub init_config { }
sub lock_file { }
sub unlock_file { }
sub backquote_command {
    my ($cmd) = @_;
    $? = 0;
    if ($cmd =~ /ntpq -p/) {
        return <<'PEERS';
     remote           refid      st t when poll reach   delay   offset   jitter
===============================================================================
 0.debian.pool.n .POOL.          16 p    -  256    0   0.0000   0.0000   0.0001
*99-28-14-242.li ....             1 u  262 1024  377  17.7697  14.1377   6.4936
+66.175.236.237  139.78.97.128    2 u  150 1024  377  21.0801  17.9759   7.0412
PEERS
    } elsif ($cmd =~ /ntpq -c ntsinfo/) {
        return <<'NTS';
NTS client sends:                       10
NTS client recvs good:                  8
NTS client recvs w error:               2
NTS server sends:                       0
NTS KE client probes good:              5
NTS KE client probes bad:               1
NTS KE serves good:                     0
NTS KE serves bad:                      0
NTS decode cookies error:               0
NTS decode cookies:                     0
NTS decode cookies old:                 0
NTS decode cookies old2:                0
NTS decode cookies older:               0
NTS decode cookies too old:             0
NTS make cookies:                       0
NTS server recvs good:                  0
NTS server recvs w error:               0
NTS fill cookies:                       0
NTS
    }
}
sub backquote_logged { }
1;
EOF
close($fh);

open(my $cfh_core, ">", $mock_core_lib) or die "Failed to create mock WebminCore.pm: $!";
print $cfh_core <<"EOF";
package WebminCore;
sub import {
    my \$caller = caller;
    # Load web-lib.pl absolute path
    do "$mock_web_lib";
    no strict 'refs';
    *{"\${caller}::init_config"} = \\&main::init_config;
    *{"\${caller}::backquote_command"} = \\&main::backquote_command;
}
1;
EOF
close($cfh_core);

# Create mock executable files for -x checks
open(my $mh, ">", "mock_ntpq") or die "Failed to create mock_ntpq: $!";
print $mh "#!/bin/sh\nexit 0\n";
close($mh);
chmod(0755, "mock_ntpq");

open(my $dh, ">", "mock_ntpdig") or die "Failed to create mock_ntpdig: $!";
print $dh "#!/bin/sh\nexit 0\n";
close($dh);
chmod(0755, "mock_ntpdig");

# Create test NTP configuration file
my $test_conf = 'test_ntp.conf';
open(my $cfh, ">", $test_conf) or die "Failed to create test config file: $!";
print $cfh <<'EOF';
# Initial configuration
driftfile /var/lib/ntpsec/ntp.drift
tos maxclock 11

pool 0.debian.pool.ntp.org iburst
server time.cloudflare.com nts iburst prefer minpoll 4 maxpoll 6

restrict default kod nomodify nopeer noquery limited
restrict 127.0.0.1
restrict ::1
EOF
close($cfh);

# Load ntpsec-lib.pl and test parsing
push(@INC, $parent_dir);
require './ntpsec-lib.pl';

print "--- Testing Configuration Parser ---\n";
my $conf = &get_ntp_config($test_conf);
print "Parsed " . scalar(@$conf) . " lines.\n";

# Assert parsed values
my $pool_count = 0;
my $server_count = 0;
my $restrict_count = 0;
my $driftfile_val = "";

foreach my $item (@$conf) {
    if ($item->{'type'} eq 'pool') {
        $pool_count++;
        die "Parsed pool address mismatch" if ($item->{'address'} ne '0.debian.pool.ntp.org');
        die "Parsed pool option mismatch" if (!$item->{'options'}->{'iburst'});
    } elsif ($item->{'type'} eq 'server') {
        $server_count++;
        die "Parsed server address mismatch" if ($item->{'address'} ne 'time.cloudflare.com');
        die "Parsed server options mismatch (nts)" if (!$item->{'options'}->{'nts'});
        die "Parsed server options mismatch (minpoll)" if ($item->{'options'}->{'minpoll'} != 4);
        die "Parsed server options mismatch (maxpoll)" if ($item->{'options'}->{'maxpoll'} != 6);
    } elsif ($item->{'type'} eq 'restrict') {
        $restrict_count++;
    } elsif ($item->{'type'} eq 'driftfile') {
        $driftfile_val = $item->{'value'};
    }
}

print "Driftfile: $driftfile_val\n";
print "Servers: $server_count, Pools: $pool_count, Restricts: $restrict_count\n";

die "Driftfile parsing failed" if ($driftfile_val ne '/var/lib/ntpsec/ntp.drift');
die "Server parsing failed" if ($server_count != 1);
die "Pool parsing failed" if ($pool_count != 1);
die "Restrict parsing failed" if ($restrict_count != 3);

print "Parser test passed successfully!\n\n";

# Test saving and serialization
print "--- Testing Configuration Serializer ---\n";
# Add a new server
push(@$conf, {
    'type' => 'server',
    'address' => 'ntp.ubuntu.com',
    'options' => { 'iburst' => 1 },
    'comment' => 'added for testing'
});

my $save_ok = &save_ntp_config($conf);
die "Failed to save configuration" if (!$save_ok);

# Re-read and assert the new server is there
my $re_conf = &get_ntp_config($test_conf);
my $found_new = 0;
foreach my $item (@$re_conf) {
    if ($item->{'type'} eq 'server' && $item->{'address'} eq 'ntp.ubuntu.com') {
        $found_new = 1;
        die "Serializer failed to write option" if (!$item->{'options'}->{'iburst'});
        die "Serializer failed to write comment" if ($item->{'comment'} ne 'added for testing');
    }
}
die "Failed to find newly added server in re-parsed configuration" if (!$found_new);
print "Serializer test passed successfully!\n\n";

# Test peers parsing
print "--- Testing Peers Parser ---\n";
my $peers = &get_ntpq_peers();
print "Parsed " . scalar(@$peers) . " peers.\n";
die "Peers parsing count mismatch" if (scalar(@$peers) != 3);
die "System peer status flag mismatch" if ($peers->[0]->{'flag'} ne ' ');
die "System peer status flag mismatch 2" if ($peers->[1]->{'flag'} ne '*');
die "System peer remote mismatch" if ($peers->[1]->{'remote'} ne '99-28-14-242.li');

# Test get_peer_flag_html helper
my $star_html = &get_peer_flag_html('*');
die "get_peer_flag_html helper failed for '*' flag" if ($star_html !~ /System Peer/);
my $plus_html = &get_peer_flag_html('+');
die "get_peer_flag_html helper failed for '+' flag" if ($plus_html !~ /Candidate/);
my $space_html = &get_peer_flag_html(' ');
die "get_peer_flag_html helper failed for ' ' flag" if ($space_html ne '');
print "Peers parsing and flag formatting tests passed successfully!\n\n";

# Test NTS info parsing
print "--- Testing NTS Info Parser ---\n";
my $nts = &get_nts_info();
die "NTS info parsing failed" if (!defined($nts));
die "NTS client sends mismatch" if ($nts->{'NTS client sends'} != 10);
die "NTS client recvs good mismatch" if ($nts->{'NTS client recvs good'} != 8);
print "NTS Info parsing test passed successfully!\n\n";

# Clean up
unlink($test_conf);
unlink($mock_web_lib);
unlink($mock_core_lib);
unlink('mock_ntpq');
unlink('mock_ntpdig');
print "--- All Tests Passed Successfully! ---\n";
