for j in `seq 1 8`
do
    sbatch --exclusive -p core -n 1 -t 3:00:00 -A snic2018-8-157 launch.sh 1
    sbatch --exclusive -p core -n 4 -t 2:00:00 -A snic2018-8-157 launch.sh 4
done

for i in 8 12 16;
do
    for j in `seq 1 8`
    do
        sbatch --exclusive -p core -n $i -t 1:00:00 -A snic2018-8-157 launch.sh $i
    done
done

for j in `seq 1 8`
do
    sbatch -p node -n 1 -t 1:00:00 -A snic2018-8-157 launch.sh 20
done
