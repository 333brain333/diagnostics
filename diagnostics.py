#!/usr/bin/env python3
"""
Запуск диагностических тестов
"""
import argparse
import datetime
import glob
import os
import platform
import cgn
import app_manager

def connect2redis_db(db_num: int):
    """
    connect2redis_db
    """
    conn = cgn.redis.Redis()
    run_suffix = get_info_version()
    assert conn.connect(cgn.redis.get_server_ip(run_suffix), 6379, 60, None, db_num)
    return conn

def test_all_redis_connection():
    """
    test_all_redis_connection
    """
    connect2redis_db(1)
    connect2redis_db(4)

def iperf(mode):
    """
    iperf
    """
    device_ip = '192.168.10.10'
    cgn.utils.run_subprocess(
        "timeout 2 ssh agrodroid@{} -f 'iperf3 -s 1>/dev/null 2>/dev/null'".format(
            device_ip), use_assert=True)
    out = cgn.utils.run_subprocess_str(
        'sleep 3 && iperf3 {} -c {}'.format(mode, device_ip), use_assert=True)
    cgn.utils.run_subprocess(
        "timeout 2 ssh agrodroid@{} -f 'killall iperf3'".format(device_ip), use_assert=True)
    return out

def process_iperf_output(out):
    """
    process_iperf_output
    """
    for line in out.split('\n'):
        if 'sender' in line:
            assert float(line.split()[4]) > 80.0
        if 'receiver' in line:
            assert float(line.split()[4]) > 80.0

def test_aarch64_eth_speed():
    """
    test_aarch64_eth_speed
    """
    model = cgn.utils.run_subprocess_str('cat /proc/device-tree/model', use_assert=True)
    if 'quill' not in model:
        modes = {'normal':'', 'reversed':'-R'}
        for mode in modes:
            print('mode: ', mode)
            out = iperf(modes[mode])
            assert 'Connection refused' not in out
            assert 'No route to host' not in out
            process_iperf_output(out)

def test_all_docker_version():
    """
    test_all_docker_compose_version
    """
    cgn.test.check_docker_version()

def test_all_architecture():
    """
    test_all_architecture
    """
    cgn.test.check_architecture(__file__)

def get_default_username():
    """
    Возвращает умолчательное имя пользователя
    """
    return 'agrodroid'

def get_flycap_bin_dir_aarch64():
    """
    Возвращает директорию, в которой лежат исполняемые файлы flycap
    Архитектура: aarch64
    """
    return '/home/{}/tools/flycapture.2.13.3.31_arm64/bin'.format(
        get_default_username())

def get_flycap_bin_dir():
    """
    Возвращает директорию, в которой лежат исполняемые файлы flycap
    """
    flycap_bin_dir = ''
    arch = platform.machine()
    if arch == 'aarch64':
        flycap_bin_dir = get_flycap_bin_dir_aarch64()
    return flycap_bin_dir

def test_all_deb_packages():
    """
    Проверка наличия deb-пакет
    """
    packages = ['jq', 'ethtool', 'arp-scan', 'expect']
    arch = platform.machine()
    if arch == 'x86_64':
        packages.extend(['libgtkmm-2.4-1v5:amd64'])
    elif arch == 'aarch64':
        packages.extend(['libgtkmm-2.4-1v5:arm64', 'docker', 'docker.io'])
    cgn.test.check_deb_packages(packages)

def test_all_docker_compose_version():
    """
    test_all_docker_compose_version
    """
    cgn.test.check_docker_compose_version()

def test_all_docker_compose_config():
    """
    test_all_docker_compose_config
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser()
    args = parser.parse_args([])
    args.arch = platform.machine()
    args.abort_on_container_exit = False
    args.app_dir = '/tmp'
    args.container_mode = 'all'
    args.force_recreate = False
    args.minimal_version_dir = os.path.abspath(os.path.join(script_dir, '..'))
    args.no_color = False
    args.popcore_version = 3
    args.run_suffix = '-' + get_info_version()
    args.without_detached = False
    args.info_version = cgn.utils.read_str_from_file(
        os.path.abspath(os.path.join(script_dir, '..', 'info', 'version.txt')))
    args.redis_address = cgn.redis.get_server_ip(args.info_version)

    yaml_config = app_manager.get_default_config()
    data = cgn.utils.load_yaml(yaml_config)
    services = list(data['services'].keys())
    if 'sys_agro_monitor' in services:
        args.update_mode = True
    else:
        args.update_mode = False

    args.path_autostart = os.path.abspath(os.path.join(script_dir, yaml_config))
    base_cmd = app_manager.get_docker_compose_cmd(args, 'config')
    result_str = cgn.utils.run_subprocess_str(base_cmd, use_assert=True, verbose=False)
    print(result_str)
    assert 'services' in result_str
    assert 'variable is not set' not in result_str

def test_all_vehicle_dict():
    """
    test_all_vehicle_dict
    """
    redis_server_db4 = connect2redis_db(4)
    vehicle_name = redis_server_db4.get('vehicle:model')
    print('vehicle_name: ', vehicle_name)

    redis_server_db1 = connect2redis_db(1)
    vehicle_data_str = redis_server_db1.get('harvesters_dict:{}'.format(vehicle_name))
    print('vehicle_data_str: ', vehicle_data_str)

    if len(vehicle_data_str) == 0:
        print('Incorrect db4.vehicle:model or db1:harvesters_dict[db4.vehicle:model]')
        assert False
    elif 'nameString' not in vehicle_data_str:
        print('Field \'nameString\' was not found in vehicle_data')
        assert False
    elif vehicle_name not in vehicle_data_str:
        print('Incorrect vehicle_name!')
        assert False

def test_all_culture_model_mapping():
    """
    test_all_culture_model_mapping
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    agrodroid_path = os.path.join(
        script_dir, '..', 'base', 'containers', 'main', 'config', 'npme', 'agrodroid.yml.main')

    assert os.path.exists(agrodroid_path)
    agrodroid_data = cgn.utils.load_opencv_yaml(agrodroid_path)
    assert 'rules' in agrodroid_data

    print(agrodroid_data['rules'])
    work_types = []
    expected_work_types = ['left', 'row', 'valok']
    for rule in agrodroid_data['rules']:
        assert 'work_type' in rule or 'culture' in rule
        assert 'net' in rule
        path = os.path.join(script_dir, rule['net'].replace('models', 'containers/main/models_ext'))
        print(path)
        if not os.path.exists(path):
            cgn.console.print_error(
                'File was not found: {}'.format(path))
            assert False
        if 'work_type' in rule:
            assert rule['work_type'] in expected_work_types
            work_types.append(rule['work_type'])
    assert set(work_types) == set(expected_work_types)

def get_info_version():
    """
    get_info_version
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return cgn.utils.read_str_from_file(
        os.path.join(script_dir, '..', 'info', 'version.txt'))

def get_major_image_version():
    """
    get_major_image_version
    """
    version_str = get_info_version()
    return int(version_str[version_str.find('-v')+2:])

def test_all_symlinks():
    """
    Проверка наличия директорий
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))

    paths = [
        os.path.join('containers', 'main', 'config'),
        os.path.join('containers', 'main', 'data'),
        os.path.join('containers', 'main', 'models')]
    if get_major_image_version() < 44:
        paths.append(os.path.join('containers', 'main', 'lib', 'libflycapture.so.2'))

    if 't51' in get_info_version():
        paths.extend([
            os.path.join('containers', 'main', 'bin', 'onnx2trt'),
            os.path.join('containers', 'main', 'lib', 'libnvonnxparser_runtime.so.0')])
    for path in paths:
        assert os.path.islink(os.path.join(script_dir, '..', path))

def test_all_directories():
    """
    Проверка наличия директорий
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    directories = [
        'info', 'scripts',
        os.path.join('containers', 'main', 'bin'),
        os.path.join('containers', 'main', 'lib'),
        os.path.join('containers', 'main', 'prj.scripts'),
        os.path.join('containers', 'main', 'testdata')]
    if get_info_version().find('agrodroid_onnx_patch') == -1:
        directories.extend([
            os.path.join('base_src', 'docker'),
            os.path.join('base_src', 'docker', 'autoheal'),
            os.path.join('base_src', 'containers', 'dir_cleaner'),
            os.path.join('base_src', 'containers', 'dir_monitor'),
            os.path.join('base_src', 'containers', 'main'),
            os.path.join('base_src', 'containers', 'main', 'bin'),
            os.path.join('base_src', 'containers', 'main', 'config'),
            os.path.join('base_src', 'containers', 'main', 'data'),
            os.path.join('base_src', 'containers', 'main', 'lib'),
            os.path.join('base_src', 'containers', 'main', 'models'),
            os.path.join('docker', 'main')])

    for directory in directories:
        assert os.path.isdir(os.path.join(script_dir, '..', directory))

def test_all_files():
    """
    Проверка наличия файлов
    """
    files = [
        'autocheck.sh', 'autostart.sh', 'stop_containers.sh',
        os.path.join('base', 'containers', 'main', 'config', 'logger-config.yaml.main'),
        os.path.join('base', 'containers', 'main', 'config', 'navigator', 'run_keys.txt.main'),
        os.path.join('base', 'containers', 'main', 'config', 'navigator', 'run_keys.txt.test'),
        os.path.join('base', 'containers', 'main', 'config', 'navigator', 'online_mode.yaml'),
        os.path.join('base', 'containers', 'main', 'config', 'npme', 'npme.yml.main'),
        os.path.join('containers', 'main', 'bin', 'npme'),
        os.path.join('containers', 'main', 'bin', 'npme_healthcheck'),
        os.path.join('containers', 'main', 'lib', 'libtensorrtserver.so'),
        os.path.join('scripts', 'install.py'),
        os.path.join('scripts', 'interactive_start.sh'),
        os.path.join('scripts', 'load_containers.sh'),
        os.path.join('scripts', 'prepare_models.sh'),
        os.path.join('scripts', 'set_flycap_serial_number.py')]

    version_str = get_info_version()
    if 't51' in version_str:
        files.append(os.path.join('base', 'containers', 'main', 'bin', 'onnx2trt'))

    cgn.test.check_files(__file__, files)

def test_all_yaml():
    """
    test_all_opencv_yaml
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    interactive_start_path = os.path.join(script_dir, 'interactive_start.sh')

    files = [
        os.path.join('config', 'drivarea', 'bisenet_0.yaml'),
        os.path.join('config', 'logger-config.yaml.main'),
        os.path.join('config', 'logger-config.yaml.test'),
        os.path.join('config', 'navigator', 'offline_mode.yaml'),
        os.path.join('config', 'navigator', 'online_mode.yaml.main'),
        os.path.join('config', 'navigator', 'online_mode.yaml.test'),
        os.path.join('config', 'npme', 'agrodroid.yml.main'),
        os.path.join('config', 'npme', 'agrodroid.yml.main'),
        os.path.join('config', 'npme', 'npme.yml.main'),
        os.path.join('config', 'npme', 'npme.yml.test'),
        os.path.join('data', 'online_calib', 'sense_poses.yml')
    ]
    for file in files:
        path = os.path.join('/external-dir', file)
        cgn.utils.run_subprocess(
            '{} python3 {} {}'.format(
                interactive_start_path,
                os.path.join('/scripts-dir', 'check_opencv_yaml.py'), path),
            use_assert=True)

def test_all_execute_right():
    """
    Проверка прав выполнения для исполняемых файлов
    """
    cgn.test.check_execute_right(
        __file__,
        relative_path=os.path.join('..', 'containers', 'main', 'bin'),
        files=['npme', 'npme_healthcheck', 'dbw_checker'])

def test_all_docker_container():
    """
    Проверка работоспособности docker-контейнера
    """
    cgn.test.check_docker_container(__file__)

def test_all_docker_images():
    """
    Проверка наличия docker-контейнеров
    """
    cgn.test.check_docker_images(
        script_file=__file__,
        extra_devops_images=['autoheal:latest', 'redis:latest', 'redis-tmp:latest'],
        extra_images=[])

def test_all_sysctl_parameters():
    """
    Проверка корректности настройки sysctl-параметров
    """
    parameters = ['net.core.wmem_max', 'net.core.wmem_default',
                  'net.core.rmem_max', 'net.core.rmem_default']
    cgn.test.check_sysctl_parameters(__file__, parameters, 33554432)

def test_all_groups():
    """
    Проверка корректности настройки списка групп
    """
    cgn.test.check_groups(['docker', 'flirimaging'])

def test_all_free_space():
    """
    Проверка свободного пространства
    """
    cgn.test.test_free_space(__file__, 2 * 1048576)

def test_all_flycap():
    """
    Проверка на то, что серийный номер камеры указан в online_mode.yaml
    """
    if get_major_image_version() < 44:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(
            script_dir, '..', 'base', 'containers', 'main',
            'config', 'navigator', 'online_mode.yaml')
        serial_number_str = cgn.test.get_serial_number_from_online_mode(path)
        assert len(serial_number_str) > 5

def test_aarch64_username():
    """
    Проверка имени пользователя для aarch64
    """
    username = os.environ.get('USER')
    assert username == get_default_username()

def test_aarch64_flycap_bin_dir():
    """
    Проверка наличия директории для flycap
    """
    if get_major_image_version() < 44:
        assert os.path.isdir(get_flycap_bin_dir_aarch64())

def test_aarch64_flycap_ldd():
    """
    Проверка наличия библиотек для flycap-приложений
    """
    if get_major_image_version() < 44:
        cmd = 'ldd {} | grep -c "not found"'.format(
            os.path.join(get_flycap_bin_dir_aarch64(), 'FlyCap2_arm'))
        assert cgn.utils.run_subprocess_int(cmd) == 0

        cmd = 'ldd {} | grep -c "not found"'.format(
            os.path.join(get_flycap_bin_dir_aarch64(), 'FlyCapture2Test'))
        assert cgn.utils.run_subprocess_int(cmd) == 0

def remove_files_by_mask(path: str):
    """
    remove_files_by_mask
    """
    print('remove_files_by_mask:', path)
    file_list = glob.glob(path)
    for file_path in file_list:
        try:
            os.remove(file_path)
        except OSError:
            print("Error while deleting file : ", file_path)

def test_all_flycap_test():
    """
    Проверка корректности работы камеры с помощью утилиты FlyCapture2Test
    """
    if get_major_image_version() < 44:
        cmd = "echo -ne '\\n' | timeout 20s {}".format(
            os.path.join(get_flycap_bin_dir(), 'FlyCapture2Test'))
        result_str = cgn.utils.run_subprocess_str(cmd)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        remove_files_by_mask(os.path.join(script_dir, '..', '*.pgm'))

        current_serial_number = ''
        params_dict = dict()
        for line in result_str.split('\n'):
            print('#', line, '#')
            if line == 'Number of cameras detected: 0':
                assert False
            arr = line.split(' - ')
            if len(arr) == 2:
                if arr[0] in ['Resolution', 'Serial number']:
                    if arr[0] == 'Serial number':
                        current_serial_number = arr[1]
                    elif arr[0] == 'Resolution':
                        params_dict[current_serial_number] = arr[1]
        print(params_dict)

        path = os.path.join(
            script_dir, '..', 'base', 'containers', 'main',
            'config', 'navigator', 'online_mode.yaml')
        serial_number = cgn.test.get_serial_number_from_online_mode(path)
        assert len(params_dict) > 0
        assert serial_number in params_dict
        assert params_dict[serial_number] == '960x600'

        #stderr = result.stderr.decode('UTF-8').strip('\n')
        #assert len(stderr) == 0

def test_aarch64_ip_for_main_connection():
    """
    Проверка текущего IP-адреса
    """
    assert cgn.utils.run_subprocess_int('ifconfig | grep -c "192.168."') > 0

def check_base_conditions():
    """
    Проверка основных условий для запуска скрипта с помощью pytest
    """
    packages = ['expect']
    pip_packages = ['cgn', 'pytest', 'PyYAML']
    cgn.test.check_deb_packages(packages)
    cgn.test.check_pip_packages(pip_packages)

def test_all_interactive_start():
    """
    test_all_interactive_start
    """
    cgn.test.check_interactive_start(__file__)

def test_aarch64_dbw_box():
    """
    test_aarch64_dbw_box
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    device = '/dev/ttyTHS0'
    model = cgn.utils.run_subprocess_str('cat /proc/device-tree/model', use_assert=True)
    if 'quill' in model:
        device = '/dev/ttyTHS2'

    cmd = '{} ./{} {}'.format(
        os.path.join(script_dir, 'interactive_start.sh'),
        os.path.join('dbw_checker'), device)

    total_cnt = 5
    for num in range(total_cnt):
        now = datetime.datetime.now()
        print(now.strftime("%Y-%m-%d %H:%M:%S"))
        print('{}. cmd: {}'.format(num, cmd))
        cgn.utils.run_subprocess(cmd, use_assert=True)

def atest_online_stand():
    """
    test_online_stand_kromka
    """
    cmd = 'python3 start_online_stand.py kromka --console --min-fps=5'
    cmd += ' --duration=$ONLINE_STAND_DURATION --serial=auto --use-asserts'
    cgn.utils.run_subprocess(cmd, use_assert=True)
    if get_major_image_version() < 44:
        cgn.utils.run_subprocess(
            'python3 check_flycap_log.py logs_online_kromka.txt --max-diff=0.5',
            use_assert=True)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    remove_files_by_mask(os.path.join(script_dir, '..', '*.pgm'))

def get_offline_stand_cmd(domain: str):
    """
    get_offline_stand_cmd
    """
    cmd = 'python3 start_offline_stand.py {}'.format(domain)
    cmd += ' --console --min-fps=2 --short-list --use-asserts'

    return cmd

def test_offline_stand_kromka():
    """
    test_offline_stand_kromka
    """
    cgn.utils.run_subprocess(get_offline_stand_cmd('kromka'), use_assert=True)

def test_offline_stand_valok():
    """
    test_offline_stand_valok
    """
    cgn.utils.run_subprocess(get_offline_stand_cmd('valok'), use_assert=True)

def test_offline_stand_corn_rows():
    """
    test_offline_stand_corn_rows
    """
    cgn.utils.run_subprocess(get_offline_stand_cmd('corn_rows'), use_assert=True)

def check_files_owner(directory: str):
    """
    check_files_owner
    """
    status = True
    for root, subdirs, files in os.walk(directory):
        print(root)
        items = list(subdirs)
        items.extend(files)
        for path in items:
            full_path = os.path.join(root, path)
            if not os.path.islink(full_path) or (
                    os.path.islink(full_path) and os.path.exists(os.path.realpath(full_path))):
                file_stat = os.stat(full_path)
                if file_stat.st_uid != os.getuid() or file_stat.st_gid != os.getgid():
                    cgn.console.print_warning('Ownership problem: ', full_path)
                    status = False
    assert status

def test_all_files_owner():
    """
    test_all_files_owner
    """
    app_dir = get_app_dir()
    app_versions_dir = os.path.join(app_dir, 'versions')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    minimal_version_dir = os.path.abspath(os.path.join(script_dir, '..'))
    minimal_version_dir_parent = os.path.abspath(os.path.join(script_dir, '..', '..'))
    check_files_owner(minimal_version_dir)
    if minimal_version_dir_parent == app_versions_dir:
        check_files_owner(app_dir)

def get_app_dir():
    """
    get_app_dir
    """
    return os.path.join('/home', os.environ.get('USER'), 'app')

def test_all_device_id():
    """
    test_all_device_id
    """
    app_dir = get_app_dir()
    device_id_path = os.path.join(app_dir, 'ids', 'device_id')

    app_versions_dir = os.path.join(app_dir, 'versions')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    minimal_version_dir_parent = os.path.abspath(os.path.join(script_dir, '..', '..'))
    if minimal_version_dir_parent == app_versions_dir:
        assert os.path.exists(device_id_path)
        device_id = cgn.utils.read_str_from_file(device_id_path)
        hostname = cgn.utils.read_str_from_file('/etc/hostname').strip('\n')
        if hostname != device_id:
            cgn.console.colored_print('Actual:   {}'.format(device_id), cgn.colors.BOLD)
            cgn.console.colored_print('Expected: {}'.format(hostname), cgn.colors.BOLD)
            cgn.console.fix_it("cat /etc/hostname |tr -d '\\n' > {}".format(device_id_path))
            assert False

def test_all_dir_cleaner():
    """
    test_all_dir_cleaner
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_config = app_manager.get_default_config()
    data = cgn.utils.load_yaml(yaml_config)
    src_keys = list(data['services'].keys())
    for key in src_keys:
        if key != 'dir_cleaner':
            del data['services'][key]
    cmd = './dir_cleaner --config=/external-dir/configs/dir_cleaner.yml --dry_run'
    data['services']['dir_cleaner']['entrypoint'] = cmd
    data['services']['dir_cleaner']['restart'] = 'no'
    cgn.utils.save_yaml('dir_cleaner_test.yml', data, ' 1.1')

    cmd = '{} --container=dir_cleaner --without-check'.format(
        os.path.abspath(os.path.join(script_dir, '..', 'autostart.sh')))
    cmd += ' --without-detached --config=dir_cleaner_test.yml --abort-on-container-exit'
    cmd += ' --no-color --force-recreate'
    cgn.utils.run_subprocess('docker ps -a')
    result_str = cgn.utils.run_subprocess_str(cmd, use_assert=True)
    assert 'all folders exists, all good' in result_str
    stop_containers = os.path.abspath(os.path.join(script_dir, '..', 'stop_containers.sh'))
    cgn.utils.run_subprocess_str(
        '{} --container=dir_cleaner --config=dir_cleaner_test.yml'.format(stop_containers))

def test_all_dir_monitor():
    """
    test_all_dir_monitor
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_config = app_manager.get_default_config()
    data = cgn.utils.load_yaml(yaml_config)
    src_keys = list(data['services'].keys())
    for key in src_keys:
        if key != 'dir_monitor':
            del data['services'][key]
    cmd = './rust_dir_monitor --config=/external-dir/configs/dir_monitor.yml --dry_run'
    data['services']['dir_monitor']['entrypoint'] = cmd
    data['services']['dir_monitor']['restart'] = 'no'
    cgn.utils.save_yaml('dir_monitor_test.yml', data, ' 1.1')

    cmd = '{} --container=dir_monitor --without-check'.format(
        os.path.abspath(os.path.join(script_dir, '..', 'autostart.sh')))
    cmd += ' --without-detached --config=dir_monitor_test.yml --abort-on-container-exit'
    cmd += ' --no-color --force-recreate'
    cgn.utils.run_subprocess('docker ps -a')
    result_str = cgn.utils.run_subprocess_str(cmd, use_assert=True)
    assert 'config is correct' in result_str
    stop_containers = os.path.abspath(os.path.join(script_dir, '..', 'stop_containers.sh'))
    cgn.utils.run_subprocess_str(
        '{} --container=dir_monitor --config=dir_monitor_test.yml'.format(stop_containers))

def test_aarch64_carrier_id():
    """
    test_aarch64_carrier_id
    """
    app_dir = get_app_dir()
    carrier_id_path = os.path.join(app_dir, 'ids', 'carrier_id')
    assert os.path.exists(carrier_id_path)
    carrier_id = cgn.utils.read_str_from_file(carrier_id_path)
    if len(carrier_id) == 0 or carrier_id == 'undefined':
        cgn.console.fix_it('nano {}'.format(carrier_id_path))
        assert False

def test_aarch64_jetson_id():
    """
    test_aarch64_jetson_id
    """
    app_dir = get_app_dir()
    jetson_id_path = os.path.join(app_dir, 'ids', 'jetson_id')
    assert os.path.exists(jetson_id_path)
    jetson_id = cgn.utils.read_str_from_file(jetson_id_path)
    if len(jetson_id) == 0 or jetson_id == 'undefined':
        cgn.console.fix_it('nano {}'.format(jetson_id_path))
        assert False

def test_aarch64_crontab():
    """
    test_aarch64_crontab
    """
    result_str = cgn.utils.run_subprocess_str('crontab -l', use_assert=True)
    result_str_arr = result_str.split('\n')

    app_dir = get_app_dir()
    jetson_id_cmd = 'cat /proc/device-tree/serial-number | tr -cd \'[[:digit:]]\''
    jetson_id_cmd += ' > {}/ids/jetson_id'.format(app_dir)
    carrier_id_cmd = 'python3 {0}/scripts/save_carrier_id.py {0}/ids/carrier_id'.format(
        app_dir)
    reboot_cmd = '@reboot sleep 60 && '
    expected_lines = [reboot_cmd + jetson_id_cmd, reboot_cmd + carrier_id_cmd]

    actual_lines = []
    for expected_line in expected_lines:
        for line in result_str_arr:
            if line.find(expected_line) == 0:
                actual_lines.append(line)

    print('Actual: ', actual_lines)
    print('Expected: ', expected_lines)
    assert len(actual_lines) == len(expected_lines)

def test_aarch64_systemd_docker():
    """
    test_aarch64_systemd_docker
    """
    version_str = get_info_version()
    if 't71' in version_str:
        docker_service_cfg = '/lib/systemd/system/docker.service'
        result_int = cgn.utils.run_subprocess_int(
            'cat {} | grep -c ExecStartPre=/bin/sleep'.format(docker_service_cfg))
        if result_int != 1:
            cgn.utils.run_subprocess_int(
                'cat {} | grep -c ExecStartPre='.format(docker_service_cfg))
            msg = 'Add line "ExecStartPre=/bin/sleep 10" to file {}\n\
sudo systemctl daemon-reload\nsudo systemctl restart docker'.format(docker_service_cfg)
            cgn.console.fix_it(msg)
            assert False

if __name__ == "__main__":
    check_base_conditions()
