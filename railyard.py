import os
import time
import yaml
import tempfile
import copy
import hashlib
import docker
import itertools
import subprocess
from multiprocessing import Pool, Process, Lock

def sort_dep_list(dep_list):
    return sorted(dep_list, key=lambda k: next(iter(k)) if type(k)==dict else k)

def get_hash(package):
    p = copy.deepcopy(package)
    
    # Name of the base stack does not matter for hash
    p.pop('name')
    
    # Sort everything by package name or put into set to make hash stable under permutations
    p['dependencies']['env'] = sort_dep_list(p['dependencies']['env'])
    p['dependencies']['apt'] = sort_dep_list(p['dependencies']['apt'])
    p['dependencies']['conda'] = sort_dep_list(p['dependencies']['conda'])
    p['dependencies']['pip'] = sort_dep_list(p['dependencies']['pip'])
    p['dependencies']['labextensions'] = sort_dep_list(p['dependencies']['labextensions'])
    p['dependencies']['scripts'] = sort_dep_list(p['dependencies']['scripts'])
    p['dependencies']['addfiles'] = sort_dep_list(p['dependencies']['addfiles'])
    
    return hashlib.sha256(repr(sorted(p.items())).encode()).hexdigest()

def dockerfile_block(name, lines):
    offset = ' ' * (len(name) + 1)
    return name + ' ' + ('\n'+offset).join(lines) + '\n'

def dockerfile_comment(comment):
    return '# ' + comment + '\n'

def readStacks(base_stack, additional_stacks):
    # Open base stack
    with open(base_stack) as file:
        base_stack_obj = yaml.safe_load(file)

    # Open additional stacks
    for stack in additional_stacks:
        with open(stack) as file:
            stack_obj = yaml.safe_load(file)
            
            if 'dependencies' in stack_obj:
                # Merge environment variables
                if 'env' in stack_obj['dependencies']:
                    base_stack_obj['dependencies']['env'].extend(stack_obj['dependencies']['env'])

                # Merge apt-get dependencies
                if 'apt' in stack_obj['dependencies']:
                    base_stack_obj['dependencies']['apt'].extend(stack_obj['dependencies']['apt'])

                # Merge conda dependencies
                if 'conda' in stack_obj['dependencies']:
                    base_stack_obj['dependencies']['conda'].extend(stack_obj['dependencies']['conda'])
                
                # Merge pip dependencies
                if 'pip' in stack_obj['dependencies']:
                    base_stack_obj['dependencies']['pip'].extend(stack_obj['dependencies']['pip'])

                # Merge jupyter labextensions
                if 'labextensions' in stack_obj['dependencies']:
                    base_stack_obj['dependencies']['labextensions'].extend(stack_obj['dependencies']['labextensions'])

                # Merge install scripts
                if 'scripts' in stack_obj['dependencies']:
                    base_stack_obj['dependencies']['scripts'].extend(stack_obj['dependencies']['scripts'])
                
                # Merge addfiles
                if 'addfiles' in stack_obj['dependencies']:
                    print(stack_obj['dependencies']['addfiles'])
                    base_stack_obj['dependencies']['addfiles'].extend(stack_obj['dependencies']['addfiles'])
    return base_stack_obj

def buildAndPush(base_stack_obj, repo, l):
    start_time = time.time()

    # Create temporary folder for Dockerfile and additional files
    # Folder is securely created with `tempfile` and is destroyed afterwards
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create list of Conda packages
        conda_packages = []
        for entry in base_stack_obj['dependencies']['conda']:
            if type(entry)==dict:
                conda_packages.append(f'{list(entry.keys())[0]}={list(entry.values())[0]}')
            elif type(entry)==str:
                conda_packages.append(entry)
        
        # Create list of pip packages
        pip_packages = []
        for entry in base_stack_obj['dependencies']['pip']:
            if type(entry)==dict:
                pip_packages.append(f'{list(entry.keys())[0]}=={list(entry.values())[0]}')
            elif type(entry)==str:
                pip_packages.append(entry)
        
        # Create list of JupyterLab exte packages
        labextensions = []
        if 'labextensions' in base_stack_obj['dependencies']:
            for entry in base_stack_obj['dependencies']['labextensions']:
                if type(entry)==dict:
                    labextensions.append(f'{list(entry.keys())[0]}@{list(entry.values())[0]}')
                elif type(entry)==str:
                    labextensions.append(entry)
        
        os.chdir(tmpdirname)
        package_hash = get_hash(base_stack_obj)
        # print('Assembling Dockerfile for container ' + package_hash + ' in ' + tmpdirname)
        
        with open('Dockerfile', 'w') as file:
            file.write(dockerfile_block('ARG', ['BASE_CONTAINER=ubuntu:bionic-20190612@sha256:9b1702dcfe32c873a770a32cfd306dd7fc1c4fd134adfb783db68defc8894b3c']))
            file.write('\n')
            file.write(dockerfile_block('FROM', ['$BASE_CONTAINER']))
            file.write('\n')
            file.write(dockerfile_block('LABEL', [f'hash="{package_hash}"']))
            file.write('\n')
            file.write(dockerfile_block('ARG', ['NB_USER="jovyan"\nARG NB_UID="1000"\nARG NB_GID="100"']))
            file.write('\n')
            # Copy files to add
            for addfile in base_stack_obj['dependencies']['addfiles']:
                name = list(addfile.keys())[0]
                dest = addfile[name]['destination']
                file_source = addfile[name]['source']
                with open(name, 'w+') as f:
                    f.write(file_source)
                if 'permissions' in addfile[name]:
                    permissions = addfile[name]['permissions']
                    os.chmod(name, permissions)
                file.write(dockerfile_block('ADD', [f'{name} {dest}']))
            file.write('\n')
            file.write(dockerfile_block('ENV', ['DEBIAN_FRONTEND=noninteractive \\',
                                                'CONDA_DIR=/opt/conda \\',
                                                'SHELL=/bin/bash \\',
                                                'NB_USER=$NB_USER \\',
                                                'NB_UID=$NB_UID \\',
                                                'NB_GID=$NB_GID \\',
                                                'LC_ALL=en_US.UTF-8 \\',
                                                'LANG=en_US.UTF-8 \\',
                                                'LANGUAGE=en_US.UTF-8']))
            file.write(dockerfile_block('ENV',[f'{list(dep.keys())[0]}={list(dep.values())[0]} \\' if i<len(base_stack_obj['dependencies']['env'])-1 else f'{list(dep.keys())[0]}={list(dep.values())[0]}' for i,dep in enumerate(base_stack_obj['dependencies']['env'])]))
            file.write('\n')
            file.write(dockerfile_block('USER', ['root']))
            file.write('\n')
            file.write(dockerfile_comment('Install all OS dependencies'))
            file.write(dockerfile_block('RUN', ['apt-get update && \\',
                                                'apt-get -y install software-properties-common && \\',
                                                'add-apt-repository ppa:apt-fast/stable && \\',
                                                'apt-get update && \\',
                                                'apt-get -y install apt-fast && \\',
                                                'apt-fast update && \\',
                                                f'apt-fast install -yq --no-install-recommends {" ".join(base_stack_obj["dependencies"]["apt"])} && \\',
                                                'rm -rf /var/lib/apt/lists/*']))
            file.write('\n')
            file.write(dockerfile_block('RUN', ['echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \\','locale-gen']))
            file.write('\n')
            file.write(dockerfile_comment("Create NB_USER with name jovyan user with UID=1000 and in the 'users' group"))
            file.write(dockerfile_comment("and make sure these dirs are writable by the `users` group."))
            file.write(dockerfile_block('RUN', ['echo "auth requisite pam_deny.so" >> /etc/pam.d/su && \\',
                                                "sed -i.bak -e 's/^%admin/#%admin/' /etc/sudoers && \\",
                                                "sed -i.bak -e 's/^%sudo/#%sudo/' /etc/sudoers && \\",
                                                'useradd -m -s /bin/bash -N -u $NB_UID $NB_USER && \\',
                                                'mkdir -p $CONDA_DIR && \\',
                                                'chown $NB_USER:$NB_GID $CONDA_DIR && \\',
                                                'chmod g+w /etc/passwd && \\',
                                                'fix-permissions $HOME && \\',
                                                'fix-permissions "$(dirname $CONDA_DIR)"']))
            file.write('\n')
            file.write(dockerfile_block('USER', ['$NB_UID']))
            file.write(dockerfile_block('WORKDIR', ['$HOME']))
            file.write('\n')
            file.write(dockerfile_block('RUN', ['cd /tmp && \\',
                                                'wget --quiet https://repo.continuum.io/miniconda/Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh && \\',
                                                'echo "0dba759b8ecfc8948f626fa18785e3d8 *Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh" | md5sum -c - && \\',
                                                '/bin/bash Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh -f -b -p $CONDA_DIR && \\',
                                                'rm Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh && \\',
                                                'echo "conda ${CONDA_VERSION}" >> $CONDA_DIR/conda-meta/pinned && \\',
                                                '$CONDA_DIR/bin/conda config --system --prepend channels bioconda && \\',
                                                '$CONDA_DIR/bin/conda config --system --prepend channels conda-forge && \\',
                                                '$CONDA_DIR/bin/conda config --system --set auto_update_conda false && \\',
                                                '$CONDA_DIR/bin/conda config --system --set show_channel_urls true && \\',
                                                '$CONDA_DIR/bin/conda config --system --set channel_priority strict && \\',
                                                '$CONDA_DIR/bin/conda install pycryptosat && \\',
                                                '$CONDA_DIR/bin/conda config --system --set sat_solver pycryptosat && \\',
                                                f'$CONDA_DIR/bin/conda install -y {" ".join(conda_packages)} && \\',
                                                f'pip install {" ".join(pip_packages)} && \\',
                                                '$CONDA_DIR/bin/conda list python | grep "^python " | tr -s " " | cut -d "." -f 1,2 | sed "s/$/.*/" >> $CONDA_DIR/conda-meta/pinned && \\',
                                                '$CONDA_DIR/bin/conda list tini | grep tini | tr -s " " | cut -d " " -f 1,2 >> $CONDA_DIR/conda-meta/pinned && \\',
                                                'npm cache clean --force && \\',
                                                'jupyter notebook --generate-config && \\',
                                                'rm -rf $CONDA_DIR/share/jupyter/lab/staging && \\',
                                                'conda clean --all -f -y && \\',
                                                'rm -rf /home/$NB_USER/.cache/yarn && \\',
                                                'find /opt/conda/ -follow -type f -name "*.a" -delete && \\',
                                                'find /opt/conda/ -follow -type f -name "*.pyc" -delete && \\',
                                                'find /opt/conda/ -follow -type f -name "*.js.map" -delete && \\',
                                                'fix-permissions $CONDA_DIR && \\',
                                                'fix-permissions /home/$NB_USER']))
            file.write('\n')
            # Extract scripts
            scripts = [item.split('\n') for sublist in [list(script.values()) for script in base_stack_obj['dependencies']['scripts']] for item in sublist]
            for s in scripts:
                file.write(dockerfile_block('RUN', s))
            file.write('\n')
            if labextensions:
                file.write(dockerfile_block('RUN', [f'jupyter labextension install --no-build {" ".join(labextensions)} && \\',
                                                    'jupyter lab build --dev-build=False && \\',
                                                    'npm cache clean --force']))
            file.write('\n')
            file.write('# Add symbolic link to the shared filesystem\n')
            file.write(dockerfile_block('RUN', ['ln -s /opt/shared shared']))
            file.write('\n')
            file.write(dockerfile_block('EXPOSE', ['8888']))
            file.write('\n')
            file.write(dockerfile_comment('Configure container startup'))
            file.write(dockerfile_block('ENTRYPOINT', ['["tini", "-g", "--"]']))
            file.write(dockerfile_block('CMD', ['["start-notebook.sh"]']))
            file.write('\n')
            file.write(dockerfile_comment('Add local files as late as possible to avoid cache busting'))
            file.write(dockerfile_block('COPY', ['start.sh /usr/local/bin/']))
            file.write(dockerfile_block('COPY', ['start-notebook.sh /usr/local/bin/']))
            file.write(dockerfile_block('COPY', ['start-singleuser.sh /usr/local/bin/']))
            file.write(dockerfile_block('COPY', ['jupyter_notebook_config.py /etc/jupyter/']))
            file.write('\n')
            file.write(dockerfile_comment('Fix permissions on /etc/jupyter as root'))
            file.write(dockerfile_block('USER', ['root']))
            file.write(dockerfile_block('RUN', ['fix-permissions /etc/jupyter/']))
            file.write('\n')
            file.write(dockerfile_comment('Switch back to jovyan to avoid accidental container runs as root'))
            file.write(dockerfile_block('USER', ['$NB_UID']))

        # Set up Docker
        client = docker.from_env()
        tag = repo + ':' + package_hash

        # Check if image already exists
        res = subprocess.run(['docker', 'manifest', 'inspect', f'{tag}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            print('Docker image ' + tag + ' already exists on Dockerhub. Skipping building and pushing')
            return

        # Check if image cache exist locally
        if client.images.list(tag) != []:
            print('Docker image ' + tag + ' already exists locally. Skipping building')
        else:
            # Build Docker container
            print('Building Docker image for ' + tag + '...')
            try:
                client.images.build(path=tmpdirname, tag=tag)
            except:
                print('Error occured while building ' + tag)

        # Push the Docker container
        l.acquire()
        try:
            print('Pushing Docker image for ' + tag + '...')
            client.images.push(repository=repo, tag=package_hash, decode=True)
            print('Done pushing ' + tag + f'. Total time: {time.time() - start_time} seconds')
            status_push = True
        except:
            print(f'Error occured while pushing {tag}')
        finally:
            l.release()

def createAllVariants(groups):
    # All combinations of groups of additional stacks + base stack
    options = []
    for l in range(len(groups)):
        for i in (itertools.combinations(groups, l)):
            s = ([item for sublist in i for item in sublist])
            options.append(s)
    return options

if __name__ == '__main__':
    repo = 'ktaletsk/polus-notebook'
    base_stack = 'base.yaml'
    groups = [
        ['Python-datascience.yaml', 'Python-dataviz.yaml'],
        ['R.yaml'],
        ['octave.yaml'],
        ['java.yaml', 'scala.yaml'],
        ['julia.yaml'],
        ['cpp.yaml'],
        ['bash.yaml']
    ]
    variants = createAllVariants(groups)
    stack_objs = [readStacks(base_stack, additional_stack) for additional_stack in variants]
    lock = Lock()
    for stack_obj in stack_objs:
        Process(target=buildAndPush, args=(stack_obj, repo, lock)).start()