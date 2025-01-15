
#!/usr/bin/python3

import sys
import os
import os.path
import logging
import threading
import time
import socket
import subprocess
import shlex
import signal
import psutil
import getpass

# Set the burnGPURenderer file to use burnGPURenderer_2025.1
adapter_dir = '/opt/Autodesk/backburner/Adapters/'
renderer_file = os.path.join(adapter_dir, 'burnGPURenderer_2025.1')

if not os.path.isfile(renderer_file):
    sys.exit(-1)

for p in psutil.process_iter():
    if 'pcoip-session-launcher' in p.name() or 'pcoip-session-launcher' in ' '.join(p.cmdline()):
        print("Cannot burn in Teradici mode")
        sys.exit(-1)

def sigterm_handler(_signo, _stack_frame):
    print("SIG called  - cleaning up killall burn_gpu")
    os.system(f'{renderer_file} -o ShutDown')
    os.system("/usr/bin/sudo killall burn_gpu")
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)

class kill_thread(threading.Thread):
    def __init__(self, name, wait_process, wait_log):
        threading.Thread.__init__(self)
        self.name = name
        self.process = None
        self.wait_process = wait_process
        self.wait_log = wait_log
        self.host_name = socket.gethostname()
        self.start_time = time.time()
        self.killed = False
        self.exit_status = 0

    def run(self):
        log_file = "/opt/Autodesk/log/burn20251_%s_shell.log" % self.host_name
        found = not self.wait_log
        count = 0
        while not found and count < 10:
            try:
                if self.start_time < os.path.getmtime(log_file):
                    found = True
            except:
                continue
            time.sleep(1)
            print('inc counter')
            count = count + 1
        print(found)
        if not found and self.wait_log:
            try:
                self.wait_process.terminate()
            except:
                pass

        command = '/usr/bin/tail -n 1000 -F %s' % log_file

        if self.killed:
            self.exit_status = -13
            return

# this is for cathing for errors to fail tasks
        self.process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
        while True and not self.killed:
            output = self.process.stdout.readline()
            if output == b'' and self.process.poll() is not None:
                break
            if output:
                output = output.strip()
                if any(err in output for err in [
                    b"Cannot reach destination library", b"Could not resolve local host gateway: Server not found",
                    b"Failed to set CUDA device", b"Fail to push CUDA context", b"Out of memory",
                    b"[General software error]", b"Burn exited prematurely (see Burn log)",
                    b"Burn task error:",
                    b"Unable to connect to framestore map server: Connection refused.",
                    b"Error initializing the framestore map; Please check sw_probed.",
                    b"ERROR: Failed to initialize Stone+Wire connection: File system init failed",
                    b"Error initialising volume . File system init failed",
                    b"Project command line error: Failed to find project", b"Could not retrieve library",
                    b"Unable to parse file", b"This application failed to start because no Qt platform plugin could be initialized.",
                    b"File system init failed", b"Batch : Error", b"Fatal: ", b"Error loading",
                    b"Unable to connect to framestore map server: Connection refused.",
		    b"Error: abnormal termination",
		    b"Project command line error:",
		    b"An error occured when trying to get the licensing system lock.Failed to lock",
		    b"Failed to allocate memory for requested buffer",
		    b"Could not submit drawlist: RIVKCmdList submit failed."

                ]):
                    if self.wait_process:
                        self.wait_process.terminate()
                    os.system("/usr/bin/sudo killall burn_gpu")
                    self.exit_status = -13

                print("shell_log", output.strip())

    def kill(self):
        print(self.process)
        if self.process:
            self.process.terminate()
        self.killed = True

batch = sys.argv[1]
project = batch.split("/")[4]
username = getpass.getuser()

tail = None
launch_app = False

if os.path.isfile("/tmp/current.batch"):
    cb = open("/tmp/current.batch").read()
    print("Current batch", cb)
    if cb != batch:
        launch_app = True

    if (time.time() - os.path.getmtime("/tmp/current.batch")) / 60.0 > 20:
        launch_app = True

else:
    launch_app = True

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 7241))
    s.close()
except:
    launch_app = True

if launch_app:
    os.system(f'{renderer_file} -o ShutDown')
    os.system("/usr/bin/sudo killall burn_gpu")

    print("Launching burnGPURenderer")
    tail = kill_thread('burn', None, True)
    tail.start()
    x = subprocess.Popen([renderer_file, '-o', 'LaunchApp', '-j', batch])
    tail.wait_process = x
    x.wait()

    file = open('/tmp/current.batch', 'w')
    file.write(batch)
    file.close()

    try:
        os.chmod('/tmp/current.batch', 0o777)
    except:
        print('chmod issue')

    start_code = x.returncode

    if start_code == 0:
        file = open('/tmp/current.batch', 'w')
        file.write(batch)
        file.close()

    print("START_CODE", start_code)
    if start_code != 0:
        os.system("/usr/bin/sudo killall tail")
        tail.kill()
        tail.join()
        sys.exit(1)
else:
    tail = kill_thread('burn', None, False)
    tail.start()

status = subprocess.Popen(shlex.split(f'{renderer_file} -o NewTask -l Debugex -j "{batch}" -s {sys.argv[2]} -n {int(sys.argv[3]) - int(sys.argv[2]) + 1} -a {batch.rsplit(".", 1)[0]}.zip'))
tail.wait_process = status
status.wait()
time.sleep(3)
tail.kill()
tail.join()

ret = status.returncode
if ret == 0:
    ret = tail.exit_status
sys.exit(ret)
