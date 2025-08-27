#!/bin/sh

inputfile=`echo $1 | cut -f1 -d"."`
outputfile=$inputfile"_signed.pdf"

python3 stamp_pdf.py $1 $outputfile --initials ./initials.png
