DOMAIN=$1
PROBLEM=$2
shift 2
./build.py && PYTHONPATH=./builds/release/bin/ ./fast-downward.py --keep-sas-file $DOMAIN $PROBLEM --search "astar(lmcut())"  --translate-options --keep-unimportant-variables $@
