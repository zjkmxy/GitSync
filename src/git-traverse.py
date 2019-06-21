#!/usr/bin/env python3

import os
import zlib
import hashlib
import sys


def path_from_hash(hash_name):
    return os.path.join(".git/objects", hash_name[:2], hash_name[2:])


def traverse(hash_name: str, expect_type: str = ""):
    print("GO>>", hash_name, expect_type)
    with open(path_from_hash(hash_name), "rb") as f:
        data = f.read()
        # decompress + header
        data = zlib.decompress(data)
        header_size = data.find(b'\x00')
        header = data[:header_size]
        content = data[header_size + 1:]
        content_type, content_len = header.decode("utf-8").split(' ')
        content_len = int(content_len)
        # length
        assert (content_len == len(content))
        # type
        if expect_type != "":
            assert (content_type == expect_type)
        # hash
        sha1 = hashlib.sha1()
        sha1.update(data)
        assert (bytes.fromhex(hash_name) == sha1.digest())
        # recursive
        if content_type == "commit":
            traverse_commit(content)
        elif content_type == "tree":
            traverse_tree(content)
        else:
            assert (content_type == "blob")


def traverse_commit(content: bytes):
    lines = content.decode("utf-8").split("\n")
    for ln in lines:
        if not ln.startswith("tree") and not ln.startswith("parent"):
            break
        expect_type, hash_name = ln.split(" ")
        if expect_type == "parent":
            expect_type = "commit"
        traverse(hash_name, expect_type)


def traverse_tree(content: bytes):
    size = len(content)
    pos = 0
    while pos < size:
        name_start = content.find(b'\x00', pos)
        hash_name = content[name_start+1:name_start+21]
        if content[pos] == 49:
            expect_type = "blob"
        else:
            expect_type = "tree"
        traverse(hash_name.hex(), expect_type)
        pos = name_start + 21


def main():
    if len(sys.argv) < 2:
        print("Usage:", sys.argv[0], "<hash-name>")
    else:
        traverse(sys.argv[1])


if __name__ == "__main__":
    main()
