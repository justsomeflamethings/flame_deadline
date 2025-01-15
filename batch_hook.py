def batch_burn_end(info, userData, *args, **kwargs):
    import subprocess
    import time
    import os
    import flame
    import glob
    import shutil
    import getpass
    import socket
    import math

    host = socket.gethostname()
  
    # can set root SAN path based on hostname, if multiple volumes
    if "-location2" in host:
        server = "/Volumes/MY_SAN2"
    else:
        server = "/Volumes/MY_SAN"

    username = getpass.getuser()

    print(info, userData)

    project_name = flame.project.current_project.name

    # we use a seperate script that will set the chunks from a flame menu deadline_chunks.py (number of frames per task)

    # this pulls the chunk number saved from the file or use 5
     chunk = "5"
    last_update_file = '%s/.flamestore/userdata/%s/%s.deadline.*' % (server, username, project_name)
    chunks = glob.glob(last_update_file)
    print("chunks", chunks)
    if len(chunks) > 0:
        chunk = chunks[0].split('.')[-1]

    export_dir = "%s/Job/%s/Post/VFX/.burn" % (server, project_name)
    print("Export Dir", export_dir)

    try:
        os.makedirs(export_dir, exist_ok=True)
    except:
        pass
    print(".burn created")

    # ip address of your burn manager
    bbm = "192.168.1.10"
    
    # secondary pool all so job will use other avail burn nodes if other pools are idle
    secondary_pool = 'all'

    # grab the burn tar file from the burn manager
    print(bbm, info['backgroundJobName'])
    batch = glob.glob('/hosts/%s/opt/Autodesk/backburner/Network/Jobs/*%s' % (bbm, info['backgroundJobName']))
    print("Batch", batch)
    retry = 0
    while retry < 5 and len(batch) == 0:
        time.sleep(3)
        batch = glob.glob('/hosts/%s/opt/Autodesk/backburner/Network/Jobs/*%s' % (bbm, info['backgroundJobName']))
        print("Retry", retry)

        print("Batch", batch)

        retry = retry + 1

    print("Batch", batch)
    basename = os.path.basename(batch[0])
    print('sleeping for 3')
    time.sleep(3)
    print('done sleeping for 3')
    strip_base = basename.split(" ")[1]

    cp_command = ['/usr/bin/cp', '-rv', batch[0], "%s/%s" % (export_dir, strip_base)]
    print(cp_command)
    x = subprocess.run(cp_command, capture_output=True)
    print("X is ", x)

    cp_command = ['/bin/ls', '-al', "%s/%s" % (export_dir, strip_base)]
    print(cp_command)
    x = subprocess.run(cp_command, capture_output=True)
    print("X is ", x.stdout.decode())
    print('sleeping for 3')
    time.sleep(0)
    print('done sleeping for 3')
    import zipfile
    z = zipfile.ZipFile("%s/%s/%s.zip" % (export_dir, strip_base, strip_base))
    print(z.infolist())
    z.extractall("%s/%s" % (export_dir, strip_base))

    tar_command = ['/usr/bin/tar', '-C', "%s/%s" % (export_dir, strip_base), '-zxvf', "%s/%s/%s.tgz" % (export_dir, strip_base, strip_base)]
    print(tar_command)
    x = subprocess.run(tar_command, capture_output=True)
    #print("X is ", x)

    xml = "%s/%s/%s.xml" % (export_dir, strip_base, strip_base)

    data = open(xml).read()
    frames = data.split('NumberTasks')[1][1:-2]
    description = data.split('Description>')[1][1:-2].strip()
    print('Description', description)
    os.system("/opt/Thinkbox/Deadline10/bin/deadlinecommand -ChangeUser %s" % username)

    # which pool the flame will submit too
    pools = {
        'flame01': 'pool1',
        'flame02': 'pool2',
	'flame03': 'pool3',
	#......
    }
    
    # could have different groups for diff spec hardware, or not use and hardcode in the commands below
    groups = {
        'flame01': 'burn',
        'flame02': 'burn',
        'flame03': 'burn'
	#.....
    }

    print("/opt/Thinkbox/Deadline10/bin/deadlinecommand -SubmitCommandLineJob -executable  /Volumes/MY_SAN/Resources/Engineering/Flame/flame.py  -arguments '<QUOTE>%s<QUOTE> <STARTFRAME> <ENDFRAME>'  '-frames'  '0-%d' -chunksize %s  -name '%s' -pool %s  -group %s -prop SecondaryPool=%s -prop TaskTimeoutMinutes=15 -prop PostJobScript=/Volumes/MY_SAN/Resources/Engineering/Flame/post_job.py  -prop ExtraInfo0='%s'" % (xml, int(frames), chunk, description, pools[os.uname()[1]], groups[os.uname()[1]], secondary_pool, os.path.basename(batch[0])))

    output = os.popen("/opt/Thinkbox/Deadline10/bin/deadlinecommand -SubmitCommandLineJob -executable  /Volumes/MY_SAN/Resources/Engineering/Flame/flame.py  -arguments '<QUOTE>%s<QUOTE> <STARTFRAME> <ENDFRAME>'  '-frames'  '0-%d' -chunksize %s  -name '%s' -pool %s  -group %s -prop SecondaryPool=%s -prop TaskTimeoutMinutes=15 -prop PostJobScript=/Volumes/MY_SAN/Resources/Engineering/Flame/post_job.py  -prop ExtraInfo0='%s'" % (xml, int(frames), chunk, description, pools[os.uname()[1]], groups[os.uname()[1]], secondary_pool, os.path.basename(batch[0]))).read()

    print(output)
    job_id = output.split('JobID=')[1].split("\n")[0]

    os.system("/opt/Thinkbox/Deadline10/bin/deadlinecommand SetJobMachineLimitMaximum %s 40" % job_id)

    print(info, userData)
    pass
