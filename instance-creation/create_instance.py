import os
import time
import paramiko

import urllib3
from novaclient import client as novaclient
from glanceclient import Client as glanceclient
from neutronclient.v2_0 import client as neutronclient
from keystoneauth1 import loading, session

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_SEC_GRPS = ['default']
DEFAULT_NETWORK_ID = 'privatenew'
DEFAULT_INSTANCE_NAME = 'temp-instance'


OS_AUTH_URL = os.environ.get('OS_AUTH_URL') or ''
OS_USERNAME = os.environ.get('OS_USERNAME') or 'admin'
OS_PASSWORD = os.environ.get('OS_PASSWORD') or ''
OS_PROJECT_NAME = os.environ.get('OS_PROJECT_NAME') or 'admin'
OS_TENANT_NAME = os.environ.get('OS_TENANT_NAME') or 'admin'
OS_PROJECT_DOMAIN_NAME = os.environ.get('OS_PROJECT_DOMAIN_NAME') or 'Default'
OS_USER_DOMAIN_NAME = os.environ.get('OS_USER_DOMAIN_NAME') or 'Default'

# INSTANCE_NAME = os.environ.get('INSTANCE_NAME') or \
#                 'touchstone-server-%s' % time.strftime('%d-%m-%Y-%H%M%S')
SNAPSHOT_NAME = os.environ.get('SNAPSHOT_NAME') or \
                'touchstone-server-snapshot-%s' % \
                time.strftime('%d-%m-%Y-%H%M%S')
SOURCE_IMAGE_NAME = os.environ.get('SOURCE_IMAGE_NAME') or ''
FLAVOR_NAME = os.environ.get('FLAVOR_NAME') or 'touchstone-flavor-small'
NETWORK_NAME = os.environ.get('NETWORK_NAME') or 'private'

USER = os.environ.get('SSH_USER') or 'root'
SSH_PASSWORD = os.environ.get('SSH_PASSWORD') or ''
SSH_KEY = os.environ.get('SSH_KEY') or None

SSH_WAIT_TIME = int(os.environ.get('SSH_WAIT_TIME') or 120)

def get_identity_version(auth_url):
    return auth_url.split('/')[-1][-1]
def get_session():
    kwargs = {'auth_url': OS_AUTH_URL, 'username': OS_USERNAME,
              'password': OS_PASSWORD}
    auth_version = get_identity_version(OS_AUTH_URL)
    if auth_version == '3':
        kwargs.update({'user_domain_name': OS_USER_DOMAIN_NAME,
                       'project_domain_name': OS_PROJECT_DOMAIN_NAME,
                       'project_name': OS_PROJECT_NAME})
    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(**kwargs)

    sess = session.Session(auth=auth, verify=False)

    return sess

def get_nova_client():
    return novaclient.Client(version='2', session=get_session())

def get_neutron_client():
    return neutronclient.Client(session=get_session())

def get_glance_client():
    return glanceclient(version='2', session=get_session())

def get_ssh_client(*args, **kwargs):
    username = kwargs['username']
    # passwd = kwargs['password']
    host = kwargs['host']
    ssh_client = paramiko.SSHClient()

    private_key = paramiko.RSAKey.from_private_key(kwargs['pkey'])

    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_client.connect(host, username=username, pkey=private_key)

    return ssh_client

def get_image_info(name):
    glance_client = get_glance_client()
    images = glance_client.images.list()
    matched_images = [image for image in images if image.name == name]
    if matched_images:
        return matched_images[0]
    else:
        return None

def get_flavor_info(name):
    nova_client = get_nova_client()
    flavors = nova_client.flavors.list()
    matched_flavors = [flavor for flavor in flavors if flavor.name == name]
    return matched_flavors[0] if matched_flavors else None

def get_network_info(name):
    nc = get_nova_client()
    # neutron_client = get_neutron_client()
    # networks = neutron_client.networks.list()

    networks = nc.networks.list()
    network = [network for network in networks if network.human_id == name]
    return network[0]

    # network_details = nc.neutron.find_network(name)
    # print str(network_details)
    # return network_details


def create_instance(flavor_name=None, image_name=None, security_groups=None, network_id=None):
    nova_client = get_nova_client()
    image = get_image_info(image_name)
    flavor = get_flavor_info(flavor_name)
    network = get_network_info(network_id)

    instance = nova_client.servers.create(name=DEFAULT_INSTANCE_NAME, image=image, flavor=flavor,
                                      security_groups=security_groups,
                                      nics=[{'net-id': network.id}])
    return instance



def add_floating_ip(instance):
    # neutron_client = get_neutron_client()
    # fips = neutron_client.list_floatingips()
    # my_fip = fips['floatingips'][0]
    print "Adding FIP to %s " % instance.name
    nc = get_nova_client()
    fip_pools = nc.floating_ip_pools.list()
    fip_pool = fip_pools[0]
    fip = nc.floating_ips.create(fip_pool.name)

    instance.add_floating_ip(fip)
    instance.fip = fip.ip

def to_wait_for_ssh(command_to_execute=None, **ssh_credentials):
    ssh_client = get_ssh_client(**ssh_credentials)


if __name__ == '__main__':

    pkey_contents = ""

    import StringIO
    pkey_file = StringIO.StringIO(pkey_contents)

    # ssh_credentials = \
    #     {'username': 'root', 'host': instance.fip, 'password': ''}

    ssh_credentials = \
        {'username': 'ubuntu', 'host': '', 'pkey': pkey_file}

    # to_wait_for_ssh(command_to_execute='hostname', **ssh_credentials)

    ssh_client = get_ssh_client(**ssh_credentials)
    print ssh_client
