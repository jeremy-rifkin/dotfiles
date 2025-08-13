#!/usr/bin/env python3

import sys

STEGOSAURUS = (
    "\\                             .       .\n"
    " \\                           / `.   .' \" \n"
    "  \\                  .---.  <    > <    >  .---.\n"
    "   \\                 |    \\  \\ - ~ ~ - /  /    |\n"
    "         _____          ..-~             ~-..-~\n"
    "        |     |   \\~~~\\.'                    `./~~~/\n"
    "       ---------   \\__/                        \\__/\n"
    "      .'  O    \\     /               /       \\  \" \n"
    "     (_____,    `._.'               |         }}  \\/~~~/\n"
    "      `----.          /       }}     |        /    \\__/\n"
    "            `-.      |       /      |       /      `. ,~~|\n"
    "                ~-.__|      /_ - ~ ^|      /- _      `..-'   \n"
    "                     |     /        |     /     ~-.     `-. _  _  _\n"
    "                     |_____|        |_____|         ~ - . _ _ _ _ _>\n"
)

def bubble(message: str) -> str:
    lines = message.splitlines() or [""]
    width = max(len(line) for line in lines)
    top = f" {'_' * (width + 2)} \n"
    bottom = f" {'-' * (width + 2)} \n"
    if len(lines) == 1:
        middle = f"< {lines[0].ljust(width)} >\n"
    else:
        middle = f"/ {lines[0].ljust(width)} \\\n"
        for line in lines[1:-1]:
            middle += f"| {line.ljust(width)} |\n"
        middle += f"\\ {lines[-1].ljust(width)} /\n"
    return top + middle + bottom

def main():
    msg = sys.argv[1]
    print(bubble(msg) + STEGOSAURUS)

if __name__ == "__main__":
    main()
