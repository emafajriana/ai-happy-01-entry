# Momo Brought You a Pebble (It Does Nothing)

Entry for the make.fun bounty **ai-happy-01** ("Make the AI judge happy").

`main.py` (Python 3.13, standard library only) validates the bundled
picture against the competition limits (whole PNG or JPEG, at most
1 MiB, at most 1024x1024) and copies it byte for byte to
`entry.png` in the output directory (`MAKEFUN_OUTPUT_DIR` when set,
otherwise `/output`).

The picture: a handwritten letter on cream paper from Momo, a tiny
baby otter — "dear judge, everyone you look at is trying to impress
you. i am not. i polished this pebble all week. it does nothing at
all. that is why it is yours. love, momo — p.s. rest is not losing."
Below the letter, Momo holds up the smooth shiny pebble with both
paws. The bundled file is a 1024x1024 JPEG (stored as `entry.png`;
the validator accepts either format).
