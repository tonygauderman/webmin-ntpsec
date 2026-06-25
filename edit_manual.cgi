#!/usr/bin/perl
# edit_manual.cgi
# Form to edit the configuration file manually.

use WebminCore;
require './ntpsec-lib.pl';

&ui_print_header(undef, $text{'manual_title'}, "");

my $file = $config{'ntp_conf'} || '/etc/ntpsec/ntp.conf';
my $data = "";
if (-r $file) {
    if (open(my $fh, "<", $file)) {
        local $/;
        $data = <$fh>;
        close($fh);
    }
}

print "<div>$text{'manual_desc'}</div><br>\n";

print &ui_form_start("save_manual.cgi", "post");
print &ui_textarea("data", $data, 24, 85, "wrap=off style='font-family:monospace;width:100%;'");
print "<br><br>\n";
print &ui_form_end([ [ undef, $text{'save'} ] ]);

&ui_print_footer("", $text{'index_title'});
