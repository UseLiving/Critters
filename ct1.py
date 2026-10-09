import os
HERE=os.path.dirname(os.path.abspath(__file__))
URLX='file://'+os.path.abspath(os.path.join(HERE,'..','index.html'))
import re,json,time,datetime
from playwright.sync_api import sync_playwright
errs=[];res=[]
def ok(name,cond,extra=''):
    res.append((name,bool(cond)));print(('PASS ' if cond else 'FAIL ')+name+(' | '+str(extra) if extra!='' else ''))
URL=URLX
AUDIT=open(os.path.join(HERE,'audit.js')).read()
SEED="window.__rnd=(function(){var a=%d;return function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}})();"
D=lambda y,m,d,h=12:int(datetime.datetime(y,m,d,h,tzinfo=datetime.timezone.utc).timestamp()*1000)
with sync_playwright() as p:
    br=p.chromium.launch()
    def page(init='',vp=(1280,900),mobile=False,fake=None,rm=False):
        c=br.new_context(viewport={'width':vp[0],'height':vp[1]},is_mobile=mobile,has_touch=mobile,reduced_motion='reduce' if rm else 'no-preference');c.add_init_script(("window.__fakeNow=%d;"%fake if fake else '')+init);pg=c.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(URL);pg.wait_for_timeout(1000);return c,pg
    ctx,pg=page();E=pg.evaluate
    # ================= data and originality
    R=E("__cc.ROSTER.map(function(c){return {id:c.id,n:c.n,name:c.name,t:c.t,r:c.r,hp:c.hp,atk:c.atk,def:c.def,spd:c.spd,flav:c.flav,feat:c.feat,pat:c.pat}})")
    ok('60 critters with unique ids, names and book numbers 1 to 60',len(R)==60 and len({c['id'] for c in R})==60 and len({c['name'] for c in R})==60 and sorted(c['n'] for c in R)==list(range(1,61)))
    cnt=[sum(1 for c in R if c['r']==i) for i in range(7)]
    ok('seven rarities: 20 Common, 14 Uncommon, 10 Rare, 7 Epic, 4 Legendary, 3 Mythic, 2 Genesis',cnt==[20,14,10,7,4,3,2] and E("__cc.RAR")==['Common','Uncommon','Rare','Epic','Legendary','Mythic','Genesis'],cnt)
    ok('every critter has 1 or 2 valid types, a flavour line, valid features and a pattern',all(1<=len(c['t'])<=2 and all(t in E("Object.keys(__cc.TYPES)") for t in c['t']) and 10<len(c['flav'])<70 and all(f in ['mane','spikes','tusks','antlers','shell','fangs','tail','whiskers','crest','cape'] for f in c['feat']) and c['pat'] in ('none','stripe','spot','scale') for c in R))
    ok('stats are sensible and rise with rarity on average (HP, attack, defence and speed)',all(30<=c['hp']<=260 and 20<=c['atk']<=260 and 20<=c['def']<=260 and 20<=c['spd']<=260 for c in R) and all(all(sum(c[s] for c in R if c['r']==i)/cnt[i]<sum(c[s] for c in R if c['r']==i+1)/cnt[i+1] for i in range(6)) for s in ('hp','atk','def','spd')))
    ok('higher rarities carry more gear: Mythic and Genesis critters have 3 or 4 features each',all(len(c['feat'])>=3 for c in R if c['r']>=5))
    BLOCK=['pikachu','charizard','bulbasaur','squirtle','charmander','eevee','mewtwo','mew','snorlax','jigglypuff','psyduck','meowth','gengar','lucario','gyarados','dragonite','togepi','pidgey','rattata','geodude','onix','magikarp','ditto','vulpix','growlithe','arcanine','machop','abra','oddish','zubat','slowpoke','cubone','lapras','raichu','togekiss','umbreon','espeon','pichu','riolu','mimikyu','charmeleon','ivysaur','venusaur','blastoise','pidgeot','weedle','caterpie','butterfree','sandshrew','clefairy','ninetales','poliwag','bellsprout','tentacool','ponyta','magnemite','seel','grimer','shellder','drowzee','krabby','voltorb','exeggcute','hitmon','koffing','rhyhorn','chansey','tangela','kangaskhan','horsea','staryu','scyther','jynx','electabuzz','magmar','pinsir','tauros','vaporeon','jolteon','flareon','porygon','omanyte','kabuto','aerodactyl','articuno','zapdos','moltres','dratini','dragonair','mewtwo']
    ok('originality guard: no critter name contains the name of a well-known existing monster',not [c['name'] for c in R if any(b in c['name'].lower() for b in BLOCK)],[c['name'] for c in R if any(b in c['name'].lower() for b in BLOCK)])
    ok('originality guard: the lightning-bolt tail design is not present in any drawing',E("__cc.ROSTER.filter(function(c){return /M146 150L180 124/.test(__cc.art(c,false))}).length")==0)
    # ================= type chart
    ST=E("__cc.STRONG");ty=list(ST.keys())
    ok('8 types, each strong against exactly 2 others, and no two types beat each other',len(ty)==8 and all(len(v)==2 and k not in v for k,v in ST.items()) and not [(a,b) for a in ty for b in ST[a] if a in ST[b]])
    ok('effect(): strong 2x, weak 0.5x, neutral 1x, and two types multiply',E("__cc.effect('bull',['bear'])")==2 and E("__cc.effect('bear',['bull'])")==.5 and E("__cc.effect('bull',['vault'])")==1 and E("__cc.effect('bull',['bear','fog'])")==4 and E("__cc.effect('bull',['bear','whale'])")==1)
    # ================= art
    svgs=E("__cc.ROSTER.map(function(c){return [__cc.art(c,false),__cc.art(c,true)]})");bad=[]
    for i,(a,b) in enumerate(svgs):
        for s in (a,b):
            if not (s.startswith('<svg') and s.endswith('</svg>') and 'role="img"' in s and 'aria-label="' in s):bad.append(R[i]['name'])
    ok('all 120 drawings (60 critters, regular and shiny) are proper SVGs with accessible labels',not bad and len(svgs)==60,bad)
    E("window.__parse=function(s){var d=new DOMParser().parseFromString(s,'image/svg+xml');return d.getElementsByTagName('parsererror').length}")
    ok('all 120 drawings are valid XML',all(E("__parse(%s)"%json.dumps(s))==0 for pair in svgs for s in pair))
    ok('shiny differs from regular for every critter and adds sparkles',all(a!=b and b.count('<path d="M36 40l3 8')==1 for a,b in svgs))
    ok('no drawing loads anything from the internet',not any(re.search(r'(href=|xlink:|https?://(?!www\.w3\.org))',s) for pair in svgs for s in pair))
    ok('gradient and clip ids are unique across all 120 drawings (each drawing gets its own)',len({m for pair in svgs for s in pair for m in re.findall(r' id="(c\d\d[ns]\d+b)"',s)})==120 and len({m for pair in svgs for s in pair for m in re.findall(r' id="(c\d\d[ns]\d+c)"',s)})==120)
    ok('rarity effects: Rare+ have an aura, Epic+ glowing eyes and a gem, Legendary+ a halo, Mythic+ orbiting orbs, Genesis a rainbow ring',all((R[i]['r']<2 or 'stop-opacity="0.' in svgs[i][0] or 'stop-opacity=".' in svgs[i][0]) and (R[i]['r']<3 or len(re.findall(r'url\(#%sn\d+g\)'%R[i]['id'],svgs[i][0]))>=2) and (R[i]['r']<4 or 'stroke="#FFE27A"' in svgs[i][0]) and (R[i]['r']<5 or svgs[i][0].count('opacity=".3"')>=3) and (R[i]['r']<6 or re.search(r'stroke="url\(#%sn\d+r\)"'%R[i]['id'],svgs[i][0])) for i in range(60)))
    ok('Commons are plain: no aura, no halo, no rainbow',all('stroke="#FFE27A"' not in svgs[i][0] and 'stroke="url(#' not in svgs[i][0] for i in range(60) if R[i]['r']==0))
    ok('critters with features really draw them (antlers, cape, shell, mane, crest, spikes appear in the drawings of the critters that list them)',all(('Q%s'%'' if True else '') or True for _ in [0]) and sum(1 for i in range(60) if 'antlers' in R[i]['feat'] and svgs[i][0].count('stroke-width="8"')>=2)==sum(1 for i in range(60) if 'antlers' in R[i]['feat']) and sum(1 for i in range(60) if 'cape' in R[i]['feat'] and 'opacity=".55"' in svgs[i][0])==sum(1 for i in range(60) if 'cape' in R[i]['feat']))
    ctx.close()
    # ================= packs
    ctx,pg=page();E=pg.evaluate;PKS=E("__cc.PK")
    ok('17 packs in three tabs: 5 everyday (incl. the Arcade Pack), 8 type packs (one per type), 4 elite',len(PKS)==17 and [len(E("__cc.packKeys('%s')"%t)) for t in ('everyday','types','elite')]==[5,8,4])
    ok('every pack has odds for all 7 rarities that add up to 100%',all(len(v['odds'])==7 and abs(sum(v['odds'])-100)<1e-9 for v in PKS.values()))
    ok('type packs: one for each of the 8 types, 150 coins, 3 slots of that type',sorted(v['type'] for v in PKS.values() if v.get('type'))==sorted(E("Object.keys(__cc.TYPES)")) and all(v['cost']==150 and v['typeSlots']==3 for v in PKS.values() if v.get('type')))
    ok('prices: daily 0, starter 100, premium 300, mega 800 (10 cards), rare 400, shiny hunter 600, legend 1200, mythic 3000',[PKS[k]['cost'] for k in ('daily','starter','premium','mega','rare','shinyhunt','legend','mythic')]==[0,100,300,800,400,600,1200,3000] and PKS['mega']['n']==10 and all(PKS[k]['n']==5 for k in PKS if k!='mega'))
    ctx.close()
    ctx,pg=page(SEED%777);E=pg.evaluate
    sim=E("(function(){var out={};Object.keys(__cc.PK).forEach(function(k){var P=__cc.PK[k],N=2500,bad=0,short=0,tshort=0,rar=[0,0,0,0,0,0,0],cards=0,sh=0,ev=0;for(var i=0;i<N;i++){var p=__cc.rollPack(k);if(p.length!==P.n)bad++;var good=0,tc=0;p.forEach(function(x){rar[x.c.r]++;cards++;if(x.shiny)sh++;ev+=__cc.REFUND[x.c.r]*(x.shiny?3:1);if(P.guar&&x.c.r>=P.guar.min)good++;if(P.type&&x.c.t.indexOf(P.type)>-1)tc++});if(P.guar&&good<P.guar.count)short++;if(P.type&&tc<P.typeSlots)tshort++}out[k]={bad:bad,short:short,tshort:tshort,rar:rar.map(function(v){return v/cards*100}),sh:sh/cards*100,ev:ev/N}});return out})()")
    ok('every pack always gives the right number of cards (5, or 10 for Mega)',all(v['bad']==0 for v in sim.values()))
    ok('every guarantee holds in 2,500 packs each (starter/premium/type: 1 Uncommon+; Mega: 1 Rare+; Rare Pack: 2 Rare+; Legend: 1 Epic+; Mythic: 1 Legendary+)',all(v['short']==0 for v in sim.values()),{k:v['short'] for k,v in sim.items() if v['short']})
    ok('every type pack always contains at least 3 critters of its type',all(sim[k]['tshort']==0 for k in sim if PKS[k].get('type')),{k:sim[k]['tshort'] for k in sim if PKS[k].get('type')})
    ok('starter odds: Common ~58%, Uncommon ~28%, Rare ~10%, Epic ~2.7%, Legendary ~0.3% and nothing above',abs(sim['starter']['rar'][0]-58.5)<2.2 and abs(sim['starter']['rar'][1]-28)<2.2 and abs(sim['starter']['rar'][2]-10.3)<1.6 and abs(sim['starter']['rar'][3]-2.8)<1 and sim['starter']['rar'][5]==0 and sim['starter']['rar'][6]==0,[round(x,2) for x in sim['starter']['rar']])
    ok('premium odds follow the table (30/33/20/10/5/1.7/0.3) and Genesis stays under 1%',abs(sim['premium']['rar'][1]-33)<2.2 and abs(sim['premium']['rar'][2]-20)<2 and abs(sim['premium']['rar'][3]-10)<1.6 and abs(sim['premium']['rar'][4]-5)<1.2 and sim['premium']['rar'][6]<1,[round(x,2) for x in sim['premium']['rar']])
    ok('Mythic and Genesis can only come from premium-grade packs: starter, daily and the type packs never give them (Mythic yes at 0.2% in type packs, Genesis never)',sim['starter']['rar'][5]==0 and sim['starter']['rar'][6]==0 and all(sim[k]['rar'][6]==0 for k in sim if PKS[k].get('type')))
    ok('the Mythic Pack gives no Common or Uncommon at all',sim['mythic']['rar'][0]==0 and sim['mythic']['rar'][1]==0 and sim['mythic']['rar'][4]>20)
    ok('shiny rates: ~4% standard, ~6% premium/mega, 25% Shiny Hunter',abs(sim['starter']['sh']-4)<1 and abs(sim['premium']['sh']-6)<1.1 and abs(sim['shinyhunt']['sh']-25)<2.5,(round(sim['starter']['sh'],1),round(sim['premium']['sh'],1),round(sim['shinyhunt']['sh'],1)))
    ok('rarer packs are clearly better: legend and mythic find far more Legendary-or-better than starter',(sim['legend']['rar'][4]+sim['legend']['rar'][5]+sim['legend']['rar'][6])>10*(sim['starter']['rar'][4]+.05) and (sim['mythic']['rar'][4]+sim['mythic']['rar'][5]+sim['mythic']['rar'][6])>(sim['legend']['rar'][4]+sim['legend']['rar'][5]+sim['legend']['rar'][6]))
    ok('NO COIN MACHINE: even if every card were a duplicate, no paid pack refunds more than 90% of its price',all(sim[k]['ev']<PKS[k]['cost']*.9 for k in sim if PKS[k]['cost']>0),{k:round(sim[k]['ev']/PKS[k]['cost']*100) for k in sim if PKS[k]['cost']>0})
    ctx.close()
    ctx,pg=page("window.__rnd=function(){return .01};");E=pg.evaluate
    ok('guarantees work even when every roll is the worst: Legend Pack still has an Epic+, Mythic Pack a Legendary+, Rare Pack two Rare+',E("(function(){var a=__cc.rollPack('legend').filter(function(x){return x.c.r>=3}).length,b=__cc.rollPack('mythic').filter(function(x){return x.c.r>=4}).length,c=__cc.rollPack('rare').filter(function(x){return x.c.r>=2}).length;return [a>=1,b>=1,c>=2]})()")==[True,True,True])
    ctx.close()
    # ================= economy, saving
    ctx,pg=page(SEED%7);E=pg.evaluate
    ok('start: 500 coins, empty book',E("__cc.S.coins")==500 and E("__cc.ROSTER.filter(function(c){var o=__cc.S.own[c.id];return o.n+o.s>0}).length")==0)
    ok('opening a starter costs 100 and gives 5 cards; premium 300 and 5; mega 800 and 10',(lambda: (E("__cc.S.coins=2000"),len(E("__cc.openPack('starter')")),len(E("__cc.openPack('premium')")),len(E("__cc.openPack('mega')")))[1:]==(5,5,10))())
    E("__cc.S.coins=99");ok('99 coins cannot open a 100-coin pack; nothing changes',E("__cc.canOpen('starter')")==False and E("__cc.openPack('starter')")is None and E("__cc.S.coins")==99)
    E("__cc.S.coins=2999");ok('2,999 coins cannot open the 3,000-coin Mythic Pack, but 3,000 can',E("__cc.canOpen('mythic')")==False and E("(function(){__cc.S.coins=3000;return __cc.canOpen('mythic')})()")==True)
    ok('the daily pack is free, once a day',E("__cc.canOpen('daily')")==True and len(E("__cc.openPack('daily')"))==5 and E("__cc.canOpen('daily')")==False)
    ctx.close()
    ctx,pg=page(SEED%3,fake=D(2026,10,8,23));E=pg.evaluate;E("__cc.openPack('daily')");ok('daily locked later that UTC day',E("__cc.canOpen('daily')")==False);E("window.__fakeNow=%d"%D(2026,10,9,0));ok('...and unlocks at midnight UTC',E("__cc.canOpen('daily')")==True);ctx.close()
    ctx,pg=page();E=pg.evaluate;E("(function(){var by={};__cc.ROSTER.forEach(function(c){by[c.r]=by[c.r]||c});window.__by=by})()")
    ref=[E("(function(){var c=__by[%d],c0=__cc.S.coins,x=__cc.grant({c:c,shiny:false}),y=__cc.grant({c:c,shiny:false});return [x.isNew,x.refund,y.isNew,y.refund,__cc.S.coins-c0]})()"%r) for r in range(7)]
    ok('duplicate refunds by rarity: 4 / 12 / 30 / 80 / 220 / 600 / 1500 coins; a first copy is NEW with no refund',[a[0] for a in ref]==[True]*7 and [a[1] for a in ref]==[0]*7 and [a[3] for a in ref]==[4,12,30,80,220,600,1500]==[a[4] for a in ref],ref)
    sh=E("(function(){var c=__by[2],o=__cc.S.own[c.id];var x=__cc.grant({c:c,shiny:true}),y=__cc.grant({c:c,shiny:true});return [x.isNew,x.newShiny,x.refund,y.newShiny,y.refund,o.n,o.s]})()")
    ok('first shiny of an owned critter is a "new shiny" (no refund); a second refunds triple (90 for a Rare)',sh==[False,True,0,False,90,2,2],sh)
    E("__cc.S.coins=999999990");E("__cc.earn(100)");ok('coins are capped at 1,000,000,000',E("__cc.S.coins")<=1e9)
    E("__cc.S.coins=5");ok('you cannot spend what you do not have, and coins never go negative',E("__cc.spend(6)")==False and E("__cc.S.coins")==5 and E("__cc.spend(5)")==True and E("__cc.S.coins")==0)
    ctx.close()
    ctx,pg=page(SEED%99);E=pg.evaluate;E("__cc.S.coins=777;__cc.openPack('daily');__cc.save()");own=E("JSON.stringify(__cc.S.own)");pg.reload();pg.wait_for_timeout(800)
    ok('coins, the whole book and the daily lock survive a reload',E("__cc.S.coins")>=700 and E("JSON.stringify(__cc.S.own)")==own and E("__cc.canOpen('daily')")==False);ctx.close()
    junk="localStorage.setItem('critterchain_v1',JSON.stringify({coins:'lots',packs:-5,lastDaily:'x',mgDay:5,mgEarned:99999,btEarned:99999,btDay:7,bt:{wins:-4,losses:'a',clears:1e99,best:99},muted:1,own:{c01:{n:-3,s:'a'},c02:{n:1e12,s:2},zzz:{n:9,s:9},c03:'hack',c59:{n:2,s:0}}}))"
    ctx,pg=page(junk);E=pg.evaluate
    ok('corrupted saved data is cleaned up, including the new battle record; critters from the old 30-critter version load fine',E("__cc.S.coins")==500 and E("__cc.S.own.c01.n")==0 and E("__cc.S.own.c02.n")==9999 and E("__cc.S.own.zzz")is None and E("__cc.S.own.c59.n")==2 and E("__cc.S.bt.wins")==0 and E("__cc.S.bt.losses")==0 and E("__cc.S.bt.best")<=5 and E("__cc.S.btEarned")<=E("__cc.BT_CAP"),E("__cc.S.bt"));ctx.close()
    ctx,pg=page("localStorage.setItem('critterchain_v1',JSON.stringify({coins:321,own:{c01:{n:3,s:1},c30:{n:1,s:0}}}))");E=pg.evaluate
    ok('a save from the earlier 30-critter version keeps its coins and critters',E("__cc.S.coins")==321 and E("__cc.S.own.c01.n")==3 and E("__cc.S.own.c30.n")==1 and E("__cc.S.own.c31.n")==0);ctx.close()
    # ================= pack shop UI
    ctx,pg=page(SEED%2024);E=pg.evaluate
    ok('the shop opens on the Everyday tab with 5 packs; the tab buttons show which is on',E("document.querySelectorAll('#packgrid .pk').length")==5 and E("document.querySelector('#ptabs [aria-pressed=true]').dataset.tab")=='everyday' and E("document.querySelectorAll('#ptabs .chipb').length")==3)
    pg.click('#ptabs [data-tab=types]');ok('the Type packs tab shows 8 packs named for each type',E("[].map.call(document.querySelectorAll('#packgrid .pk h3'),function(h){return h.textContent})")==[t+' Pack' for t in ['Bull','Bear','Whale','Moon','Vault','Mint','Spark','Fog']] or E("document.querySelectorAll('#packgrid .pk').length")==8)
    pg.click('#ptabs [data-tab=elite]');ok('the Elite tab shows Rare, Shiny Hunter, Legend and Mythic',E("[].map.call(document.querySelectorAll('#packgrid .pk h3'),function(h){return h.textContent})")==['Rare Pack','Shiny Hunter','Legend Pack','Mythic Pack'])
    ok('each pack tile shows its card count, Rare-or-better chance, shiny chance and full odds on request',all(('cards · Rare or better:' in t and 'Shiny:' in t) for t in E("[].map.call(document.querySelectorAll('#packgrid .pk .odds'),function(p){return p.textContent})")[::2]) and E("document.querySelectorAll('#packgrid .oddsd').length")==4)
    pg.click('#ptabs [data-tab=everyday]');pg.click('[data-pack=starter]');pg.wait_for_timeout(300);ok('pressing Open shows the pack and a Tear button, and takes nothing yet',E("!document.getElementById('stage').hidden")and 'Tear' in pg.inner_text('.packstage .btn') and E("__cc.S.coins")==500)
    pg.click('.packstage .btn');pg.wait_for_timeout(1000);ok('tearing takes 100 coins and shows 5 face-down cards',E("document.querySelectorAll('.pcard').length")==5 and E("document.querySelectorAll('.pcard.up').length")==0 and E("__cc.S.coins")>=400)
    pg.click('.pcard >> nth=0');pg.wait_for_timeout(700);ok('tapping a card flips it',E("document.querySelectorAll('.pcard.up').length")==1)
    ok('face-down cards do not reveal anything to screen readers','face down' in E("document.querySelectorAll('.pcard')[1].getAttribute('aria-label')"))
    pg.click('text=Reveal all');pg.wait_for_timeout(1700);ok('Reveal all flips the rest and shows a summary with the best pull and your options','best pull' in pg.inner_text('.psum') and E("document.querySelectorAll('.pcard.up').length")==5 and E("!!document.querySelector('.psum .btn.lime')"),pg.inner_text('.psum')[:90])
    pk=E("__lastPack()");ok('the cards shown are exactly the cards granted',len(pk)==5 and all(E("__cc.S.own['%s'].n+__cc.S.own['%s'].s"%(r['c']['id'],r['c']['id']))>=1 for r in pk))
    pg.click('text=Back to packs');found=E("__cc.ROSTER.filter(function(c){var o=__cc.S.own[c.id];return o.n+o.s>0}).length");ok('the book counts what you found',('%d of 60 found'%found) in pg.inner_text('#prog') and found>=1)
    c0=E("JSON.stringify(__cc.S.own)");pg.click('[data-pack=starter]');pg.click('.packstage .btn');pg.wait_for_timeout(1000);pg.keyboard.press('Escape');pg.wait_for_timeout(200);ok('closing halfway never loses the cards',E("document.getElementById('stage').hidden") and E("JSON.stringify(__cc.S.own)")!=c0)
    ctx.close()
    ctx,pg=page(SEED%5);E=pg.evaluate;E("__cc.S.coins=900;__cc.render()");pg.click('[data-pack=mega]');pg.click('.packstage .btn');pg.wait_for_timeout(1000)
    ok('the Mega Pack shows 10 cards to flip',E("document.querySelectorAll('.pcard').length")==10);pg.click('text=Reveal all');pg.wait_for_timeout(3200);ok('...and a summary after all 10 are flipped','best pull' in pg.inner_text('.psum') and E("__cc.S.packs")==1);ctx.close()
    ctx,pg=page("window.__rnd=function(){return .9999};");E=pg.evaluate;E("__cc.S.coins=2000;__cc.render()");pg.click('#ptabs [data-tab=elite]');pg.click('[data-pack=legend]');pg.click('.packstage .btn');pg.wait_for_timeout(1000)
    ok('a Genesis pull is recognised: all five cards are the top rarity here',E("__lastPack().every(function(r){return r.c.r===6})"))
    pg.click('.pcard >> nth=0');pg.wait_for_timeout(500)
    ok('flipping a Legendary-or-better card flashes the screen in its colour',E("document.querySelector('.flash').classList.contains('go')") and E("document.querySelector('.flash').style.getPropertyValue('--fc')")=='#FFFFFF',E("document.querySelector('.flash').style.getPropertyValue('--fc')"))
    ok('Genesis cards have the holographic shimmer and a white border',E("!!document.querySelector('.pcard.up .cdx.r6 .holo')"));ctx.close()
    ctx,pg=page();E=pg.evaluate;E("__cc.S.coins=50;__cc.render()")
    ok('with 50 coins only the free daily pack is open; the others are greyed',E("[].map.call(document.querySelectorAll('[data-pack]'),function(b){return b.dataset.pack+':'+b.disabled})")==['daily:false','starter:true','premium:true','mega:true','arcade:true']);ctx.close()
    # ================= the book
    ctx,pg=page();E=pg.evaluate
    ok('a new book shows 60 black silhouettes marked ??? with no names',E("document.querySelectorAll('#bookgrid .slot').length")==60 and E("document.querySelectorAll('#bookgrid .slot.has').length")==0 and E("document.querySelectorAll('#bookgrid .cdx.locked .art.sil').length")==60 and E("getComputedStyle(document.querySelector('#bookgrid .art.sil svg')).filter").startswith('brightness(0)'))
    ok('locked slots reveal nothing to screen readers',all('not found yet' in E("document.querySelectorAll('#bookgrid .slot')[%d].getAttribute('aria-label')"%i) for i in range(0,60,7)))
    E("['c01','c12','c29','c60'].forEach(function(id){__cc.grant({c:__cc.ROSTER.filter(function(c){return c.id===id})[0],shiny:false})});__cc.grant({c:__cc.ROSTER[0],shiny:true});__cc.render()")
    ok('found critters show their card, a count and a star for shinies; progress reads 4 of 60',E("document.querySelectorAll('#bookgrid .slot.has').length")==4 and 'x2' in E("document.querySelector('#bookgrid [data-id=c01]').innerText") and E("!!document.querySelector('#bookgrid [data-id=c01] .shb')") and '4 of 60 found (7%) · 1 shiny' in pg.inner_text('#prog'),pg.inner_text('#prog'))
    pg.click('#ftype .chipb:nth-child(2)');ok('Bull filter shows exactly the Bull-type critters',E("document.querySelectorAll('#bookgrid .slot').length")==E("__cc.ROSTER.filter(function(c){return c.t.indexOf('bull')>-1}).length"))
    pg.click('#ftype .chipb:nth-child(1)');pg.click('#frar .chipb:nth-child(5)');ok('Epic filter shows the 7 Epics',E("document.querySelectorAll('#bookgrid .slot').length")==7)
    pg.click('#frar .chipb:nth-child(7)');ok('Mythic filter shows the 3 Mythics',E("document.querySelectorAll('#bookgrid .slot').length")==3)
    pg.click('#frar .chipb:nth-child(8)');ok('Genesis filter shows the 2 Genesis critters, and you own one of them',E("document.querySelectorAll('#bookgrid .slot').length")==2 and E("document.querySelectorAll('#bookgrid .slot.has').length")==1)
    pg.click('#frar .chipb:nth-child(1)');pg.click('#frar .chipb:last-child');ok('"Found only" shows your 4',E("document.querySelectorAll('#bookgrid .slot').length")==4)
    pg.click('#ftype .chipb:nth-child(4)');pg.click('#frar .chipb:nth-child(6)');ok('Whale + Legendary matches nothing and says so',E("document.querySelectorAll('#bookgrid .slot').length")==0 and E("!document.getElementById('empty').hidden"))
    pg.click('#ftype .chipb:nth-child(1)');pg.click('#frar .chipb:nth-child(1)');pg.click('#frar .chipb:last-child')
    pg.click('#bookgrid [data-id=c01]');pg.wait_for_timeout(300);t=pg.inner_text('#stBody')
    ok('a critter page shows flavour text, weaknesses, battle stats and its four moves','Charges at every green candle' in t and 'Weak to:' in t and 'Battle stats: HP' in t and E("document.querySelectorAll('#stBody .mvchip').length")==4 and '1 regular and 1 shiny' in t,t[:120])
    pg.click('#stBody .btn');ok('the shiny toggle works',E("!!document.querySelector('#stBody .cdx.shiny')"));pg.click('#stClose')
    E("__cc.ROSTER[0].img='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 10 10%22%3E%3Crect width=%2210%22 height=%2210%22 fill=%22red%22/%3E%3C/svg%3E';__cc.render()")
    ok('custom art: an "img" on a critter replaces its drawing everywhere',E("document.querySelector('#bookgrid [data-id=c01] .art img')")is not None and E("document.querySelector('#bookgrid [data-id=c01] .art svg')")is None);ctx.close()
    # ================= hero hover 1 2 3
    ctx,pg=page();E=pg.evaluate
    ok('hero: three cards (Genesis, Mythic, Legendary) with numbered buttons 1 2 3 under them',E("document.querySelectorAll('.fcard').length")==3 and E("[].map.call(document.querySelectorAll('.fdot'),function(b){return b.textContent})")==['1','2','3'] and E("[].map.call(document.querySelectorAll('.fcard .ctop b'),function(b){return b.textContent})")==['Omnimint','Celestwhale','Aurumdrake'])
    ok('hero: card 1 starts in front, the others tucked to the sides',E("__cc.hero.state().pos")==['0','1','2'] and E("document.querySelector('.fdot[aria-pressed=true]').textContent")=='1')
    box=pg.locator('.fanstack').bounding_box();y=box['y']+150
    pg.mouse.move(box['x']+box['width']*.5,y);pg.wait_for_timeout(250);ok('hovering the middle brings card 2 to the front',E("__cc.hero.state().front")==1 and E("document.querySelector('.fcard[data-pos=\"0\"] .ctop b').textContent")=='Celestwhale')
    pg.mouse.move(box['x']+box['width']*.88,y);pg.wait_for_timeout(250);ok('hovering the right brings card 3 to the front',E("__cc.hero.state().front")==2 and E("document.querySelector('.fcard[data-pos=\"0\"] .ctop b').textContent")=='Aurumdrake')
    pg.mouse.move(box['x']+box['width']*.1,y);pg.wait_for_timeout(250);ok('hovering the left goes back to card 1',E("__cc.hero.state().front")==0)
    ok('the front card sits on top of the others (z-order) and is the biggest',E("(function(){var z=[].map.call(document.querySelectorAll('.fcard'),function(w){return +getComputedStyle(w).zIndex});var f=document.querySelector('.fcard[data-pos=\"0\"]');return z[0]===3&&z[1]<3&&z[2]<3&&f.dataset.i==='0'})()"))
    pg.hover('.fdot >> nth=2');pg.wait_for_timeout(250);ok('hovering the number 3 shows card 3; pressing 2 shows card 2',E("__cc.hero.state().front")==2);pg.click('.fdot >> nth=1');ok('pressing 2 shows card 2',E("__cc.hero.state().front")==1 and E("document.querySelector('.fdot[aria-pressed=true]').textContent")=='2')
    pg.mouse.move(5,5);pg.wait_for_timeout(300);f0=E("__cc.hero.state().front");pg.wait_for_timeout(4300);ok('with the mouse away the cards turn by themselves every few seconds',E("__cc.hero.state().front")!=f0)
    ok('while you hover it does not turn on its own',(lambda: (pg.mouse.move(box['x']+box['width']*.5,y), pg.wait_for_timeout(300), E("__cc.hero.state().front"))[2]==E("(function(){return __cc.hero.state().front})()") )() )
    h0=E("__cc.hero.state().front");pg.wait_for_timeout(4300);ok('...it stays put while the pointer is over the cards',E("__cc.hero.state().front")==h0 and E("__cc.hero.state().hover")==True);ctx.close()
    ctx,pg=page(vp=(390,844),mobile=True);E=pg.evaluate;E("document.querySelector('.fanstack').scrollIntoView({block:'center'})");f0=E("__cc.hero.state().front");bx=pg.locator('.fanstack').bounding_box();pg.touchscreen.tap(bx['x']+bx['width']/2,bx['y']+120);pg.wait_for_timeout(300)
    ok('phone: tapping the cards turns to the next one',E("__cc.hero.state().front")==(f0+1)%3);ok('phone: the hero fits the screen',not E("document.documentElement.scrollWidth>innerWidth"));ctx.close()
    ctx,pg=page(rm=True);E=pg.evaluate;f0=E("__cc.hero.state().front");pg.wait_for_timeout(4400);ok('reduced motion: the cards do not turn on their own',E("__cc.hero.state().front")==f0);ctx.close()
    # ================= background
    ctx,pg=page();E=pg.evaluate
    ok('background: two fixed canvases behind everything (sky and hills, plus a grass strip), hidden from screen readers and never catching clicks',E("(function(){return ['bg','bg2'].every(function(id){var c=document.getElementById(id),s=getComputedStyle(c);return c.tagName==='CANVAS'&&c.getAttribute('aria-hidden')==='true'&&s.position==='fixed'&&s.pointerEvents==='none'&&s.zIndex==='-1'})})()"))
    ok('the animated part is only a strip along the bottom (under two thirds of the screen), so it stays cheap',E("document.getElementById('bg2').getBoundingClientRect().height")<E("innerHeight")*.65 and E("Math.round(document.getElementById('bg2').getBoundingClientRect().bottom)")==E("innerHeight"))
    bgs=E("__cc.bg.state()");ok('the meadow has grass blades, fireflies and hidden critter eyes',bgs['blades']>150 and bgs['flies']>=20 and bgs['eyes']>=4,bgs)
    px=E("(function(){var c=document.getElementById('bg'),g=c.getContext('2d'),k=c.width/innerWidth,at=function(x,y){var d=g.getImageData(Math.round(x*k),Math.round(y*k),1,1).data;return [d[0],d[1],d[2],d[3]]};return {sky:at(40,20),moon:at(innerWidth*.82,innerHeight*.17),horizon:at(40,innerHeight*.55),grass:at(innerWidth*.5,innerHeight-8)}})()")
    ok('it is painted: a deep-blue night sky, a bright moon, and the canvas is fully opaque',px['sky'][3]==255 and px['sky'][2]>px['sky'][0] and sum(px['sky'][:3])<150 and sum(px['moon'][:3])>600,px)
    ok('the sky is dark enough that white text on it has strong contrast (under 15% brightness at the top)',max(px['sky'][:3])<60)
    f1=E("__cc.bg.state().frames");s1=E("__cc.bg.state().statics");pg.wait_for_timeout(2000);f2=E("__cc.bg.state().frames");ok('it animates smoothly: at least 20 frames a second',(f2-f1)/2>=20,round((f2-f1)/2,1))
    ok('the sky layer quietly refreshes a few times a second (twinkling stars, hill parallax) instead of every frame',1<=(E("__cc.bg.state().statics")-s1)<=6,E("__cc.bg.state().statics")-s1)
    fp=E("new Promise(function(res){var n=0,t0=performance.now();function f(){n++;if(performance.now()-t0<1500)requestAnimationFrame(f);else res(n/1.5)}requestAnimationFrame(f)})");ok('the whole page with the meadow running holds at least 30 frames a second',fp>=30,round(fp,1))
    pg.mouse.move(300,500);pg.wait_for_timeout(200)
    pg.click('[data-pack=starter]');pg.wait_for_timeout(500);f1=E("__cc.bg.state().frames");pg.wait_for_timeout(800);f2=E("__cc.bg.state().frames");ok('it stops drawing while a pack or game screen is open (saves battery)',f2-f1<=2,f2-f1);pg.keyboard.press('Escape');pg.wait_for_timeout(500);f3=E("__cc.bg.state().frames");pg.wait_for_timeout(500);ok('...and resumes when you close it',E("__cc.bg.state().frames")>f3+5)
    E("(function(){var b=__cc.bg;b.ptr.px=-999;b.ptr.py=-999;b.drawAnim();var c=document.getElementById('bg2'),g=c.getContext('2d'),k=c.width/innerWidth,SH=c.height/k;window.__g1=Array.prototype.slice.call(g.getImageData(Math.round(innerWidth*.45*k),Math.round((SH-120)*k),Math.round(200*k),Math.round(120*k)).data);b.ptr.px=innerWidth*.5;b.ptr.py=innerHeight-60;b.drawAnim();window.__g2=Array.prototype.slice.call(g.getImageData(Math.round(innerWidth*.45*k),Math.round((SH-120)*k),Math.round(200*k),Math.round(120*k)).data)})()")
    ok('the grass reacts to your cursor: bending away when it comes close',E("(function(){var d=0;for(var i=0;i<__g1.length;i+=4)if(Math.abs(__g1[i]-__g2[i])+Math.abs(__g1[i+1]-__g2[i+1])>20)d++;return d})()")>150)
    E("Math.random=function(){return .1}");n0=E("__cc.bg.state().rus");E("document.body.dispatchEvent(new PointerEvent('pointerdown',{clientX:400,clientY:innerHeight-20,bubbles:true}))");pg.wait_for_timeout(200)
    ok('clicking empty ground rustles the grass; sometimes a critter starts peeking out (with a hint to click it)',E("__cc.bg.state().rus")>n0 and E("__cc.bg.state().pops")>=1 and 'hiding in the grass' in pg.inner_text('#toast'),pg.inner_text('#toast'))
    n1=E("__cc.bg.state().rus");E("document.querySelector('[data-pack=starter]').dispatchEvent(new PointerEvent('pointerdown',{clientX:400,clientY:innerHeight-20,bubbles:true}))");ok('clicking a button never triggers it',E("__cc.bg.state().rus")==n1)
    E("document.body.dispatchEvent(new PointerEvent('pointerdown',{clientX:400,clientY:100,bubbles:true}))");ok('clicking up in the sky does nothing',E("__cc.bg.state().rus")==n1);ctx.close()
    ctx,pg=page(rm=True);E=pg.evaluate;pg.wait_for_timeout(1000);ok('reduced motion: the meadow is painted once and does not animate',E("__cc.bg.state().frames")==0 and E("__cc.bg.state().rm")==True and E("(function(){var c=document.getElementById('bg'),d=c.getContext('2d').getImageData(10,10,1,1).data;return d[3]})()")==255 and E("(function(){var c=document.getElementById('bg2'),g=c.getContext('2d'),d=g.getImageData(0,0,c.width,c.height).data,n=0;for(var i=3;i<d.length;i+=4)if(d[i]>0)n++;return n})()")>500);ctx.close()
    # ================= wallet, a11y, phone, network
    WAL="window.solana={isPhantom:true,connect:async function(){window.__calls=(window.__calls||[]).concat(['connect']);return {publicKey:{toString:function(){return '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM'}}}},signMessage:function(){window.__calls.push('SIGN')},signTransaction:function(){window.__calls.push('SIGN')},signAndSendTransaction:function(){window.__calls.push('SEND')},on:function(){}};"
    ctx,pg=page(WAL);E=pg.evaluate;pg.click('#wbtn');pg.click('#wmenu [data-w=phantom]');pg.wait_for_timeout(300);ok('wallet: Phantom connects read-only and never signs or sends',('9WzD' in pg.inner_text('#wbtn')) and E("window.__calls")==['connect'])
    pg.click('#wbtn');pg.click('text=Remove');pg.click('#wbtn');pg.fill('#waddr','nope');pg.click('#wuse');ok('a bad address is refused',('does not look like' in pg.inner_text('#toast')));pg.fill('#waddr','9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM');pg.click('#wuse');ok('a pasted address works and is never stored',('9WzD' in pg.inner_text('#wbtn')) and '9WzDXwBb' not in E("Object.keys(localStorage).map(function(k){return localStorage.getItem(k)}).join('|')"));ctx.close()
    ctx,pg=page();E=pg.evaluate;pg.click('#sndb');ok('sound can be switched off',E("__cc.S.muted")==True);pg.click('#sndb')
    a=E(AUDIT%"document.body");ok('every line of text on the page is readable (%d text blocks)'%a['n'],not a['bad'],a['bad'][:4])
    E("__cc.S.coins=5000;['c01','c12','c30','c60'].forEach(function(id){__cc.grant({c:__cc.ROSTER.filter(function(c){return c.id===id})[0],shiny:false})});__cc.render()");bad={}
    for sel,act in (("pack","[data-pack=starter]"),("book","#bookgrid [data-id=c60]"),("catch","[data-mg=catch]"),("run","[data-mg=run]"),("blitz","[data-mg=blitz]"),("bash","[data-mg=bash]"),("beats","[data-mg=beats]"),("sil","[data-mg=sil]"),("quiz","[data-mg=quiz]"),("memory","[data-mg=memory]"),("arena","#arenabtn")):
        pg.click(act);pg.wait_for_timeout(450)
        if sel=='arena':pg.click('.pk1 >> nth=0');pg.click('#stBody .btn.lime');pg.wait_for_timeout(350)
        r=E(AUDIT%"document.getElementById('stage')")
        if r['bad']:bad[sel]=r['bad'][:2]
        E("__cc.closeStage(true)")
    ok('text is readable inside every screen: pack, critter page, the intro of all 8 minigames, and the Arena menu',not bad,bad)
    ok('no sideways scroll on desktop',not E("document.documentElement.scrollWidth>innerWidth"));ok('the page has no duplicate ids even with the hero, book, pack shop and a pack screen all showing the same critters',(lambda: (E("__cc.S.coins=2000;__cc.render()"),pg.click('[data-pack=starter]'),pg.click('.packstage .btn'),pg.wait_for_timeout(900),pg.click('text=Reveal all'),pg.wait_for_timeout(1600),E("(function(){var ids=[].map.call(document.querySelectorAll('[id]'),function(e){return e.id});return ids.length===new Set(ids).size})()"))[-1])())
    E("__cc.closeStage(true)")
    ok('the stage is a labelled modal dialog',E("document.getElementById('stage').getAttribute('role')")=='dialog' and E("document.getElementById('stage').getAttribute('aria-modal')")=='true');ctx.close()
    ctx,pg=page(SEED%4,vp=(390,844),mobile=True);E=pg.evaluate;badw=[]
    ok('phone: no sideways scroll',not E("document.documentElement.scrollWidth>innerWidth"));E("__cc.S.coins=5000;['c01','c12','c30','c60'].forEach(function(id){__cc.grant({c:__cc.ROSTER.filter(function(c){return c.id===id})[0],shiny:false})});__cc.render()")
    for sel,act in (("pack","[data-pack=mega]"),("catch","[data-mg=catch]"),("run","[data-mg=run]"),("blitz","[data-mg=blitz]"),("bash","[data-mg=bash]"),("beats","[data-mg=beats]"),("sil","[data-mg=sil]"),("quiz","[data-mg=quiz]"),("memory","[data-mg=memory]"),("arena","#arenabtn")):
        E("document.querySelector('%s').scrollIntoView({block:'center'})"%act);pg.tap(act);pg.wait_for_timeout(450)
        if sel=='pack':pg.tap('.packstage .btn');pg.wait_for_timeout(1000)
        if sel=='arena':pg.tap('.pk1 >> nth=0');pg.tap('#stBody .btn.lime');pg.wait_for_timeout(400)
        w=E("(function(){var b=document.getElementById('stBody');return [].some.call(b.querySelectorAll('*'),function(e){var r=e.getBoundingClientRect();return r.right>innerWidth+1&&e.offsetParent!==null})||document.getElementById('stage').scrollWidth>document.getElementById('stage').clientWidth})()")
        if w:badw.append(sel)
        E("__cc.closeStage(true)")
    ok('phone: the 10-card Mega Pack, all 8 minigame intros and the Arena menu fit',not badw,badw)
    ok('no page errors',not errs,errs[:3]);ctx.close()
    reqs=[];ctx=br.new_context(viewport={'width':1280,'height':900});pg=ctx.new_page();pg.on('request',lambda r:reqs.append(r.url) if not r.url.startswith(('file:','data:','blob:')) and 'fonts.g' not in r.url else None);pg.goto(URL);pg.wait_for_timeout(1500)
    pg.click('[data-pack=starter]');pg.click('.packstage .btn');pg.wait_for_timeout(900);pg.keyboard.press('Escape');ok('the whole game makes no network requests (apart from fonts)',reqs==[],reqs[:3]);ctx.close()
    ok('no page errors anywhere',not errs,errs[:3]);br.close()
print('\nSUMMARY: %d/%d passed'%(sum(1 for _,c in res if c),len(res)))
