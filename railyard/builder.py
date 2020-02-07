import docker
import railyard.tools as tools
import time

def build(path, tag):
    """
    Build container image at the given path and tag it with the given tag
    """
    client = docker.from_env()

    print(f'Building Docker image for {tag}...')

    start_time = time.time()
    with tools.cd(path):
        successful = False
        build_retries = 3
        counter = 0
        while not successful and counter<build_retries:
            try:
                client.images.build(path=path, tag=tag, rm=True, forcerm=True)
                print(f'Done building {tag}. Total time: {time.time() - start_time} seconds')
                successful = True
            except Exception as e:
                print(f'Error occured while building {tag}. Log: "{e}". Retrying...')
            finally:
                counter += 1

def pushImage(package_hash, repo):
    client = docker.from_env()
    client.login(username='ktaletsk', password='d477e5c5-5652-4d75-a610-634b70c789c8')
    tag = repo + ':' + package_hash
    start_time = time.time()

    # Push the Docker container
    successful = False
    while not successful:
        try:
            print('Pushing Docker image for ' + tag + '...')
            # time.sleep(10)
            client.images.push(repository=repo, tag=package_hash)
            print('Done pushing ' + tag + f'. Total time: {time.time() - start_time} seconds')
            successful = True
        except Exception as e:
            print(f'Error occured while pushing {tag}. Log: "{e}". Retrying...')
