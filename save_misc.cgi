#!/usr/bin/perl
# save_misc.cgi
# Saves miscellaneous NTPsec configuration parameters.

use WebminCore;
require './ntpsec-lib.pl';

&ReadParse();
&error_setup($text{'misc_err'});

# 1. Validation
my $tinker = $in{'tinker'};
$tinker =~ s/^\s+//;
$tinker =~ s/\s+$//;
if ($tinker ne '') {
    if ($tinker !~ /^\d+$/) {
        &error($text{'misc_etinker'});
    }
}

my $conf = &get_ntp_config();

# In-place editor helper
sub set_or_add_value {
    my ($c, $type, $val, $comment) = @_;
    my $found = 0;
    foreach my $item (@$c) {
        if ($item->{'type'} eq $type) {
            if (defined($val) && $val ne '') {
                $item->{'value'} = $val;
                $item->{'type'} = $type; # Restore from empty if it was cleared
            } else {
                $item->{'type'} = 'empty';
                $item->{'value'} = '';
            }
            $found = 1;
            last;
        }
    }
    if (!$found && defined($val) && $val ne '') {
        push(@$c, {
            'type' => $type,
            'value' => $val,
            'comment' => $comment
        });
    }
}

# 2. Update values
&set_or_add_value($conf, 'driftfile', $in{'driftfile'});
&set_or_add_value($conf, 'logfile', $in{'logfile'});
&set_or_add_value($conf, 'statsdir', $in{'statsdir'});

my @stats_sel = split(/\0/, $in{'stats'});
my $stats_val = join(" ", @stats_sel);
&set_or_add_value($conf, 'statistics', $stats_val);

&set_or_add_value($conf, 'tinker_panic', $tinker);

&set_or_add_value($conf, 'nts_cert', $in{'nts_cert'});
&set_or_add_value($conf, 'nts_key', $in{'nts_key'});

my $nts_enable_val = $in{'nts_enable'} ? 1 : undef;
&set_or_add_value($conf, 'nts_enable', $nts_enable_val);

&lock_file($config{'ntp_conf'});
my $ok = &save_ntp_config($conf);
&unlock_file($config{'ntp_conf'});

if (!$ok) {
    &error("Failed to write to configuration file");
}

&redirect("");
