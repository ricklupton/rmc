# rmc

Command line tool for converting to/from remarkable `.rm` version 6 (software version 3) files.

``` shellsession
$ rmc -t txt file.rm
$ rmc -t svg -o file.svg file.rm
$ rmc file.rm -o file.pdf
```

Or create a `.rm` file with specified text:

``` shellsession
$ rmc -t rm text.md -o text.rm
```

## SVG/PDF Conversion Status

Right now the converter works well while there are no text boxes. If you add text boxes, there are x issues:

1. if the text box contains multiple lines, the lines are actually printed in the same line, and
2. the position of the strokes gets corrupted.

# Acknowledgements

`rmc` uses [rmscene](https://github.com/ricklupton/rmscene) to read the `.rm` files, for which https://github.com/ddvk/reader helped a lot in figuring out the structure and meaning of the files.

[@chemag](https://github.com/chemag) added initial support for converting to svg and pdf.
