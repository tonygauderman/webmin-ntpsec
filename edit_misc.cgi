#!/usr/bin/perl
# edit_misc.cgi
# Form to edit miscellaneous drift, log, stats, tinker panic, and NTS server settings.

use WebminCore;
require './ntpsec-lib.pl';

&ui_print_header(undef, $text{'misc_title'}, "");

my $conf = &get_ntp_config();
my ($driftfile, $logfile, $statsdir, $statistics, $tinker_panic, $nts_cert, $nts_key, $nts_enable);

foreach my $item (@$conf) {
    if ($item->{'type'} eq 'driftfile') {
        $driftfile = $item->{'value'};
    } elsif ($item->{'type'} eq 'logfile') {
        $logfile = $item->{'value'};
    } elsif ($item->{'type'} eq 'statsdir') {
        $statsdir = $item->{'value'};
    } elsif ($item->{'type'} eq 'statistics') {
        $statistics = $item->{'value'};
    } elsif ($item->{'type'} eq 'tinker_panic') {
        $tinker_panic = $item->{'value'};
    } elsif ($item->{'type'} eq 'nts_cert') {
        $nts_cert = $item->{'value'};
    } elsif ($item->{'type'} eq 'nts_key') {
        $nts_key = $item->{'value'};
    } elsif ($item->{'type'} eq 'nts_enable') {
        $nts_enable = 1;
    }
}

print &ui_form_start("save_misc.cgi", "post");
print &ui_table_start($text{'misc_header'}, "width=100%", 2);

# Driftfile
print &ui_table_row($text{'misc_drift'},
    &ui_textbox("driftfile", $driftfile, 50)
);

# Logfile
print &ui_table_row($text{'misc_log'},
    &ui_textbox("logfile", $logfile, 50)
);

# Statsdir
print &ui_table_row($text{'misc_stats'},
    &ui_textbox("statsdir", $statsdir, 50)
);

# Statistics checkboxes
my %has_stat;
if ($statistics) {
    $has_stat{$_} = 1 for (split(/\s+/, $statistics));
}
my $stats_html = &ui_checkbox("stats", "loopstats", $text{'misc_stat_loop'}, $has_stat{'loopstats'}) . " &nbsp;&nbsp; " .
                 &ui_checkbox("stats", "peerstats", $text{'misc_stat_peer'}, $has_stat{'peerstats'}) . " &nbsp;&nbsp; " .
                 &ui_checkbox("stats", "clockstats", $text{'misc_stat_clock'}, $has_stat{'clockstats'});
print &ui_table_row($text{'misc_statistics'}, $stats_html);

# Tinker panic threshold
print &ui_table_row($text{'misc_tinker'},
    &ui_textbox("tinker", $tinker_panic, 10) . " <span style='color:#666;'>$text{'misc_tinker_desc'}</span>"
);

print &ui_table_end();

# NTS Server settings section
print &ui_table_start($text{'misc_nts_header'}, "width=100%", 2);

# NTS certificate
print &ui_table_row($text{'misc_nts_cert'},
    &ui_textbox("nts_cert", $nts_cert, 50)
);

# NTS private key
print &ui_table_row($text{'misc_nts_key'},
    &ui_textbox("nts_key", $nts_key, 50)
);

# NTS server mode enable
print &ui_table_row($text{'misc_nts_enable'},
    &ui_yesno_radio("nts_enable", $nts_enable || 0)
);

print &ui_table_end();

print &ui_form_end([ [ undef, $text{'save'} ] ]);

&ui_print_footer("", $text{'index_title'});
