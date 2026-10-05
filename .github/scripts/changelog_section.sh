#!/bin/sh
# Print the body of one version's section of CHANGELOG.md, without its
# "## [x.y.z]" heading, for use as release notes. Exits non-zero when the
# section is missing or empty, so a release cannot ship without an entry.
#
# usage: changelog_section.sh VERSION [CHANGELOG.md]
set -eu

version=${1:?usage: changelog_section.sh VERSION [CHANGELOG.md]}
changelog=${2:-CHANGELOG.md}

# A section runs from its heading to the next "## [" heading, or to the link
# reference definitions at the bottom of the file. Leading and trailing blank
# lines are dropped.
#
# The second pass unwraps the file's 80-column hard wrapping: GitHub renders a
# single newline in a release body as a line break, so a wrapped paragraph
# would come out ragged. A line that starts a block (list item, heading, table
# row, quote) or follows a blank line starts a new output line; anything else
# is joined onto the previous one. Fenced code is passed through untouched.
body=$(awk -v heading="## [${version}]" '
    /^## \[/              { if (found) exit; if (index($0, heading) == 1) { found = 1; next } }
    /^\[[^]]+\]: /        { if (found) exit }
    found                 { print }
' "${changelog}" | sed '/./,$!d' | awk '
    /^```/                { if (open) print line; print; line = ""; open = 0; fence = !fence; next }
    fence                 { print; next }
    /^[ \t]*$/            { if (open) print line; print ""; line = ""; open = 0; next }
    open && !/^[ \t]*([-*] |#|[|>]|[0-9]+\. )/ {
                            sub(/^[ \t]+/, ""); line = line " " $0; next }
                          { if (open) print line; line = $0; open = 1 }
    END                   { if (open) print line }
')

if [ -z "${body}" ]; then
    echo "changelog_section: no \"## [${version}]\" section with content in ${changelog}" >&2
    exit 1
fi

printf '%s\n' "${body}"
