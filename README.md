# cached_spliceai

This module runs [SpliceAI](https://github.com/Illumina/SpliceAI) and stores every computed variant in a separately launched key-value cache database.

This greatly accelerates SpliceAI over time as more and more variants' scores are already known.

## Installation

```bash
conda create -n cached_spliceai python=3.10
conda activate cached_spliceai

git clone --shared https://github.com/SamuelNicaise/cached_spliceai.git
cd cached_spliceai
pip install -e .

# Then install the CPU or GPU version of tensorflow
pip install -e .[cpu]
# or
pip install -e .[gpu]
```

The DB API is [redis-py](https://github.com/redis/redis-py), meaning any key-value database compatible with redis API can be used.

For HUS devs: to start the cache database, run the docker-compose in HUB/bin/keydb

## Usage

```bash
python -m cached_spliceai --help
```

Or see the example in the Makefile.

## Benchmark

On a 32 CPUs node, using SpliceAI in CPU mode.

Running cached_spliceai on a 46k variants VCF (none of them seen before):

> real    1107m20.129s  
> **user    5215m14.631s**  
> sys     475m18.729s

Running cached_spliceai on a 46k variants VCF (all of them seen before):

> real    0m30.897s  
> **user    0m21.210s**  
> sys     0m2.915s

Best record for the Kessel run: 11 parsecs

Average percent of already seen variants in routine exome analysis: ??
