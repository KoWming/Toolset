#!/usr/bin/env python3
import argparse
import os
import platform
import ssl
import subprocess
import shutil
import re
import time
from urllib.request import urlopen

texts = {
    'docker-not-installed': {
        'en': 'Docker is not installed.',
        'zh': '未检测到 Docker。'
    },
    'docker-compose-not-installed': {
        'en': 'Docker Compose is not installed.',
        'zh': '未检测到 Docker Compose。'
    },
    'docker-version-too-low': {
        'en': 'Docker version is too low.',
        'zh': 'Docker 版本过低。'
    },
    'docker-compose-version-too-low': {
        'en': 'Docker Compose version is too low.',
        'zh': 'Docker Compose 版本过低。'
    },
    'install-docker': {
        'en': 'Installing Docker, please wait...',
        'zh': '正在安装 Docker，请稍候...'
    },
    'install-docker-compose': {
        'en': 'Installing Docker Compose, please wait...',
        'zh': '正在安装 Docker Compose，请稍候...'
    },
    'install-docker-failed': {
        'en': 'Failed to install Docker.',
        'zh': '安装 Docker 失败。'
    },
    'install-docker-compose-failed': {
        'en': 'Failed to install Docker Compose.',
        'zh': '安装 Docker Compose 失败。'
    },
    'docker-installed': {
        'en': 'Docker is installed.',
        'zh': 'Docker 已安装。'
    },
    'docker-compose-installed': {
        'en': 'Docker Compose is installed.',
        'zh': 'Docker Compose 已安装。'
    },
    'os-not-supported': {
        'en': 'Only Linux is supported.',
        'zh': '仅支持 Linux 系统。'
    },
    'need-root': {
        'en': 'Root privileges are required.',
        'zh': '需要 root 权限。'
    },
    'done': {
        'en': 'Check and installation finished.',
        'zh': '检测与安装完成。'
    },
    'docker-status': {
        'en': 'Show Docker status',
        'zh': '查看 Docker 状态'
    }
}

LANG = 'zh'

def text(label):
    return texts.get(label, {}).get(LANG, label)

def log_info(msg):
    print('\033[36m[INFO]\033[0m', msg)

def log_warn(msg):
    print('\033[33m[WARN]\033[0m', msg)

def log_error(msg):
    print('\033[31m[ERROR]\033[0m', msg)

def exec_command(*args, shell=False):
    try:
        proc = subprocess.run(args, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=shell)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return -1, '', str(e)

def check_docker():
    code, out, _ = exec_command('docker', '--version')
    if code != 0:
        log_warn(text('docker-not-installed'))
        return False
    log_info(text('docker-installed') + f" ({out})")
    m = re.search(r'(\d+)\.', out)
    if m and int(m.group(1)) < 20:
        log_warn(text('docker-version-too-low'))
        return False
    return True

def check_docker_compose():
    code, out, _ = exec_command('docker', 'compose', 'version')
    if code == 0:
        log_info(text('docker-compose-installed') + f" ({out})")
        m = re.search(r'(\d+)\.', out)
        if m and int(m.group(1)) < 2:
            log_warn(text('docker-compose-version-too-low'))
            return False
        return True
    code, out, _ = exec_command('docker-compose', 'version')
    if code == 0:
        log_info(text('docker-compose-installed') + f" ({out})")
        m = re.search(r'(\d+)\.', out)
        if m and int(m.group(1)) < 2:
            log_warn(text('docker-compose-version-too-low'))
            return False
        return True
    log_warn(text('docker-compose-not-installed'))
    return False

def install_docker():
    if not check_dependencies():
        return False
        
    total_steps = 7  # 总步骤数
    current_step = 0
    
    def show_progress(step_name):
        nonlocal current_step
        current_step += 1
        print(f'\033[36m[{current_step}/{total_steps}]\033[0m {step_name}')
    
    log_info('正在安装 Docker...')
    
    try:
        # 1. 清理旧版本
        show_progress('清理旧版本')
        exec_command('systemctl', 'stop', 'docker')
        exec_command('systemctl', 'disable', 'docker')
        exec_command('apt-get', 'remove', '-y', 'docker', 'docker-engine', 'docker.io', 'containerd.io')
        exec_command('apt-get', 'purge', '-y', 'docker-ce', 'docker-ce-cli', 'containerd.io', 'docker-buildx-plugin', 'docker-compose-plugin')
        
        # 2. 更新包管理器
        show_progress('更新包管理器')
        code, _, err = exec_command('apt-get', 'update')
        if code != 0:
            log_error(f'更新包管理器失败: {err}')
            return False
        
        # 3. 安装基础依赖
        show_progress('安装基础依赖')
        code, _, err = exec_command('apt-get', 'install', '-y', 'apt-transport-https', 'ca-certificates', 'curl', 'gnupg', 'lsb-release')
        if code != 0:
            log_error(f'安装基础依赖失败: {err}')
            return False
        
        # 4. 下载安装脚本
        show_progress('下载 Docker 安装脚本')
        url = 'https://get.docker.com'
        script = '/tmp/get-docker.sh'
        with urlopen(url, timeout=30, context=ssl._create_unverified_context()) as resp:
            with open(script, 'wb') as f:
                f.write(resp.read())
        os.chmod(script, 0o755)
        
        # 5. 执行安装脚本
        show_progress('执行 Docker 安装')
        code, out, err = exec_command('bash', script)
        if code != 0:
            log_error(f'Docker 安装脚本执行失败:\nSTDOUT:\n{out}\nSTDERR:\n{err}')
            return False
        
        # 6. 启动服务
        show_progress('启动 Docker 服务')
        exec_command('systemctl', 'start', 'docker')
        exec_command('systemctl', 'enable', 'docker')
        time.sleep(3)
        
        # 7. 验证安装
        show_progress('验证安装')
        if not is_docker_installed():
            log_error('Docker 命令不存在，尝试修复...')
            exec_command('apt-get', 'install', '--reinstall', 'docker-ce-cli')
            time.sleep(2)
            
            if not is_docker_installed():
                log_error('Docker 安装失败，命令不可用')
                return False
        
        # 测试运行
        code, _, err = exec_command('docker', 'run', '--rm', 'hello-world')
        if code == 0:
            log_info('\n\033[32m✓ Docker 安装成功并正常工作！\033[0m')
            return True
        else:
            log_error(f'Docker 已安装但运行测试失败: {err}')
            return False
            
    except Exception as e:
        log_error(f'安装过程发生错误: {e}')
        return False

def install_docker_compose():
    if not check_dependencies():
        return False
        
    total_steps = 4  # 总步骤数
    current_step = 0
    
    def show_progress(step_name):
        nonlocal current_step
        current_step += 1
        print(f'\033[36m[{current_step}/{total_steps}]\033[0m {step_name}')
    
    log_info('正在安装 Docker Compose...')
    
    try:
        # 1. 检查 Docker
        show_progress('检查 Docker 环境')
        if not is_docker_installed():
            log_error('请先安装 Docker')
            return False
            
        # 2. 下载 Docker Compose
        show_progress('下载 Docker Compose')
        uname_s = platform.system()
        uname_m = platform.machine()
        url = f'https://github.com/docker/compose/releases/latest/download/docker-compose-{uname_s}-{uname_m}'
        target = '/usr/local/bin/docker-compose'
        
        code, _, err = exec_command(f'curl -L {url} -o {target}', shell=True)
        if code != 0:
            log_error(f'下载失败: {err}')
            return False
            
        # 3. 设置权限
        show_progress('设置执行权限')
        try:
            os.chmod(target, 0o755)
        except Exception as e:
            log_error(f'设置权限失败: {e}')
            return False
            
        # 4. 验证安装
        show_progress('验证安装')
        if is_docker_compose_installed():
            code, out, _ = exec_command('docker-compose', '--version')
            if code == 0:
                log_info('\n\033[32m✓ Docker Compose 安装成功！\033[0m')
                log_info(f'版本信息: {out}')
                return True
            else:
                log_error('Docker Compose 已安装但无法获取版本信息')
                return False
        else:
            log_error('Docker Compose 安装失败，命令不可用')
            return False
            
    except Exception as e:
        log_error(f'安装过程发生错误: {e}')
        return False

def is_docker_installed():
    # 检查二进制文件
    docker_paths = ['/usr/bin/docker', '/usr/local/bin/docker']
    for path in docker_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return True
            
    # 检查服务状态
    code, _, _ = exec_command('systemctl', 'is-active', 'docker')
    if code == 0:
        return True
        
    # 检查命令可用性
    code, _, _ = exec_command('docker', '--version')
    return code == 0

def is_docker_compose_installed():
    code, _, _ = exec_command('docker', 'compose', 'version')
    if code == 0:
        return True
    code, _, _ = exec_command('docker-compose', '--version')
    return code == 0

def uninstall_docker():
    if not is_docker_installed():
        log_warn('未检测到 Docker，无需卸载。' if LANG == 'zh' else 'Docker not found, nothing to uninstall.')
        return

    total_steps = 5  # 总步骤数
    current_step = 0
    
    def show_progress(step_name):
        nonlocal current_step
        current_step += 1
        print(f'\033[36m[{current_step}/{total_steps}]\033[0m {step_name}')
    
    log_info('卸载 Docker ...' if LANG == 'zh' else 'Uninstalling Docker ...')
    
    try:
        # 1. 停止服务
        show_progress('停止 Docker 服务')
        exec_command('systemctl', 'stop', 'docker')
        exec_command('systemctl', 'disable', 'docker')
        exec_command('pkill', 'docker')
        
        # 2. 卸载包
        show_progress('移除 Docker 包')
        exec_command('apt-get', 'remove', '-y', 'docker', 'docker-engine', 'docker.io', 'containerd', 'runc')
        exec_command('apt-get', 'purge', '-y', 'docker-ce', 'docker-ce-cli', 'containerd.io')
        exec_command('yum', 'remove', '-y', 'docker', 'docker-client', 'docker-client-latest', 'docker-common', 'docker-latest', 'docker-latest-logrotate', 'docker-logrotate', 'docker-engine')
        exec_command('snap', 'remove', 'docker')
        
        # 3. 清理二进制文件
        show_progress('清理二进制文件')
        for path in ['/usr/bin/docker', '/usr/local/bin/docker', '/snap/bin/docker']:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    log_info(f'已删除: {path}')
            except Exception as e:
                log_warn(f'删除 {path} 失败: {e}')
        
        # 4. 清理数据目录
        show_progress('清理数据目录')
        dirs_to_remove = ['/var/lib/docker', '/etc/docker', '/var/run/docker']
        for dir_path in dirs_to_remove:
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    log_info(f'已删除: {dir_path}')
                except Exception as e:
                    log_warn(f'删除 {dir_path} 失败: {e}')
        
        # 5. 验证卸载结果
        show_progress('验证卸载结果')
        if is_docker_installed():
            log_warn('Docker 仍然存在，请手动检查残留文件或其他安装方式。' if LANG == 'zh' else 'Docker still exists, please check for leftover files or other install methods.')
        else:
            log_info('\n\033[32m✓ Docker 已完全卸载！\033[0m' if LANG == 'zh' else '\n\033[32m✓ Docker completely uninstalled!\033[0m')
            
    except Exception as e:
        log_error(f'卸载过程发生错误: {e}')

def uninstall_docker_compose():
    if not is_docker_compose_installed():
        log_warn('未检测到 Docker Compose，无需卸载。' if LANG == 'zh' else 'Docker Compose not found, nothing to uninstall.')
        return

    total_steps = 4  # 总步骤数
    current_step = 0
    
    def show_progress(step_name):
        nonlocal current_step
        current_step += 1
        print(f'\033[36m[{current_step}/{total_steps}]\033[0m {step_name}')
    
    log_info('卸载 Docker Compose ...' if LANG == 'zh' else 'Uninstalling Docker Compose ...')
    
    try:
        # 1. 停止进程
        show_progress('停止相关进程')
        exec_command('pkill', '-f', 'docker-compose')
        
        # 2. 移除二进制文件
        show_progress('移除二进制文件')
        compose_paths = [
            '/usr/local/bin/docker-compose',
            '/usr/bin/docker-compose',
            '/snap/bin/docker-compose',
            '/usr/libexec/docker/cli-plugins/docker-compose'
        ]
        for path in compose_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    log_info(f'已删除: {path}')
                except Exception as e:
                    log_warn(f'删除 {path} 失败: {e}')

        # 3. 清理系统包和配置
        show_progress('清理系统包和配置')
        exec_command('apt-get', 'remove', '-y', 'docker-compose-plugin')
        exec_command('apt-get', 'purge', '-y', 'docker-compose-plugin')
        exec_command('snap', 'remove', 'docker-compose')
        
        user_config_paths = [
            os.path.expanduser('~/.docker/cli-plugins/docker-compose'),
            os.path.expanduser('~/.docker/compose'),
        ]
        for path in user_config_paths:
            if os.path.exists(path):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    log_info(f'已删除: {path}')
                except Exception as e:
                    log_warn(f'删除 {path} 失败: {e}')

        # 4. 验证卸载结果
        show_progress('验证卸载结果')
        if is_docker_compose_installed():
            log_warn('Docker Compose 仍然存在，请检查以下位置：')
            code, out, _ = exec_command('which', '-a', 'docker-compose')
            if code == 0 and out:
                for line in out.splitlines():
                    log_warn(f'- {line}')
        else:
            log_info('\n\033[32m✓ Docker Compose 已完全卸载！\033[0m' if LANG == 'zh' else '\n\033[32m✓ Docker Compose completely uninstalled!\033[0m')
            
    except Exception as e:
        log_error(f'卸载过程发生错误: {e}')

def show_docker_version():
    code, out, _ = exec_command('docker', '--version')
    if code == 0:
        log_info(out)
    else:
        log_error('未检测到 Docker。' if LANG == 'zh' else 'Docker not found.')

def show_docker_compose_version():
    code, out, _ = exec_command('docker', 'compose', 'version')
    if code == 0:
        log_info(out)
        return
    code, out, _ = exec_command('docker-compose', 'version')
    if code == 0:
        log_info(out)
    else:
        log_error('未检测到 Docker Compose。' if LANG == 'zh' else 'Docker Compose not found.')

def show_docker_status():
    # 检查服务状态
    code, out, _ = exec_command('systemctl', 'status', 'docker')
    if code == 0:
        log_info(out)
    else:
        log_error('Docker 服务未运行或无法获取状态。')
    
    # 检查运行中的容器
    code, out, _ = exec_command('docker', 'ps')
    if code == 0:
        if out.strip():
            log_info("\n运行中的容器：\n" + out)
        else:
            log_info("当前没有运行中的容器。")
    
    # 检查系统信息
    code, out, _ = exec_command('docker', 'info')
    if code == 0:
        log_info("\nDocker 系统信息：\n" + out)

def menu():
    menu_text = {
        'zh': '''
\033[36m==========================================
|         Docker 管理工具菜单             |
==========================================\033[0m
  \033[32m1. 一键安装全部\033[0m
  \033[32m2. 安装最新 Docker\033[0m
  \033[32m3. 安装最新 Docker Compose\033[0m
  \033[36m4. 查看 Docker 状态\033[0m
  \033[36m5. 查看 Docker 版本\033[0m
  \033[36m6. 查看 Docker Compose 版本\033[0m
  \033[31m7. 一键卸载全部\033[0m
  \033[31m8. 卸载 Docker\033[0m
  \033[31m9. 卸载 Docker Compose\033[0m
  \033[90m0. 退出\033[0m
\033[36m------------------------------------------\033[0m
请输入数字选择操作：''',
        'en': '''
\033[36m==========================================
|         Docker Management Menu          |
==========================================\033[0m
  \033[32m1. Install all\033[0m
  \033[32m2. Install latest Docker\033[0m
  \033[32m3. Install latest Docker Compose\033[0m
  \033[36m4. Show Docker status\033[0m
  \033[36m5. Show Docker version\033[0m
  \033[36m6. Show Docker Compose version\033[0m
  \033[31m7. Uninstall all\033[0m
  \033[31m8. Uninstall Docker\033[0m
  \033[31m9. Uninstall Docker Compose\033[0m
  \033[90m0. Exit\033[0m
\033[36m------------------------------------------\033[0m
Enter your choice:'''
    }
    while True:
        try:
            choice = input(menu_text[LANG]).strip()
        except (KeyboardInterrupt, EOFError):
            print('\n\033[32mBye!\033[0m')
            break
        if choice == '1':
            log_info('开始一键安装 Docker 和 Docker Compose...')
            if install_docker():
                log_info('Docker 安装成功！')
                if install_docker_compose():
                    log_info('Docker Compose 安装成功！')
                    log_info('所有组件安装完成！')
                else:
                    log_error('Docker Compose 安装失败！')
            else:
                log_error('Docker 安装失败！')
        elif choice == '2':
            install_docker()
        elif choice == '3':
            install_docker_compose()
        elif choice == '4':
            show_docker_status()
        elif choice == '5':
            show_docker_version()
        elif choice == '6':
            show_docker_compose_version()
        elif choice == '7':
            uninstall_docker_compose()
            uninstall_docker()
        elif choice == '8':
            uninstall_docker()
        elif choice == '9':
            uninstall_docker_compose()
        elif choice == '0':
            print('\033[90m已退出。\033[0m' if LANG == 'zh' else '\033[90mExited.\033[0m')
            break
        else:
            print('\033[31m无效选择，请重新输入。\033[0m' if LANG == 'zh' else '\033[31mInvalid choice, please try again.\033[0m')

def check_dependencies():
    # 检查包管理器
    pkg_mgrs = ['apt-get', 'yum']
    found_mgr = False
    for mgr in pkg_mgrs:
        code, _, _ = exec_command('which', mgr)
        if code == 0:
            found_mgr = True
            break
    if not found_mgr:
        log_error('未检测到支持的包管理器(apt-get/yum)')
        return False

    # 检查必要工具
    for cmd in ['curl', 'bash', 'systemctl']:
        code, _, _ = exec_command('which', cmd)
        if code != 0:
            log_error(f'依赖缺失：{cmd}')
            return False

    # 检查系统服务
    code, _, _ = exec_command('systemctl', 'status')
    if code != 0:
        log_error('系统服务(systemd)异常')
        return False

    return True

def main():
    global LANG
    parser = argparse.ArgumentParser()
    parser.add_argument('--en', action='store_true', help='Use English')
    args = parser.parse_args()
    if args.en:
        LANG = 'en'

    if platform.system() != 'Linux':
        log_error(text('os-not-supported'))
        return
    if os.geteuid() != 0:
        log_error(text('need-root'))
        return

    menu()

if __name__ == '__main__':
    main()