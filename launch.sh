#!/bin/sh

BASE_DIR=`pwd`

cp -r $BASE_DIR/template $TMPDIR
mkdir results/$SLURM_JOB_ID
cd $TMPDIR/template

module load gsl/2.3
source activate orchestral
{ time python3 $BASE_DIR/orchestrator.py config.json network.json profiling.json 2> $BASE_DIR/results/$SLURM_JOB_ID/stderr.txt ; } 2>> $BASE_DIR/${1}_total_time.txt

cp data/orchestral.log $BASE_DIR/results/$SLURM_JOB_ID/
cp data/profiling.json $BASE_DIR/results/$SLURM_JOB_ID/
cp data/cell-100-1.out $BASE_DIR/results/$SLURM_JOB_ID/
