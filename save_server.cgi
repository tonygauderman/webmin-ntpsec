#!/usr/bin/perl
# save_server.cgi
# Handles saving a new or edited server, pool or peer.

use WebminCore;
require './ntpsec-lib.pl';

&ReadParse();
&error_setup($text{'servers_err'});

# 1. Validation
my $address = $in{'address'};
$address =~ s/^\s+//;
$address =~ s/\s+$//;
if ($address eq '') {
    &error($text{'servers_eaddress'});
}

my $type = $in{'type'};
if ($type ne 'server' && $type ne 'pool' && $type ne 'peer') {
    &error("Invalid time source type");
}

my $minpoll = $in{'minpoll'};
if ($minpoll ne '') {
    if ($minpoll !~ /^\d+$/ || $minpoll < 3 || $minpoll > 17) {
        &error($text{'servers_eminpoll'});
    }
}

my $maxpoll = $in{'maxpoll'};
if ($maxpoll ne '') {
    if ($maxpoll !~ /^\d+$/ || $maxpoll < 3 || $maxpoll > 17) {
        &error($text{'servers_emaxpoll'});
    }
}

if ($minpoll ne '' && $maxpoll ne '' && $maxpoll < $minpoll) {
    &error($text{'servers_emaxpoll'});
}

# 2. Save
my $conf = &get_ntp_config();
my $item = {
    'type' => $type,
    'address' => $address,
    'comment' => $in{'comment'},
    'options' => {}
};

# Options
$item->{'options'}->{'nts'} = 1 if ($in{'nts'} && $type ne 'pool'); # pools do not support NTS
$item->{'options'}->{'iburst'} = 1 if ($in{'iburst'});
$item->{'options'}->{'prefer'} = 1 if ($in{'prefer'});
$item->{'options'}->{'minpoll'} = $minpoll if ($minpoll ne '');
$item->{'options'}->{'maxpoll'} = $maxpoll if ($maxpoll ne '');

if ($in{'idx'} eq 'new') {
    push(@$conf, $item);
} else {
    my $idx = $in{'idx'};
    # Retain structural variables of the original item if needed, but we replace the essential properties
    $conf->[$idx]->{'type'} = $item->{'type'};
    $conf->[$idx]->{'address'} = $item->{'address'};
    $conf->[$idx]->{'options'} = $item->{'options'};
    $conf->[$idx]->{'comment'} = $item->{'comment'};
}

&lock_file($config{'ntp_conf'});
my $ok = &save_ntp_config($conf);
&unlock_file($config{'ntp_conf'});

if (!$ok) {
    &error("Failed to write to configuration file");
}

# Webmin standard: restart service after changes to make them active (optional but good practice)
# We won't restart automatically here, or maybe we can? Usually Webmin has an "Apply Changes" button on index.
# But for now, returning to list is standard.
&redirect("edit_servers.cgi");
