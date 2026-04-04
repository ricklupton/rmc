# rmc

Command line tool for converting to/from remarkable `.rm` version 6 (software version 3) files.

## Installation

To install in your current Python environment:

    pip install rmc
    
Or use [pipx](https://pypa.github.io/pipx/) to install in an isolated environment (recommended):

    pipx install rmc

## Usage

Convert a remarkable v6 file to other formats, specified by `-t FORMAT`:

    $ rmc -t markdown file.rm
    Text in the file is printed to standard output.

Specify the filename to write the output to with `-o`:

    $ rmc -t svg -o file.svg file.rm
    
The format is guessed based on the filename if not specified:
    
    $ rmc file.rm -o file.pdf

Create a `.rm` file containing the text in `text.md`:

    $ rmc -t rm text.md -o text.rm
    
## SVG/PDF Conversion Status

Right now the converter works well while there are no text boxes. If you add text boxes, there are x issues:

1. if the text box contains multiple lines, the lines are actually printed in the same line, and
2. the position of the strokes gets corrupted.

## Setting Up Development Environment - Quickstart
To enable debugging and code execution in your cloned repository, you can set up manually your environment following these steps:

1. Install scoop command line interface, [refer to the Quickstart section](https://scoop.sh/).
2. Install pipx using scoop:
   ```
   scoop install pipx
   ```
3. Install poetry for create your python virtual environment:
   ```
   pipx install poetry
   ```
4. Add poetry to your PATH environment variable.
5. Install dependencies for your poetry environment
   ```
   poetry install
   ```

It is also suggested to check if your IDE has an easier way of setting up a poetry environment with a few clicks - avoid user errors.
## _InkML Addition - Excustic_
This fork introduces the possibility of converting `.rm` files to OneNote compatible files.
To use this functionality insert the following command in your editor's configuration:
* module: `rmc.cli`
* Script parameters: `-t inkml ./tests/rm/<INPUT_FILE>.rm -o ./tests/out/<GENERATED_FILES_NAME>`

Alternatively, here's an example using a terminal (assuming it is opened from the project's root dir):
```
cd src/rmc/
python -m rmc.cli -t inkml <FULL_PATH_TO_PROJECT>\tests\rm\<INPUT_FILE>.rm -o <FULL_PATH_TO_PROJECT>\tests\rm\test_rmpp
```

Note that the output name should be without extensions as the converter outputs two different files:
* XML - Contains all the ink data extracted from the `.rm` file, retaining full quality.
* HTML (Optional) - Extracts all the text data extracted from the `.rm` file.

### How to test with OneNote
Using cURL or any other tool for API interaction (e.g. Postman) you can send a POST page request which will create a new page identical (mostly) to the .rm version.
See the example below:
```
curl --location 'https://graph.microsoft.com/v1.0/users/<USER_REGISTERED_MAIL>/onenote/sections/<SECTION_URL>/pages' \
--header 'Content-Disposition: form-data; name=presentation-onenote-inkml' \
--header 'Authorization: Bearer <GRAPH_API_TOKEN>' \
--form 'presentation-onenote-inkml=@"<GENERATED_XML_FILEPATH>"' \
--form 'presentation=@"<GENERATED_HTML_FILE>"'
```
To attain all of the API relevant data - see [Microsoft's GraphAPI Console](https://developer.microsoft.com/en-us/graph/graph-explorer)

# Acknowledgements

`rmc` uses [rmscene](https://github.com/ricklupton/rmscene) to read the `.rm` files, for which https://github.com/ddvk/reader helped a lot in figuring out the structure and meaning of the files.

[@chemag](https://github.com/chemag) added initial support for converting to svg and pdf.

[@Seb-sti1](https://github.com/Seb-sti1) made lots of improvements to svg export and updating to newer `rmscene` versions.

[@ChenghaoMou](https://github.com/ChenghaoMou) added support for new pen types/colours.

[@EelcovanVeldhuizen](https://github.com/EelcovanVeldhuizen) for code updates/fixes.

[@p4xel](https://github.com/p4xel) for code fixes.
