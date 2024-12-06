install:
	pip install -e .
	pip install -e .[cpu]

install_gpu:
	pip install -e .
	pip install -e .[gpu]

test_exome_nocache:
	python -m cached_spliceai -I /home1/L_PROD/NGS/BAS/HOWARD/data/nicaises/KLA2403985.final.vcf -O /home1/L_PROD/NGS/BAS/HOWARD/data/nicaises/KLA2403985.spliceai_uncached.vcf -R /home1/DB/STARK/genomes/current/hg19.fa -A grch37
	
test_exome:
	python -m cached_spliceai -I /home1/L_PROD/NGS/BAS/HOWARD/data/nicaises/KLA2403985.final.vcf -O /home1/L_PROD/NGS/BAS/HOWARD/data/nicaises/KLA2403985.spliceai_uncached.vcf -R /home1/DB/STARK/genomes/current/hg19.fa -A grch37 -H 0.0.0.0 -P 4262