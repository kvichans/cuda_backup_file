''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '0.5.0 2017-01-23'
ToDo: (see end of file)
'''

import  re, os, sys, datetime, json, collections
from    fnmatch         import fnmatch
import  cudatext            as app
from    cudatext        import ed
import  cudatext_cmd        as cmds
import  cudax_lib           as apx
from    .cd_plug_lib    import *

OrdDict = collections.OrderedDict

pass;                           LOG = (-2==-2)  # Do or dont logging.
pass;                           from pprint import pformat
pass;                           pf=lambda d:pformat(d,width=150)

_   = get_translation(__file__) # I18N

def parent(s, level=1):
    for ind in range(level):
        s   = os.path.dirname(s)
    return s
def upper(s):   return s.upper()
def lower(s):   return s.lower()
def title(s):   return s.title()
def width(s, w):
    return s.zfill(w)
#   return s if w<=len(s) else str(c)*(w-len(s))+s
def get_bk_path(path:str, dr_mask:str, fn_mask:str, ops='')->str:
    """ Calculate path for backup.
        Params
            path    Source path
            dr_mask How to caclucate target dir
            fn_mask How to caclucate target file name
            ops     Options
        Wait macros in dr_mask and fn_mask      (path = 'p1/p2/p3/stem.ext')
            {FILE_DIR}                          ('p1/p2/p3')
            {FILE_NAME}                         ('stem.ext')
            {FILE_STEM}                         ('stem')
            {FILE_EXT}                          ('ext')
            {YY} {YYYY}             Year    as  '17' or '2017 '
            {M} {MM} {MMM} {MMMM}   Month   as  '7' or '07' or 'jul' or 'july'
            {D} {DD}                Day     as  '7' or '07'
            {h} {hh}                Hours   as  '7' or '07' 
            {m} {mm}                Minutes as  '7' or '07' 
            {s} {ss}                Seconds as  '7' or '07' 
        Wait filters in macros                  (path = 'p1/p2/p3/stem.ext')
            {VAR|parent:level} - cut path, default level is 1
            {VAR|p}            - short name
                '{FILE_DIR}'                    'p1/p2/p3'
                '{FILE_DIR|parent:0}'           'p1/p2/p3'
                '{FILE_DIR|p}'                  'p1/p2'
                '{FILE_DIR|parent:2}'           'p1'
                '{FILE_DIR|p:2}'                'p1'
            {VAR|upper} {VAR|lower} {VAR|title} - convert case
            {VAR|u}     {VAR|l}     {VAR|t}     - short names
                '{FILE_STEM|u}'                 'STEM'
                '{FILE_EXT|title}'              'Ext'
    """
    if '{' not in dr_mask+fn_mask:
        return dr_mask + os.sep + fn_mask
    dr,fn   = os.path.split(path)
    st,ex   = fn.rsplit('.', 1) + ([] if '.' in fn else [''])
    nw      = datetime.datetime.now()
    mkv     = dict(FILE_DIR =dr
                  ,FILE_NAME=fn
                  ,FILE_STEM=st
                  ,FILE_EXT =ex
                  ,YY       =str(nw.year % 100)
                  ,YYYY     =str(nw.year)
                  ,M        =str(nw.month)
                  ,MM       =f('{:02}', nw.month)
                  ,MMM      =nw.strftime('%b').lower()
                  ,MMMM     =nw.strftime('%B')
                  ,D        =str(       nw.day)
                  ,DD       =f('{:02}', nw.day)
                  ,h        =str(       nw.hour)
                  ,hh       =f('{:02}', nw.hour)
                  ,m        =str(       nw.minute)
                  ,mm       =f('{:02}', nw.minute)
                  ,s        =str(       nw.second)
                  ,ss       =f('{:02}', nw.second)
                  )
    FILTER_REDUCTS={
        'p':'parent'
    ,   'u':'upper'
    ,   'l':'lower'
    ,   't':'title'
    }
    def fltrd_to(mcr_flt, base_val):
        """ Apply filter[s] for
                NM|func1[:par1,par2[|func2]]
            as func2(func1(base_val,par1,par2)) 
        """
        pass;                  #LOG and log('mcr_flt, base_val={}',(mcr_flt, base_val))
        flt_val     = base_val
        func_parts  = mcr_flt.split('|')[1:]
        for func_part in func_parts:
            pass;              #LOG and log('func_part={}',(func_part))
            func_nm,\
            *params = func_part.split(':')
            pass;              #LOG and log('flt_val, func_nm, params={}',(flt_val, func_nm, params))
            params  = ','+params[0] if params else ''
            func_nm = FILTER_REDUCTS.get(func_nm, func_nm)
            if '.' in func_nm:
                pass;          #LOG and log('import {}','.'.join(func_nm.split('.')[:-1]))
                importlib.import_module('.'.join(func_nm.split('.')[:-1]))
            pass;              #LOG and log('eval({})', f('{}({}{})', func_nm, repr(flt_val), params))
            try:
                flt_val = eval(f('{}({}{})', func_nm, repr(flt_val), params))
            except Exception as ex:
                flt_val = 'Error: '+str(ex)
           #for func_part
        pass;                  #LOG and log('flt_val={}',(flt_val))
        return str(flt_val)
       #fltrd_to
    for mk,mv in mkv.items():
        mkb     = '{' + mk + '}'
        if mkb in dr_mask:
            dr_mask = dr_mask.replace(mkb, mv)
        if mkb in fn_mask:
            fn_mask = fn_mask.replace(mkb, mv)
        mkf     = '{' + mk + '|'
        if mkf in dr_mask:
            dr_mask = re.sub(re.escape(mkf) + r'[^}]+}'
                        ,lambda match: fltrd_to(match.group(0).strip('{}'), mv)
                        ,dr_mask)
        if mkf in fn_mask:
            dr_mask = re.sub(re.escape(mkf) + r'[^}]+}'
                        ,lambda match: fltrd_to(match.group(0).strip('{}'), mv)
                        ,fn_mask)
    bk_path = dr_mask + os.sep + fn_mask

    if '{COUNTER' not in fn_mask:
        return bk_path
    mtch_w  = re.search('{COUNTER(\|limit:\d+)?(\|w:\d+)?}', fn_mask)
    if not mtch_w:
        return bk_path
    counter = mtch_w.group(0)
    mod_n   = int(mtch_w.group(1)[len('|limit:'):])   if mtch_w.group(1) else -1
    wdth    = int(mtch_w.group(2)[len('|w:'    ):])   if mtch_w.group(2) else 0
    pass;                      #LOG and log('fn_mask, re.compile={}',(fn_mask,fn_mask[:mtch_w.start()],f(r'(\d{})', '{'+str(wdth)+'}' if wdth else '+'),fn_mask[mtch_w.end():]))
    cntd_re = re.compile(re.escape(fn_mask[:mtch_w.start()]) 
                        +f(r'(\d{})', '{'+str(wdth)+'}' if wdth else '+') 
                        +re.escape(fn_mask[mtch_w.end():]))
    best_cnt    = -1
    best_dt     = 0
    filenames   = list(os.walk(os.path.abspath(dr_mask)))[0][2] # all files in dr_mask
    for filename in filenames:
        mtch    = cntd_re.search(filename)
        if mtch:
            pass;              #LOG and log('filename={}',(filename))
            dt  = os.path.getmtime(dr_mask + os.sep + filename)
            if best_dt < dt:
                best_dt = dt
                best_cnt= int(mtch.group(1))
    next_cnt    = 1 if best_cnt==-1         else \
                  1 if best_cnt==1+mod_n    else \
                  1+best_cnt
    cnt_s       = width(str(next_cnt), wdth)#, fllr)
    bk_path     = dr_mask + os.sep + fn_mask.replace(counter, cnt_s)
    pass;                      #LOG and log('cnt_s,counter,bk_path={}',(cnt_s,counter,bk_path))
    return bk_path
   #def get_bk_path

cfg_json= app.app_path(app.APP_DIR_SETTINGS)+os.sep+'cuda_backup_file.json'

class Command:

    def menuBK(self):#NOTE: menuBK
        pass;                   LOG and log('ok',())
        pass;                   return
        sDiffExe= r'c:\Program Files (x86)\WinMerge\WinMergeU.exe'
        sBkDir      = 'bk\\'
        nMaxBks     = 9

        sWkFile     = ed.get_filename()
        sWkDir      = os.path.dirname(sWkFile)+os.sep
        sWkFName    = os.path.basename(sWkFile)
        sWkExt      = sWkFName[sWkFName.rfind('.'):]
        sWkStem     = sWkFName[:sWkFName.rfind('.')]

        if os.path.isdir(sWkDir+sBkDir):
            root, dirs, files = list(os.walk(sWkDir+sBkDir))[0]
            prevs    = list((f,os.path.getmtime(root+f)) for f in files if f.startswith(sWkStem) and f.endswith(sWkExt))
            pass;              #log('prevs={}'.format(prevs))
            prevs    = sorted(prevs, key=lambda ft: ft[1], reverse=True)
            prevs    = list(zip(itertools.count(1), prevs))
            prevs    = prevs[:nMaxBks]
        else:
            prevs    = ()
        pass;                  #log('prevs={}'.format(prevs))
        pass;                  #app.msg_status('sWkFile={}'.format(sWkFile))
        tNow    = datetime.datetime.now()
        months  = ('jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec')
        sSfx    = '_{:02}{}{}-{:02}'.format(tNow.day, months[tNow.month-1], tNow.year%100, tNow.hour)
        sBkDSSE = sBkDir+sWkStem+sSfx+sWkExt                                        # Dir+Stem+Sfx+Ext
        what    = app.dlg_menu(app.MENU_LIST
                , '\n'.join(
                [    'Copy to     "{}"...'.format(sBkDSSE)                          # 0
                ]+[  'Diff with    "{}"'.format(sBkDir+f) for n,(f,t) in prevs]     # 1..
                ))
        pass;                  #log('what={}'.format(what))
        pass;                  #return
        if 0:pass # cases
        elif None is what: # or 1==what:
            return
        elif 0==what:
            if not os.path.isdir(sWkDir+sBkDir):
                os.mkdir(sWkDir+sBkDir)
            sBkStem    = app.dlg_input('Stem for SaveAs', sWkStem+sSfx)
            if sBkStem is None or 0==len(sBkStem): return
            sBkFile    = sWkDir+sBkDir+sBkStem+sWkExt
            shutil.copyfile(sWkFile, sBkFile)
            app.msg_status('Save copy to {}'.format(sBkFile))
        else:
            pass;              #log('what={}'.format(what))
            sBkFile    = sWkDir+sBkDir+prevs[what-1][1][0]
            pass;              #log('cmp {} with {}'.format(sBkFile, sWkFile))
            subprocess.Popen((sDiffExe, sWkFile, sBkFile))
       #def menuBK

    def on_save_pre(self, ed_self):#NOTE: on_save_pre
        if not self.save_on: return
        pass;                   LOG and log('ok',())
       #def on_save_pre

    def dlg_config(self):
        MAX_HIST= apx.get_opt('ui_max_history_edits', 20)
        def add_to_history(val:str, lst:list, max_len:int, unicase=True)->list:
            """ Add/Move val to list head. """
            lst_u = [ s.upper() for s in lst] if unicase else lst
            val_u = val.upper()               if unicase else val
            if val_u in lst_u:
                if 0 == lst_u.index(val_u):   return lst
                del lst[lst_u.index(val_u)]
            lst.insert(0, val)
            if len(lst)>max_len:
                del lst[max_len:]
            return lst
           #def add_to_history
        cf_path = ed.get_filename()
        cf_path = cf_path if os.path.isfile(cf_path) else 'p'+os.sep+'a'+os.sep+'t'+os.sep+'h'+os.sep+'file.ext'
        stores  = json.loads(open(cfg_json).read(), object_pairs_hook=OrdDict) \
                    if os.path.exists(cfg_json) and os.path.getsize(cfg_json) != 0 else \
                  OrdDict()
        DLG_W,  \
        DLG_H   = 690, 280
        svon_c  = _('Au&toCreate backup before each savind')
        v4wo_h  = _('Insert macro')
        b4wo_h  = _('Brawse dir')
        v4mo_h  = _('Insert macro')

        stores['wher_hist'] = add_to_history(self.where,      stores.get('wher_hist', []), MAX_HIST, unicase=(os.name=='nt'))
        stores['mask_hist'] = add_to_history(self.fn_mask,    stores.get('mask_hist', []), MAX_HIST, unicase=(os.name=='nt'))
        stores['whon_hist'] = add_to_history(self.where_on,   stores.get('whon_hist', []), MAX_HIST, unicase=(os.name=='nt'))
        stores['maon_hist'] = add_to_history(self.fn_mask_on, stores.get('maon_hist', []), MAX_HIST, unicase=(os.name=='nt'))
        vals    = dict(wher=self.where
                      ,mask=self.fn_mask
#                     ,dcmd=self.diff_cmd
#                     ,mxmn=self.max_in_mn
                      ,svon=self.save_on
                      ,whon=self.where_on
                      ,maon=self.fn_mask_on
                      )
        fid     = 'mask'
        while True:
            wher_l      = [s for s in stores['wher_hist'] if s]
            mask_l      = [s for s in stores['mask_hist'] if s]
            if vals['svon']:
                whon_l  = [s for s in stores['whon_hist'] if s]
                maon_l  = [s for s in stores['maon_hist'] if s]
            else:
                whon_l  = []
                maon_l  = []
            dma_path    = get_bk_path(cf_path, vals['wher'], vals['mask'])
            dmo_path    = get_bk_path(cf_path, vals['whon'], vals['maon']) if vals['svon'] else ''
            vals.update(dict(
                       d4ma=dma_path
                      ,d4mo=dmo_path
                      ))
            cnts    =[dict(           tp='lb'   ,t=5        ,l=125      ,w=180  ,cap=_('Backup with command')                       ) # 

                     ,dict(           tp='lb'   ,tid='wher' ,l=5        ,w=120  ,cap=_('Save to &dir:')                             ) # &d 
                     ,dict(cid='wher',tp='cb'   ,t=30       ,l=5+120    ,w=400  ,items=wher_l                                       ) #
                     ,dict(cid='v4wh',tp='bt'   ,tid='wher' ,l=5+120+400,w= 80  ,cap=_('Add &var')                                  ) # &v 
                     ,dict(cid='b4wh',tp='bt'   ,tid='wher' ,l=5+520+ 80,w= 25  ,cap=_('…')                                         ) #  

                     ,dict(           tp='lb'   ,tid='mask' ,l=5        ,w=120  ,cap=_('Save with &name:')                          ) # &n 
                     ,dict(cid='mask',tp='cb'   ,t=60       ,l=5+120    ,w=400  ,items=mask_l                                       ) #
                     ,dict(cid='v4ma',tp='bt'   ,tid='mask' ,l=5+120+400,w= 80  ,cap=_('Add v&ar')                                  ) # &a 
                     ,dict(cid='c4ma',tp='bt'   ,tid='mask' ,l=5+520+ 80,w= 80  ,cap=_('&Presets')                                  ) # &p
                     ,dict(           tp='lb'   ,tid='d4ma' ,l=5        ,w=120  ,cap=_('Demo: ')                                    ) # 
                     ,dict(cid='d4ma',tp='ed'   ,t= 90      ,l=5+120    ,w=480                                      ,props='1,0,1'  ) #     ro,mono,brd
                     ,dict(cid='u4ma',tp='bt'   ,tid='d4ma' ,l=5+120+480,w= 80  ,cap=_('&Update')                                   ) #  
                     
                     ,dict(           tp='--'   ,t=115      ,l=0                                                                    ) # 
                     ,dict(cid='svon',tp='ch'   ,t=130      ,l=5+120    ,w=290  ,cap=svon_c                         ,act=1          ) # &t

                     ,dict(           tp='lb'   ,tid='whon' ,l=5        ,w=120  ,cap=_('Save to d&ir:')                             ) # &i
                     ,dict(cid='whon',tp='cb'   ,t=160      ,l=5+120    ,w=400  ,items=whon_l                       ,en=vals['svon']) #
                     ,dict(cid='v4wo',tp='bt'   ,tid='whon' ,l=5+120+400,w= 80  ,cap=_('Add va&r')  ,hint=v4wo_h    ,en=vals['svon']) # &r
                     ,dict(cid='b4wo',tp='bt'   ,tid='whon' ,l=5+520+80 ,w= 30  ,cap=_('…')         ,hint=b4wo_h    ,en=vals['svon']) #  

                     ,dict(           tp='lb'   ,tid='maon' ,l=5        ,w=120  ,cap=_('Save with na&me:')                          ) # &m
                     ,dict(cid='maon',tp='cb'   ,t=190      ,l=5+120    ,w=400  ,items=maon_l                       ,en=vals['svon']) #
                     ,dict(cid='v4mo',tp='bt'   ,tid='maon' ,l=5+120+400,w= 80  ,cap=_('Ad&d var')  ,hint=v4mo_h    ,en=vals['svon']) # &d
                     ,dict(cid='c4mo',tp='bt'   ,tid='maon' ,l=5+520+80 ,w= 80  ,cap=_('Pre&sets')                  ,en=vals['svon']) # &s
                     ,dict(           tp='lb'   ,tid='d4mo' ,l=5        ,w=120  ,cap=_('Demo: ')                                    ) # 
                     ,dict(cid='d4mo',tp='ed'   ,t=220      ,l=5+120    ,w=480                                      ,props='1,0,1'  ) #     ro,mono,brd
                     ,dict(cid='u4mo',tp='bt'   ,tid='d4mo' ,l=5+120+480,w= 80  ,cap=_('&Update')                   ,en=vals['svon']) #  

                     ,dict(cid='?'   ,tp='bt'   ,t=DLG_H-30 ,l=DLG_W-255,w=80   ,cap=_('&Help')                                     ) # &h
                     ,dict(cid='!'   ,tp='bt'   ,t=DLG_H-30 ,l=DLG_W-170,w=80   ,cap=_('OK')                        ,props='1'      ) #     default
                     ,dict(cid='-'   ,tp='bt'   ,t=DLG_H-30 ,l=DLG_W-85 ,w=80   ,cap=_('Cancel')                                    ) #  
                    ]#NOTE: cfg
            aid, vals,fid,chds = dlg_wrapper(_('Configure "Backup current file"'), DLG_W, DLG_H, cnts, vals, focus_cid=fid)
            if aid is None or aid=='-':    return#while True
            
            if aid=='?':
                dlg_help()
                continue

            if aid=='svon' and vals['svon']:
                fid     = 'whon'
                continue
            
            if not vals['wher'].strip():
                app.msg_status('Fill "Save to dir"')
                fid     = 'wher'
                continue
            if not vals['mask'].strip():
                app.msg_status('Fill "Save with name"')
                fid     = 'mask'
                continue
            if not vals['whon'].strip() and vals['svon']:
                app.msg_status('Fill "Save to dir"')
                fid     = 'whon'
                continue
            if not vals['maon'].strip() and vals['svon']:
                app.msg_status('Fill "Save with name"')
                fid     = 'maon'
                continue

            if aid in ('b4wh', 'b4wo'):
                fold    = app.dlg_dir('')
                if fold is None:   continue
                id      = {'b4wh':'wher'
                          ,'b4wo':'whon'}[aid]
                vals[id]= fold
                fid     = id

            if aid in ('v4wh', 'v4ma', 'v4wo', 'v4mo'):
                prms_l  =([]
                        +[_('{FILE_DIR}             \tDirectory of current file')]
                        +[_('{FILE_NAME}            \tName of current file with extention')]
                        +[_('{FILE_STEM}            \tName of current file without extention')]
                        +[_('{FILE_EXT}             \tExtention of current file')]
                        +[_('{YY}                   \tCurrent year as 99')]
                        +[_('{YYYY}                 \tCurrent year as 9999')]
                        +[_('{M}                    \tCurrent month as 9')]
                        +[_('{MM}                   \tCurrent month as 09')]
                        +[_('{MMM}                  \tCurrent month as sep')]
                        +[_('{MMMM}                 \tCurrent month as September')]
                        +[_('{D}                    \tCurrent day as 9')]
                        +[_('{DD}                   \tCurrent day as 09')]
                        +[_('{h}                    \tCurrent hour as 9')]
                        +[_('{hh}                   \tCurrent hour as 09')]
                        +[_('{m}                    \tCurrent minute as 9')]
                        +[_('{mm}                   \tCurrent minute as 09')]
                        +[_('{s}                    \tCurrent second as 9')]
                        +[_('{ss}                   \tCurrent second as 09')]
                        )+([] if aid not in ('v4ma', 'v4mo') else []
                        +[_('{COUNTER}              \tAuto-incremented number: 1, 2, 3, …')]
                        +[_('{COUNTER|limit:5}      \tAuto-incremented number with only values: 1, 2, 3, 4, 5')]
                        +[_('{COUNTER|w:3}          \tAuto-incremented number with equal width: 001, 002, 003, …')]
                        +[_('{COUNTER|limit:99|w:2} \tAuto-incremented number: 01, 02, 03, …, 99, 01, …')]
                        )
                prm_i   = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(prms_l))
                if prm_i is None:   continue
                id      = {'v4wh':'wher'
                          ,'v4ma':'mask'
                          ,'v4wo':'whon'
                          ,'v4mo':'maon'}[aid]
                vals[id]+= prms_l[prm_i].split('\t')[0].strip()
                fid     = id
                
            if aid == 'c4ma':
                rds_l   =([]
                        +[_('name.25-01-17.ext\t{FILE_STEM}.{DD}-{MM}-{YY}.{FILE_EXT}')]
                        +[_('name_25jan17-22.ext\t{FILE_STEM}_{DD}{MMM}{YY}-{hh}.{FILE_EXT}')]
                        +[_('name-2017-12-31-23-59-59.ext\t{FILE_STEM}-{YYYY}-{MM}-{DD}-{hh}-{mm}-{ss}.{FILE_EXT}')]
                        +[_('name.25jan17-001.ext\t{FILE_STEM}.{DD}{MMM}{YY}-{COUNTER|w:3}.{FILE_EXT}')]
                        )
                rd_i    = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(rds_l))
                if rd_i is None:   continue
                vals['mask']= rds_l[rd_i].split('\t')[1]
                fid     = 'mask'
            
            if aid == 'c4mo':
                rds_l   =([]
                        +[_('name.ext.bak\t{FILE_STEM}.{FILE_EXT}.bak')]
                        +[_('name~.ext\t{FILE_STEM}~.{FILE_EXT}')]
                        +[_('name.~ext\t{FILE_STEM}.~{FILE_EXT}')]
                        +[_('name.1.ext  name.2.ext …\t{FILE_STEM}.{COUNTER}.{FILE_EXT}')]
                        +[_('name.001.ext  name.002.ext …\t{FILE_STEM}.{COUNTER|w:3}.{FILE_EXT}')]
                        +[_('name.1.ext  name.2.ext  name.3.ext  name.1.ext …\t{FILE_STEM}.{COUNTER|limit:3}.{FILE_EXT}')]
                        +[_('name.01.ext … name.99.ext  name.01.ext …\t{FILE_STEM}.{COUNTER|limit:99|w:2}.{FILE_EXT}')]
                        )
                rd_i    = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(rds_l))
                if rd_i is None:   continue
                vals['maon']= rds_l[rd_i].split('\t')[1]
                fid     = 'maon'
            
            stores['wher_hist'] = add_to_history(vals['wher'],  stores.get('wher_hist', []), MAX_HIST, unicase=(os.name=='nt'))
            stores['mask_hist'] = add_to_history(vals['mask'],  stores.get('mask_hist', []), MAX_HIST, unicase=(os.name=='nt'))
            stores['whon_hist'] = add_to_history(vals['whon'],  stores.get('whon_hist', []), MAX_HIST, unicase=(os.name=='nt'))
            stores['maon_hist'] = add_to_history(vals['maon'],  stores.get('maon_hist', []), MAX_HIST, unicase=(os.name=='nt'))
            
            if aid=='!':
                open(cfg_json, 'w').write(json.dumps(stores, indent=4))
                self.where      = vals['wher']
                self.fn_mask    = vals['mask']
                self.save_on    = vals['svon']
                self.where_on   = vals['whon']
                self.fn_mask_on = vals['maon']
                break#while
           #while
       #def dlg_config

    def __init__(self):#NOTE: init
        stores  = json.loads(open(cfg_json).read(), object_pairs_hook=OrdDict) \
                    if os.path.exists(cfg_json) and os.path.getsize(cfg_json) != 0 else \
                  OrdDict()
        self.where      = stores.get('dir',        '{FILE_DIR}/bk')
        self.fn_mask    = stores.get('mask',       '{FILE_STEM}_{DD}{MMM}{YY}-{hh}.{FILE_EXT}')
        self.diff_cmd   = stores.get('diff_cmd',   r'c:\Program Files (x86)\WinMerge\WinMergeU.exe {CF_PATH} {CP_PATH}')
        self.max_in_mn  = stores.get('max_in_menu',9)
        self.save_on    = stores.get('saveon',     False)
        self.where_on   = stores.get('saveon_dir' ,r'{FILE_DIR}\bk')
        self.fn_mask_on = stores.get('saveon_mask','{FILE_STEM}.{COUNTER|w:3}.{FILE_EXT}')
#       self.where_on   = stores.get('saveon_dir' ,'{FILE_DIR}')
#       self.fn_mask_on = stores.get('saveon_mask','{FILE_STEM}.bak.{FILE_EXT}')
    
   #class Command

def dlg_help():
    HELP_BODY   = \
_('''In the fields
    Save to dir
    Save with name
the following macros are processed.     (If path is 'p1/p2/p3/stem.ext')
    {FILE_DIR}            -             ('p1/p2/p3')
    {FILE_NAME}           -             ('stem.ext')
    {FILE_STEM}           -             ('stem')
    {FILE_EXT}            -             ('ext')
    {YY} {YYYY}           - Year    as  '17' or '2017'
    {M} {MM} {MMM} {MMMM} - Month   as  '7' or '07' or 'jul' or 'July'
    {D} {DD}              - Day     as  '7' or '07'
    {h} {hh}              - Hours   as  '7' or '07' 
    {m} {mm}              - Minutes as  '7' or '07' 
    {s} {ss}              - Seconds as  '7' or '07' 
    {COUNTER}             - Auto-incremented number
 
Filters. 
All macros can include suffix (function) to transform value.
   {Data|fun}             - gets fun({Data})
   {Data|fun:p1,p2}       - gets fun({Data},p1,p2)
   {Data|f1st:p1,p2|f2nd} - gets f2nd(f1st({Data},p1,p2))
Predefined filters are:
    p - parent for path
    u - upper: "word"     -> "WORD"
    l - lower: "WORD"     -> "word"
    t - title: "he is"    -> "He Is"
    Examples: If path is     'p1/p2/p3/stem.ext'
        {FILE_DIR}        -> 'p1/p2/p3'
        {FILE_DIR|p}      -> 'p1/p2'
        {FILE_DIR|p:2}    -> 'p1'
        {FILE_STEM|u}     -> 'STEM'
        {FILE_EXT|t}      -> 'Ext'
Predefined filters for {COUNTER} are:
    w     - set width for value
    limit - set maximum value
    Examples: 
        {COUNTER}             -> 1 -> 2 -> 3 -> 4 -> 5 -> …
        {COUNTER|w:3}         -> 001 -> 002 -> 003 -> …
        {COUNTER|limit:3}     -> 1 -> 2 -> 3 -> 1 -> 2 -> …
        {COUNTER|limit:3|w:2} -> 01 -> 02 -> 03 -> 01 -> …
''')
    dlg_wrapper(_('Help'), GAP*2+550, GAP*3+25+650,
         [dict(cid='htx',tp='me'    ,t=GAP  ,h=650  ,l=GAP          ,w=550  ,props='1,1,1' ) #  ro,mono,border
         ,dict(cid='-'  ,tp='bt'    ,t=GAP+650+GAP  ,l=GAP+550-90   ,w=90   ,cap='&Close'  )
         ], dict(htx=HELP_BODY), focus_cid='htx')
   #def dlg_help

'''
ToDo
[ ][at-kv][23jan17] Start
'''