#!/usr/bin/env python3

"""Script for operating on reMarkable tablet ".rm" files."""

import argparse
import datetime
import glob
import json
import subprocess
import sys
import tempfile
import os
import os.path


ENUM_COMMANDS = ["list", "convert", "convert-all"]

default_values = {
    "debug": 0,
    "regenerate": False,
    "rootdir": None,
    "outdir": None,
    "width": 1404,
    "height": 1872,
    "command": None,
    "infile": None,
    "outfile": None,
}


def read_metadata(rootdir, uuid):
    metadata_file = os.path.join(rootdir, uuid + ".metadata")
    with open(metadata_file, "r") as f:
        json_text = f.read()
    return json.loads(json_text)


def read_content(rootdir, uuid):
    content_file = os.path.join(rootdir, uuid + ".content")
    with open(content_file, "r") as f:
        json_text = f.read()
    return json.loads(json_text)


def read_pagedata(rootdir, uuid):
    pagedata_file = os.path.join(rootdir, uuid + ".pagedata")
    with open(pagedata_file, "r") as f:
        text = f.read()
    return text.split()


class Node:
    def __init__(self, uuid, metadata):
        self.uuid = uuid
        self.metadata = metadata
        self.children = []
        self.next = None

    def __str__(self):
        s = 'uuid: "%s"' % self.uuid
        s += " metadata: %r" % self.metadata
        s += " children: %r" % self.children
        s += " next: %r" % self.next
        return s


# parses the (raw) root directory
def get_repo_info(rootdir, debug):
    # create an unordered node list
    node_list = []
    metadata_list = glob.glob(os.path.join(rootdir, "*.metadata"))
    for metadata_file in metadata_list:
        uuid, _ = os.path.basename(metadata_file).split(".")
        metadata = read_metadata(rootdir, uuid)
        node_list.append([uuid, metadata])

    # add the node list into a tree
    rootnode = Node("", None)
    cur_uuid_list = [rootnode.uuid]
    cur_node = [rootnode]
    prev_node = None
    while node_list:
        new_cur_uuid_list = []
        new_cur_node = []
        new_node_list = []
        for uuid, metadata in node_list:
            if metadata["parent"] == "trash":
                # ignore it
                pass
            elif metadata["parent"] in cur_uuid_list:
                # found the parent
                index = cur_uuid_list.index(metadata["parent"])
                node = Node(uuid, metadata)
                cur_node[index].children.append(node)
                new_cur_uuid_list.append(uuid)
                new_cur_node.append(node)
                if prev_node is not None:
                    prev_node.next = node
                prev_node = node
            else:
                # keep looking
                new_node_list.append([uuid, metadata])
        # reset status
        cur_uuid_list = new_cur_uuid_list
        cur_node = new_cur_node
        node_list = new_node_list

    # sort nodes alphabetically (visibleName)
    # using bubble-sort as sizes should be small
    # TODO(chemag): use some interview-acceptable sort here
    def do_bubble_sort(node):
        for indexl in range(len(node.children)):
            for indexr in range(indexl + 1, len(node.children)):
                vall = node.children[indexl].metadata["visibleName"]
                valr = node.children[indexr].metadata["visibleName"]
                if vall > valr:
                    # swap nodes
                    tmp = node.children[indexl]
                    node.children[indexl] = node.children[indexr]
                    node.children[indexr] = tmp
        # fix next pointers
        for index in range(len(node.children) - 1):
            node.children[index].next = node.children[index + 1]
        if len(node.children) > 0:
            node.children[len(node.children) - 1].next = None

    def node_sort(node):
        # start with the node itself
        do_bubble_sort(node)
        for node in node.children:
            node_sort(node)

    node_sort(rootnode)
    return rootnode


def list_repo(rootdir, debug):
    rootnode = get_repo_info(rootdir, debug)

    # dump lines
    def print_node(node, tab):
        if node.uuid == "":
            # do not print the root node
            pass
        else:
            uuid = node.uuid
            unix_ts = int(node.metadata["lastModified"])
            unix_dt = datetime.datetime.fromtimestamp(unix_ts / 1000)
            unix_str = unix_dt.strftime("%Y%m%d-%H:%M:%S.%f")
            visible_name = node.metadata["visibleName"]
            print("%s %s %s %s" % ("  " * tab, uuid, unix_str, visible_name))
        for node in node.children:
            print_node(node, tab + 1)

    tab = 0
    print_node(rootnode, tab)


def run(command, dry_run, **kwargs):
    env = kwargs.get("env", None)
    stdin = subprocess.PIPE if kwargs.get("stdin", False) else None
    bufsize = kwargs.get("bufsize", 0)
    universal_newlines = kwargs.get("universal_newlines", False)
    default_close_fds = True if sys.platform == "linux2" else False
    close_fds = kwargs.get("close_fds", default_close_fds)
    shell = type(command) in (type(""), type(""))
    if dry_run:
        return 0, b"stdout", b"stderr"
    p = subprocess.Popen(
        command,
        stdin=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=bufsize,
        universal_newlines=universal_newlines,
        env=env,
        close_fds=close_fds,
        shell=shell,
    )
    # wait for the command to terminate
    if stdin is not None:
        out, err = p.communicate(stdin)
    else:
        out, err = p.communicate()
    returncode = p.returncode
    # clean up
    del p
    # return results
    return returncode, out, err


HEADER_STRING = b"reMarkable .lines file, version="


def get_version(pagerm):
    with open(pagerm, "rb") as ifd:
        header = ifd.read(len(HEADER_STRING))
        if header != HEADER_STRING:
            raise ValueError("Invalid .rm header: %r" % header)
        chars = ifd.read(11)
        return int(chars)


def convert_file(infile, outfile, rootdir, width, height, debug):
    if debug > 0:
        debug_str = "-d " * debug
        print(
            f"$ {__file__} convert {debug_str}--root {rootdir} --width {width} --height {width} {infile} {outfile}"
        )
    # get uuid
    uuid = os.path.basename(infile).split(".")[0]
    if not rootdir:
        rootdir = os.path.dirname(infile)
    # get file info
    # metadata = read_metadata(rootdir, uuid)
    content = read_content(rootdir, uuid)
    # pagedata = read_pagedata(rootdir, uuid)
    # create tempdir
    tmpdir = tempfile.mkdtemp(prefix="rmtool.tmp.", dir="/tmp")
    # convert pages to pdf
    pagepdf_list = []
    invalid_rm_version = False

    # get page list
    if content["formatVersion"] == 1:
        page_uuid_list = content["pages"]
    elif content["formatVersion"] == 2:
        page_uuid_list = [
            page["id"] for page in content["cPages"]["pages"] if "deleted" not in page
        ]

    for page_uuid in page_uuid_list:
        # ensure the file exists
        pagerm = os.path.join(rootdir, uuid, page_uuid + ".rm")
        assert os.path.exists(pagerm), f"error: non-existent file: {pagerm}"
        # check the rm version
        rm_version = get_version(pagerm)
        if rm_version < 6:
            if debug > 0:
                print(f"warn: input {pagerm} has version {rm_version}")
            invalid_rm_version = True
            continue
        # convert to svg
        # pagesvg = os.path.join(tmpdir, page_uuid + '.svg')
        # colored_annotations = True
        # rm2svg.rm2svg(pagerm, pagesvg, colored_annotations, width, height)
        # convert to pdf
        pagepdf = os.path.join(tmpdir, page_uuid + ".pdf")
        command = f"rmc {pagerm} -o {pagepdf}"
        returncode, out, err = run(command, False)
        assert returncode == 0, f"command failed: {command}\n{err}\n{page_uuid_list}"
        pagepdf_list.append(pagepdf)
    # check no invalid rm pages
    if invalid_rm_version:
        dirpath = os.path.join(rootdir, uuid)
        if debug > 0:
            print(f"warn: input {dirpath} has unsupported version(s)")
        return
    # put all the pages together
    command = 'pdfunite %s "%s"' % (" ".join(pagepdf_list), outfile)
    returncode, out, err = run(command, False)
    assert returncode == 0, f"command failed: {command}\n{err}"


def convert_all(rootdir, outdir, width, height, regenerate, debug):
    rootnode = get_repo_info(rootdir, debug)

    # traverse the tree
    def traverse_node(node, rootdir, outdir, width, height, regenerate, debug):
        if node.uuid == "":
            # ignore the root node
            pass
        else:
            uuid = node.uuid
            unix_ts_ms = int(node.metadata["lastModified"])
            unix_ts = unix_ts_ms / 1000
            visible_name = node.metadata["visibleName"]
            visible_name = visible_name.replace(" ", "_")
            t = node.metadata["type"]
            if t == "CollectionType":
                # folder: make sure the directory exists
                outdir = os.path.join(outdir, visible_name)
                if not os.path.exists(outdir):
                    os.mkdir(outdir, mode=0o755)
            elif t == "DocumentType":
                # file: convert the file into a pdf
                # check whether the file already exists (with right timestamp)
                infile = os.path.join(rootdir, uuid)
                outfile = os.path.join(outdir, visible_name + ".pdf")
                do_convert = True
                # check whether the final file already exists
                if regenerate:
                    do_convert = True
                elif os.path.exists(outfile) and not regenerate:
                    if debug > 0:
                        print(f"info: output {outfile} already exists")
                    # output file already exists: check mtime
                    file_mtime = os.stat(outfile).st_mtime
                    if file_mtime > unix_ts:
                        # output file exists and is younger
                        do_convert = False
                if do_convert:
                    if debug > 0:
                        print("..converting %s -> %s" % (infile, outfile))
                    try:
                        convert_file(infile, outfile, rootdir, width, height, debug)
                    except Exception as e:
                        print(f"\n-- error: cannot convert {infile} -> {outfile}\n{e}")

        for node in node.children:
            traverse_node(node, rootdir, outdir, width, height, regenerate, debug)

    traverse_node(rootnode, rootdir, outdir, width, height, regenerate, debug)


def get_options(argv):
    """Generic option parser.

    Args:
        argv: list containing arguments

    Returns:
        Namespace - An argparse.ArgumentParser-generated option object
    """
    # init parser
    # usage = 'usage: %prog [options] arg1 arg2'
    # parser = argparse.OptionParser(usage=usage)
    # parser.print_help() to get argparse.usage (large help)
    # parser.print_usage() to get argparse.usage (just usage line)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-d",
        "--debug",
        action="count",
        dest="debug",
        default=default_values["debug"],
        help="Increase verbosity (use multiple times for more)",
    )
    parser.add_argument(
        "--quiet",
        action="store_const",
        dest="debug",
        const=-1,
        help="Zero verbosity",
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        dest="regenerate",
        default=default_values["regenerate"],
        help="Dry run",
    )
    parser.add_argument(
        "--no-regenerate",
        action="store_false",
        dest="regenerate",
        help="Do not regenerate",
    )
    parser.add_argument(
        "-r",
        "--root",
        action="store",
        type=str,
        dest="rootdir",
        default=default_values["rootdir"],
        metavar="ROOT",
        help="use ROOT as root directory (xochitl)",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        action="store",
        type=str,
        dest="outdir",
        default=default_values["outdir"],
        metavar="OUTDIR",
        help="use OUTDIR as outdir directory",
    )
    parser.add_argument(
        "--width",
        action="store",
        type=int,
        dest="width",
        default=default_values["width"],
        metavar="WIDTH",
        help=("use WIDTH width (default: %i)" % default_values["width"]),
    )
    parser.add_argument(
        "--height",
        action="store",
        type=int,
        dest="height",
        default=default_values["height"],
        metavar="HEIGHT",
        help=("HEIGHT height (default: %i)" % default_values["height"]),
    )
    # add command
    parser.add_argument(
        "command",
        action="store",
        type=str,
        default=default_values["command"],
        choices=ENUM_COMMANDS,
        metavar="[%s]"
        % (
            " | ".join(
                ENUM_COMMANDS,
            )
        ),
        help="command",
    )
    # add i/o
    parser.add_argument(
        "infile",
        type=str,
        nargs="?",
        default=default_values["infile"],
        metavar="input-file",
        help="input file",
    )
    parser.add_argument(
        "outfile",
        type=str,
        nargs="?",
        default=default_values["outfile"],
        metavar="output-file",
        help="output file",
    )
    # do the parsing
    options = parser.parse_args(argv[1:])
    return options


def main(argv):
    # parse options
    options = get_options(argv)
    # print results
    if options.debug > 0:
        print(options)
    # need a valid infile or root directory

    # do something
    if options.command == "list":
        list_repo(options.rootdir, options.debug)
    elif options.command == "convert":
        convert_file(
            options.infile,
            options.outfile,
            options.rootdir,
            options.width,
            options.height,
            options.debug,
        )
    elif options.command == "convert-all":
        convert_all(
            options.rootdir,
            options.outdir,
            options.width,
            options.height,
            options.regenerate,
            options.debug,
        )


if __name__ == "__main__":
    # at least the CLI program name: (CLI) execution
    main(sys.argv)
