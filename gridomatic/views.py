from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings
from forms import *
from .xen import Xen
import json
import tasks

def vm_list(request):
	return render(request, 'gridomatic/vm_list.html', {'vms': Xen().vm_list()})

def vm_details(request, uuid):
	return render(request, 'gridomatic/vm_details.html', {'details': Xen().vm_details(uuid)})

def vm_edit(request, uuid):
	details = Xen().vm_details(uuid)
	form = VMEditForm(request.POST or None, initial={
		'description': details['name_description'],
		'cpu_cores':   details['VCPUs_at_startup'],
		'mem_size':    int(details['memory_static_max'])/1024/1024,
	})

	if form.is_valid():
		Xen().vm_update(uuid, form.cleaned_data)
		return redirect('vm_details', uuid )

	return render(request, 'gridomatic/vm_edit.html', {'details': details, 'form': form})

def vm_start(request):
	uuid = request.POST.get('uuid', None)
	task_id = tasks.vm_start.delay(uuid).id
	return HttpResponse(json.dumps({'task_id': task_id}), content_type="application/json")

def vm_stop(request):
	uuid = request.POST.get('uuid', None)
	task_id = tasks.vm_stop.delay(uuid).id
	return HttpResponse(json.dumps({'task_id': task_id}), content_type="application/json")

def vm_restart(request):
	uuid = request.POST.get('uuid', None)
	task_id = tasks.vm_restart.delay(uuid).id
	return HttpResponse(json.dumps({'task_id': task_id}), content_type="application/json")

def deploy(name, ip, gw, netmask, ns, network, template, host, ip6, gw6, netmask6, sshkey):
	import subprocess, os
	(name, domain) = name.split('.', 1)

	env = os.environ.copy()
	env['VMNAME']      = name
	env['VMIP']        = ip
	env['VMGW']        = gw
	env['VMMASK']      = netmask
	env['VMNS']        = ns
	env['VMDM']        = domain
	env['VMHOST']      = host
	env['NETWORKUUID'] = network
	env['TMPLUUID']    = template
	env['VMIP6']       = ip6
	env['VMGW6']       = gw6
	env['VMMASK6']     = netmask6
	env['SSHKEY']      = sshkey

	subprocess.Popen(os.path.dirname(os.path.dirname(__file__)) + '/gridomatic/deploy.sh', env=env)


def vm_create(request):
	form = VMCreateForm(request.POST or None)
	x = Xen()
	form.fields['network'].choices  = x.get_network_list()
	form.fields['template'].choices = x.get_template_list()
	form.fields['host'].choices     = x.get_host_list()

	if form.is_valid():
		deploy(
			name     = form.cleaned_data['hostname'],
			ip       = form.cleaned_data['ip_address'],
			gw       = form.cleaned_data['gateway'],
			netmask  = form.cleaned_data['netmask'],
			ns       = form.cleaned_data['dns'],
			network  = form.cleaned_data['network'],
			template = form.cleaned_data['template'],
			host     = form.cleaned_data['host'],
			ip6      = form.cleaned_data['ip_address6'],
			gw6      = form.cleaned_data['gateway6'],
			netmask6 = form.cleaned_data['netmask6'],
			sshkey   = form.cleaned_data['sshkey'],
		)
		return redirect('vm_list')
	return render(request, 'gridomatic/vm_create.html', {'form': form})

def network_list(request):
	network_list = Xen().network_list_dev()
	return render(request, 'gridomatic/network_list.html', {'networks': network_list})

def network_create(request):
	form = NetworkCreateForm(request.POST or None)

	if form.is_valid():
		Xen().network_create(form.cleaned_data)
		return redirect('network_list')
	return render(request, 'gridomatic/network_create.html', {'form': form})
