python3 modlist.py
git add mods.json
c="${@}"
[ -z "${c}" ] && c='idk'
git commit -am "${c}"
