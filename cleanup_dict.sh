words=$(cat dict.txt | sort | uniq)

# dump back word per line
for word in $words; do
    echo $word
done > dict.txt
