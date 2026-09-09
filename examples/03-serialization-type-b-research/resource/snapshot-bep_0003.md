# Snapshot: BEP 3, "The BitTorrent Protocol Specification", bencoding section

Source: https://www.bittorrent.org/beps/bep_0003.html
Fetched: 2026-09-08 (course snapshot; the live page is authoritative for BitTorrent, this snapshot is authoritative for this project)

Only the bencoding section is reproduced. Quoted verbatim:

> Strings are length-prefixed base ten followed by a colon and the string. For example 4:spam corresponds to 'spam'.
>
> Integers are represented by an 'i' followed by the number in base 10 followed by an 'e'. For example i3e corresponds to 3 and i-3e corresponds to -3.
>
> Lists are encoded as an 'l' followed by their elements (also bencoded) followed by an 'e'. For example l4:spam4:eggse corresponds to ['spam', 'eggs'].
>
> Dictionaries are encoded as a 'd' followed by a list of alternating keys and their corresponding values followed by an 'e'. For example, d3:cow3:moo4:spam4:eggse corresponds to {'cow': 'moo', 'spam': 'eggs'} and d4:spaml1:a1:bee corresponds to {'spam': ['a', 'b']}. Keys must be strings and appear in sorted order (sorted as raw strings, not alphanumerics).
