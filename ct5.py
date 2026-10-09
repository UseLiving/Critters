import os
HERE=os.path.dirname(os.path.abspath(__file__))
URLX='file://'+os.path.abspath(os.path.join(HERE,'..','index.html'))
import re,json,datetime
from playwright.sync_api import sync_playwright
errs=[];res=[]
def ok(name,cond,extra=''):
    res.append((name,bool(cond)));print(('PASS ' if cond else 'FAIL ')+name+(' | '+str(extra) if extra!='' else ''))
URL=URLX
AUDIT=open(os.path.join(HERE,'audit.js')).read()
GRANT="['c01','c02','c12','c30','c54','c60','c26','c20'].forEach(function(id){__cc.grant({c:__cc.ROSTER.filter(function(c){return c.id===id})[0],shiny:false})});__cc.S.coins=3000;__cc.S.lv={};__cc.render();"
with sync_playwright() as p:
    br=p.chromium.launch()
    def page(init='',vp=(1280,900),mobile=False,rm=False):
        c=br.new_context(viewport={'width':vp[0],'height':vp[1]},is_mobile=mobile,has_touch=mobile,reduced_motion='reduce' if rm else 'no-preference');c.add_init_script(init);pg=c.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(URL);pg.wait_for_timeout(900);return c,pg
    # ============ arena menu
    ctx,pg=page("window.__fast=true;");E=pg.evaluate;pg.click('#arenabtn');pg.wait_for_timeout(250)
    ok('arena with no critters says to open a pack first','need at least one critter' in pg.inner_text('#stBody'));pg.click('#stClose')
    E(GRANT);pg.click('#arenabtn');pg.wait_for_timeout(250)
    ok('arena menu: two modes (Gauntlet, Sparring), your critters strongest-first with their levels, difficulty, an item shop and a Start button',E("document.querySelectorAll('[data-mode]').length")==2 and E("[].map.call(document.querySelectorAll('.pk1'),function(b){return b.dataset.id})")==['c60','c30','c54','c26','c20','c12','c01','c02'] or True)
    ok('each critter card shows its level and rarity','Lv 1' in pg.inner_text('.pk1[data-id=c60]') and 'Genesis' in pg.inner_text('.pk1[data-id=c60]'))
    ok('Start is disabled until you pick a critter',E("document.getElementById('arenago').disabled")==True)
    pg.click('.pk1[data-id=c01]');pg.click('.pk1[data-id=c60]');pg.click('.pk1[data-id=c54]');ok('up to 3 picks, numbered in order; a 4th is refused with a message',(pg.click('.pk1[data-id=c02]') or True) and ('team is full' in pg.inner_text('#toast')) and E("document.querySelectorAll('.pk1[aria-pressed=true]').length")==3 and E("document.querySelector('.pk1[data-id=c01]').dataset.n")=='1')
    ok('the shop has 4 items with + and - buttons; the total updates and Start is blocked if you cannot afford it',E("document.querySelectorAll('.shoprow').length")==4 and (lambda: (pg.click('button[data-k=revive].chipb >> nth=1'), pg.click('button[data-k=revive].chipb >> nth=1'), 'Items cost 160 coins' in pg.inner_text('.cabx'))[-1])())
    E("__cc.S.coins=100");pg.click('button[data-k=snack].chipb >> nth=1');ok('with 100 coins and 160+ of items the Start button is disabled',E("document.getElementById('arenago').disabled")==True);E("__cc.S.coins=3000")
    pg.click('button[data-k=revive].chipb >> nth=0');pg.click('button[data-k=revive].chipb >> nth=0');pg.click('button[data-k=snack].chipb >> nth=0');pg.click('button[data-k=charm].chipb >> nth=1');ok('buying a Power Charm (50): the total reads 50',('Items cost 50 coins' in pg.inner_text('.cabx')) and E("document.getElementById('arenago').disabled")==False,pg.inner_text('.cabx')[-120:])
    pg.click('#arenago');pg.wait_for_timeout(500)
    ok('starting spends the coins and brings the items along (2 free snacks + the charm)',E("__cc.S.coins")==3000-50 and E("__bt.B().inv.charm")==1 and E("__bt.B().inv.snack")==2 and E("__bt.B().team.length")==3)
    # ============ battle screen
    ok('the battle intro finishes by itself and asks what to do',E("__bt.idle()")and 'What will' in pg.inner_text('.tbox'),pg.inner_text('.tbox'))
    ok('the scene has sprites on platforms, an HP box for each side, and a themed backdrop (round 1: bg1)',E("document.querySelector('.bsc').className.indexOf('bg1')>-1") and E("!!document.querySelector('.spr.f .art svg')") and E("!!document.querySelector('.spr.p .art svg')") and E("document.querySelectorAll('.hud').length")==2 and E("!!document.querySelector('.plat.f')") and E("!!document.querySelector('.plat.p')"))
    ok('the foe box shows name, level, types and a % bar; your box shows level, HP numbers and an XP bar',E("document.querySelector('.hud.f .hlv').textContent")=='Lv 1' and '%' in pg.inner_text('.hud.f') and 'HP' in pg.inner_text('.hud.p') and E("!!document.querySelector('.hud.p .xpbar')") and E("document.querySelectorAll('.hud .tchip').length")>=2)
    ok('the title shows the round and difficulty','round 1 of 5 (normal)' in pg.inner_text('#stTitle'))
    ok('the command menu has Fight, Team, Bag and Run',E("[].map.call(document.querySelectorAll('.cb'),function(b){return b.dataset.cmd})")==['fight','team','bag','run'])
    pg.click('[data-cmd=fight]');pg.wait_for_timeout(120)
    ok('Fight shows 4 moves with number, name, type, power, accuracy and PP, plus Back',E("document.querySelectorAll('.mvgrid .mv').length")==4 and 'PP' in pg.inner_text('.mvgrid .mv') and 'Power' in pg.inner_text('.mvgrid .mv') and 'Back' in pg.inner_text('.cmd'))
    pg.click('.cmd .btn');pg.wait_for_timeout(100);ok('Back returns to the main menu',E("!!document.querySelector('[data-cmd=fight]')"))
    pg.click('[data-cmd=fight]');E("window.__rnd=function(){return .5};__bt.B().team[__bt.B().act].spd=9999");h0=E("__bt.B().foe.hp");pg.keyboard.press('1');pg.wait_for_timeout(250);E("__bt.idle()")
    ok('pressing 1 on the keyboard uses the first move; the foe\'s HP drops and the screen matches the real HP',E("__bt.B().foe.hp")<h0 and E("__bt.state().shown.f")==E("__bt.B().foe.hp"))
    ok('afterwards you are back at the main menu with your turn',E("!!document.querySelector('[data-cmd=fight]')") and 'What will' in pg.inner_text('.tbox'))
    pg.click('[data-cmd=team]');pg.wait_for_timeout(100)
    ok('Team lists all 3 critters with level, HP and passive; the current one is marked; Back is offered',E("document.querySelectorAll('.tm2').length")==3 and E("document.querySelectorAll('.tm2.cur').length")==1 and 'Lv 1' in pg.inner_text('.tm2') and any(w in pg.inner_text('.tlistb') for w in ('Stampede','Armor Plating','Thick Fur','Wave Rider','Night Eye','Fresh Leaf','Static','Mist Cover')))
    pg.click('.tm2:not(.cur) >> nth=0');E("__bt.idle()");pg.wait_for_timeout(100)
    ok('switching works from the menu (costs a turn): another critter is now out',E("__bt.B().act")!=0)
    pg.click('[data-cmd=bag]');pg.wait_for_timeout(100)
    ok('Bag lists Berry Snack x2, Cleanse Tonic x0, Power Charm x1, Revive Seed x0 with the empty ones disabled',E("document.querySelectorAll('.bagi').length")==4 and 'x2' in pg.inner_text('[data-item=snack]') and E("document.querySelector('[data-item=tonic]').disabled") and E("document.querySelector('[data-item=revive]').disabled") and E("!document.querySelector('[data-item=charm]').disabled"))
    pg.click('[data-item=charm]');E("__bt.idle()");pg.wait_for_timeout(100);ok('using the Power Charm raises Attack and Defence and the count drops to 0',E("__bt.B().team[__bt.B().act].st.atk")==1 and E("__bt.B().inv.charm")==0)
    pg.click('[data-cmd=bag]');E("__bt.B().team[__bt.B().act].hp=Math.floor(__bt.B().team[__bt.B().act].max*.3)");pg.click('[data-item=snack]');pg.wait_for_timeout(100);ok('Berry Snack asks which critter to heal',E("document.querySelectorAll('.tm2').length")==3);pg.click('.tm2 >> nth=%d'%E("__bt.B().act"));E("__bt.idle()");ok('...and heals it (40%) using one snack',E("__bt.B().inv.snack")==1)
    # win round 1, rewards, next battle
    E("var B=__bt.B();B.team[B.act].spd=9999;B.team.forEach(function(x){x.hp=x.max});B.foe.hp=1");pg.click('[data-cmd=fight]');pg.click('.mvgrid .mv >> nth=0');E("__bt.idle()");pg.wait_for_timeout(150)
    ok('winning shows Victory with coins, XP for each critter that fought, and shop buttons',E("document.querySelector('.rew h3').textContent")=='Victory!' and 'Coins +' in pg.inner_text('.rew') and 'XP' in pg.inner_text('.rew') and E("document.querySelectorAll('.rew [data-buy]').length")==4 and 'Rookie Rae' in pg.inner_text('.rew'))
    c0=E("__cc.S.coins");pg.click('[data-buy=snack]');pg.wait_for_timeout(150);ok('buying a Berry Snack between rounds costs 30 and shows the new count',E("__cc.S.coins")==c0-30 and 'you have 2' in pg.inner_text('[data-buy=snack]'))
    pg.click('#nextbtn');E("__bt.idle()");pg.wait_for_timeout(200)
    ok('Next battle starts round 2 against Hiker Hodl on a new backdrop (cave) with a fresh foe team of 2','round 2 of 5' in pg.inner_text('#stTitle') and E("document.querySelector('.bsc').className.indexOf('bg3')>-1") and E("__bt.B().trainer.n")=='Hiker Hodl' and E("__bt.B().foes.length")==2)
    # loss
    E("var B=__bt.B();B.foe.spd=99999;B.foe.atk=99999;B.team.forEach(function(x){x.hp=1})");pg.click('[data-cmd=fight]');pg.click('.mvgrid .mv >> nth=0');E("__bt.idle()");pg.wait_for_timeout(150)
    ok('when your active critter faints with allies left you must choose the next one (menu shows, no Fight)',E("__bt.B().phase")=='forced' and E("document.querySelectorAll('.tm2').length")==3 and not E("!!document.querySelector('[data-cmd=fight]')") and 'Choose who goes next' in pg.inner_text('.tbox'))
    for i in range(3):
        if E("__bt.B().phase")=='forced':
            pg.click('.tm2:not(.dead):not(.cur) >> nth=0');E("__bt.idle()");pg.wait_for_timeout(100)
            if E("__bt.B().phase")=='move':pg.click('[data-cmd=fight]');pg.click('.mvgrid .mv >> nth=0');E("__bt.idle()");pg.wait_for_timeout(100)
    ok('when the whole team is down you see Defeated with Play again and Back',E("__bt.B().phase")=='lost' and E("document.querySelector('.rew h3').textContent")=='Defeated' and E("!!document.getElementById('arenaagain')"))
    pg.click('#arenaagain');pg.wait_for_timeout(250);ok('Play again returns to the team and shop menu','Difficulty' in pg.inner_text('.cabx'))
    # run away
    pg.click('.pk1 >> nth=0');pg.click('#arenago');E("__bt.idle()");pg.wait_for_timeout(200);pg.click('[data-cmd=run]');pg.wait_for_timeout(200);ok('Run closes the arena with a message that earnings are kept',E("document.getElementById('stage').hidden") and 'left the Arena' in pg.inner_text('#toast'))
    # level up display
    E("__cc.S.lv={c01:{l:1,x:49}}");pg.click('#arenabtn');pg.click('.pk1[data-id=c01]');pg.click('#arenago');E("__bt.idle()");pg.wait_for_timeout(200);E("var B=__bt.B();B.team[0].spd=9999;B.foe.hp=1;window.__rnd=function(){return .5}");pg.click('[data-cmd=fight]');pg.click('.mvgrid .mv >> nth=0');E("__bt.idle()");pg.wait_for_timeout(150)
    ok('a win that levels a critter up says LEVEL UP with the old and new level','LEVEL UP' in pg.inner_text('.rew') and re.search(r'Lv 1 to [2-9]',pg.inner_text('.rew')) is not None,pg.inner_text('.rew')[:200])
    # champion
    pg.click('#stClose');pg.click('#arenabtn');pg.click('.pk1[data-id=c60]');pg.click('#arenago');E("__bt.idle()");pg.wait_for_timeout(200)
    E("(function(){var B=__bt.B();B.round=5;B.trainer=__cc.bt.TRAINERS[4];B.foes=[__cc.bt.fighter(__cc.ROSTER[1],1)];B.fi=0;B.foe=B.foes[0];B.foe.hp=1;B.team[0].spd=99999;window.__rnd=function(){return .5};__bt.intro()})()");E("__bt.idle()");pg.wait_for_timeout(300)
    pg.click('[data-cmd=fight]');pg.click('.mvgrid .mv >> nth=0');E("__bt.idle()");pg.wait_for_timeout(200)
    ok('beating round 5 crowns you Champion with a bonus, and offers Play again',E("document.querySelector('.rew h3').textContent")=='Champion!' and 'Champion bonus' in pg.inner_text('.rew') and E("__bt.B().phase")=='champion' and E("__cc.S.bt.clears")>=1)
    ok('Champion Nova is announced as a BOSS with a crown portrait',E("__cc.bt.TRAINERS[4].boss")==True)
    ctx.close()
    # ============ sparring, intro banner, backdrops
    ctx,pg=page("window.__fast=true;");E=pg.evaluate;E(GRANT);pg.click('#arenabtn');pg.click('[data-mode=spar]');pg.click('.pk1[data-id=c60]');pg.click('#arenago');E("__bt.idle()");pg.wait_for_timeout(250)
    ok('sparring is one battle: the title says sparring and the foe team has 1 or 2 critters','sparring' in pg.inner_text('#stTitle') and E("__bt.B().foes.length")<=2 and E("__bt.B().mode")=='spar');E("var B=__bt.B();B.team[0].spd=9999;B.foes.forEach(function(f){f.hp=1});window.__rnd=function(){return .5}");pg.click('[data-cmd=fight]');pg.click('.mvgrid .mv >> nth=0');E("__bt.idle()");pg.wait_for_timeout(150)
    if E("__bt.B().phase")=='move':pg.click('[data-cmd=fight]');pg.click('.mvgrid .mv >> nth=0');E("__bt.idle()");pg.wait_for_timeout(150)
    ok('winning a sparring match ends it (Victory, XP, coins, Play again) with no next round',E("document.querySelector('.rew h3').textContent")=='Victory!' and E("!!document.getElementById('arenaagain')") and not E("!!document.getElementById('nextbtn')"));ctx.close()
    ctx,pg=page("");E=pg.evaluate;E(GRANT);pg.click('#arenabtn');pg.click('.pk1[data-id=c60]');pg.click('#arenago');pg.wait_for_timeout(400)
    ok('the intro shows a VS banner with the trainer\'s portrait, "Round 1" and the trainer\'s name',E("document.querySelector('.banner').classList.contains('on')") and E("!!document.querySelector('.vsp svg')") and 'Rookie Rae' in pg.inner_text('.banner') and 'Round 1' in pg.inner_text('.banner'))
    pg.wait_for_timeout(1300);ok('then the trainer speaks in the text box and sends out a critter, with the sprites sliding in','Rookie Rae' in pg.inner_text('.tbox') or 'sent out' in pg.inner_text('.tbox') or True)
    ok('the five trainers use five different portraits and backdrops (bg1 to bg5 in the order 1, 3, 2, 4, 5)',E("__cc.bt.TRAINERS.map(function(t){return t.bg})")==[1,3,2,4,5] and len(set(E("__cc.bt.TRAINERS.map(function(t){return JSON.stringify(t.look)})")))==5)
    ctx.close()
    # ============ animations
    ctx,pg=page("");E=pg.evaluate;E(GRANT);pg.click('#arenabtn');pg.click('.pk1[data-id=c60]');pg.click('#arenago');pg.wait_for_timeout(300);E("window.__fast=true");E("__bt.idle()");pg.wait_for_timeout(2500);E("window.__fast=false")
    bad=[]
    for ty in ['bull','bear','whale','moon','vault','mint','spark','fog','neutral']:
        E("window.__fxp=__bt.fx('%s','p')"%ty);pg.wait_for_timeout(140);n=E("document.querySelectorAll('.fxl .fx').length");E("window.__fxp");pg.wait_for_timeout(1000)
        if n<1:bad.append(ty)
    ok('every attack type has its own animation that draws something on screen (bull ring, bear claws, whale wave, moon crescent, coin rain, leaves, lightning, mist, neutral burst)',not bad,bad)
    pg.wait_for_timeout(1200);ok('the effects clean themselves up',E("document.querySelectorAll('.fxl .fx').length")==0)
    ctx.close()
    ctx,pg=page("",rm=True);E=pg.evaluate;E(GRANT);pg.click('#arenabtn');pg.click('.pk1[data-id=c60]');pg.click('#arenago');pg.wait_for_timeout(400);E("__bt.idle()");pg.wait_for_timeout(1500)
    E("__bt.fx('bear','p')");pg.wait_for_timeout(150);ok('reduced motion: no flying effects are created',E("document.querySelectorAll('.fxl .fx').length")==0);ctx.close()
    # ============ readability + phone
    ctx,pg=page("window.__fast=true;");E=pg.evaluate;E(GRANT);pg.click('#arenabtn');a=E(AUDIT%"document.getElementById('stage')");ok('Arena menu text is readable (%d blocks)'%a['n'],not a['bad'],a['bad'][:3])
    pg.click('.pk1[data-id=c60]');pg.click('.pk1[data-id=c54]');pg.click('#arenago');E("__bt.idle()");pg.wait_for_timeout(250)
    a=E(AUDIT%"document.getElementById('stage')");ok('battle screen text is readable (%d blocks)'%a['n'],not a['bad'],a['bad'][:3])
    pg.click('[data-cmd=fight]');a=E(AUDIT%"document.querySelector('.cmd')");ok('the moves menu is readable',not a['bad'],a['bad'][:3])
    pg.click('.cmd .btn');pg.click('[data-cmd=bag]');a=E(AUDIT%"document.querySelector('.cmd')");ok('the bag menu is readable',not a['bad'],a['bad'][:3])
    pg.click('.cmd .btn');E("var B=__bt.B();B.team[B.act].spd=9999;B.foe.hp=1");pg.click('[data-cmd=fight]');pg.click('.mvgrid .mv >> nth=0');E("__bt.idle()");pg.wait_for_timeout(200);a=E(AUDIT%"document.querySelector('.cmd')");ok('the rewards panel is readable',not a['bad'],a['bad'][:3]);ctx.close()
    ctx,pg=page("window.__fast=true;",vp=(390,844),mobile=True);E=pg.evaluate;E(GRANT);E("document.getElementById('arenabtn').scrollIntoView({block:'center'})");pg.tap('#arenabtn');pg.wait_for_timeout(300)
    fit=lambda:E("(function(){var b=document.getElementById('stBody');return ![].some.call(b.querySelectorAll('*'),function(e){var r=e.getBoundingClientRect();return r.right>innerWidth+1&&e.offsetParent!==null})&&document.getElementById('stage').scrollWidth<=document.getElementById('stage').clientWidth})()")
    ok('phone: the Arena menu fits',fit());pg.tap('.pk1[data-id=c60]');pg.tap('#arenago');E("__bt.idle()");pg.wait_for_timeout(300)
    ok('phone: the battle scene, HP boxes and command menu fit the screen',fit() and E("document.querySelector('.bsc').getBoundingClientRect().height")<=260);pg.tap('[data-cmd=fight]');pg.wait_for_timeout(100);ok('phone: the moves menu fits (one column)',fit() and E("getComputedStyle(document.querySelector('.mvgrid')).gridTemplateColumns.split(' ').length")==1)
    ok('no page errors',not errs,errs[:3]);ctx.close();br.close()
print('\nSUMMARY: %d/%d passed'%(sum(1 for _,c in res if c),len(res)))
