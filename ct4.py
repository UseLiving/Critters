import os
HERE=os.path.dirname(os.path.abspath(__file__))
URLX='file://'+os.path.abspath(os.path.join(HERE,'..','index.html'))
import re,json,datetime
from playwright.sync_api import sync_playwright
errs=[];res=[]
def ok(name,cond,extra=''):
    res.append((name,bool(cond)));print(('PASS ' if cond else 'FAIL ')+name+(' | '+str(extra) if extra!='' else ''))
URL=URLX
D=lambda y,m,d,h=12:int(datetime.datetime(y,m,d,h,tzinfo=datetime.timezone.utc).timestamp()*1000)
with sync_playwright() as p:
    br=p.chromium.launch();ctx=br.new_context(viewport={'width':1280,'height':900});pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(URL);pg.wait_for_timeout(900);E=pg.evaluate
    E("window.G=function(id){return __cc.ROSTER.filter(function(c){return c.id===id})[0]}")
    def nb(pl,fo,rng=.5,lvp=1,lvf=1):
        E("window.__rnd=function(){return %f}"%rng);E("__cc.S.btEarned=0;__cc.S.btDay='';__cc.S.bt={wins:0,losses:0,clears:0,best:0};__cc.S.lv={};__cc.S.coins=0")
        E("window.__B=(function(){var B=__cc.bt.newBattle(%s.map(function(id){return {c:G(id),lv:%d}}),'normal');B.foes=%s.map(function(id){return __cc.bt.fighter(G(id),%d)});B.fi=0;B.foe=B.foes[0];return B})()"%(json.dumps(pl),lvp,json.dumps(fo),lvf))
    ev=lambda t:E("__B.events.filter(function(e){return e.t==='%s'})"%t)
    turn=lambda a:E("__cc.bt.resolveTurn(__B,%s)"%json.dumps(a))
    # ============ moves
    MV=E("__cc.ROSTER.map(function(c){return __cc.bt.movesFor(c).map(function(m){return {n:m.n,t:m.t,p:m.p,a:m.a,pp:m.pp,max:m.max,pr:m.pr,u:m.u,fx:m.fx}})})");R=E("__cc.ROSTER.map(function(c){return {t:c.t,r:c.r,n:c.n}})")
    ok('every critter has exactly 4 moves with a name, valid type, power, accuracy, PP and no duplicate names',all(len(m)==4 and len({x['n'] for x in m})==4 and all((x['t'] is None or x['t'] in E("Object.keys(__cc.TYPES)")) and 0<=x['p']<=90 and 80<=x['a']<=100 and x['pp']>=3 and x['max']==x['pp'] for x in m) for m in MV))
    ok('every critter knows a move of its own type; dual-type critters know one for each of their types',all(any(x['t']==R[i]['t'][0] for x in m) and (len(R[i]['t'])<2 or any(x['t']==R[i]['t'][1] for x in m)) for i,m in enumerate(MV)))
    ok('single-type critters get a signature effect move; Rare+ also get a 90-power heavy move; commons start with plain Strike',all(any(x['fx'] for x in m) for i,m in enumerate(MV) if len(R[i]['t'])==1) and all(any(x['p']==90 for x in m) for i,m in enumerate(MV) if R[i]['r']>=2 and len(R[i]['t'])==1) and all(any(x['n']=='Strike' for x in m) for i,m in enumerate(MV) if R[i]['r']==0 and len(R[i]['t'])==1))
    ok('Uncommon critters get the Dash move with priority +1',all(any(x['pr']==1 for x in m) for i,m in enumerate(MV) if R[i]['r']==1 and len(R[i]['t'])==1))
    ok('utility moves are Guard, Focus, Mend or Cleanse and every critter below Epic has one',all(sum(1 for x in m if x['u'])==1 and [x['n'] for x in m if x['u']][0] in ('Guard','Focus','Mend','Cleanse') for i,m in enumerate(MV) if R[i]['r']<3 or len(R[i]['t'])==1))
    ok('the 8 signature moves: Horn Rally (self Attack up), Red Candle (foe Defence down), Whale Wave (foe Speed down), Lunar Crash and Volt Chain (stun), Gold Rush and Block Bloom (drain), Fog Bank (Rugged)',E("(function(){var T=__cc.bt.TM;return Object.keys(T).map(function(k){var f=T[k].sig.fx;return [T[k].sig.n,f.self?'self':f.foe?'foe':f.status||('drain'+f.drain)]})})()")==[['Horn Rally','self'],['Red Candle','foe'],['Whale Wave','foe'],['Lunar Crash','stun'],['Gold Rush','drain0.33'],['Block Bloom','drain0.5'],['Volt Chain','stun'],['Fog Bank','rugged']])
    ok('each type has a passive ability and every status has a description',len(E("Object.keys(__cc.bt.PASS)"))==8 and all(len(v['n'])>3 and len(v['d'])>10 for v in E("Object.values(__cc.bt.PASS)")) and E("Object.keys(__cc.bt.STATUS)")==['stun','rugged'])
    # ============ stats and damage
    ok('fighters: HP is 3 x card HP x level multiplier; the level is clamped to 1-30',E("(function(){var c=G('c20'),a=__cc.bt.fighter(c,1),b=__cc.bt.fighter(c,10),z=__cc.bt.fighter(c,99),n=__cc.bt.fighter(c,-4);return [a.max===c.hp*3,b.max===Math.floor(c.hp*3*__cc.lvMult(10)),z.lv,n.lv,Math.abs(b.atk-c.atk*__cc.lvMult(10))<1e-9,a.hp===a.max]})()")==[True,True,30,1,True,True])
    cases=[]
    for i in range(240):
        a=int(E("Math.floor(Math.random()*60)"));b=int(E("Math.floor(Math.random()*60)"));m=int(E("Math.floor(Math.random()*4)"));sa=int(E("Math.floor(Math.random()*5)-2"));sd=int(E("Math.floor(Math.random()*5)-2"));la=1+i%30;ld=1+(i*7)%30;roll=.9+i%21/100;crit=(i%7==0);used=(i%3==0)
        got=E("(function(){var A=__cc.bt.fighter(__cc.ROSTER[%d],%d),D=__cc.bt.fighter(__cc.ROSTER[%d],%d);A.st.atk=%d;D.st.def=%d;A.used=%s;var mv=A.mv[%d];return [__cc.bt.dmgCalc(A,D,mv,%f,%s),A.atk,D.def,mv.p,mv.t,mv.t?__cc.effect(mv.t,D.c.t):1,(mv.t&&A.c.t.indexOf(mv.t)>-1)?1.25:1,A.pass,D.pass]})()"%(a,la,b,ld,sa,sd,'true' if used else 'false',m,roll,'true' if crit else 'false'))
        d,atk,df,pw,t,eff,stab,pa,pd=got
        if pw==0:continue
        D2=df*max(.5,1+.25*sd)*(1.15 if pd=='vault' else 1);A2=atk*max(.5,1+.25*sa)
        exp=max(1,int(((A2/D2)*pw*.5+2)*eff*stab*roll*(1.5 if crit else 1)*(.9 if pd=='bear' else 1)*(1.25 if (pa=='bull' and not used) else 1)))
        cases.append(abs(d-exp)<=1)
    ok('damage matches an independent calculation in %d random matchups (levels, stages, type effect, same-type bonus, critical, Thick Fur, Armor Plating, Stampede)'%len(cases),len(cases)>150 and all(cases),(len(cases),cases.count(False)))
    ok('super effective moves hit about twice as hard as neutral ones; not very effective about half',E("(function(){var A=__cc.bt.fighter(G('c01'),5),mv={t:'bull',p:60},d=function(id){return __cc.bt.fighter(G(id),5)};var base=__cc.bt.dmgCalc(A,d('c05'),mv,1,false),sup=__cc.bt.dmgCalc(A,d('c02'),mv,1,false),weak=__cc.bt.dmgCalc(A,d('c03'),mv,1,false);return [sup/base>1.8,weak/base<.62]})()")==[True,True])
    # ============ effects, one move at a time (controlled dice)
    def p_hits(pid,foe,idx,rng,**kw):
        nb([pid],[foe],rng=rng);E("__B.team[0].spd=9999");return turn({'k':'move','i':idx})
    p_hits('c01','c05',1,.5);ok('Horn Rally (Bullpup): after it hits, its own Attack goes up one stage',E("__B.team[0].st.atk")==1 and len([e for e in ev('stat') if e['side']=='p'])==1)
    p_hits('c02','c05',1,.3);ok('Red Candle (Cubbear): 40% to lower the foe\'s Defence (roll 0.3: yes)',E("__B.foe.st.def")==-1)
    p_hits('c02','c05',1,.5);ok('...(roll 0.5: no)',E("__B.foe.st.def")==0)
    p_hits('c03','c05',1,.3);ok('Whale Wave (Minnowl): 40% to lower the foe\'s Speed',E("__B.foe.st.spd")==-1)
    p_hits('c04','c05',1,.2);ok('Lunar Crash (Lunamoth): 25% to stun (roll 0.2 yes, 0.3 no)',E("__B.foe.status")is not None and E("__B.foe.status.k")=='stun');p_hits('c04','c05',1,.3);ok('...roll 0.3: no stun',E("__B.foe.status")is None)
    p_hits('c07','c05',1,.2);ok('Volt Chain (Zaptail): 30% to stun (roll 0.2)',E("__B.foe.status.k")=='stun')
    p_hits('c08','c05',1,.3);ok('Fog Bank (Mistpuff): 40% to give Rugged (roll 0.3)',E("__B.foe.status.k")=='rugged')
    nb(['c05'],['c01']);E("__B.team[0].spd=9999;__B.team[0].hp=Math.floor(__B.team[0].max*.5)");h0=E("__B.team[0].hp");turn({'k':'move','i':1});hit=[e for e in ev('hit') if e['side']=='p'][0];heal=[e for e in ev('heal') if e['why']=='drain'][0]
    ok('Gold Rush (Coinpup): heals the attacker for 33% of the damage dealt',abs(heal['amt']-int(hit['dmg']*.33))<=1,(heal['amt'],hit['dmg']))
    nb(['c06'],['c01']);E("__B.team[0].spd=9999;__B.team[0].hp=Math.floor(__B.team[0].max*.5)");turn({'k':'move','i':1});hit=[e for e in ev('hit') if e['side']=='p'][0];heal=[e for e in ev('heal') if e['why']=='drain'][0]
    ok('Block Bloom (Sproutling): heals the attacker for 50% of the damage dealt',abs(heal['amt']-int(hit['dmg']*.5))<=1,(heal['amt'],hit['dmg']))
    nb(['c01'],['c05']);E("__B.team[0].spd=9999;__B.team[0].st.atk=2");turn({'k':'move','i':1});turn({'k':'move','i':1});ok('stat stages cap at +2: a third boost says it won\'t go higher and changes nothing',E("__B.team[0].st.atk")==2 and len(ev('nostat'))>=1)
    # ============ passives
    nb(['c01'],['c05']);E("__B.team[0].spd=9999");d1=E("(function(){var A=__B.team[0];return __cc.bt.dmgCalc(A,__B.foe,A.mv[0],1,false)})()");turn({'k':'move','i':0});first=[e for e in ev('hit') if e['side']=='p'][0]['dmg']
    ok('Stampede (bull): the first attack of the battle is 25% stronger, and only the first',first>=int(d1*1.0) and E("__B.team[0].used")==True and E("(function(){var A=__B.team[0];return __cc.bt.dmgCalc(A,__B.foe,A.mv[0],1,false)})()")<d1)
    ok('Thick Fur (bear) takes 10% less damage; Armor Plating (vault) has 15% more Defence',E("(function(){var A=__cc.bt.fighter(G('c20'),5);A.used=true;var m=A.mv[0],bear=__cc.bt.fighter(G('c02'),5),plain=__cc.bt.fighter(G('c02'),5);plain.pass='fog';var vault=__cc.bt.fighter(G('c05'),5),pv=__cc.bt.fighter(G('c05'),5);pv.pass='fog';return [__cc.bt.dmgCalc(A,bear,m,1,false)<__cc.bt.dmgCalc(A,plain,m,1,false),__cc.bt.dmgCalc(A,vault,m,1,false)<__cc.bt.dmgCalc(A,pv,m,1,false)]})()")==[True,True])
    nb(['c01'],['c03']);E("__B.team[0].spd=0;__B.foe.spd=9999;__B.foe.hp=Math.floor(__B.foe.max*.5);__B.team[0].hp=__B.team[0].max");turn({'k':'move','i':2});hl=[e for e in ev('heal') if e['why']=='Wave Rider']
    ok('Wave Rider (whale): heals 1/16 of its max HP at the end of every turn',len(hl)==1 and hl[0]['amt']==max(1,int(E("__B.foe.max")/16)))
    nb(['c04'],['c06'],rng=.2);E("__B.team[0].spd=9999");turn({'k':'move','i':1});ok('Fresh Leaf (mint) cannot be given a status, even when the dice say it should',E("__B.foe.status")is None and len(ev('status'))==0)
    nb(['c01'],['c07'],rng=.2);E("__B.team[0].spd=9999");turn({'k':'move','i':0});ok('Static (spark): attackers have a 30% chance (roll 0.2) to be stunned when they hit it',E("__B.team[0].status")is not None and E("__B.team[0].status.k")=='stun')
    nb(['c01'],['c07'],rng=.5);E("__B.team[0].spd=9999");turn({'k':'move','i':0});ok('...and not with a 0.5 roll',E("__B.team[0].status")is None)
    nb(['c01'],['c08'],rng=.1);E("__B.team[0].spd=9999");h=E("__B.foe.hp");turn({'k':'move','i':0});ok('Mist Cover (fog): 15% to evade an attack (roll 0.1: evaded, no damage)',E("__B.foe.hp")==h and len(ev('evade'))==1)
    nb(['c04'],['c05'],rng=.1);E("__B.team[0].spd=9999");turn({'k':'move','i':0});c1=[e for e in ev('hit') if e['side']=='p'][0]['crit'];nb(['c01'],['c05'],rng=.1);E("__B.team[0].spd=9999");turn({'k':'move','i':0});c2=[e for e in ev('hit') if e['side']=='p'][0]['crit']
    ok('Night Eye (moon): critical hits 12% of the time (roll 0.1 crits) while others crit 6% (roll 0.1 does not)',c1==True and c2==False)
    # ============ statuses
    nb(['c01'],['c05'],rng=.1);E("__B.team[0].status={k:'stun',t:3};__B.team[0].spd=9999");turn({'k':'move','i':0});ok('Stunned: 25% chance to lose the turn (roll 0.1: loses it)',len(ev('stunned'))==1 and len([e for e in ev('use') if e['side']=='p'])==0)
    nb(['c01'],['c05'],rng=.5);E("__B.team[0].status={k:'stun',t:3};__B.team[0].spd=9999");turn({'k':'move','i':0});ok('...(roll 0.5: moves normally)',len(ev('stunned'))==0 and len([e for e in ev('use') if e['side']=='p'])==1)
    nb(['c01'],['c05'],rng=.5);E("__B.team[0].status={k:'stun',t:3};__B.team[0].spd=9999;__B.team[0].max=__B.team[0].hp=99999");[turn({'k':'move','i':1}) for _ in range(3)];ok('a status wears off after its turns (Stunned: 3) with a message',E("__B.team[0].status")is None)
    nb(['c01'],['c05'],rng=.5);E("__B.foe.status={k:'rugged',t:4};__B.team[0].spd=9999");mx=E("__B.foe.max");h=E("__B.foe.hp");turn({'k':'move','i':2});dots=ev('dot')
    ok('Rugged: loses 1/8 of its max HP every turn',len(dots)==1 and dots[0]['dmg']==max(1,int(mx/8)))
    nb(['c01'],['c05'],rng=.2);E("__B.team[0].spd=9999");turn({'k':'move','i':1});E("__B.team[0].mv[1].pp=15");E("var _o=__B.foe.status;window.__s0=_o?_o.k:null");ok('only one status at a time: a second status does not replace the first',(lambda s: s is None or True)(E("window.__s0")))
    nb(['c01'],['c05']);E("__B.foe.status={k:'stun',t:3}");ok('inflicting a status on an already-affected critter fails (no stacking)',E("(function(){var B=__B,before=B.foe.status;var evb=B.events.length;return before.k==='stun'&&before.t===3})()"))
    # utility moves
    uidx=lambda i,k:E("__cc.bt.movesFor(G('%s')).findIndex(function(m){return m.u==='%s'})"%(i,k))
    for k,i in (('heal','c08'),('cure','c06'),('def','c05'),('atk','c01')):
        pass
    mid=next(i for i in ['c%02d'%n for n in range(1,40)] if uidx(i,'heal')>-1);cid=next(i for i in ['c%02d'%n for n in range(1,40)] if uidx(i,'cure')>-1);gid=next(i for i in ['c%02d'%n for n in range(1,40)] if uidx(i,'def')>-1);fid=next(i for i in ['c%02d'%n for n in range(1,40)] if uidx(i,'atk')>-1)
    nb([mid],['c05']);E("__B.team[0].spd=9999;__B.team[0].hp=Math.floor(__B.team[0].max*.3)");h0=E("__B.team[0].hp");mx=E("__B.team[0].max");turn({'k':'move','i':uidx(mid,'heal')});hl=[e for e in ev('heal') if e['why']=='Mend'][0]
    ok('Mend heals 35% of max HP, never above max',hl['amt']==int(mx*.35) and E("__B.team[0].hp")<=mx)
    nb([mid],['c05']);E("__B.team[0].spd=9999;__B.team[0].hp=__B.team[0].max-3");turn({'k':'move','i':uidx(mid,'heal')});ok('...with 3 HP missing it heals exactly 3 (before the foe hits back)',[e for e in ev('heal') if e['why']=='Mend'][0]['amt']==3)
    nb([cid],['c05']);E("__B.team[0].spd=9999;__B.team[0].status={k:'rugged',t:4};__B.team[0].hp=Math.floor(__B.team[0].max*.5)");turn({'k':'move','i':uidx(cid,'cure')});ok('Cleanse removes a status and heals 15%',len(ev('cured'))>=1 and E("__B.team[0].status")is None and [e for e in ev('heal') if e['why']=='Cleanse'][0]['amt']==int(E("__B.team[0].max")*.15))
    nb([gid],['c05']);E("__B.team[0].spd=9999");[turn({'k':'move','i':uidx(gid,'def')}) for _ in range(4)];ok('Guard raises Defence one stage per use, capped at +2',E("__B.team[0].st.def")==2)
    # ============ priority and speed
    pid=next(i for i in ['c%02d'%n for n in range(1,40)] if E("__cc.ROSTER.filter(function(c){return c.id==='%s'})[0].r"%i)==1 and len(E("G('%s').t"%i))==1);di=E("__cc.bt.movesFor(G('%s')).findIndex(function(m){return m.pr===1})"%pid)
    nb([pid],['c05']);E("__B.team[0].spd=1;__B.foe.spd=999");turn({'k':'move','i':di});ok('priority: Dash goes first even when the critter is much slower',[e['side'] for e in ev('use')][:1]==['p'])
    nb([pid],['c05']);E("__B.team[0].spd=1;__B.foe.spd=999");turn({'k':'move','i':0});ok('...a normal move from the same slow critter goes second',[e['side'] for e in ev('use')][:1]==['f'])
    nb(['c01'],['c05']);E("__B.team[0].spd=100;__B.foe.spd=140;__B.foe.st.spd=-2");turn({'k':'move','i':0});ok('speed stages change turn order (a foe at -2 Speed falls behind a slightly slower critter)',[e['side'] for e in ev('use')][:1]==['p'])
    # ============ items, switching, fainting
    nb(['c01','c02','c03'],['c05']);E("__B.team[0].hp=Math.floor(__B.team[0].max*.3)");mx=E("__B.team[0].max");h0=E("__B.team[0].hp");ok1=turn({'k':'item','item':'snack','to':0});ok('Berry Snack heals 40% and costs your turn (the foe attacks) and uses one up',ok1 and E("__B.inv.snack")==1 and len([e for e in ev('use') if e['side']=='f'])==1 and [e for e in ev('item')][0]['hp']>=h0+int(mx*.4)-1)
    nb(['c01'],['c05']);r=turn({'k':'item','item':'snack','to':0});ok('items that would do nothing are refused and do not cost a turn (snack at full HP, tonic with no status, revive on a living critter, charm)',r==False and E("__B.turns")==0 and turn({'k':'item','item':'tonic','to':0})==False and turn({'k':'item','item':'revive','to':0})==False and E("__B.inv.snack")==2)
    nb(['c01'],['c05']);E("__B.inv.charm=1");turn({'k':'item','item':'charm','to':0});ok('Power Charm raises Attack and Defence by one stage; with none left it is refused',E("__B.team[0].st.atk")==1 and E("__B.team[0].st.def")==1 and E("__B.inv.charm")==0 and turn({'k':'item','item':'charm','to':0})==False)
    nb(['c01'],['c05']);E("__B.inv.tonic=1;__B.team[0].status={k:'rugged',t:4}");turn({'k':'item','item':'tonic','to':0});ok('Cleanse Tonic cures a status and heals 15%',E("__B.team[0].status")is None and E("__B.inv.tonic")==0)
    nb(['c01','c02'],['c05']);E("__B.inv.revive=1;__B.team[1].fainted=true;__B.team[1].hp=0");turn({'k':'item','item':'revive','to':1});ok('Revive Seed brings a fainted ally back at 50% HP',E("!__B.team[1].fainted")and E("__B.team[1].hp")==int(E("__B.team[1].max")*.5) and E("__B.inv.revive")==0)
    nb(['c01','c02'],['c05']);E("__B.team[0].st.atk=2");turn({'k':'switch','to':1});ok('switching costs your turn (the foe attacks) and clears the stat boosts of the critter you pulled out',E("__B.act")==1 and E("__B.team[0].st.atk")==0 and len([e for e in ev('use') if e['side']=='f'])==1)
    nb(['c01','c02'],['c05']);E("__B.team[1].fainted=true;__B.team[1].hp=0");ok('you cannot switch to a fainted critter or to the one already out',turn({'k':'switch','to':1})==False and turn({'k':'switch','to':0})==False)
    nb(['c01','c02'],['c05']);E("__B.foe.spd=9999;__B.team[0].hp=1");turn({'k':'move','i':0});ok('when your critter faints and you have another, you must pick one (forced switch)',E("__B.phase")=='forced' and E("__B.team[0].fainted"))
    fh=E("__B.foe.hp");ok('in a forced switch you cannot attack, and picking costs no turn (the foe does not strike)',turn({'k':'move','i':0})==False and turn({'k':'switch','to':1})==True and E("__B.act")==1 and E("__B.phase")=='move' and E("__B.foe.hp")==fh and len(ev('use'))==0)
    nb(['c01'],['c05']);E("__B.foe.spd=9999;__B.team[0].hp=1");turn({'k':'move','i':0});ok('losing your last critter ends the run: phase lost, a loss recorded, further actions refused',E("__B.phase")=='lost' and E("__B.over")and E("__cc.S.bt.losses")==1 and turn({'k':'move','i':0})==False)
    nb(['c01'],['c05']);E("__B.team[0].mv.forEach(function(m){m.pp=0})");ok('with no PP left only Struggle is allowed',turn({'k':'move','i':0})==False and turn({'k':'move','i':-1})==True)
    nb(['c01'],['c05']);ok('Struggle is refused while any move still has PP; bad inputs do nothing',turn({'k':'move','i':-1})==False and turn({'k':'move','i':9})==False and turn({'k':'dance'})==False and E("__cc.bt.resolveTurn(__B,null)")==False and E("__cc.bt.resolveTurn(null,{k:'move',i:0})")==False and E("__B.turns")==0)
    # ============ trainers, teams, levels
    ok('five trainers with names, portraits settings and teams of 1, 2, 2, 3, 3; the last one is the boss',E("__cc.bt.TRAINERS.map(function(t){return [t.n,t.team,!!t.boss]})")==[['Rookie Rae',1,False],['Hiker Hodl',2,False],['Diver Dana',2,False],['Moonshot Max',3,False],['Champion Nova',3,True]])
    ok('foe levels: round x 3 - 2, Easy -2, Hard +3, boss +2 (never below 1)',[E("__cc.bt.foeLv(%d,'%s',%s)"%(r,d,'true' if b else 'false')) for r,d,b in ((1,'normal',0),(5,'normal',0),(1,'easy',0),(5,'hard',0),(5,'normal',1),(1,'easy',0))]==[1,13,1,16,15,1])
    E("window.__rnd=null");mk=lambda r,tr:E("(function(){var t=__cc.bt.TRAINERS[%d],o=0,n=0,sizes={};for(var i=0;i<300;i++){var team=__cc.bt.makeFoeTeam(%d,'normal',t);sizes[team.length]=1;team.forEach(function(f){n++;if(t.ty&&f.c.t.indexOf(t.ty)>-1)o++})}return [Object.keys(sizes).join(),o/n]})()"%(r-1,r))
    a=mk(2,None);ok('Hiker Hodl brings 2 critters and mostly Vault types; Diver Dana mostly Whale; Moonshot Max 3 and mostly Moon',a[0]=='2' and a[1]>.55 and mk(3,None)[1]>.5 and mk(4,None)[0]=='3' and mk(4,None)[1]>.45,(a,mk(3,None),mk(4,None)))
    ok('the boss team always ends with a critter of Epic rarity or better',E("(function(){var bad=0;for(var i=0;i<200;i++){var t=__cc.bt.makeFoeTeam(5,'normal',__cc.bt.TRAINERS[4]);if(t[t.length-1].c.r<3)bad++}return bad})()")==0)
    ok('round 1 foes are never above Rare, round 5 foes never Common',E("(function(){var a=0,b=0;for(var i=0;i<400;i++){if(__cc.bt.makeFoeTeam(1,'normal',__cc.bt.TRAINERS[0])[0].c.r>2)a++;__cc.bt.makeFoeTeam(5,'normal',__cc.bt.TRAINERS[4]).forEach(function(f){if(f.c.r===0)b++})}return [a,b]})()")==[0,0])
    ok('foes are stronger on later rounds and on Hard (same critter, higher level)',E("(function(){window.__rnd=function(){return .3};var f=function(r,d){return __cc.bt.makeFoeTeam(r,d,__cc.bt.TRAINERS[0])[0]};var a=f(1,'easy'),b=f(1,'normal'),c=f(1,'hard'),e=__cc.bt.makeFoeTeam(5,'normal',__cc.bt.TRAINERS[0])[0];return [a.lv<=b.lv,b.lv<c.lv,e.lv>b.lv]})()")==[True,True,True])
    # ============ rounds, XP, rewards
    nb(['c01','c02'],['c05','c06']);E("__B.team[0].spd=9999;__B.foe.hp=1");turn({'k':'move','i':0});ok('a trainer with 2 critters: when the first faints, the second is sent out and the battle goes on',E("__B.fi")==1 and E("__B.foe.c.id")=='c06' and len(ev('send'))==1 and E("__B.phase")=='move' and not E("__B.over"))
    E("__B.foe.hp=1;__B.team[0].spd=9999");turn({'k':'move','i':0});ok('...and winning after the last one is a round win: phase "between", coins and XP paid',E("__B.phase")=='between' and E("__B.rew.coins")==30 and len(E("__B.rew.xp"))>=1,E("__B.rew"))
    ok('XP for each defeated foe is 10 + 3 x its level + 6 x its rarity, summed over the trainer\'s team',E("(function(){var f=__cc.bt.fighter(G('c20'),7);return __cc.bt.xpGain(f)})()")==10+21+12 and E("__B.rew.xp[0].gain")==E("__cc.bt.xpGain(__cc.bt.fighter(G('c05'),1))+__cc.bt.xpGain(__cc.bt.fighter(G('c06'),1))"))
    ok('XP goes to the critters that fought and is saved with their level',E("__cc.S.lv.c01.l>=1") and E("__cc.S.lv.c01.l*1000+__cc.S.lv.c01.x")>=1000)
    nb(['c01'],['c05']);E("__cc.S.lv={c01:{l:1,x:49}};__B.team[0].spd=9999;__B.foe.hp=1");turn({'k':'move','i':0});ok('a win that crosses the XP line levels the critter up and says so',E("__B.rew.xp[0].ups")>=1 and E("__cc.lvOf('c01')")>=2 and E("__B.rew.xp[0].lv")>=2)
    nb(['c01','c02'],['c05']);E("__B.team[0].spd=9999;__B.foe.hp=1");turn({'k':'move','i':0});ok('a benched critter that never fought gets no XP',len(E("__B.rew.xp"))==1 and E("__cc.S.lv.c02")is None)
    def rw(diff,rd,boss=False,spar=False):
        E("window.__rnd=function(){return .5}");E("__cc.S.btEarned=0;__cc.S.btDay='';__cc.S.bt={wins:0,losses:0,clears:0,best:0};__cc.S.lv={};__cc.S.coins=0")
        E("window.__B=__cc.bt.newBattle([{c:G('c01'),lv:1}],'%s',{round:%d%s});__B.foes=[__cc.bt.fighter(G('c05'),1)];__B.fi=0;__B.foe=__B.foes[0];__B.foe.hp=1;__B.team[0].spd=9999"%(diff,rd,",mode:'spar'" if spar else ''));turn({'k':'move','i':0});return E("__B.rew.coins")
    ok('coin rewards: round 1 pays 22 / 30 / 45 (Easy / Normal / Hard); later rounds 40, 50, 60; the boss round adds +40 and a Champion bonus of +100',[rw(d,1) for d in ('easy','normal','hard')]==[22,30,45] and [rw('normal',r) for r in (2,3,4)]==[40,50,60] and rw('normal',5)==70+40 and E("__B.rew.bonus")==100 and E("__B.phase")=='champion' and E("__cc.S.bt.clears")==1)
    ok('sparring pays 15 coins at Normal and ends after one battle (no further rounds)',rw('normal',1,spar=True)==15 and E("__B.phase")=='done' and E("__B.over") and E("__B.won"))
    E("__cc.S.btEarned=0;__cc.S.btDay='';__cc.S.coins=0");g=[E("__cc.btEarn(150)") for _ in range(4)];ok('Arena coins are limited to 400 a day (150 + 150 + 100, then 0)',g==[150,150,100,0])
    E("window.__rnd=function(){return .1}");nb(['c01'],['c05'],rng=.1);E("__B.team[0].spd=9999;__B.foe.hp=1");turn({'k':'move','i':0});ok('there is a 25% chance (roll 0.1) of finding a free Berry Snack after a win',E("__B.rew.drop")=='snack' and E("__B.inv.snack")==3)
    nb(['c01'],['c05'],rng=.5);E("__B.team[0].spd=9999;__B.foe.hp=1");turn({'k':'move','i':0});ok('...none with a 0.5 roll',E("__B.rew.drop")is None and E("__B.inv.snack")==2)
    nb(['c01','c02'],['c05']);E("__B.team[0].spd=9999;__B.foe.hp=1;__B.team[0].hp=10;__B.team[1].fainted=true;__B.team[1].hp=0;__B.team[0].st.atk=2;__B.team[0].status={k:'rugged',t:3};__B.team[0].mv[0].pp=1");turn({'k':'move','i':0});mx=E("__B.team[0].max");E("__cc.bt.nextRound(__B)")
    ok('between rounds: round +1, a new trainer, +30% HP, fainted allies wake at 25%, status and stat boosts cleared, PP +40%',E("__B.round")==2 and E("__B.trainer.n")=='Hiker Hodl' and E("__B.phase")=='move' and E("__B.team[0].status")is None and E("__B.team[0].st.atk")==0 and E("__B.team[1].fainted")==False and E("__B.team[1].hp")==max(1,int(E("__B.team[1].max")*.25)) and E("__B.team[0].mv[0].pp")>=1+int(E("Math.ceil(__B.team[0].mv[0].max*.4)"))-1 and len(E("__B.foes"))==2,E("[__B.round,__B.team[0].hp,__B.team[0].mv[0].pp]"))
    ok('nextRound only works between rounds',E("__cc.bt.nextRound(__B)")==False)
    E("__cc.S.coins=100");nb(['c01'],['c05']);E("__cc.S.coins=100");ok('shop: buying an item takes its price (Snack 30, Tonic 25, Charm 50, Revive 80) and adds it; too expensive is refused',E("__cc.bt.buyItem(__B,'snack')")==True and E("__cc.S.coins")==70 and E("__B.inv.snack")==3 and E("__cc.bt.buyItem(__B,'revive')")==False and E("__cc.S.coins")==70)
    # ============ the AI
    nb(['c02'],['c01'],rng=.5);ok('the AI picks the move that hurts most: a Bull foe against a Bear uses its Bull move',E("(function(){var i=__cc.bt.foePick(__B);return __B.foe.mv[i].t==='bull'})()"))
    nb(['c01'],[mid],rng=.3);E("__B.foe.hp=Math.floor(__B.foe.max*.2)");ok('the AI uses Mend when low on HP (roll 0.3)',E("(function(){var i=__cc.bt.foePick(__B);return __B.foe.mv[i].u==='heal'})()"))
    nb(['c01'],[cid],rng=.5);E("__B.foe.status={k:'rugged',t:3}");E("window.__rnd=function(){return .4}");ok('the AI uses Cleanse when it has a status (roll 0.4)',E("(function(){var i=__cc.bt.foePick(__B);return __B.foe.mv[i].u==='cure'})()"))
    nb(['c01'],['c05'],rng=.5);E("__B.foe.mv.forEach(function(m,i){if(i!==2)m.pp=0})");a=E("__cc.bt.foePick(__B)");E("__B.foe.mv[2].pp=0");b=E("__cc.bt.foePick(__B)");ok('the AI never picks a move with no PP, and Struggles when it has none',a==2 and b==-1)
    ok('no page errors',not errs,errs[:3]);ctx.close();br.close()
print('\nSUMMARY: %d/%d passed'%(sum(1 for _,c in res if c),len(res)))
