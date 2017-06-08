#!/bin/bash
for f in capt_multi*.jpg; do
    echo $f
    convert -resize 2000x1333 $f resize_$f
done
