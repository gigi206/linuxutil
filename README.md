# linuxutil
Python linux library for system engineer (processus, network...)

_**Exemple :**_
```python
>>> from linuxutil import *
>>> p=pid.id(603)
>>> p.name
'apache2'
>>> p.exe
'/usr/sbin/apache2'
>>> p.cpid
[15350, 15351, 15352, 15353, 15492, 15661, 17134, 18940, 20516, 28453]
```
