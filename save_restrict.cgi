#!/usr/bin/perl
# save_restrict.cgi
# Handles saving a new or edited access control rule.

use WebminCore;
require './ntpsec-lib.pl';

&ReadParse();
&error_setup($text{'restrict_err'});

# 1. Validation
my $address;
if ($in{'addr_mode'} eq 'default') {
    $address = 'default';
} else {
    $address = $in{'address'};
    $address =~ s/^\s+//;
    $address =~ s/\s+$//;
    if ($address eq '') {
        &error($text{'restrict_eaddress'});
    }
}

my $mask = $in{'mask'};
$mask =~ s/^\s+//;
$mask =~ s/\s+$//;
if ($mask ne '') {
    if ($mask !~ /^[0-9a-fA-F\.\:]+$/) {
        &error($text{'restrict_emask'});
    }
}

my @flags = split(/\0/, $in{'flags'});

# 2. Save
my $conf = &get_ntp_config();
my $item = {
    'type' => 'restrict',
    'address' => $address,
    'mask' => ($mask ne '' ? $mask : undef),
    'flags' => \@flags,
    'comment' => $in{'comment'}
};

if ($in{'idx'} eq 'new') {
    push(@$conf, $item);
} else {
    my $idx = $in{'idx'};
    $conf->[$idx]->{'type'} = $item->{'type'};
    $conf->[$idx]->{'address'} = $item->{'address'};
    $conf->[$idx]->{'mask'} = $item->{'mask'};
    $conf->[$idx]->{'flags'} = $item->{'flags'};
    $conf->[$idx]->{'comment'} = $item->{'comment'};
}

&lock_file($config{'ntp_conf'});
my $ok = &save_ntp_config($conf);
&unlock_file($config{'ntp_conf'});

if (!$ok) {
    &error("Failed to write to configuration file");
}

&redirect("edit_restrict.cgi");
