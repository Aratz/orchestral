for i in 4 8 12 16;
do
    for j in `seq 1 16`
    do
        sbatch -p core -n $i -t 1:00:00 -A snic2018-8-157 launch.sh $i
    done
done

for j in `seq 1 16`
do
    sbatch -p node -n 1 -t 1:00:00 -A snic2018-8-157 launch.sh 20
done
