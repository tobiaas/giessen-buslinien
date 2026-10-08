import json
d=json.load(open('data2.json')); t=json.load(open('times.json'))
for v in t.values(): v.pop('rep',None)
d['times']=t
j=json.dumps(d,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')
body=open('tpl4.html').read().replace('const D=__DATA__;','const D='+j+';')
open('giessen-buslinien.html','w').write(body)
old=open('site/index.html').read()
head=old[:old.index('<style>*,*::before')]+'<style>*,*::before,*::after{box-sizing:border-box}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
b=body.replace('<meta charset="utf-8">\n','',1); i=b.index('<div class="wrap">')
open('site/index.html','w').write(head+b[:i]+'</head>\n<body>\n'+b[i:]+'\n</body>\n</html>\n')
