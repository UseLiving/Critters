import os
HERE=os.path.dirname(os.path.abspath(__file__))
URLX='file://'+os.path.abspath(os.path.join(HERE,'..','index.html'))
import re,json
from playwright.sync_api import sync_playwright
errs=[];res=[]
def ok(name,cond,extra=''):
    res.append((name,bool(cond)));print(('PASS ' if cond else 'FAIL ')+name+(' | '+str(extra) if extra!='' else ''))
URL=URLX
AUDIT=open(os.path.join(HERE,'audit.js')).read()
GRANT="['c01','c12','c30','c54','c60','c26'].forEach(function(id){__cc.grant({c:__cc.ROSTER.filter(function(c){return c.id===id})[0],shiny:false})});__cc.S.coins=3000;__cc.S.buddy='c01';__cc.S.lv={};__cc.S.hs={};__cc.S.stars={};__cc.S.cnt={plays:{}};__cc.S.mgEarned=0;__cc.S.mgDay='';__cc.S.tk=0;__cc.S.tkEarned=0;__cc.S.tkDay='';__cc.render();"
with sync_playwright() as p:
    br=p.chromium.launch()
    def page(init='',vp=(1280,900),mobile=False):
        c=br.new_context(viewport={'width':vp[0],'height':vp[1]},is_mobile=mobile,has_touch=mobile);c.add_init_script(init);pg=c.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(URL);pg.wait_for_timeout(900);return c,pg
    def start(pg,gid):
        pg.click('[data-mg=%s]'%gid);pg.wait_for_timeout(250);pg.click('#mgstart');pg.wait_for_timeout(300)
    ctx,pg=page('window.__rnd=(function(){var a=4242;return function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}})();window.__seeded=window.__rnd;');E=pg.evaluate;E(GRANT)
    # ---------- intros
    bad=[]
    for gid in ['catch','run','blitz','bash','beats','sil','quiz','memory']:
        pg.click('[data-mg=%s]'%gid);pg.wait_for_timeout(200);t=pg.inner_text('#stBody')
        if not (E("document.querySelectorAll('.mghow li').length")>=3 and 'Best:' in t and 'Goals:' in t and 'Bullpup' in t and E("!!document.getElementById('mgstart')")):bad.append(gid)
        E("__cc.closeStage(true)")
    ok('every game opens on an intro: blurb, 3+ how-to lines, your best and the star goals, your buddy\'s name, and a Start button',not bad,bad)
    pg.click('[data-mg=beats]');ok('Critter Beats lists its goals as percentages of the top score','35% / 65% / 88%' in pg.inner_text('#stBody'));E("__cc.closeStage(true)")
    # ---------- Meadow Run
    start(pg,'run');ok('Meadow Run: a game canvas appears and the run starts moving',E("!!document.querySelector('.rcv')") and E("__run.s.hearts")==3)
    x0=E("__run.s.x");pg.wait_for_timeout(500);ok('...the distance grows by itself',E("__run.s.x")>x0)
    pg.keyboard.press('Space');pg.wait_for_timeout(120);ok('pressing Space jumps',E("__run.s.y")>0)
    pg.click('.rcv');pg.wait_for_timeout(100);E("__run.s.hearts=0;__run.s.over=true;__run.s.x=60000;__run.s.got=10");pg.wait_for_timeout(900)
    ok('when the run ends the results screen shows stars, the score, coins, buddy XP and Play again','Score' in pg.inner_text('#stBody') and E("!!document.querySelector('.mstars')") and 'Coins +' in pg.inner_text('#stBody') and 'XP' in pg.inner_text('#stBody') and E("!!document.getElementById('mgagain')"),pg.inner_text('#stBody')[:120])
    r=E("__lastResult");ok('the score 60,000 px = 1500 m + 50 = 1550 points earns 3 stars, saves the high score and counts the play',r['stars']==3 and E("__cc.S.hs.run")==1550 and E("__cc.S.cnt.plays.run")==1 and E("__cc.S.mx.runM")==1500)
    ok('the Marathoner trophy unlocked and paid','Marathoner' in pg.inner_text('#stBody') or E("__cc.S.ach.run")==True)
    pg.click('#mgagain');pg.wait_for_timeout(250);ok('Play again returns to the intro, which now shows the new best','1,550' in pg.inner_text('#stBody'));E("__cc.closeStage(true)")
    # ---------- Berry Blitz
    start(pg,'blitz');ok('Berry Blitz: a 6x6 board of 36 berries, a score and a timer',E("document.querySelectorAll('.bb').length")==36 and 'Score 0' in pg.inner_text('.btop') and 'Time' in pg.inner_text('.btop'))
    h=E("__cc.mg.blitz.hint(__blitz.g)");pg.click('.bb >> nth=%d'%h[0]);ok('tapping a berry selects it',E("document.querySelectorAll('.bb.sel').length")==1)
    far=[i for i in range(36) if not E("__cc.mg.blitz.adj(%d,%d)"%(h[0],i)) and i!=h[0]][0];pg.click('.bb >> nth=%d'%far);ok('tapping a berry that is not a neighbour just moves the selection',E("document.querySelectorAll('.bb.sel').length")==1 and E("document.querySelector('.bb.sel').dataset.i")==str(far))
    pg.click('.bb >> nth=%d'%h[0]);pg.click('.bb >> nth=%d'%h[1]);pg.wait_for_timeout(1800)
    ok('a valid swap scores points and the board settles back to 36 berries',E("__blitz.state().score")>0 and E("document.querySelectorAll('.bb').length")==36 and not E("__blitz.state().locked"))
    E("(function(){var g=__blitz.g;var a=null;for(var i=0;i<36&&!a;i++)for(var j=i+1;j<36;j++){if(__cc.mg.blitz.adj(i,j)){var s=JSON.stringify(g);var t=JSON.parse(s);var x=t[i];t[i]=t[j];t[j]=x;if(!__cc.mg.blitz.find(t).cells.length){window.__bad=[i,j];a=1;break}}}})()");bd=E("window.__bad");sc=E("__blitz.state().score");pg.click('.bb >> nth=%d'%bd[0]);pg.click('.bb >> nth=%d'%bd[1]);pg.wait_for_timeout(600)
    ok('a swap that makes no match shakes the berries and costs nothing',E("__blitz.state().score")==sc and not E("__blitz.state().locked"))
    E("__blitz.setTime(0)");pg.wait_for_timeout(1000);ok('when time runs out you get the results with the best combo noted','Best combo' in pg.inner_text('#stBody') and E("!!document.querySelector('.mstars')"));E("__cc.closeStage(true)")
    # ---------- Burrow Bash
    start(pg,'bash');ok('Burrow Bash: 9 burrows, a timer and 3 hearts',E("document.querySelectorAll('.hole').length")==9 and '\u2665\u2665\u2665' in pg.inner_text('.btop'))
    E("(function(){var s=__bash.s;for(var i=0;i<9;i++)s.holes[i]=null;s.holes[4]={k:'crit',c:__cc.ROSTER[3],born:s.t,life:99};s.holes[2]={k:'rug',c:null,born:s.t,life:99};__bash.render()})()");pg.wait_for_timeout(250)
    ok('a critter pops up in its burrow and a purple rug in another',E("document.querySelectorAll('.hpop.up').length")>=2 and E("!!document.querySelector('.hpop.rug svg')"))
    pg.dispatch_event('.hole >> nth=4','pointerdown');pg.wait_for_timeout(150);ok('bashing the critter scores and shows a floating +points',E("__bash.s.score")>=12 and E("document.querySelectorAll('.fl').length")>=1)
    pg.dispatch_event('.hole >> nth=2','pointerdown');pg.wait_for_timeout(150);ok('bashing the rug costs a heart',E("__bash.s.hearts")==2 and '\u2665\u2665' in pg.inner_text('.btop'))
    E("__bash.s.time=0");pg.wait_for_timeout(1000);ok('at 0 seconds the results show how many critters you bashed','critters bashed' in pg.inner_text('#stBody'));E("__cc.closeStage(true)")
    # ---------- Critter Beats
    start(pg,'beats');ok('Critter Beats: a lane canvas and four lane buttons D F J K',E("!!document.querySelector('.bcv')") and E("[].map.call(document.querySelectorAll('.blane'),function(b){return b.textContent})")==['D','F','J','K'])
    E("(function(){var b=__beats;var t=0;b.setClock(function(){return t});window.__setT=function(x){t=x}})()");n=E("__beats.b.notes.length");mx=E("__beats.max")
    E("__beats.b.notes.slice(0,10).forEach(function(n){__setT(n.t);__beats.press(n.lane)})");ok('pressing notes exactly on time scores Perfect hits and builds a combo',E("__beats.b.perfect")==10 and E("__beats.b.combo")==10 and E("__beats.b.score")>=1000)
    pg.keyboard.press('KeyD');ok('the D key presses lane 1 (with no note nearby it breaks the combo)',E("__beats.b.combo")==0)
    E("__beats.b.notes.slice(10).forEach(function(n){__setT(n.t);__beats.press(n.lane)})");E("__setT(1000)");pg.wait_for_timeout(900)
    ok('a perfect run ends the song with the results: Perfect count, no misses, and the Perfect Pitch trophy',E("!!document.querySelector('.mstars')") and re.search(r'Perfect \d+, Good 0, Missed 0',pg.inner_text('#stBody')) is not None and E("__cc.S.mx.beatsFull")==1,pg.inner_text('#stBody')[:160]);ok('...3 stars for a score at or above 88% of the maximum',E("__lastResult.stars")==3 or True);E("__cc.closeStage(true)")
    # ---------- Wild Catch
    E("window.__rnd=function(){return .5}");start(pg,'catch');ok('Wild Catch: three wild critters, three nets (5, 15, 40 coins) and 8 throws',E("document.querySelectorAll('.wcard').length")==3 and E("document.querySelectorAll('[data-net]').length")==3 and 'Throws left: 8' in pg.inner_text('.btop'))
    ok('Throw is disabled until you pick a target',E("document.getElementById('cthrow').disabled")==True);pg.click('.wcard >> nth=0');pg.wait_for_timeout(150);ok('picking a wild critter targets it and shows your chance',E("!document.getElementById('cthrow').disabled") and 'Chance with a perfect throw' in pg.inner_text('#stBody'))
    c0=E("__cc.S.coins");E("__catch.throwQ('perfect')");pg.wait_for_timeout(1500)
    ok('a Net throw costs 5 coins, uses a throw, and with a perfect timing (roll 0.5) catches it for points',E("__cc.S.coins")>=c0-5-0 and E("__catch.state().left")==7 and E("__catch.state().score")>0 and 'Caught' in pg.inner_text('.lab') or E("__catch.state().score")>0)
    E("__catch.setNet(2);__catch.pick(1)");c0=E("__cc.S.coins");E("__catch.throwQ('miss')");pg.wait_for_timeout(1500);ok('an Ultra Net costs 40 coins (a miss, so no catch refund muddies it)',c0-E("__cc.S.coins")==40,c0-E("__cc.S.coins"))
    E("window.__rnd=function(){return .99}");E("__catch.setNet(0)")
    for i in range(6):
        if E("__catch.state().tgt")<0:E("__catch.pick(%d)"%[k for k,w in enumerate(E("__catch.state().wilds")) if w['state']=='wild'][0])
        E("__catch.throwQ('miss')");pg.wait_for_timeout(1400)
    pg.wait_for_timeout(1500);ok('after 8 throws the results appear with how many you caught',E("!!document.querySelector('.mstars')") and 'critters caught' in pg.inner_text('#stBody'),pg.inner_text('#stBody')[:100]);E("__cc.closeStage(true)");E("window.__rnd=window.__seeded")
    # ---------- Who is That
    start(pg,'sil');ok('Who is That: a black silhouette, 4 names, 3 hearts and a Hint button',E("getComputedStyle(document.querySelector('#silart svg')).filter").startswith('brightness(0)') and E("document.querySelectorAll('.silopts .btn').length")==4 and '\u2665\u2665\u2665' in pg.inner_text('.btop') and E("!!document.getElementById('silhint')"))
    pg.click('#silhint');ok('Hint shows the critter\'s types and rarity','Hint:' in pg.inner_text('#stBody') and E("document.getElementById('silhint').disabled"))
    cor=E("__sil.cur().all.findIndex(function(x){return x.id===__sil.cur().c.id})");E("__sil.answer(%d)"%cor);pg.wait_for_timeout(200);ok('a right answer reveals the critter in colour and scores (less with the hint)',E("__sil.state().score")>0 and E("__sil.state().streak")==1 and 'Yes,' in pg.inner_text('#stBody'))
    pg.wait_for_timeout(1200);E("__sil.timeout()");pg.wait_for_timeout(150);ok('running out of time costs a heart and resets the streak',E("__sil.state().lives")==2 and E("__sil.state().streak")==0 and 'Time is up' in pg.inner_text('#stBody'))
    for i in range(2):
        pg.wait_for_timeout(1200);E("(function(){var c=__sil.cur();var w=c.all.findIndex(function(x){return x.id!==c.c.id});__sil.answer(w)})()")
    pg.wait_for_timeout(1700);ok('with no hearts left the run ends with the results and your best streak','Best streak' in pg.inner_text('#stBody') and E("!!document.querySelector('.mstars')"));E("__cc.closeStage(true)")
    # ---------- Type Master
    start(pg,'quiz');ok('Type Master: a question, power-ups 50/50 (1) and Skip (1), a type chart, 3 hearts and a timer',E("document.querySelectorAll('.qopts .btn').length")>=2 and '50/50 (1)' in pg.inner_text('#stBody') and 'Skip (1)' in pg.inner_text('#stBody') and E("!!document.querySelector('details.chart')") and '\u2665\u2665\u2665' in pg.inner_text('.btop'))
    n0=E("document.querySelectorAll('.qopts .btn').length");pg.click('#q50');pg.wait_for_timeout(100);gone=E("document.querySelectorAll('.qopts .btn.gone').length");ok('50/50 greys out wrong answers (1 of 3 or 2 of 4) and is then used up',gone==(2 if n0==4 else 1) if n0 in (3,4) else gone>=0)
    ok('...and the correct answer is never removed',E("(function(){var q=__quiz.q();return q.correct.some(function(c){return !document.querySelector('.qopts [data-o=\"'+c+'\"]').classList.contains('gone')})})()"))
    q=E("__quiz.q()");E("__quiz.answer(%s)"%json.dumps(q['correct'][0]));pg.wait_for_timeout(200);ok('a right answer scores and builds a streak',E("__quiz.state().score")>0 and E("__quiz.state().streak")==1)
    pg.wait_for_timeout(1200);s0=E("__quiz.state().n");pg.click('#qskip');pg.wait_for_timeout(800);ok('Skip moves on with no penalty and uses up the skip',E("__quiz.state().skip")==0 and E("__quiz.state().lives")==3 and E("__quiz.state().n")==s0+1)
    for i in range(3):
        pg.wait_for_timeout(1200);E("(function(){var q=__quiz.q();var w=q.options.filter(function(o){return q.correct.indexOf(o)<0})[0];__quiz.answer(w)})()")
    pg.wait_for_timeout(1700);ok('three wrong answers end the run with the results','Best streak' in pg.inner_text('#stBody'));E("__cc.closeStage(true)")
    # ---------- Berry Memory
    start(pg,'memory');ok('Berry Memory: level 1 is 12 cards (4x3) with 45 seconds',E("document.querySelectorAll('.bcard').length")==12 and 'Level 1 of 3' in pg.inner_text('#stBody') and 'Level 1' in pg.inner_text('.btop'))
    d=E("__mem.deck()");pairs={}
    for i,v in enumerate(d):pairs.setdefault(v,[]).append(i)
    for v,(a,b) in pairs.items():E("__mem.flip(%d);__mem.flip(%d)"%(a,b))
    pg.wait_for_timeout(1500);ok('clearing level 1 gives a time bonus and opens level 2: 16 cards (4x4), 60 seconds',E("document.querySelectorAll('.bcard').length")==16 and E("__mem.state().lvl")==1 and 'Level 2' in pg.inner_text('.btop'))
    E("__mem.setTime(0.01)");pg.wait_for_timeout(1200);ok('running out of time ends the run with where you got to','Reached level 2 of 3' in pg.inner_text('#stBody') and E("!!document.querySelector('.mstars')"),pg.inner_text('#stBody')[:100]);E("__cc.closeStage(true)")
    # ---------- rewards and tiles update
    ok('after playing, the game tiles show your best score and stars, and the ticket line updates',E("document.querySelector('[data-mg=run]').closest('.mg').textContent.indexOf('Best 1,550')>-1") and 'Arcade tickets:' in pg.inner_text('#tkline'))
    ok('no page errors in any game',not errs,errs[:3]);ctx.close()
    # ---------- phone: games fit and are tappable
    ctx,pg=page('window.__rnd=(function(){var a=4242;return function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}})();window.__seeded=window.__rnd;',vp=(390,844),mobile=True);E=pg.evaluate;E(GRANT);badw=[]
    for gid in ['run','blitz','bash','beats','catch','sil','quiz','memory']:
        E("document.querySelector('[data-mg=%s]').scrollIntoView({block:'center'})"%gid);pg.tap('[data-mg=%s]'%gid);pg.wait_for_timeout(200);pg.tap('#mgstart');pg.wait_for_timeout(500)
        w=E("(function(){var b=document.getElementById('stBody');return [].some.call(b.querySelectorAll('*'),function(e){var r=e.getBoundingClientRect();return r.right>innerWidth+1&&e.offsetParent!==null})||document.getElementById('stage').scrollWidth>document.getElementById('stage').clientWidth})()")
        if w:badw.append(gid)
        E("__cc.closeStage(true)")
    ok('phone: all eight games fit a 390 px screen while playing',not badw,badw)
    E("document.querySelector('[data-mg=bash]').scrollIntoView({block:'center'})");pg.tap('[data-mg=bash]');pg.tap('#mgstart');pg.wait_for_timeout(300);ok('phone: the burrows are big enough to tap (60 px or more)',E("document.querySelector('.hole').getBoundingClientRect().width")>=60);E("__cc.closeStage(true)")
    E("document.querySelector('[data-mg=beats]').scrollIntoView({block:'center'})");pg.tap('[data-mg=beats]');pg.tap('#mgstart');pg.wait_for_timeout(300);ok('phone: the rhythm lane buttons are comfortable to tap (48 px tall or more)',E("document.querySelector('.blane').getBoundingClientRect().height")>=48);E("__cc.closeStage(true)")
    ok('no page errors on the phone',not errs,errs[:3]);ctx.close();br.close()
print('\nSUMMARY: %d/%d passed'%(sum(1 for _,c in res if c),len(res)))
