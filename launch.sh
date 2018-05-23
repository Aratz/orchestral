#!/bin/sh

BASE_DIR=`pwd`

MYTMPDIR=$BASE_DIR/distributed/$SLURM_JOB_ID
mkdir $MYTMPDIR
cp -r $BASE_DIR/template16 $MYTMPDIR
mkdir results/distributed/$SLURM_JOB_ID
cd $MYTMPDIR/template16

module load gsl/2.3
source activate orchestral2

screen -d -m dask-scheduler --scheduler-file $MYTMPDIR/scheduler.json
sleep 20
screen -d -m srun dask-worker --scheduler-file $MYTMPDIR/scheduler.json
sleep 20

{ time python3 $BASE_DIR/orchestrator.py config.json network.json profiling.json 2> $BASE_DIR/results/distributed/$SLURM_JOB_ID/stderr.txt ; } 2>> $BASE_DIR/${1}_distributed_total_time.txt
echo $SLURM_JOB_ID >> $BASE_DIR/${1}_distributed_total_time.txt

cp orchestral.log $BASE_DIR/results/distributed/$SLURM_JOB_ID/
cp profiling.json $BASE_DIR/results/distributed/$SLURM_JOB_ID/
cp data/cell-100-1.out $BASE_DIR/results/distributed/$SLURM_JOB_ID/

cat data/cell-100-1.in

if [[ -s data/cell-100-1.in ]];
then
    exit 0
else
    exit 1
fi
