python3 modlist.py
python3 modsort.py
git add mods.json
c="${@}"
[ -z "${c}" ] && c='idk'
git commit -am "${c}"
