#!/usr/bin/env python3
# coding=utf-8
import json
import os
import sys

current_file_dir = os.path.dirname(__file__)  # 当前文件所在的目录
template_dir = current_file_dir+'/../../template'
sys.path.append(current_file_dir+'/../components')
from my_file.my_file import *
from my_exe.my_exe import my_exe_simple, my_exe_get_install_path

class my_ide_gcc:
    json_file = ""

    src = {'c_files':[],'h_dirs':[],'l_files':[],'s_files':[],
           'h_dir_str':'','l_files_str':'','l_dirs_str':''}
    tool = {}
    flash = {}
    output = {}

    def __init__(self,JSON_FILE):
        self.json_file = JSON_FILE

    def __json_deep_search(self, area, i=0):
        for k in area:
            #print('----' * i, k, sep='')
            if  isinstance(area[k],dict):
                self.__json_deep_search(area[k], i+1)
            else:
                if k == "c_files":
                    self.src['c_files'] += area[k]
                elif k == "h_dir":
                    self.src['h_dirs'] += area[k]
                elif k == "s_files":
                    self.src['s_files'] += area[k]
                elif k == "l_files":
                    self.src['l_files'] += area[k]
                #else:            
                    #print(area[k])
    
    def __get_variable_map(self):
        log_path = '.log'
        
        # Get the path to the current python interpreter
        PYTHON_PATH = sys.executable
        
        # Get the keil path
        EXE_USED_MAP = my_file_str_list_count(self.json_file,['$KEIL_PATH'])
        print(EXE_USED_MAP)
        for key in EXE_USED_MAP:
            if EXE_USED_MAP[key] == 0:
                EXE_USED_MAP[key] = ""
            else:
                EXE_USED_MAP[key] = my_exe_get_install_path(key)
           
        # FW
        output_path = self.output['path']
        DEMO_NAME = self.output['fw']['name']
        DEMO_FIRMWARE_VERSION =  self.output['fw']['ver']
        
        UA_SUFFIX = os.path.splitext(os.path.basename(self.output['fw']['output']['UA']))[1]
        PROD_SUFFIX = os.path.splitext(os.path.basename(self.output['fw']['output']['PROD']))[1]
        
        FW_UA = output_path+'/'+DEMO_NAME+'_UA_'+DEMO_FIRMWARE_VERSION+UA_SUFFIX
        FW_PROD = output_path+'/'+DEMO_NAME+'_PROD_'+DEMO_FIRMWARE_VERSION+PROD_SUFFIX
        
        return {
            '$OUTPUT':log_path,
            '$O_FILES':' '.join(my_file_find_files_in_paths([log_path],'.o')),
            '$L_FILES':' '.join(self.src['l_files']),
            '$LIB_DIRS':self.src['l_dirs_str'],
            '$LIBS':self.src['l_files_str'],
            '$MAP':log_path+'/output.map',
            '$ELF':log_path+'/output.elf',
            '$LST':log_path+'/output.lst',
            '$PYTHON':PYTHON_PATH,
            '$KEIL_PATH':EXE_USED_MAP['$KEIL_PATH'],
            '$UA':FW_UA,
            '$PROD':FW_PROD,
       }
    
    def tmake(self):
        # get all value
        my_file_str_replace(self.json_file,'$PROJECT_ROOT','.')#PROJECT_PATH
        with open(self.json_file,'r') as load_f:
            load_dict = json.load(load_f)
            self.__json_deep_search(load_dict)
        
        self.tool['path'] =             my_file_get_abs_path_and_formart(load_dict['tool']['gcc']['toochain']['bin_path'])

        self.tool['cc'] =               load_dict['tool']['gcc']['cmd']['gcc']['cc']
        self.tool['asm'] =              load_dict['tool']['gcc']['cmd']['gcc']['asm']
        self.tool['c_flags'] =          load_dict['tool']['gcc']['cmd']['gcc']['c_flags']
        self.tool['s_flags'] =          load_dict['tool']['gcc']['cmd']['gcc']['s_flags']
        self.tool['c_macros'] =         load_dict['tool']['gcc']['cmd']['gcc']['c_macros']
        self.tool['ld'] =               load_dict['tool']['gcc']['cmd']['ld']
        self.tool['objcopy'] =          load_dict['tool']['gcc']['cmd']['objcopy']
        self.tool['objdump'] =          load_dict['tool']['gcc']['cmd']['objdump']
        self.tool['size'] =             load_dict['tool']['gcc']['cmd']['size']
        self.tool['ar'] =               load_dict['tool']['gcc']['cmd']['ar']
        self.tool['before-build'] =     load_dict['tool']['gcc']['cmd']['before-build']
        self.tool['after-build'] =      load_dict['tool']['gcc']['cmd']['after-build']
        
        
        self.flash['bin_path'] =        my_file_get_abs_path_and_formart(load_dict['tool']['gcc']['flash']['bin_path'])
        self.flash['flash_user_cmd'] =  load_dict['tool']['gcc']['flash']['flash_user_cmd']
        self.flash['flash_all_cmd'] =   load_dict['tool']['gcc']['flash']['flash_all_cmd']

        self.output = load_dict['output']
        self.output['sdk'].update({'components':load_dict['components']})
        self.output['fw'].update({'output':load_dict['tool']['gcc']['output']})

        # h_dirs list change to string
        for h_dir in self.src['h_dirs']:
            self.src['h_dir_str'] += (' -I'+h_dir)
       
        # get l_dirs and change to string
        # l_files change to string
        l_dirs = []
        for l_file in self.src['l_files']:
            self.src['l_files_str'] += (' -l'+os.path.splitext(os.path.basename(l_file))[0][3:])

            l_dir = os.path.dirname(l_file)
            if l_dir not in l_dirs:
                l_dirs.append(l_dir)
                self.src['l_dirs_str'] += (' -L'+l_dir)

    def tsdk(self):
        my_file_clear_folder(self.output['path']) 
        
        print('# 1.Create Output Package...')
        output_path     = self.output['path']
        app_path        = output_path + '/apps'
        comp_path       = output_path + '/components'
        docs_path       = output_path + '/docs'
        incs_path       = output_path + '/include'
        libs_path       = output_path + '/libs'
        scripts_path    = output_path + '/scripts'
        tools_path      = output_path + '/tools'
        vendor_path     = output_path + '/vendor'
        log_path        = output_path + '/log'
    
        project_root = self.output['project_path']
        docs_root    = project_root+'/docs'
        include_root = project_root+'/include'
        adapter_root = project_root+'/adapter'
        vendor_root  = project_root+'/vendor'
        
        my_file_clear_folder(app_path)
        my_file_clear_folder(comp_path)
        my_file_copy_dir_to(docs_root,docs_path)
        my_file_copy_dir_to(include_root,incs_path)
        my_file_clear_folder(libs_path)
        my_file_clear_folder(scripts_path)
        my_file_clear_folder(tools_path)
        my_file_copy_dir_to(vendor_root,vendor_path)
        my_file_clear_folder(log_path)
        
        my_file_copy_files_to([project_root+'/CHANGELOG.md',
                               project_root+'/LICENSE',
                               project_root+'/README.md',
                               project_root+'/RELEASE.md',
                               template_dir+'/sdk/build_app.py'],output_path)
        my_file_copy_files_to([template_dir+'/sdk/pre_build.py'],scripts_path)

        print('# 2.Create include/base  include/vendor/adapter...')        
        adapters = my_file_find_subdir_in_path(adapter_root)
        for adapter in adapters:
            src_path = adapter_root+'/'+adapter+'/include'
            dst_path = incs_path+'/vendor/adapter/'+adapter+'/include'
            my_file_copy_dir_to(src_path,dst_path)
            print('    [cp] cp %s to %s'%(src_path,dst_path))
            
        print('# 3.Create libs...')
        cmd_dict = self.__get_variable_map()
        libs = self.output['sdk']['libs']
        evn = self.tool['path']
        print('-> to libs:',libs)
        for k,v in self.output['sdk']['components'].items():
            if k in libs:
                print('    ->[Y]',k)
                # create lib
                cur_lib = libs_path+'/lib'+k+'.a' 
                cur_o_files = ''

                for c_file in v['c_files']:
                    o_file = log_path+'/'+os.path.splitext(os.path.basename(c_file))[0]+'.o'
                    cur_o_files += (' '+o_file)
                    cmd = "%s %s %s -c %s -o %s %s"%(self.tool['cc'],self.tool['c_flags'],self.src['h_dir_str'],c_file,o_file,self.tool['c_macros'])
                    my_exe_simple(cmd,1,evn,cmd_dict)
                    print("        [cc] %s"%(c_file))
                
                cmd = '%s -rc %s %s'%(self.tool['ar'],cur_lib,cur_o_files)
                my_exe_simple(cmd,1,evn,cmd_dict)
                print("        [ar] %s"%(cur_lib))

                # copy .h to include
                my_file_copy_one_kind_files_to(v['h_dir'],'.h',incs_path+'/components/'+k+'/include')
            else:
                print('    ->[N]',k)
                # copy .c to src
                my_file_copy_files_to(v['c_files'], comp_path+'/'+k+'/src')
                # copy .h to include
                my_file_copy_one_kind_files_to(v['h_dir'],'.h', comp_path+'/'+k+'/include')

        print('# 4.End...')
        my_file_rm_dir(log_path)


    def tbuild(self):  
        evn = self.tool['path']
        cmd_dict = self.__get_variable_map()
        output_path = self.output['path']
        log_path = cmd_dict['$OUTPUT']
        my_file_clear_folder(log_path)
        my_file_clear_folder(output_path)
        
        # before build
        for cmd in self.tool['before-build']:
            my_exe_simple(cmd,1,evn,cmd_dict)
            print("\n[o-before-build] %s"%(cmd))

        # c to .o
        for c_file in self.src['c_files']:
            o_file = log_path+'/'+os.path.splitext(os.path.basename(c_file))[0]+'.o'
            cmd = "%s %s %s -c %s -o %s %s"%(self.tool['cc'],self.tool['c_flags'],self.src['h_dir_str'],c_file,o_file,self.tool['c_macros'])
            my_exe_simple(cmd,1,evn,cmd_dict)
            print("[cc] %s"%(c_file))

        # .s to .o
        for s_file in self.src['s_files']:
            o_file = log_path+'/'+os.path.splitext(os.path.basename(s_file))[0]+'.o'
            cmd = "%s %s -c %s -o %s"%(self.tool['asm'],self.tool['s_flags'],s_file,o_file)
            my_exe_simple(cmd,1,evn,cmd_dict)
            print("[cc] %s"%(s_file))

        # ld
        cmd = self.tool['ld'];
        print("\n[ld] %s"%(cmd))
        my_exe_simple(cmd,1,evn,cmd_dict)

        # create list
        cmd = self.tool['objdump']
        print("\n[o-list] %s"%(cmd))
        my_exe_simple(cmd,1,evn,cmd_dict)

        # change format
        cmd = self.tool['objcopy']
        print("\n[o-bin] %s"%(cmd))
        my_exe_simple(cmd,1,evn,cmd_dict)

        # print size
        cmd = self.tool['size']
        print("\n[o-size] %s"%(cmd))
        my_exe_simple(cmd,1,evn,cmd_dict)

        # after build
        for cmd in self.tool['after-build']:
            print("\n[o-after-build] %s"%(cmd))
            my_exe_simple(cmd,1,evn,cmd_dict)
        
        
        DEMO_NAME = self.output['fw']['name']
        DEMO_FIRMWARE_VERSION =  self.output['fw']['ver']
                
        for k in self.output['fw']['output']:
            fw = log_path+'/'+self.output['fw']['output'][k]
            if os.path.exists(fw):
                suffix = os.path.splitext(os.path.basename(fw))[1]
                shutil.copy(fw, output_path+'/'+DEMO_NAME+'_'+k+'_'+DEMO_FIRMWARE_VERSION+suffix)
                if k == 'UA':
                    shutil.copy(fw, output_path+'/'+DEMO_NAME+'_'+DEMO_FIRMWARE_VERSION+suffix)
            else:
                print('build fail')
                return
                
        print('build success')

    def tflash(self,OP):
        cmd_dict = self.__get_variable_map()
        flash_evn = self.flash['bin_path'];
        
        if OP == 'flash_user':
            cmd = self.flash['flash_user_cmd']
            print("\n[flash] flash user: %s\n"%(cmd))
            my_exe_simple(cmd,1,flash_evn,cmd_dict)
        if OP == 'flash_all': 
            cmd = self.flash['flash_all_cmd']
            print("\n[flash] flash all: %s\n"%(cmd))        
            my_exe_simple(cmd,1,flash_evn,cmd_dict)

