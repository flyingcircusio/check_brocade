from prettytable import PrettyTable
from xml.etree import ElementTree
import datetime
import pytz
import requests
import sys
import xml.etree

# TODO
# show in local time (and say so) 
# show log in local time and better formatting
# status check


LOCAL_TIME = pytz.timezone('Europe/Berlin')

OK = 0
WARN = 1
CRIT = 2
UNKN = 3


class Status(object):

    status = OK

    def update(self, status):
        self.status = max([self.status, status])

check_status = Status()

ns = {'clock': 'urn:brocade.com:mgmt:brocade-clock',
      'system': 'urn:brocade.com:mgmt:brocade-system',
      'system-monitor': 'urn:brocade.com:mgmt:brocade-system-monitor-ext',
      'raslog': 'urn:brocade.com:mgmt:brocade-ras-ext',
      'vcs': 'urn:brocade.com:mgmt:brocade-vcs'}

host_fqdn = sys.argv[1]
host = host_fqdn.split('.')[0]


c = requests.Session()
c.auth = ('user', 'insulate-aye-aquiline')

print('Brocade VDX status - {}\n'.format(host))

print('System\n')

system = PrettyTable()
system.field_names = ['item', 'info', 'status']
system.header = False
system.align = 'l'

r = c.post('http://{}/rest/operational-state/show-clock'.format(host_fqdn), data='<show-clock></show-clock>').content
r = ElementTree.fromstring(r)
time = r.find('.//clock:current-time', ns).text
zone = r.find('.//clock:timezone', ns).text
tz = pytz.timezone(zone)
time = time.split('+')[0]
time = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=tz)
time = time.astimezone(LOCAL_TIME)

now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
offset = abs(now - time).total_seconds()

time_state = OK if offset < 5 else WARN if offset < 30 else CRIT
check_status.update(time_state)
time_state = 'OK' if time_state == OK else 'WARN' if time_state == 'WARN' else 'CRIT' if time_state == 'CRIT' else '?'

system.add_row(['Current time', time.strftime('%Y-%m-%d %H:%M:%S'), time_state])

r = c.post('http://{}/rest/operational-state/get-last-config-update-time'.format(host_fqdn), data='<get-last-config-update-time></get-last-config-update-time>').content
r = ElementTree.fromstring(r)
timestamp = int(r.find('.//vcs:last-config-update-time', ns).text)
last_change = datetime.datetime.fromtimestamp(timestamp, tz).astimezone(LOCAL_TIME)
system.add_row(['Last config change', last_change.strftime('%Y-%m-%d %H:%M:%S'), ''])

r = c.post('http://{}/rest/operational-state/get-system-uptime'.format(host_fqdn), data='<get-system-uptime></get-system-uptime>').content
r = ElementTree.fromstring(r)
days = int(r.find('.//system:days', ns).text)
hours = int(r.find('.//system:hours', ns).text)
minutes = int(r.find('.//system:minutes', ns).text)
seconds = int(r.find('.//system:seconds', ns).text)

total_uptime = days * 24
total_uptime = (total_uptime + hours) * 60
total_uptime = (total_uptime + minutes) * 60
total_uptime = (total_uptime + seconds)

uptime_status = 'OK'
if total_uptime < (30*60):
    check_status.update(CRIT)
    uptime_status = 'CRIT'
elif total_uptime < (2*60*60):
    check_status.update(WARN)
    uptime_status = 'WARN'

uptime = '{} days {:02d}:{:02d}:{:02d}'.format(days, hours, minutes, seconds)
system.add_row(['Uptime', uptime, uptime_status])



r = c.post('http://{}/rest/operational-state/show-system-monitor'.format(host_fqdn), data='<show-system-monitor></show-system-monitor>').content
r = ElementTree.fromstring(r)
state = r.find('.//system-monitor:switch-state', ns).text
state = 'OK' if state == 'state-healthy' else 'CRIT'
state_info = r.find('.//system-monitor:switch-state-reason', ns).text
state_info = state_info.rstrip()

system.add_row(['Switch state', state_info, state])

for component in r.findall('.//system-monitor:component-status', ns):
    name = component.find('./system-monitor:component-name', ns).text
    name = name.replace(' monitor', '')
    status_raw = component.find('./system-monitor:component-state', ns).text
    if status_raw == 'state-healthy':
        status = 'OK'
        status_info = ''
        check_status.update(OK)
    else:
        status = 'CRIT'
        status_info = status_raw
        check_status.update(CRIT)
    system.add_row([name, status_info, status])

system = str(system)
system = system.replace('\n', '\n\t')
system = '\t' + system + '\n'
print(system)

print('Virtual Cluster Switch\n')

vcs = PrettyTable()
vcs.field_names = ['item', 'info', 'status']
vcs.header = False
vcs.align = 'l'

r = c.post('http://{}/rest/operational-state/show-vcs'.format(host_fqdn),
           data='<show-vcs></show-vcs>').content
r = ElementTree.fromstring(r)

cluster_generic_status = r.find('.//vcs:cluster-generic-status', ns).text
cluster_specific_status = r.find('.//vcs:cluster-specific-status', ns).text
total_nodes = r.find('.//vcs:total-nodes-in-cluster', ns).text
disconnected_nodes = int(r.find('.//vcs:nodes-disconnected-from-cluster', ns).text)

cluster_status = 'OK' if cluster_generic_status == 'Good' else 'CRIT'
if cluster_status == 'OK':
    check_status.update(OK)
else:
    check_status.update(CRIT)

vcs.add_row(['Cluster Status', cluster_specific_status, cluster_status])
vcs.add_row(['Total Nodes', total_nodes, ''])
vcs.add_row(['Disconnected Nodes', disconnected_nodes, 'CRIT' if disconnected_nodes else 'OK'])

vcs = str(vcs)
vcs = vcs.replace('\n', '\n\t')
vcs = '\t' + vcs + '\n'
print(vcs)


rbridges = PrettyTable()
rbridges.field_names = ['RBridge', 'Name', 'Serial', 'Status', 'Principal', 'Co-Ordinator', 'Firmware', 'Fabric']
rbridges.align = 'l'

for rbridge in r.findall('.//vcs:vcs-node-info', ns):
    rbridge_id = rbridge.find('./vcs:node-rbridge-id', ns).text
    name = rbridge.find('./vcs:node-switchname', ns).text
    serial = rbridge.find('./vcs:node-serial-num', ns).text
    status = rbridge.find('./vcs:node-condition', ns).text
    status2 = rbridge.find('./vcs:node-status', ns).text
    status3 = rbridge.find('./vcs:node-state', ns).text
    is_principal = rbridge.find('./vcs:node-is-principal', ns).text == 'true'
    is_coordinator = rbridge.find('./vcs:co-ordinator', ns).text == 'true'
    firmware = rbridge.find('./vcs:firmware-version', ns).text
    fabric_state = rbridge.find('./vcs:node-fabric-state', ns).text

    rbridges.add_row([rbridge_id, name, serial, '{}, {}, {}'.format(status, status2, status3),
              '*****' if is_principal else '', '*****' if is_coordinator else '', firmware, fabric_state])

rbridges = str(rbridges)
rbridges = rbridges.replace('\n', '\n\t')
rbridges = '\t' + rbridges + '\n'
print(rbridges)

print('Last 10 log messages\n')

log = PrettyTable()
log.field_names = ['time', 'severity', 'type', 'message']
log.header = False
log.align = 'l'
log.sortby = 'time'
log.reversesort = True
log.end = 10

r = c.post('http://{}/rest/operational-state/show-raslog'.format(host_fqdn),
           data='<show-raslog></show-raslog>').content
r = ElementTree.fromstring(r)

for entry in r.findall('.//raslog:raslog-entries', ns):
    time = entry.find('./raslog:date-and-time-info', ns).text
    severity = entry.find('./raslog:severity', ns).text
    type = entry.find('./raslog:log-type', ns).text
    message = entry.find('./raslog:message', ns).text
    message = message.replace('\n.', '')
    if 'Login information: User [user] Last Successful Login Time' in message:
        continue
    log.add_row([time, severity, type, message])

log = str(log)
log = log.replace('\n', '\n\t')
log = '\t' + log+ '\n'
print(log)


print('Last 10 important messages\n')

log = PrettyTable()
log.field_names = ['time', 'severity', 'type', 'message']
log.header = False
log.align = 'l'
log.sortby = 'time'
log.reversesort = True
log.end = 10

for entry in r.findall('.//raslog:raslog-entries', ns):
    time = entry.find('./raslog:date-and-time-info', ns).text
    severity = entry.find('./raslog:severity', ns).text
    if severity in ['warning', 'informational']:
        continue
    type = entry.find('./raslog:log-type', ns).text
    message = entry.find('./raslog:message', ns).text
    message = message.replace('\n.', '')
    log.add_row([time, severity, type, message])

log = str(log)
log = log.replace('\n', '\n\t')
log = '\t' + log+ '\n'
print(log)
print('All times given in {}'.format(LOCAL_TIME))
sys.exit(check_status.status)
