"""
@Goal: Greatly accelerate SpliceAI when encountering already annotated variants
@Author: Samuel Nicaise
@Date: December 2024
"""

import argparse
import logging as log
import sys

try:
    from sys.stdin import buffer as std_in
    from sys.stdout import buffer as std_out
except ImportError:
    from sys import stdin as std_in
    from sys import stdout as std_out

import pysam
from spliceai.utils import Annotator, get_delta_scores

import cached_spliceai
from cached_spliceai.commons import set_log_level
from cached_spliceai.cache import CacheDB, get_db_key


def get_options() -> argparse.Namespace:

    parser = argparse.ArgumentParser(description="Version: 1.3.1")
    parser.add_argument(
        "-I",
        metavar="input",
        nargs="?",
        default=std_in,
        help="path to the input VCF file, defaults to standard in",
    )
    parser.add_argument(
        "-O",
        metavar="output",
        nargs="?",
        default=std_out,
        help="path to the output VCF file, defaults to standard out",
    )
    parser.add_argument(
        "-R",
        metavar="reference",
        required=True,
        help="path to the reference genome fasta file",
    )
    parser.add_argument(
        "-A",
        metavar="annotation",
        required=True,
        help='"grch37" (GENCODE V24lift37 canonical annotation file in '
        'package), "grch38" (GENCODE V24 canonical annotation file in '
        "package), or path to a similar custom gene annotation file",
    )
    parser.add_argument(
        "-D",
        metavar="distance",
        nargs="?",
        default=50,
        type=int,
        choices=range(0, 5000),
        help="maximum distance between the variant and gained/lost splice "
        "site, defaults to 50",
    )
    parser.add_argument(
        "-M",
        metavar="mask",
        nargs="?",
        default=0,
        type=int,
        choices=[0, 1],
        help="mask scores representing annotated acceptor/donor gain and "
        "unannotated acceptor/donor loss, defaults to 0",
    )

    parser.add_argument(
        "-V",
        "--verbosity",
        type=str,
        default="info",
        help="verbosity level, defaults to info",
    )
    parser.add_argument(
        "-H",
        "--cache_host",
        type=str,
        required=True,
        help="cache DB host",
    )
    parser.add_argument(
        "-P",
        "--cache_port",
        type=str,
        required=True,
        help="cache DB port",
    )
    parser.add_argument(
        "-N",
        "--cache_number",
        type=int,
        default=0,
        help="cache DB number (see redis documentation), defaults to 0",
    )
    parser.add_argument(
        "-S",
        "--cache_password_file",
        type=str,
        default="",
        help="secret file containing cache DB's connection password, defaults to empty",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{parser.prog} {cached_spliceai.__version__}",
        help="show cached_spliceai version",
    )

    args = parser.parse_args()

    return args


def main():

    args = get_options()

    set_log_level(args.verbosity)

    if None in [args.I, args.O, args.D, args.M]:
        log.error(
            "Usage: spliceai [-h] [-I [input]] [-O [output]] -R reference -A annotation "
            "[-D [distance]] [-M [mask]]"
        )
        exit()

    if args.cache_password_file == "":
        log.warning("No password specified for cache database")
        cache_db = CacheDB(args.cache_host, args.cache_port, db=args.cache_number)
    else:
        with open(args.cache_password_file, "r") as f:
            password = f.readlines()[0].strip()
        cache_db = CacheDB(
            args.cache_host,
            args.cache_port,
            password=password,
            db=args.cache_number,
        )

    try:
        vcf = pysam.VariantFile(args.I)
    except (IOError, ValueError) as e:
        log.error("{}".format(e))
        exit()

    header = vcf.header
    header.add_line(
        '##INFO=<ID=SpliceAI,Number=.,Type=String,Description="SpliceAIv1.3.1 variant '
        "annotation. These include delta scores (DS) and delta positions (DP) for "
        "acceptor gain (AG), acceptor loss (AL), donor gain (DG), and donor loss (DL). "
        'Format: ALLELE|SYMBOL|DS_AG|DS_AL|DS_DG|DS_DL|DP_AG|DP_AL|DP_DG|DP_DL">'
    )

    try:
        output = pysam.VariantFile(args.O, mode="w", header=header)
    except (IOError, ValueError) as e:
        log.error("{}".format(e))
        exit()

    ann = Annotator(args.R, args.A)
    annotator_str = f"Annotator({args.R}, {args.A})"

    for record in vcf:
        db_key = get_db_key(record, annotator_str, args.D, args.M)
        res = cache_db.get(db_key)
        if res:
            scores = res
        else:
            scores = get_delta_scores(record, ann, args.D, args.M)
            cache_db.set(db_key, scores)

        if len(scores) > 0:
            record.info["SpliceAI"] = scores
        output.write(record)

    vcf.close()
    output.close()


if __name__ == "__main__":
    main()
