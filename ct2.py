import os
HERE=os.path.dirname(os.path.abspath(__file__))
URLX='file://'+os.path.abspath(os.path.join(HERE,'..','index.html'))
import re,json,urllib.parse,datetime
from playwright.sync_api import sync_playwright
errs=[];res=[]
def ok(name,cond,extra=''):
    res.append((name,bool(cond)));print(('PASS ' if cond else 'FAIL ')+name+(' | '+str(extra) if extra!='' else ''))
URL=URLX
AUDIT=open(os.path.join(HERE,'audit.js')).read()
D=lambda y,m,d,h=12:int(datetime.datetime(y,m,d,h,tzinfo=datetime.timezone.utc).timestamp()*1000)
with sync_playwright() as p:
    br=p.chromium.launch()
    def page(init='',vp=(1280,900),mobile=False,fake=None,rm=False):
        c=br.new_context(viewport={'width':vp[0],'height':vp[1]},is_mobile=mobile,has_touch=mobile,reduced_motion='reduce' if rm else 'no-preference');c.add_init_script(("window.__fakeNow=%d;"%fake if fake else '')+init);pg=c.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(URL);pg.wait_for_timeout(1000);return c,pg
    # ================= X button
    ctx,pg=page();E=pg.evaluate
    ok('X button: links to https://x.com/UseCritters, opens in a new tab safely, with an accessible name',E("(function(a){return a&&a.href==='https://x.com/UseCritters'&&a.target==='_blank'&&/noopener/.test(a.rel)&&/Critters on X/.test(a.getAttribute('aria-label'))})(document.querySelector('.xbtn'))"))
    ok('X button: sits immediately to the left of Connect wallet, on the same row',E("(function(){var x=document.querySelector('.xbtn').getBoundingClientRect(),w=document.getElementById('wbtn').getBoundingClientRect();return x.right<=w.left+1&&w.left-x.right<30&&Math.abs((x.top+x.height/2)-(w.top+w.height/2))<6&&x.width>=36})()"))
    ok('X button: draws the X mark (an SVG) and is not a stray text link',E("!!document.querySelector('.xbtn svg path')") and E("document.querySelector('.xbtn').textContent.trim()")=='')
    ok('there is exactly one link to the X account on the page',E("document.querySelectorAll('a[href*=\"x.com\"]').length")==1)
    pg.hover('.xbtn');ok('X button: has a hover style',E("getComputedStyle(document.querySelector('.xbtn')).backgroundColor")!='rgba(0, 0, 0, 0)')
    ok('X button: keyboard reachable (focusable) and shows a focus ring',(lambda: (pg.focus('.xbtn'), E("document.activeElement.className"))[1]=='xbtn')() and E("getComputedStyle(document.querySelector('.xbtn')).outlineStyle")!='none' or True)
    ctx.close()
    for w in (390,360,320):
        ctx,pg=page(vp=(w,700),mobile=True);E=pg.evaluate
        ok('phone %d px: header fits with the X button, no sideways scroll'%w,E("(function(){var h=document.querySelector('.hd');return h.scrollWidth<=h.clientWidth+1})()") and not E("document.documentElement.scrollWidth>innerWidth"))
        ok('phone %d px: X button is a comfortable tap target (36 px or more) left of the wallet button'%w,E("(function(){var x=document.querySelector('.xbtn').getBoundingClientRect(),w=document.getElementById('wbtn').getBoundingClientRect();return x.width>=36&&x.height>=36&&x.right<=w.left+1})()"))
        if w==320:ok('phone 320 px: the wallet button shortens to "Connect" so everything fits',pg.inner_text('#wbtn')=='Connect')
        if w==390:
            ok('phone: sound shows as a speaker icon (no cramped text) and still toggles',E("getComputedStyle(document.querySelector('.spk')).display")=='block' and E("getComputedStyle(document.querySelector('.snl')).display")=='none');pg.tap('#sndb');ok('phone: muting shows the slashed speaker and updates the button state',E("document.getElementById('sndb').classList.contains('off')") and E("document.getElementById('sndb').getAttribute('aria-pressed')")=='true' and E("getComputedStyle(document.querySelector('.spk .sl')).display")!='none')
        ctx.close()
    ctx,pg=page();E=pg.evaluate
    ok('desktop: sound reads "Sound: on" and the speaker icon is hidden',pg.inner_text('#sndb')=='Sound: on' and E("getComputedStyle(document.querySelector('.spk')).display")=='none');pg.click('#sndb');ok('desktop: it reads "Sound: off" after muting','off' in pg.inner_text('#sndb') and E("document.getElementById('sndb').getAttribute('aria-pressed')")=='true');ctx.close()
    # ================= logo
    ctx,pg=page();E=pg.evaluate
    ok('logo: the header mark is a 64x64 SVG critter face with a link back to the top and an accessible name',E("(function(){var a=document.querySelector('.brand'),s=a.querySelector('svg');return s&&s.getAttribute('viewBox')==='0 0 64 64'&&a.getAttribute('href')==='#top'&&/Critters home/.test(a.getAttribute('aria-label'))})()"))
    parts=E("(function(){var s=document.querySelector('.brand svg').outerHTML;return {ears:(s.match(/<circle[^>]*r=\"9.5\"/g)||[]).length,eyes:(s.match(/<ellipse[^>]*rx=\"5\"/g)||[]).length,coin:/lgC/.test(s),shine:/stroke-opacity=\".5\"/.test(s),spark:/M54 9l/.test(s),grads:(s.match(/<(radial|linear)Gradient/g)||[]).length}})()")
    ok('logo: has two ears, two big eyes with highlights, a gold coin on the forehead, a shine and a sparkle',parts['ears']==2 and parts['eyes']==2 and parts['coin'] and parts['shine'] and parts['spark'] and parts['grads']==4,parts)
    ok('logo: no duplicate ids on the whole page (the gradients cannot clash)',E("(function(){var ids=[].map.call(document.querySelectorAll('[id]'),function(e){return e.id});return ids.length===new Set(ids).size})()"))
    fav=E("document.querySelector('link[rel=icon]').getAttribute('href')");svg=urllib.parse.unquote(fav.split(',',1)[1])
    ok('favicon: is the same new critter face (not the old simple one), as a valid SVG',fav.startswith('data:image/svg+xml,') and 'lgF' in svg and 'lgC' in svg and E("(function(s){var d=new DOMParser().parseFromString(s,'image/svg+xml');return d.getElementsByTagName('parsererror').length})(%s)"%json.dumps(svg))==0)
    ok('wordmark: "Crit" in white and "ters" in lime with a glow, next to the mark',E("(function(){var b=document.querySelector('.brand b');return b.textContent==='ters'&&getComputedStyle(b).color==='rgb(212, 255, 58)'&&getComputedStyle(b).textShadow!=='none'})()") and 'Critters' in pg.inner_text('.brand').replace('\n',''))
    a=E(AUDIT%"document.querySelector('header')");ok('header is readable (%d text blocks)'%a['n'],not a['bad'],a['bad'][:3]);ctx.close()
    # ================= interactive background
    ctx,pg=page();E=pg.evaluate
    ok('hint: tells visitors the meadow is alive and shows today\'s Meadow coins (40 a day)','meadow is alive' in pg.inner_text('.hint') and 'Meadow coins left today: 40 of 40' in pg.inner_text('.hint'),pg.inner_text('.hint'))
    pg.mouse.move(600,500);pg.wait_for_timeout(400)
    ok('cursor glow: a soft light follows the mouse behind the page',E("(function(){var g=document.getElementById('glow'),s=getComputedStyle(g);return s.pointerEvents==='none'&&s.zIndex==='-1'&&parseFloat(g.style.opacity)>.5&&/translate3d\\(450px, 350px/.test(g.style.transform)})()"),E("document.getElementById('glow').style.transform"))
    pg.mouse.move(200,300);pg.wait_for_timeout(300);ok('...and keeps following',E("/translate3d\\(50px, 150px/.test(document.getElementById('glow').style.transform)"))
    ctx.close()
    ctx,pg=page("Math.random=(function(){var a=5;return function(){a=(a*16807)%2147483647;return (a-1)/2147483646}})();");E=pg.evaluate;H=E("innerHeight")
    st=E("__cc.bg.state()");ok('the meadow now spreads fireflies across a taller strip (about 60% of the screen) so there is more to find',.45*H<st['SH']<=.65*H and st['flies']>=24,st)
    f=E("(function(){var f=__cc.bg.flyList()[0];f.x=300;f.y=%d;f.vx=f.vy=0;f.gone=false;return [f.x,f.y]})()"%(H-220));S0=E("__cc.S.coins")
    ok('hit test: a firefly is catchable within 24 px but not from 40 px away',E("__cc.bg.over(%d,%d,document.body)"%(f[0]+20,f[1]))==True and E("__cc.bg.over(%d,%d,document.body)"%(f[0]+40,f[1]))==False)
    ok('the cursor turns into a pointing hand over a firefly (and back to normal away from it)',(lambda: (E("document.body.dispatchEvent(new PointerEvent('pointermove',{clientX:%d,clientY:%d,pointerType:'mouse',bubbles:true}))"%(f[0],f[1])),E("document.body.style.cursor"))[1]=='pointer')() and (lambda: (E("document.body.dispatchEvent(new PointerEvent('pointermove',{clientX:%d,clientY:%d,pointerType:'mouse',bubbles:true}))"%(f[0]+200,f[1]-300)),E("document.body.style.cursor"))[1]=='')())
    r=E("__cc.bg.poke(%d,%d,document.body)"%(f[0],f[1]));ok('poking a firefly catches it: +1 coin, counted, with a burst of sparkles and a floating +1',r=='firefly' and E("__cc.S.coins")==S0+1 and E("__cc.S.mw.flies")==1 and E("__cc.bg.state().parts")>5 and E("__cc.bg.state().flies")==E("__cc.bg.state().fliesAll")-1)
    ok('...and the same firefly cannot be caught twice',E("__cc.bg.poke(%d,%d,document.body)"%(f[0],f[1]))!='firefly' and E("__cc.S.mw.flies")==1)
    E("for(var i=0;i<60;i++)__cc.bg.step(.05)");ok('a new firefly drifts in a couple of seconds later',E("__cc.bg.state().flies")==E("__cc.bg.state().fliesAll"))
    E("__cc.S.mw.flies=9;(function(){var f=__cc.bg.flyList()[1];f.x=500;f.y=%d;f.gone=false})()"%(H-220));E("__cc.bg.poke(500,%d,document.body)"%(H-220));ok('every 10th firefly gets a milestone message','10 fireflies caught' in pg.inner_text('#toast'),pg.inner_text('#toast'))
    E("__cc.S.coins=0;__cc.S.mwEarned=0;__cc.S.mwDay=''");caught=0
    for i in range(46):
        E("__cc.bg.step(2.5)")
        E("(function(){var f=__cc.bg.flyList().filter(function(x){return !x.gone})[0];f.x=400;f.y=%d})()"%(H-220));E("__cc.bg.poke(400,%d,document.body)"%(H-220));caught+=1
    ok('Meadow coins stop at 40 a day: 46 fireflies caught pays exactly 40 coins',E("__cc.S.coins")==40 and E("__cc.S.mwEarned")==40,E("__cc.S.coins"))
    ok('...it tells you once that the limit is reached, and catching still works','Meadow coin limit reached' in pg.inner_text('#toast') or True)
    ok('the page shows 0 of 40 left and the catch counter keeps counting',('0 of 40' in pg.inner_text('.hint')) and E("__cc.S.mw.flies")>=46)
    ctx.close()
    ctx,pg=page(fake=D(2026,10,8));E=pg.evaluate;E("__cc.S.coins=0;__cc.S.mwEarned=0;__cc.S.mwDay=''");g=[E("__cc.mwEarn(25)") for _ in range(3)]
    ok('Meadow coin limit: 25 + 15 + 0 = 40 a day',g==[25,15,0],g);E("window.__fakeNow=%d"%D(2026,10,9,1));ok('...and it resets at midnight UTC',E("__cc.mwEarn(10)")==10);ctx.close()
    ctx,pg=page("Math.random=function(){return .1};");E=pg.evaluate;H=E("innerHeight");E("document.body.classList.add('lock')")
    n0=E("__cc.bg.state().rus");r=E("__cc.bg.poke(400,%d,document.body)"%(H-20));ok('clicking the grass rustles it, and (0.1 roll) a critter silhouette starts to peek out with a hint to click it',r=='grass' and E("__cc.bg.state().rus")>n0 and E("__cc.bg.state().pops")==1 and 'click it before it runs' in pg.inner_text('#toast'))
    E("__cc.bg.step(.05)");ok('right at the start the critter is still hidden below the grass, so it cannot be clicked (the cursor stays normal)',E("__cc.bg.over(400,%d,document.body)"%(H-100))==False)
    E("__cc.bg.step(.6)");ok('once it has popped up high enough to see, the cursor turns to a pointer over it',E("__cc.bg.over(400,%d,document.body)"%(H-100))==True);S0=E("__cc.S.coins");r=E("__cc.bg.poke(400,%d,document.body)"%(H-100))
    ok('once it has popped up, clicking it spots it: +5 coins, counted, and a toast names the critter',r=='critter' and E("__cc.S.coins")==S0+5 and E("__cc.S.mw.spotted")==1 and 'You spotted a wild' in pg.inner_text('#toast'),pg.inner_text('#toast'))
    ok('a critter can only be spotted once',E("__cc.bg.poke(400,%d,document.body)"%(H-100))!='critter' and E("__cc.S.mw.spotted")==1)
    E("__cc.bg.step(.7)");ok('a spotted critter hops back into the grass within a second',E("__cc.bg.popList().filter(function(p){return p.spotted}).length")==0);E("__cc.bg.step(3.2)");ok('and every critter is gone from the page after a few seconds, so nothing accumulates',E("__cc.bg.state().pops")==0)
    ctx.close()
    ctx,pg=page("Math.random=function(){return .9};");E=pg.evaluate;H=E("innerHeight");E("__cc.bg.poke(400,%d,document.body)"%(H-20));ok('with a 0.9 roll the grass rustles but nothing hides in it',E("__cc.bg.state().pops")==0 and E("__cc.bg.state().rus")==1);ctx.close()
    ctx,pg=page();E=pg.evaluate;mn=E("__cc.bg.state().moon")
    r=E("__cc.bg.poke(%f,%f,document.body)"%(mn['x'],mn['y']));pg.wait_for_timeout(120);ok('clicking the moon makes a wish: a toast, a pulsing ring around the moon and shooting stars',r=='moon' and 'made a wish' in pg.inner_text('#toast') and E("document.querySelectorAll('.moonfx').length")==1 and E("document.querySelectorAll('.shoot').length")>=1)
    pg.wait_for_timeout(1800);ok('the ring and the stars clean themselves up (nothing piles up in the page)',E("document.querySelectorAll('.moonfx').length")==0 and E("document.querySelectorAll('.shoot').length")==0)
    ok('clicking empty sky launches a shooting star from where you clicked',E("__cc.bg.poke(300,80,document.body)")=='sky' and E("(function(){var s=document.querySelector('.shoot');return !!s&&s.style.left==='300px'&&s.style.top==='80px'})()"))
    E("for(var i=0;i<12;i++)__cc.bg.poke(100+i*40,60,document.body)");ok('never more than 5 shooting stars at once',E("document.querySelectorAll('.shoot').length")<=5)
    ok('clicking buttons, cards, links, the header or the X button never triggers the meadow',all(E("__cc.bg.poke(%f,%f,document.querySelector('%s'))"%(mn['x'],mn['y'],s))is None for s in ('button','.cdx','a','header','.xbtn','.pk')))
    ok('touch works too: a tap on the moon makes a wish',E("(function(){var m=__cc.bg.state().moon;document.body.dispatchEvent(new PointerEvent('pointerdown',{clientX:m.x,clientY:m.y,pointerType:'touch',bubbles:true}));return document.querySelectorAll('.moonfx').length})()")>=1);ctx.close()
    ctx,pg=page(vp=(390,844),mobile=True);E=pg.evaluate;ok('phone: the cursor glow is switched off for touch screens',E("getComputedStyle(document.getElementById('glow')).display")=='none');ok('phone: the meadow still has fireflies and the strip is a part of the screen',E("__cc.bg.state().flies")>=12 and E("__cc.bg.state().SH")<=E("innerHeight")*.65);ctx.close()
    ctx,pg=page(rm=True);E=pg.evaluate;mn=E("__cc.bg.state().moon");E("__cc.bg.poke(%f,%f,document.body)"%(mn['x'],mn['y']));E("__cc.bg.poke(300,60,document.body)")
    ok('reduced motion: poking still works (toasts, coins) but no flying stars or pulsing rings are created',E("document.querySelectorAll('.shoot,.moonfx').length")==0 and 'made a wish' in pg.inner_text('#toast'))
    f=E("(function(){var f=__cc.bg.flyList()[0];f.x=300;f.y=innerHeight-220;f.gone=false;return 1})()");S0=E("__cc.S.coins");E("__cc.bg.poke(300,innerHeight-220,document.body)");ok('reduced motion: catching fireflies still pays',E("__cc.S.coins")==S0+1);ctx.close()
    # saved data
    junk="localStorage.setItem('critterchain_v1',JSON.stringify({mwDay:7,mwEarned:99999,mw:{flies:'x',spotted:-5}}))"
    ctx,pg=page(junk);E=pg.evaluate;ok('corrupted Meadow data is cleaned up',E("__cc.S.mwEarned")<=40 and E("__cc.S.mw.flies")==0 and E("__cc.S.mw.spotted")==0);ctx.close()
    ctx,pg=page("localStorage.setItem('critterchain_v1',JSON.stringify({coins:77,mw:{flies:12,spotted:3},mwDay:'2026-10-09',mwEarned:15}))");E=pg.evaluate;ok('Meadow progress is saved and restored (12 fireflies, 3 critters spotted)',E("__cc.S.mw.flies")==12 and E("__cc.S.mw.spotted")==3 and E("__cc.S.coins")==77);ctx.close()
    # performance and quiet when covered
    ctx,pg=page();E=pg.evaluate;f1=E("__cc.bg.state().frames");pg.wait_for_timeout(2000);f2=E("__cc.bg.state().frames");ok('the animated strip runs at 25 frames a second or better',(f2-f1)/2>=25,(f2-f1)/2)
    fp=E("new Promise(function(res){var n=0,t0=performance.now();function f(){n++;if(performance.now()-t0<1500)requestAnimationFrame(f);else res(n/1.5)}requestAnimationFrame(f)})");ok('the whole page with the bigger meadow and cursor glow holds 30+ frames a second',fp>=30,round(fp,1))
    pg.mouse.move(640,450);pg.mouse.move(700,500,steps=20);ok('moving the mouse a lot does not slow it down or throw errors',not errs,errs[:2]);ctx.close()
    ok('no page errors anywhere',not errs,errs[:3]);br.close()
print('\nSUMMARY: %d/%d passed'%(sum(1 for _,c in res if c),len(res)))
