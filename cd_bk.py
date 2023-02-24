''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
    Alexey Torgashin (CudaText)
Version:
    '0.9.11 2023-02-24'
ToDo: (see end of file)
'''

import  re, os, shutil, sys, datetime, json, collections, itertools, subprocess
from    fnmatch         import fnmatch
import  cudatext            as app
from    cudatext        import ed
import  cudatext_cmd        as cmds
import  cudax_lib           as apx
from    .cd_plug_lib    import *

OrdDict = collections.OrderedDict

pass;                           LOG = (-2== 2)  # Do or dont logging.
pass;                           from pprint import pformat
pass;                           pf=lambda d:pformat(d,width=150)

_   = get_translation(__file__) # I18N

VERSION     = re.split('Version:', __doc__)[1].split("'")[1]
VERSION_V,  \
VERSION_D   = VERSION.split(' ')

CFG_JSON    = CdSw.get_setting_dir()+os.sep+'cuda_backup_file.json'
#CFG_JSON   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'cuda_backup_file.json'
MAX_HIST    = CdSw.get_opt('ui_max_history_edits', 20)
#MAX_HIST   = apx.get_opt('ui_max_history_edits', 20)

DEMO_PATH   = 'demo'+os.sep+'path'+os.sep+'demofilename.demoext'


get_proj_vars   = lambda:{}
if app.__name__=='cudatext':
    try:
        import cuda_project_man
        def get_proj_vars():
            prj_vars = cuda_project_man.project_variables()
            if prj_vars.get('ProjDir', ''):
                # Project loaded
                return prj_vars
            return {}
        test    = get_proj_vars()
    except:
        pass;                      #LOG and log('No proj vars',())
        get_proj_vars   = lambda:{}


def parent(s, level=1):
    for ind in range(level):
        s   = os.path.dirname(s)
    return s
def name(s):
    return os.path.basename(s)
def upper(s):   return s.upper()
def lower(s):   return s.lower()
def title(s):   return s.title()
def width(s, w):
    return s.zfill(w)
#   return s if w<=len(s) else str(c)*(w-len(s))+s
def get_bk_path(path:str, dr_mask:str, fn_mask:str, ops='')->str:
    """ Calculation of path for backup.
        Params
            path    Source path
            dr_mask How to caclucate target dir
            fn_mask How to caclucate target file name
            ops     Options
        Supported macros in dr_mask and fn_mask (path = 'p1/p2/p3/stem.ext')
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
            {APP_DIR}               CudaText folder path
            {APP_DRIVE}             CudaText drive/disk letter (Windows only)
        Supported filters in macros             (path = 'p1/p2/p3/stem.ext')
            {VAR|parent:level} - cut path, default level is 1
            {VAR|name}         - last segment of path
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
#       return (dr_mask + os.sep + fn_mask).strip(os.sep)
    dr,fn   = os.path.split(path)
    st,ex   = fn.rsplit('.', 1) + ([] if '.' in fn else [''])
    nw      = datetime.datetime.now()
    app_dir = app.app_path(app.APP_DIR_EXE)
    app_drv = app_dir[:2] if (os.name=='nt' and app_dir[1]==':') else ''
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
                  ,APP_DIR  =app_dir
                  ,APP_DRIVE=app_drv
                  )
    mkv.update(get_proj_vars())
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
#       return bk_path.strip(os.sep)
    mtch_w  = re.search('{COUNTER(\|lim:\d+)?(\|w:\d+)?}', fn_mask)
    if not mtch_w:
        return bk_path
#       return bk_path.strip(os.sep)
    counter = mtch_w.group(0)
    mod_n   = int(mtch_w.group(1)[len('|lim:'):])   if mtch_w.group(1) else -1
    wdth    = int(mtch_w.group(2)[len('|w:'  ):])   if mtch_w.group(2) else 0
    pass;                      #LOG and log('fn_mask, re.compile={}',(fn_mask,fn_mask[:mtch_w.start()]
                               #                                     ,f(r'(\d{})', '{'+str(wdth)+'}' if wdth else '+'),fn_mask[mtch_w.end():]))
    cntd_re = re.compile(re.escape(fn_mask[:mtch_w.start()]) 
                        +f(r'(\d{})', '{'+str(wdth)+'}' if wdth else '+') 
                        +re.escape(fn_mask[mtch_w.end():]))
    best_cnt    = -1
    best_dt     = 0
    dir_mask    = os.path.abspath(dr_mask)
    filenames   = [] if not os.path.isdir(dir_mask) else \
                    list(os.walk(dir_mask))[0][2] # all files in dr_mask
    for filename in filenames:
        mtch    = cntd_re.search(filename)
        if mtch:
            pass;              #LOG and log('filename={}',(filename))
            dt  = os.path.getmtime(dr_mask + os.sep + filename)
            if  best_dt < dt:
                best_dt = dt
                best_cnt= int(mtch.group(1))
    next_cnt    = 1 if best_cnt==-1         else \
                  1 if best_cnt==1+mod_n    else \
                  1+best_cnt
    cnt_s       = width(str(next_cnt), wdth)
    bk_path     = dr_mask + os.sep + fn_mask.replace(counter, cnt_s)
    pass;                      #LOG and log('cnt_s,counter,bk_path={}',(cnt_s,counter,bk_path))
    return bk_path
#   return bk_path.strip(os.sep)
   #def get_bk_path

def save_cfg(stores):
    open(CFG_JSON, 'w').write(json.dumps(stores, indent=4))
def load_cfg(modify=False, ops=''):
    stores      = json.loads(open(CFG_JSON).read(), object_pairs_hook=OrdDict) \
                    if os.path.exists(CFG_JSON) and os.path.getsize(CFG_JSON) != 0 else \
                  OrdDict()
    all_vrns    = stores.setdefault('all_vrns', [])     \
                    if modify else                      \
                  stores.get(       'all_vrns', [])
    vrn_num     = stores.setdefault('vrn_num' , 0)      \
                    if modify else                      \
                  stores.get(       'vrn_num' , 0)
    vrn_data    = setdefault(all_vrns, vrn_num, OrdDict())

    if ops=='vrn_data':
        return vrn_data
    return stores, all_vrns, vrn_num, vrn_data
   #def load_cfg

class Command:

    def copy_bk_or_compare(self):#NOTE: menuBK
        cf_path     = ed.get_filename()
        if not cf_path: return
        if ed.get_prop(app.PROP_MODIFIED) and \
            app.msg_box(  _('Text modified!'
                          '\nThe command will use old state.'
                        '\n\nContinue?')
                           ,app.MB_YESNO+app.MB_ICONQUESTION
                           )!=app.ID_YES:   return 

        vrn_data    = load_cfg(ops='vrn_data')
        if not vrn_data.get('mask'):
            if not self.dlg_config():   return
            vrn_data= load_cfg(ops='vrn_data')

        sv_path = get_bk_path(cf_path, vrn_data['wher'], vrn_data['mask'])
        pass;                   LOG and log('sv_path={}',(sv_path))
        sv_dir, \
        sv_fn   = os.path.split(sv_path)

        if not os.path.isdir(sv_dir):
            if app.msg_box(f(_('Backup File needs to create dir\n{}'), sv_dir)
                          ,app.MB_OKCANCEL+app.MB_ICONQUESTION)!=app.ID_OK:  return
            try:
                os.makedirs(sv_dir)
            except:
                app.msg_status(f(_('Cannot create dir "{}"'), sv_dir))
                return
        prevs_a = ()
        files   = list(os.walk(sv_dir))[0][2]
        mask    = vrn_data['mask']
        pass;                   LOG and log('mask={}',(mask))
        cf_dir, \
        cf_fn   = os.path.split(cf_path)
        cf_stem,\
        cf_ext  = cf_fn.rsplit('.', 1) + ([] if '.' in cf_fn else [''])
        if mask.startswith('{FILE_STEM}') and \
           mask.endswith(  '.{FILE_EXT}'):
            mask    = re.escape(cf_stem) + r'.*\.' + re.escape(cf_ext)
        else:
            mask    = mask.replace('.'              , r'\.')
            mask    = mask.replace('{FILE_STEM}'    ,         re.escape(cf_stem))
            mask    = mask.replace(r'\.{FILE_EXT}'  , r'.*\.'+re.escape(cf_ext))
            mask    = mask.replace('{FILE_EXT}'     ,         re.escape(cf_ext))
            mask    = mask.replace('{YY}'           , r'\d\d')
            mask    = mask.replace('{YYYY}'         , r'\d\d\d\d')
            mask    = mask.replace('{M}'            , r'\d')
            mask    = mask.replace('{MM}'           , r'\d\d')
            mask    = mask.replace('{MMM}'          , r'\w\w\w')
            mask    = mask.replace('{D}'            , r'\d')
            mask    = mask.replace('{DD}'           , r'\d\d')
            mask    = mask.replace('{h}'            , r'\d')
            mask    = mask.replace('{hh}'           , r'\d\d')
            mask    = mask.replace('{m}'            , r'\d')
            mask    = mask.replace('{mm}'           , r'\d\d')
            mask    = mask.replace('{s}'            , r'\d')
            mask    = mask.replace('{ss}'           , r'\d\d')
            mask    = re.sub(r'([^}]){MMMM}([^{])'          , r'\1\\w+\2', mask)
            mask    = re.sub(r'([^}]){COUNTER[^}]*}([^{])'  , r'\1\\d+\2', mask)
        pass;                   LOG and log('mask={}',(mask))
        re_mask = re.compile('^'+mask+'$')

        opdf    = vrn_data.get('opdf', self.def_opdf)
        if opdf:
            prevs_a = list( (f, os.path.getmtime(sv_dir+os.sep+f)) 
                            for f in files 
                            if re_mask.match(f)
                        )
            pass;              #log('prevs_a={}', prevs_a)
            prevs_a = sorted(prevs_a, key=lambda ft: ft[1], reverse=True)
            prevs_a = list(zip(itertools.count(1), prevs_a))
            dfmx    = vrn_data.get('dfmx', self.def_dfmx)
            prevs   = prevs_a[:dfmx] if dfmx else prevs_a
            pass;                  #log('prevs={}', prevs)
            what_p  = -1
            if prevs:
                for one_two in range(2):
                    CdSw.msg_status_alt(f(_('Backup dir: {}'), sv_dir), 60)
        #           app.msg_status(f(_('Backup dir: {}'), sv_dir))
                    menu_l  =([  f(_('Copy to…\t{}'), sv_fn)                        ]     # 0
                            + [  ':::::::::::'                                      ]     # skip
                            + [  f(_('Diff with\t{}'), fn) for n,(fn,t) in prevs    ]     # 2..
                            +([] if len(prevs_a)==len(prevs) else []
                            + [  _('more…')+f('\t({})',len(prevs_a)-len(prevs))     ]     # all
                            ))
                    what_m  = CdSw.dlg_menu(app.DMENU_LIST, '\n'.join(menu_l))
#                   what_m  = CdSw.dlg_menu(CdSw.MENU_LIST, '\n'.join(menu_l))
                    CdSw.msg_status_alt('', 0)
        #           app.msg_status('')
                    if None is what_m or menu_l[what_m]==':::::::::::':
                        return
                    if 0==what_m:
                        what_p  = -1
                        break
                    if menu_l[what_m].startswith(_('more…')):
                        prevs   = prevs_a
                        continue
                    what_p  = what_m - 2 
                    break
        pass;                  #log('what={}'.format(what))
        pass;                  #return
        if opdf and prevs and what_p!=-1:
            # Compare
            pass;              #log('what={}'.format(what))
            old_path    = sv_dir + os.sep + prevs[what_p][1][0]
            app_dir     = app.app_path(app.APP_DIR_EXE)
            app_drv     = app_dir[:2] if (os.name=='nt' and app_dir[1]==':') else ''
            diff        = vrn_data['diff']
            diff        = diff.replace('{BACKUP_PATH}'  , old_path)
            diff        = diff.replace('{COPY_PATH}'    , old_path)
            diff        = diff.replace('{CURRENT_PATH}' , cf_path)
            diff        = diff.replace('{FILE_PATH}'    , cf_path)
            diff        = diff.replace('{APP_DIR}'      , app_dir)
            diff        = diff.replace('{APP_DRIVE}'    , app_drv)
            pass;               LOG and log('diff={}', (diff))
            print('Backup File runs:', diff)
            subprocess.Popen(diff, shell=vrn_data['dfsh'])
            return
        
        # Copy
        while True:
            CdSw.msg_status_alt(f(_('Backup dir: {}'), sv_dir), 60)
            sv_fn    = app.dlg_input(_('Create backup with name'), sv_fn)
            CdSw.msg_status_alt('', 0)
            if sv_fn is None or 0==len(sv_fn): return
            if not os.path.isfile(sv_dir+os.sep+sv_fn):
                break#while
            if app.msg_box(f(_('Overwrite file\n{}\n?'), '    '+(sv_dir+os.sep+sv_fn).replace(os.sep, os.sep+'\n    '))
                           ,app.MB_YESNO+app.MB_ICONQUESTION
                           )==app.ID_YES:
                break#while
        try:
            shutil.copyfile(cf_path, sv_dir+os.sep+sv_fn)
            pass;               LOG and log('src, trg={}',(cf_path, sv_dir+os.sep+sv_fn))
        except:
            app.msg_status(f(_('Cannot create backup copy: invalid path "{}"'), sv_dir+os.sep+sv_fn))
            return
        app.msg_status(_('Copy to {}').format(sv_dir+os.sep+sv_fn))
       #def copy_bk_or_compare

    def on_save_pre(self, ed_self):#NOTE: on_save_pre
        pass;                  #LOG and log('',())
        if not self.save_on: return
        cf_path = ed.get_filename()
        if not cf_path: return
        pass;                  #LOG and log('??',())
        vrn_data= load_cfg(ops='vrn_data')
        if  not vrn_data: return
        sv_path = get_bk_path(cf_path, vrn_data['whon'], vrn_data['maon'])
        pass;                  #LOG and log('sv_path={}',(sv_path))
        sv_dir, \
        sv_fn   = os.path.split(sv_path)
        if not os.path.isdir(sv_dir):
            if re.search(r'{\w+}', sv_dir):
                CdSw.msg_status_alt(f(_('Cannot create backup copy: invalid dir "{}"'), sv_dir), 6)
                return
            try:
                os.makedirs(sv_dir)
            except:
                CdSw.msg_status_alt(f(_('Cannot create backup copy: invalid dir "{}"'), sv_dir), 6)
                return
        try:
            shutil.copyfile(cf_path, sv_path)
        except:
            CdSw.msg_status_alt(f(_('Cannot create backup copy: invalid path "{}"'), sv_path), 6)
            return
        CdSw.msg_status_alt(f(_('Create backup: {}'), sv_path), 3)
        pass;                   LOG and log('ok',())
       #def on_save_pre

    def dlg_config(self):
        def add_to_history(val:str, lst:list, max_len:int, unicase=True)->list:
            """ Add/Move val to list head. """
            if not val.strip():
                return lst
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
        
        # Currenf file
        cf_path = ed.get_filename()
        cf_path = cf_path if os.path.isfile(cf_path) else DEMO_PATH
        
        # Stored options and its copies
        #   Level 0: into file CFG_JSON             (between calls)
        #   Level 1: into stores, all_vrns, vrn_*   (content of/for file)
        #   Level 2: into vds                       (all for current variant)
        #   Level 3: into vals                      (visibled)
        stores, \
        all_vrns,\
        vrn_num,\
        vrn_data= load_cfg(modify=True)
        if vrn_num==0 and len(vrn_data)==0:
            vrn_data['wher']    = self.def_wher
            vrn_data['mask']    = self.def_mask
            vrn_data['opdf']    = self.def_opdf
            vrn_data['diff']    = self.def_diff
            vrn_data['dfmx']    = self.def_dfmx
            vrn_data['svon']    = self.def_svon
            vrn_data['whon']    = self.def_whon
            vrn_data['maon']    = self.def_maon
        vds     = vrn_data.copy()
        vds.setdefault('opdf', self.def_opdf)
        vds.setdefault('diff', self.def_diff)
        vds.setdefault('dfsh', self.def_dfsh)
        vds.setdefault('dfmx', self.def_dfmx)

        DLG_W,  \
        DLG_H   = 800, 340
        svon_c  = _('Au&to-create backup before each saving')
        v4wo_h  = _('Insert macro')
        b4wo_h  = _('Browse dir')
        v4mo_h  = _('Insert macro')
        diff_h  = _('Command to compare (and merge) current file with one of its copy.'
                  '\r    {COPY_PATH} - path of copy,'
                  '\r    {FILE_PATH} - path of current file.')
        dfmx_h  = _('How many copies will be shown to compare'
                  '\r    0 - all')
        
        stores['wher_hist'] = add_to_history(vds['wher'], stores.get('wher_hist', []), MAX_HIST, unicase=(os.name=='nt'))
        stores['mask_hist'] = add_to_history(vds['mask'], stores.get('mask_hist', []), MAX_HIST, unicase=(os.name=='nt'))
        stores['diff_hist'] = add_to_history(vds['diff'], stores.get('diff_hist', []), MAX_HIST, unicase=(os.name=='nt'))
        stores['whon_hist'] = add_to_history(vds['whon'], stores.get('whon_hist', []), MAX_HIST, unicase=(os.name=='nt'))
        stores['maon_hist'] = add_to_history(vds['maon'], stores.get('maon_hist', []), MAX_HIST, unicase=(os.name=='nt'))
        adva    = stores.get('adva', False)
        fid     = 'mask'
        while True:
            vrns_l  = ['#'+str(1+n) for n in range(len(all_vrns))] + [_('Add variant'), _('Clone variant'), _('Remove variant')]
            wher_l  = [s for s in stores['wher_hist'] if s]
            mask_l  = [s for s in stores['mask_hist'] if s]
            diff_l  = [s for s in stores['diff_hist'] if s]
            whon_l  = [s for s in stores['whon_hist'] if s]
            maon_l  = [s for s in stores['maon_hist'] if s]


            opdf    = vds['opdf']
            # vds -> vals
            vals    = dict(wher=vds['wher']
                          ,mask=vds['mask']
                          ,svon=vds['svon']
                          )
            if vds['svon']:
                vals.update(dict(
                           whon=vds['whon']
                          ,maon=vds['maon']
                          ))
            if adva and not vds['svon']:
                dma_path= get_bk_path(cf_path, vals['wher'], vals['mask'])
                vals.update(dict(
                           d4ma=dma_path
                          ,opdf=opdf
                          ,diff=vds['diff']
                          ,dfsh=vds['dfsh']
                          ,dfmx=vds['dfmx']
                          ,vrns=vrn_num
                          ))
            if adva and vds['svon']:
                dma_path= get_bk_path(cf_path, vals['wher'], vals['mask'])
                dmo_path= get_bk_path(cf_path, vals['whon'], vals['maon'])
                vals.update(dict(
                           d4ma=dma_path
                          ,opdf=opdf
                          ,diff=vds['diff']
                          ,dfsh=vds['dfsh']
                          ,dfmx=vds['dfmx']
                          ,d4mo=dmo_path
                          ,vrns=vrn_num
                          ))
            
            g1          = 0 if adva    else -60
            g2          = apx.icase(not adva and not vds['svon'], -120
                                   ,not adva and     vds['svon'],  -60
                                   ,    adva and not vds['svon'], -120
                                   ,    adva and     vds['svon'],  -30)
            DLGH,DLGW   = DLG_H+  g1+g2, DLG_W
            pass;              #LOG and log('vals={}',(vals))
            cnts=([]
                    +([] 
                 +[dict(           tp='lb'  ,t=  5      ,l=5+120        ,w=180  ,cap=_('Options for manual backup')                 )] # 
                    if not adva else []                        
                 +[dict(           tp='lb'  ,tid='opdf' ,l=5+120        ,w=180  ,cap=_('Options for manual backup')                 )] # 
                 +[dict(cid='opdf',tp='ch'  ,t=  3      ,l=5+400        ,w=170  ,cap=_('and to c&ompare')           ,act=1          )] # &o
                    )
                 +[dict(           tp='lb'  ,tid='wher' ,l=5            ,w=120  ,cap=_('Copy to &dir:')                             )] # &d 
                 +[dict(cid='wher',tp='cb'  ,t= 25      ,l=5+120        ,w=500  ,items=wher_l                                       )] #
                 +[dict(cid='v4wh',tp='bt'  ,tid='wher' ,l=5+120+500+ 5 ,w= 80  ,cap=_('Add &var')                                  )] # &v 
                 +[dict(cid='b4wh',tp='bt'  ,tid='wher' ,l=5+620+ 80+10 ,w= 35  ,cap=_('…')                                         )] #  
                 +[dict(           tp='lb'  ,tid='mask' ,l=5            ,w=120  ,cap=_('Planned &name:')                            )] # &n 
                 +[dict(cid='mask',tp='cb'  ,t= 55      ,l=5+120        ,w=500  ,items=mask_l                                       )] #
                 +[dict(cid='v4ma',tp='bt'  ,tid='mask' ,l=5+120+500+ 5 ,w= 80  ,cap=_('Add v&ar')                                  )] # &a 
                 +[dict(cid='c4ma',tp='bt'  ,tid='mask' ,l=5+620+ 80+10 ,w= 80  ,cap=_('&Presets')                                  )] # &p
                    +([] if not adva else []                        
                 +[dict(           tp='lb'  ,tid='d4ma' ,l=5            ,w=120  ,cap=_('Demo: ')                    ,en=opdf        )] # 
                 +[dict(cid='d4ma',tp='ed'  ,t= 85      ,l=5+120        ,w=580+5                            ,en=opdf, ex0='1', ex1='0', ex2='1'  )] #     ro,mono,brd
                 +[dict(cid='u4ma',tp='bt'  ,tid='d4ma' ,l=5+120+580+10 ,w= 80  ,cap=_('&Update')                   ,en=opdf        )] #  
                 +[dict(           tp='lb'  ,tid='diff' ,l=5            ,w=120  ,cap=_('Di&ff command:'),hint=diff_h,en=opdf        )] # &f 
                 +[dict(cid='diff',tp='cb'  ,t=115      ,l=5+120        ,w=400  ,items=diff_l                       ,en=opdf        )] #
                 +[dict(cid='dfsh',tp='ch'  ,tid='diff' ,l=5+520+ 30    ,w= 90  ,cap=_('Shell')                     ,en=opdf        )] # &t
                 +[dict(           tp='lb'  ,tid='diff' ,l=5+640        ,w=100  ,cap=_('Ma&x shown:')   ,hint=dfmx_h,en=opdf        )] # &x
                 +[dict(cid='dfmx',tp='sp-ed',tid='diff',l=5+630+100+10 ,w= 50                              ,en=opdf, ex0='0', ex1='20', ex2='1' )] #
                    )
                 +[dict(           tp='--'  ,t=140+g1   ,l=0                                                                        )] # 
                 +[dict(cid='svon',tp='ch'  ,t=155+g1   ,l=5+120        ,w=290  ,cap=svon_c                         ,act=1          )] # &t
                    +([] if not vds['svon'] else []                        
                 +[dict(           tp='lb'  ,tid='whon' ,l=5            ,w=120  ,cap=_('Copy to d&ir:')                             )] # &i
                 +[dict(cid='whon',tp='cb'  ,t=175+g1   ,l=5+120        ,w=500  ,items=whon_l                                       )] #
                 +[dict(cid='v4wo',tp='bt'  ,tid='whon' ,l=5+120+500+ 5 ,w= 80  ,cap=_('Add va&r')  ,hint=v4wo_h                    )] # &r
                 +[dict(cid='b4wo',tp='bt'  ,tid='whon' ,l=5+620+80 +10 ,w= 35  ,cap=_('…')         ,hint=b4wo_h                    )] #  
                 +[dict(           tp='lb'  ,tid='maon' ,l=5            ,w=120  ,cap=_('Copy with na&me:')                          )] # &m
                 +[dict(cid='maon',tp='cb'  ,t=205+g1   ,l=5+120        ,w=500  ,items=maon_l                                       )] #
                 +[dict(cid='v4mo',tp='bt'  ,tid='maon' ,l=5+120+500+ 5 ,w= 80  ,cap=_('Ad&d var')  ,hint=v4mo_h                    )] # &d
                 +[dict(cid='c4mo',tp='bt'  ,tid='maon' ,l=5+620+80 +10 ,w= 80  ,cap=_('Pre&sets')                                  )] # &s
                    +([] if not adva else []                        
                 +[dict(           tp='lb'  ,tid='d4mo' ,l=5            ,w=120  ,cap=_('Demo: ')                                    )] # 
                 +[dict(cid='d4mo',tp='ed'  ,t=235      ,l=5+120        ,w=580+5                                    ,ex0='1', ex1='0', ex2='1'  )] #     ro,mono,brd
                 +[dict(cid='u4mo',tp='bt'  ,tid='d4mo' ,l=5+120+580+10 ,w= 80  ,cap=_('&Update')                                   )] #  
                    )
                    )
                 +[dict(           tp='--'  ,t=DLGH-45  ,l=0                                                                        )] # 
                 +[dict(cid='more',tp='bt'  ,t=DLGH-30  ,l=5            ,w=100  ,cap=_('L&ess <<') if adva else _('Mor&e >>')       )] # &e
                    +([] if not adva else []                        
                 +[dict(           tp='lb'  ,tid='-'    ,l=5+120        ,w= 80  ,cap=_('Variant&:')                                 )] # &:
                 +[dict(cid='vrns',tp='cb-ro',tid='-'   ,l=5+120+ 80    ,w=160  ,items=vrns_l                       ,act=1          )] #
                    )
                 +[dict(cid='?'   ,tp='bt'  ,tid='-'    ,l=DLGW-260     ,w=80   ,cap=_('&Help')                                     )] # &h
                 +[dict(cid='!'   ,tp='bt'  ,tid='-'    ,l=DLGW-175     ,w=80   ,cap=_('OK')                        ,ex0='1'      )] #     default
                 +[dict(cid='-'   ,tp='bt'  ,t=DLGH-30  ,l=DLGW-90      ,w=80   ,cap=_('Cancel')                                    )] #  
                )#NOTE: cfg
            aid, vals,fid,chds = dlg_wrapper(f(_('Configure "Backup File" ({})'), VERSION_V), DLGW, DLGH, cnts, vals, focus_cid=fid)
            if aid is None or aid=='-':    return#while True
            pass;              #LOG and log('vals={}',(vals))
            
            vds.update({k:v for (k,v) in vals.items() if k in ('wher', 'mask', 'opdf', 'diff', 'dfsh', 'dfmx', 'svon', 'whon', 'maon')})
            if aid=='more':
                adva    = not adva
            if aid=='?':
                dlg_help()
                continue

            if aid=='vrns':
                vrn_data.update(vds)
                vrn_act = 'rem'     if vals['vrns']==len(vrns_l)-1 else \
                          'cln'     if vals['vrns']==len(vrns_l)-2 else \
                          'add'     if vals['vrns']==len(vrns_l)-3 else \
                          'shw'
                if vrn_act!='rem' and not vals['wher'].strip():
                    app.msg_status(_('Fill "Copy to dir"'))
                    fid     = 'wher'
                    continue
                if vrn_act!='rem' and not vals['mask'].strip():
                    app.msg_status(_('Fill "Planned name"'))
                    fid     = 'mask'
                    continue
                if vrn_act!='rem' and vds['svon'] and not vals['whon'].strip():
                    app.msg_status(_('Fill "Copy to dir"'))
                    fid     = 'whon'
                    continue
                if vrn_act!='rem' and vds['svon'] and not vals['maon'].strip():
                    app.msg_status(_('Fill "Copy with name"'))
                    fid     = 'maon'
                    continue

                pass;          #LOG and log('vrn_act={}',(vrn_act))
                if False:pass
                elif vrn_act=='rem':               # Remove
                    pass;      #LOG and log('?? Remove len=',(len(all_vrns)))
                    if len(all_vrns)==1 or app.msg_box( f(_('Remove Variant #{}?'), 1+vrn_num)
                                  , app.MB_YESNO+app.MB_ICONQUESTION)!=app.ID_YES:
                        pass;  #LOG and log('eject Remove',())
                        continue
                    all_vrns.pop(vrn_num)
                    vrn_num     = min(vrn_num, len(all_vrns)-1)
                elif vrn_act=='cln':               # Clone
                    all_vrns   += [vrn_data.copy()]
                    vrn_num     = len(all_vrns)-1
                elif vrn_act=='add':               # Add
                    all_vrns   += [{'wher': '',
                                    'mask': '',
                                    'opdf': False,
                                    'diff': '',
                                    'dfsh': False,
                                    'dfmx': 0,
                                    'svon': self.def_svon,
                                    'whon': '',
                                    'maon': '',
                                    }]
                    vrn_num     = len(all_vrns)-1
                else:                                           # Switch
                    vrn_num     = vals['vrns']
                pass;          #LOG and log('all_vrns={}',(all_vrns))
                vrn_data        = all_vrns[vrn_num]
                vds             = vrn_data.copy()
                continue

            if aid=='svon':
                if vds['svon']:
                    fid     = 'whon'
                    continue
            
            if aid in ('b4wh', 'b4wo'):
                fold    = CdSw.dlg_dir('')
                if fold is None:   continue
                id      = {'b4wh':'wher'
                          ,'b4wo':'whon'}[aid]
                vals[id]= fold
                fid     = id
                vds.update({k:v for (k,v) in vals.items() if k in ('wher', 'mask', 'opdf', 'diff', 'dfsh', 'dfmx', 'svon', 'whon', 'maon')})

            if aid in ('v4wh', 'v4ma', 'v4wo', 'v4mo'):
                prms_l  =([]
                        +['{FILE_DIR}             \t'+_('Path of directory of current file')]
                        +['{FILE_DIR|name}        \t'+_('Name of directory of current file')]
                        +['{FILE_DIR|p}           \t'+_('Path of directory level upper, than {FILE_DIR}')]
                        +['{FILE_DIR|p|name}      \t'+_('Name of directory level upper, than {FILE_DIR}')]
                        +['{FILE_NAME}            \t'+_('Name of current file with extention')]
                        +['{FILE_STEM}            \t'+_('Name of current file without extention')]
                        +['{FILE_EXT}             \t'+_('Extention of current file')]
                        +['{YY}                   \t'+_('Current year as 99')]
                        +['{YYYY}                 \t'+_('Current year as 9999')]
                        +['{M}                    \t'+_('Current month as 9')]
                        +['{MM}                   \t'+_('Current month as 09')]
                        +['{MMM}                  \t'+_('Current month as sep')]
                        +['{MMMM}                 \t'+_('Current month as September')]
                        +['{D}                    \t'+_('Current day as 9')]
                        +['{DD}                   \t'+_('Current day as 09')]
                        +['{h}                    \t'+_('Current hours as 9')]
                        +['{hh}                   \t'+_('Current hours as 09')]
                        +['{m}                    \t'+_('Current minutes as 9')]
                        +['{mm}                   \t'+_('Current minutes as 09')]
                        +['{s}                    \t'+_('Current seconds as 9')]
                        +['{ss}                   \t'+_('Current seconds as 09')]
                        +['{APP_DIR}              \t'+_('CudaText folder path')]
                        +['{APP_DRIVE}            \t'+_('CudaText drive/disk letter (Windows only)')]
                        )+([] if aid not in ('v4ma', 'v4mo') else []
                        +['{COUNTER}              \t'+_('Auto-incremented as: 1, 2, 3, 4, 5, …')]
                        +['{COUNTER|lim:3}        \t'+_('Auto-incremented as: 1, 2, 3, 1, 2, …')]
                        +['{COUNTER|w:2}          \t'+_('Auto-incremented as: 01, 02, 03, 04, …')]
                        +['{COUNTER|lim:3|w:2}    \t'+_('Auto-incremented as: 01, 02, 03, 01, …')]
                        )
                prms_l +=['{'+pj_k+'}             \t'+pj_v 
                            for pj_k, pj_v in get_proj_vars().items()]
#               prm_i   = CdSw.dlg_menu(CdSw.MENU_LIST, '\n'.join(prms_l))
                prm_i   = CdSw.dlg_menu(app.DMENU_LIST_ALT, '\n'.join(prms_l))
#               prm_i   = CdSw.dlg_menu(CdSw.MENU_LIST_ALT, '\n'.join(prms_l))
                if prm_i is None:   continue
                id      = {'v4wh':'wher'
                          ,'v4ma':'mask'
                          ,'v4wo':'whon'
                          ,'v4mo':'maon'}[aid]
                vals[id]+= prms_l[prm_i].split('\t')[0].strip()
                fid     = id
                vds.update({k:v for (k,v) in vals.items() if k in ('wher', 'mask', 'opdf', 'diff', 'dfsh', 'dfmx', 'svon', 'whon', 'maon')})
                
            if aid == 'c4ma':
                rds_l   =([]
                        +[_('name.25-01-17.ext\t{FILE_STEM}.{DD}-{MM}-{YY}.{FILE_EXT}')]
                        +[_('name_25jan17-22.ext\t{FILE_STEM}_{DD}{MMM}{YY}-{hh}.{FILE_EXT}')]
                        +[_('name_2017-12-31_23-59-59.ext\t{FILE_STEM}_{YYYY}-{MM}-{DD}_{hh}-{mm}-{ss}.{FILE_EXT}')]
                        +[_('name.25jan17-001.ext\t{FILE_STEM}.{DD}{MMM}{YY}-{COUNTER|w:3}.{FILE_EXT}')]
                        )
                rd_i    = CdSw.dlg_menu(app.DMENU_LIST_ALT, '\n'.join(rds_l))
#               rd_i    = CdSw.dlg_menu(CdSw.MENU_LIST_ALT, '\n'.join(rds_l))
                if rd_i is None:   continue
                vals['mask']= rds_l[rd_i].split('\t')[1]
                fid     = 'mask'
                vds.update({k:v for (k,v) in vals.items() if k in ('wher', 'mask', 'opdf', 'diff', 'dfsh', 'dfmx', 'svon', 'whon', 'maon')})
            
            if aid == 'c4mo':
                rds_l   =([]
                        +[_('name.bak.ext\t{FILE_STEM}.bak.{FILE_EXT}')]
                        +[_('name~.ext\t{FILE_STEM}~.{FILE_EXT}')]
                        +[_('name.1.ext  name.2.ext …\t{FILE_STEM}.{COUNTER}.{FILE_EXT}')]
                        +[_('name.001.ext  name.002.ext …\t{FILE_STEM}.{COUNTER|w:3}.{FILE_EXT}')]
                        +[_('name.1.ext  name.2.ext  name.3.ext  name.1.ext …\t{FILE_STEM}.{COUNTER|lim:3}.{FILE_EXT}')]
                        +[_('name.01.ext … name.99.ext  name.01.ext …\t{FILE_STEM}.{COUNTER|lim:99|w:2}.{FILE_EXT}')]
                        )
                rd_i    = CdSw.dlg_menu(app.DMENU_LIST_ALT, '\n'.join(rds_l))
#               rd_i    = CdSw.dlg_menu(CdSw.MENU_LIST_ALT, '\n'.join(rds_l))
                if rd_i is None:   continue
                vals['maon']= rds_l[rd_i].split('\t')[1]
                fid     = 'maon'
                vds.update({k:v for (k,v) in vals.items() if k in ('wher', 'mask', 'opdf', 'diff', 'dfsh', 'dfmx', 'svon', 'whon', 'maon')})
            
            if aid=='!':
                if not vals['wher'].strip():
                    app.msg_status(_('Fill "Copy to dir"'))
                    fid     = 'wher'
                    continue
                if not vals['mask'].strip():
                    app.msg_status(_('Fill "Planned name"'))
                    fid     = 'mask'
                    continue
                if vds['svon'] and not vals['whon'].strip():
                    app.msg_status(_('Fill "Copy to dir"'))
                    fid     = 'whon'
                    continue
                if vds['svon'] and not vals['maon'].strip():
                    app.msg_status(_('Fill "Copy with name"'))
                    fid     = 'maon'
                    continue

                vrn_data.update(vds)
                save_cfg(stores)
                break#while
            
            stores['wher_hist'] = add_to_history(vds['wher'],  stores.get('wher_hist', []), MAX_HIST, unicase=(os.name=='nt'))
            stores['mask_hist'] = add_to_history(vds['mask'],  stores.get('mask_hist', []), MAX_HIST, unicase=(os.name=='nt'))
            stores['diff_hist'] = add_to_history(vds['diff'],  stores.get('diff_hist', []), MAX_HIST, unicase=(os.name=='nt'))
            stores['whon_hist'] = add_to_history(vds['whon'],  stores.get('whon_hist', []), MAX_HIST, unicase=(os.name=='nt'))
            stores['maon_hist'] = add_to_history(vds['maon'],  stores.get('maon_hist', []), MAX_HIST, unicase=(os.name=='nt'))
            stores['adva']      = adva
            save_cfg(stores)
           #while
        
        self.save_on= vrn_data.get('svon', self.def_svon)
        return True
       #def dlg_config

    def __init__(self):#NOTE: init
        self.save_on    = False

        self.def_wher   = '{FILE_DIR}'+os.sep+'bk'
        self.def_mask   = '{FILE_STEM}_{DD}{MMM}{YY}-{hh}.{FILE_EXT}'
        self.def_svon   = False
        self.def_whon   = r'{FILE_DIR}'+os.sep+'bk'
        self.def_maon   = '{FILE_STEM}.{COUNTER|w:3}.{FILE_EXT}'
        self.def_opdf   = False
        self.def_diff   = r'"c:\Program Files (x86)\WinMerge\WinMergeU.exe" "{COPY_PATH}" "{FILE_PATH}"' \
                            if os.name=='nt' else \
                          r'diff -u "{COPY_PATH}" "{FILE_PATH}"'
        self.def_dfsh   = False if os.name=='nt' else True
        self.def_dfmx   = 0

        vrn_data    = load_cfg(ops='vrn_data')
        self.save_on= vrn_data.get('svon', self.def_svon)
       #def __init__
   #class Command

def dlg_help():
    HELP_BODY   = \
_('''In the fields
    Copy to dir
    Planned name
    Copy with name
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
    {APP_DIR}             - CudaText folder path
    {APP_DRIVE}           - CudaText drive/disk letter (Windows only)
 
Filters. 
All macros can include suffix (function) to transform value.
   {Data|fun}             - gets fun({Data})
   {Data|fun:p1,p2}       - gets fun({Data},p1,p2)
   {Data|f1st:p1,p2|f2nd} - gets f2nd(f1st({Data},p1,p2))
Predefined filters are:
    p    - parent for path
    p:N  - N-parent for path ("p" is same as "p:1")
    name - last segment in path
    u    - upper: "word"  -> "WORD"
    l    - lower: "WORD"  -> "word"
    t    - title: "he is" -> "He Is"
    Examples: If path is     'head/p1/p2/p3/stem.ext'
        {FILE_DIR}        -> 'head/p1/p2/p3'
        {FILE_DIR|p}      -> 'head/p1/p2'
        {FILE_DIR|p|name} -> 'p2'
        {FILE_DIR|p:2}    -> 'head/p1'
        {FILE_EXT|u}      -> 'EXT'
        {FILE_EXT|t}      -> 'Ext'
Predefined filters for {COUNTER} are:
    w:N   - set width for value
    lim:N - set maximum value
    Examples: 
        {COUNTER}           -> 1 -> 2 -> 3 -> 4 -> 5 -> …
        {COUNTER|w:3}       -> 001 -> 002 -> 003 -> …
        {COUNTER|lim:3}     -> 1 -> 2 -> 3 -> 1 -> 2 -> …
        {COUNTER|lim:3|w:2} -> 01 -> 02 -> 03 -> 01 -> …
''')
    dlg_wrapper(_('Help'), GAP*2+600, GAP*3+25+650,
         [dict(cid='htx',tp='me'    ,t=GAP  ,h=650  ,l=GAP          ,w=600  ,ex0=1, ex1=1 ) #  ro,mono,border
         ,dict(cid='-'  ,tp='bt'    ,t=GAP+650+GAP  ,l=GAP+600-90   ,w=90   ,cap=_('&Close')  )
         ], dict(htx=HELP_BODY), focus_cid='htx')
   #def dlg_help

######################################
######################################
# Utilits
def setdefault(lst:list, pos, defv):
    if pos < len(lst):  return lst[pos]
    for p in range(len(lst), pos):
        lst.append(None)
    lst.append(defv)
    return defv
   #def setdefault

'''
ToDo
[ ][kv-kv][01feb17] ?? Подмешать макры из cuda_exttools
[ ][kv-kv][26jan17] ?? Разрешать пустые where и where_on?
[ ][at-kv][23jan17] Start
'''
